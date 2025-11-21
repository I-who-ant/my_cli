"""
阶段 28：Task 工具 - 子 Agent 系统

学习目标：
1. 理解子 Agent 的创建和管理
2. 理解 Wire 消息的转发机制
3. 理解 SubagentEvent 的包装

对应源码：kimi-cli-fork/src/kimi_cli/tools/task/__init__.py (186行)
"""

import asyncio
from pathlib import Path
from typing import Any, override

from kosong.tooling import CallableTool2, ToolError, ToolOk, ToolReturnType
from pydantic import BaseModel, Field

from my_cli.agentspec import ResolvedAgentSpec, SubagentSpec
from my_cli.exception import AgentSpecError
from my_cli.soul import MaxStepsReached, get_wire_or_none, run_soul
from my_cli.soul.agent import Agent, load_agent
from my_cli.soul.context import Context
from my_cli.soul.kimisoul import KimiSoul
from my_cli.soul.runtime import Runtime
from my_cli.soul.toolset import get_current_tool_call_or_none
from my_cli.tools.utils import load_desc
from my_cli.utils.logging import logger
from my_cli.utils.message import message_extract_text
from my_cli.utils.path import next_available_rotation
from my_cli.wire import WireMessage, WireUISide
from my_cli.wire.message import ApprovalRequest, SubagentEvent

# Maximum continuation attempts for task summary
MAX_CONTINUE_ATTEMPTS = 1


CONTINUE_PROMPT = """
Your previous response was too brief. Please provide a more comprehensive summary that includes:

1. Specific technical details and implementations
2. Complete code examples if relevant
3. Detailed findings and analysis
4. All important information that should be aware of by the caller
""".strip()


class Params(BaseModel):
    """
    Task 工具参数 ⭐ Stage 28

    对应源码：kimi-cli-fork/src/kimi_cli/tools/task/__init__.py:37-49
    """

    description: str = Field(description="A short (3-5 word) description of the task")
    subagent_name: str = Field(
        description="The name of the specialized subagent to use for this task"
    )
    prompt: str = Field(
        description=(
            "The task for the subagent to perform. "
            "You must provide a detailed prompt with all necessary background information "
            "because the subagent cannot see anything in your context."
        )
    )


class Task(CallableTool2[Params]):
    """
    Task 工具 - 子 Agent 系统 ⭐ Stage 28

    用于创建和管理子 Agent，实现上下文隔离和并行多任务处理。

    对应源码：kimi-cli-fork/src/kimi_cli/tools/task/__init__.py:51-186
    """

    name: str = "Task"
    params: type[Params] = Params

    def __init__(self, agent_spec: ResolvedAgentSpec, runtime: Runtime, **kwargs: Any):
        """
        初始化 Task 工具 ⭐ Stage 28

        Args:
            agent_spec: 已解析的 Agent 规范（包含子 Agent 定义）
            runtime: 运行时（提供 LLM 和 Session）
            **kwargs: 其他参数传给父类

        对应源码：kimi-cli-fork/src/kimi_cli/tools/task/__init__.py:55-79
        """
        super().__init__(
            description=load_desc(
                Path(__file__).parent / "task.md",
                {
                    "SUBAGENTS_MD": "\n".join(
                        f"- `{name}`: {spec.description}"
                        for name, spec in agent_spec.subagents.items()
                    ),
                },
            ),
            **kwargs,
        )

        self._runtime = runtime
        self._session = runtime.session
        self._subagents: dict[str, Agent] = {}

        try:
            loop = asyncio.get_running_loop()
            self._load_task = loop.create_task(self._load_subagents(agent_spec.subagents))
        except RuntimeError:
            # In case there's no running event loop, e.g., during synchronous tests
            self._load_task = None
            asyncio.run(self._load_subagents(agent_spec.subagents))

    async def _load_subagents(self, subagent_specs: dict[str, SubagentSpec]) -> None:
        """
        加载所有子 Agent ⭐ Stage 28

        Args:
            subagent_specs: 子 Agent 规范字典

        对应源码：kimi-cli-fork/src/kimi_cli/tools/task/__init__.py:81-85
        """
        for name, spec in subagent_specs.items():
            agent = await load_agent(spec.path, self._runtime, mcp_configs=[])
            self._subagents[name] = agent

    async def _get_subagent_history_file(self) -> Path:
        """
        生成子 Agent 的历史文件路径 ⭐ Stage 28

        Returns:
            Path: 唯一的历史文件路径

        对应源码：kimi-cli-fork/src/kimi_cli/tools/task/__init__.py:87-96
        """
        main_history_file = self._session.history_file
        subagent_base_name = f"{main_history_file.stem}_sub"
        main_history_file.parent.mkdir(parents=True, exist_ok=True)  # just in case
        sub_history_file = await next_available_rotation(
            main_history_file.parent / f"{subagent_base_name}{main_history_file.suffix}"
        )
        assert sub_history_file is not None
        return sub_history_file

    @override
    async def __call__(self, params: Params) -> ToolReturnType:
        """
        执行 Task 工具 ⭐ Stage 28

        Args:
            params: 工具参数

        Returns:
            ToolReturnType: 子 Agent 的执行结果

        对应源码：kimi-cli-fork/src/kimi_cli/tools/task/__init__.py:98-125
        """
        if self._load_task is not None:
            try:
                await self._load_task
            except AgentSpecError as e:
                logger.exception("Failed to load subagents:")
                return ToolError(
                    message=f"Failed to load subagents: {e}",
                    brief="Failed to load subagents",
                )
            finally:
                self._load_task = None

        if params.subagent_name not in self._subagents:
            return ToolError(
                message=f"Subagent not found: {params.subagent_name}",
                brief="Subagent not found",
            )
        agent = self._subagents[params.subagent_name]
        try:
            result = await self._run_subagent(agent, params.prompt)
            return result
        except Exception as e:
            return ToolError(
                message=f"Failed to run subagent: {e}",
                brief="Failed to run subagent",
            )

    async def _run_subagent(self, agent: Agent, prompt: str) -> ToolReturnType:
        """
        运行子 Agent ⭐ Stage 28

        核心逻辑：
        1. 获取主 Wire 并创建消息转发函数
        2. 创建子 Agent 的 Context 和 KimiSoul
        3. 运行子 Agent 并收集结果
        4. 如果结果太短，尝试继续执行

        Args:
            agent: 子 Agent 实例
            prompt: 任务提示

        Returns:
            ToolReturnType: 子 Agent 的执行结果

        对应源码：kimi-cli-fork/src/kimi_cli/tools/task/__init__.py:127-185
        """
        super_wire = get_wire_or_none()
        assert super_wire is not None
        current_tool_call = get_current_tool_call_or_none()
        assert current_tool_call is not None
        current_tool_call_id = current_tool_call.id

        def _super_wire_send(msg: WireMessage) -> None:
            """
            消息转发函数 ⭐ Stage 28

            将子 Agent 的消息包装为 SubagentEvent 后发送到主 Wire。
            ApprovalRequest 直接转发（不包装）。
            """
            if isinstance(msg, ApprovalRequest):
                super_wire.soul_side.send(msg)
                return

            event = SubagentEvent(
                task_tool_call_id=current_tool_call_id,
                event=msg,
            )
            super_wire.soul_side.send(event)

        async def _ui_loop_fn(wire: WireUISide) -> None:
            """
            子 Agent 的 UI Loop ⭐ Stage 28

            从子 Wire 接收消息并转发到主 Wire。
            """
            while True:
                msg = await wire.receive()
                _super_wire_send(msg)

        subagent_history_file = await self._get_subagent_history_file()
        context = Context(file_backend=subagent_history_file)
        soul = KimiSoul(agent, runtime=self._runtime, context=context)

        try:
            await run_soul(soul, prompt, _ui_loop_fn, asyncio.Event())
        except MaxStepsReached as e:
            return ToolError(
                message=(
                    f"Max steps {e.n_steps} reached when running subagent. "
                    "Please try splitting the task into smaller subtasks."
                ),
                brief="Max steps reached",
            )

        _error_msg = (
            "The subagent seemed not to run properly. Maybe you have to do the task yourself."
        )

        # Check if the subagent context is valid
        if len(context.history) == 0 or context.history[-1].role != "assistant":
            return ToolError(message=_error_msg, brief="Failed to run subagent")

        final_response = message_extract_text(context.history[-1])

        # Check if response is too brief, if so, run again with continuation prompt
        n_attempts_remaining = MAX_CONTINUE_ATTEMPTS
        if len(final_response) < 200 and n_attempts_remaining > 0:
            await run_soul(soul, CONTINUE_PROMPT, _ui_loop_fn, asyncio.Event())

            if len(context.history) == 0 or context.history[-1].role != "assistant":
                return ToolError(message=_error_msg, brief="Failed to run subagent")
            final_response = message_extract_text(context.history[-1])

        return ToolOk(output=final_response)

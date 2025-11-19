"""
阶段 4-8：Soul 模块 - Protocol 定义 + Wire 机制集成 + 工具调用

学习目标：
1. 理解 Protocol（接口）的设计思想
2. 理解为什么要分离接口和实现
3. 使用工厂函数简化创建流程
4. 使用配置文件管理多个 API Provider ⭐
5. 理解 Wire 机制和 run_soul() 架构 ⭐
6. 理解工具系统集成 ⭐ Stage 8

对应源码：kimi-cli-fork/src/kimi_cli/soul/__init__.py

阶段演进：
- Stage 4-5：基础 Soul 引擎 ✅
  * Soul Protocol 协议定义
  * create_soul() 工厂函数（使用配置文件）
  * Agent/Runtime/Context 基础组件
  * kosong.generate() 调用 LLM

- Stage 6：Wire 机制 + 流式输出 ✅
  * 新增 wire_send() 全局函数 ✅
  * 修改 KimiSoul.run() 使用 on_message_part 回调 ✅
  * run_soul() 函数：连接 Soul 和 UI Loop ✅
  * 新增异常类（LLMNotSet, RunCancelled 等）✅

- Stage 7：工具系统基础 ✅
  * 实现 Bash/ReadFile/WriteFile 工具
  * 实现 SimpleToolset 管理器
  * 实现 utils.py（ToolResultBuilder 等）

- Stage 8：工具调用集成 ✅ ⭐
  * 切换到 kosong.step() API
  * KimiSoul 集成 Toolset
  * 实现 Agent 循环（多轮工具调用）
  * create_soul() 传入 Toolset

- Stage 9+：高级特性（待实现）
  * Context 压缩（Compaction）
  * Checkpoint/Rollback 机制
  * 重试机制（tenacity）
  * Approval 系统
"""

from __future__ import annotations

import asyncio
import contextlib
from collections.abc import Callable, Coroutine
from contextvars import ContextVar
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from kosong.chat_provider.kimi import Kimi
from kosong.message import ContentPart
from pydantic import SecretStr

from my_cli.config import LLMModel, LLMProvider, load_config
from my_cli.soul.agent import Agent
# ⭐ 延迟导入 KimiSoul 以避免循环导入（官方做法）
# from my_cli.soul.kimisoul import KimiSoul
from my_cli.soul.runtime import Runtime
from my_cli.wire import Wire, WireMessage, WireUISide

if TYPE_CHECKING:
    from my_cli.llm import LLM, ModelCapability

__all__ = [
    # 核心接口和工厂
    "Soul",
    "create_soul",
    # 异常类（UI 层需要捕获）
    "LLMNotSet",
    "LLMNotSupported",  # ⭐ Stage 16 新增
    "MaxStepsReached",  # ⭐ Stage 16 新增
    "RunCancelled",
    # Wire 机制相关
    "run_soul",
    "wire_send",
    "get_wire_or_none",
    # 类型和数据类
    "StatusSnapshot",
    "UILoopFn",
]

# ============================================================
# Stage 16：异常类定义扩展 ⭐
# ============================================================


class LLMNotSet(Exception):
    """
    LLM 未设置异常

    当尝试调用 LLM 但未配置 API Key 时抛出。

    对应源码：kimi-cli-fork/src/kimi_cli/soul/__init__.py:18-21
    """

    pass


class LLMNotSupported(Exception):
    """
    LLM 不支持所需能力异常 ⭐ Stage 16 新增

    当 LLM 不支持所需的能力（如 image_in, thinking）时抛出。

    对应源码：kimi-cli-fork/src/kimi_cli/soul/__init__.py:24-35
    """

    def __init__(self, llm: LLM, capabilities: list[ModelCapability]):
        """
        初始化异常 ⭐ Stage 17 完整实现（与官方一致）

        Args:
            llm: LLM 对象（包含模型名称和能力信息）
            capabilities: 缺失的能力列表（ModelCapability 类型）

        对应源码：kimi-cli-fork/src/kimi_cli/soul/__init__.py:28-35
        """
        self.llm = llm
        self.capabilities = capabilities
        capabilities_str = "capability" if len(capabilities) == 1 else "capabilities"
        super().__init__(
            f"LLM model '{llm.model_name}' does not support required {capabilities_str}: "
            f"{', '.join(capabilities)}."
        )


class MaxStepsReached(Exception):
    """
    达到最大步数限制异常 ⭐ Stage 16 新增

    当 Agent 循环达到最大步数限制时抛出。

    对应源码：kimi-cli-fork/src/kimi_cli/soul/__init__.py:37-44
    """

    def __init__(self, n_steps: int):
        """
        初始化异常

        Args:
            n_steps: 已执行的步数
        """
        self.n_steps = n_steps
        super().__init__(f"Maximum number of steps reached: {n_steps}")


class RunCancelled(Exception):
    """
    运行取消异常

    当用户取消运行（Ctrl+C）时抛出。

    对应源码：kimi-cli-fork/src/kimi_cli/soul/__init__.py:97-99
    """

    pass


# ============================================================
# Stage 6：数据类定义 ✅
# ============================================================


@dataclass(frozen=True, slots=True)
class StatusSnapshot:
    """
    状态快照 - 记录 Soul 的运行状态

    对应源码：kimi-cli-fork/src/kimi_cli/soul/__init__.py:48-51
    """

    context_usage: float
    """Context 使用率（百分比，0.0-1.0）"""


# ============================================================
# Stage 6：类型定义 ✅
# ============================================================

type UILoopFn = Callable[[WireUISide], Coroutine[Any, Any, None]]
"""
UI Loop 函数类型

这是一个长时间运行的异步函数，用于可视化 Agent 行为。
接收 WireUISide 参数，从 Wire 接收消息并渲染到 UI。

对应源码：kimi-cli-fork/src/kimi_cli/soul/__init__.py:93-94
"""


@runtime_checkable
class Soul(Protocol):
    """
    Soul Protocol - AI Agent 核心引擎的接口定义

    这是一个 Protocol（接口），不是抽象基类！
    任何实现了这些方法的类都自动符合 Soul Protocol。

    对应源码：kimi-cli-main/src/kimi_cli/soul/__init__.py:52-86

    阶段演进：
    - Stage 4-5：基础接口 ✅
      * name: Agent 名称
      * model_name: 模型名称
      * run(): 运行 Agent

    - Stage 16：扩展接口 ⭐ 新增
      * model_capabilities: 模型能力（image_in, thinking）
      * status: 运行状态（context_usage）
      * message_count: 消息计数
    """

    @property
    def name(self) -> str:
        """Agent 的名称"""
        ...

    @property
    def model_name(self) -> str:
        """使用的 LLM 模型名称"""
        ...

    @property
    def model_capabilities(self) -> set[str] | None:
        """
        模型能力集合 ⭐ Stage 16 新增

        可能的能力：
        - "image_in": 支持图片输入
        - "thinking": 支持思考模式

        Returns:
            set[str] | None: 能力集合，None 表示未配置 LLM

        对应源码：kimi-cli-fork/src/kimi_cli/soul/__init__.py:66-69
        """
        ...

    @property
    def status(self) -> StatusSnapshot:
        """
        当前状态快照 ⭐ Stage 16 新增

        Returns:
            StatusSnapshot: 包含 context_usage 等状态信息

        对应源码：kimi-cli-fork/src/kimi_cli/soul/__init__.py:70-73
        """
        ...

    @property
    def message_count(self) -> int:
        """
        消息计数 ⭐ Stage 16 新增

        Returns:
            int: 当前对话轮次数

        对应源码：kimi-cli-fork/src/kimi_cli/soul/__init__.py:82-85
        """
        ...

    async def run(self, user_input: str):
        """
        运行 Agent，处理用户输入

        Stage 4-5：返回 AsyncIterator[str]（简化的流式接口）
        Stage 6：改为 -> None，通过 Wire 发送消息
        """
        ...


def create_soul(
    work_dir: Path,
    agent_name: str = "MyCLI Assistant",
    model_name: str | None = None,
    config_file: Path | None = None,
) -> KimiSoul:
    """
    便捷工厂函数 - 创建 KimiSoul 实例（使用配置文件）

    Stage 4-5 实现：
    - 从配置文件加载 Provider 和 Model
    - 创建 Agent/Runtime/KimiSoul
    - 使用 kosong.generate() 调用 LLM

    Stage 8 实现：⭐
    - 创建 SimpleToolset 并注册工具
    - KimiSoul 集成 Toolset
    - 使用 kosong.step() 支持工具调用

    Stage 9+ 补充：
    - 传入 MCP 配置（mcp_configs）
    - 传入 Session（会话管理）
    - 创建 Context 并恢复历史
    - 集成 Approval 系统

    Args:
        work_dir: 工作目录
        agent_name: Agent 名称
        model_name: 模型名称（None 则使用配置文件中的 default_model）
        config_file: 配置文件路径（None 则使用默认路径 .mycli_config.json）

    Returns:
        KimiSoul: 配置好的 Soul 实例

    Raises:
        ValueError: 如果配置文件无效或模型不存在

    对应源码：kimi-cli-fork/src/kimi_cli/app.py:26-121
    """
    # ⭐ 延迟导入 KimiSoul 以避免循环导入
    from my_cli.soul.kimisoul import KimiSoul

    # ============================================================
    # Stage 4-5：基础实现 ✅
    # Stage 19.1：对齐官方架构 ⭐
    # ============================================================

    # 1. 加载配置文件
    config = load_config(config_file)

    # 2. 从 config 中获取 Provider 和 Model 配置 ⭐ Stage 19.1
    model: LLMModel | None = None
    provider: LLMProvider | None = None

    # 尝试使用配置文件
    if not model_name and config.default_model:
        # 没有指定 model_name 且配置文件中有 default_model
        model = config.models[config.default_model]
        provider = config.providers[model.provider]
    if model_name and model_name in config.models:
        # 指定了 model_name 且模型在配置文件中
        model = config.models[model_name]
        provider = config.providers[model.provider]

    if not model:
        # 创建默认 model 和 provider（等待环境变量覆盖）
        model = LLMModel(provider="", model="", max_context_size=100_000)
        provider = LLMProvider(type="kimi", base_url="", api_key=SecretStr(""))

    # 3. 应用环境变量覆盖 ⭐ Stage 19.1
    from my_cli.llm import augment_provider_with_env_vars

    env_overrides = augment_provider_with_env_vars(provider, model)

    # 4. 创建 Agent
    agent = Agent(
        name=agent_name,
        work_dir=work_dir,
    )

    # ============================================================
    # Stage 17：使用 create_llm() 创建 LLM ⭐
    # ============================================================

    # 5. 创建 LLM（使用 create_llm() 工厂函数）⭐ Stage 17
    from my_cli.llm import create_llm

    llm = create_llm(
        provider=provider,
        model=model,
        stream=True,
        session_id=None,  # Stage 17+：传入 session.id
    )

    # 6. 创建 Runtime（传入 LLM）⭐ Stage 17
    runtime = Runtime(
        llm=llm,  # ⭐ Stage 17：传入 LLM 而不是 ChatProvider
        max_steps=20,
    )

    # ============================================================
    # Stage 8：工具系统集成 ⭐
    # ============================================================

    # 7. 创建 SimpleToolset
    from my_cli.tools.toolset import SimpleToolset

    toolset = SimpleToolset()  # ⭐ SimpleToolset 自动注册 Bash/ReadFile/WriteFile

    # 8. 创建 KimiSoul（传入 toolset）⭐
    soul = KimiSoul(
        agent=agent,
        runtime=runtime,
        toolset=toolset,  # ⭐ Stage 8：传入工具集
    )

    return soul

    # ============================================================
    # TODO: Stage 6+ 完整实现（参考官方）
    # ============================================================
    # 官方参考：kimi-cli-fork/src/kimi_cli/app.py:26-121
    #
    # Stage 6+ 需要添加：
    #
    # 1. Session 管理：
    #    session = Session.create(work_dir) or Session.continue_(work_dir)
    #    context = Context(session.history_file)
    #    await context.restore()
    #
    # 2. MCP 工具系统（Stage 7）：
    #    mcp_configs: list[dict[str, Any]] | None = None
    #    agent = await load_agent(agent_file, runtime, mcp_configs=mcp_configs or [])
    #
    # 3. Approval 系统（Stage 8+）：
    #    yolo: bool = False  # 是否自动批准所有操作
    #    runtime = await Runtime.create(config, llm, session, yolo)
    #
    # 4. Thinking 模式（Stage 8+）：
    #    thinking: bool = False
    #    if thinking and llm:
    #        soul.set_thinking(True)
    #
    # 5. 完整的 KimiSoul 创建：
    #    soul = KimiSoul(agent, runtime, context=context)
    #
    # 完整伪代码：
    #
    # async def create_soul(
    #     work_dir: Path,
    #     agent_name: str = "MyCLI Assistant",
    #     model_name: str | None = None,
    #     config_file: Path | None = None,
    #     session: Session | None = None,  # Stage 6+
    #     yolo: bool = False,              # Stage 8+
    #     thinking: bool = False,          # Stage 8+
    #     mcp_configs: list[dict] | None = None,  # Stage 7+
    # ) -> KimiSoul:
    #     # 加载配置
    #     config = load_config(config_file)
    #     provider, model = get_provider_and_model(config, model_name)
    #
    #     # 创建 Session（Stage 6+）
    #     if session is None:
    #         session = Session.create(work_dir)
    #
    #     # 创建 LLM
    #     llm = create_llm(provider, model, stream=True, session_id=session.id)
    #
    #     # 创建 Runtime（Stage 8+ 支持 Approval）
    #     runtime = await Runtime.create(config, llm, session, yolo)
    #
    #     # 加载 Agent（Stage 7+ 支持 MCP 工具）
    #     agent = await load_agent(DEFAULT_AGENT_FILE, runtime, mcp_configs=mcp_configs or [])
    #
    #     # 恢复 Context（Stage 6+）
    #     context = Context(session.history_file)
    #     await context.restore()
    #
    #     # 创建 KimiSoul
    #     soul = KimiSoul(agent, runtime, context=context)
    #
    #     # 设置 Thinking 模式（Stage 8+）
    #     if thinking:
    #         soul.set_thinking(True)
    #
    #     return soul
    # ============================================================


# ============================================================
# Stage 6：Wire 机制核心函数 ✅
# ============================================================

# ContextVar: 线程安全的全局变量（用于异步环境）
_current_wire = ContextVar[Wire | None]("current_wire", default=None)
"""
当前 Wire 的 ContextVar

ContextVar 是 Python 3.7+ 提供的线程安全的上下文变量：
- 每个异步任务有独立的上下文副本
- 不会在并发任务间互相干扰
- 非常适合在 asyncio 环境中传递"全局"状态

对应源码：kimi-cli-fork/src/kimi_cli/soul/__init__.py:164
"""


def get_wire_or_none() -> Wire | None:
    """
    获取当前 Wire（如果存在）

    Returns:
        Wire | None: 当前 Wire，如果不在 Soul 运行中则返回 None

    使用场景：
    - 在 Agent 循环中获取 Wire 并发送消息

    对应源码：kimi-cli-fork/src/kimi_cli/soul/__init__.py:167-172
    """
    return _current_wire.get()


def wire_send(msg: WireMessage) -> None:
    """
    发送消息到当前 Wire

    这是 Soul 层的"print"和"input"函数！
    Soul 应该始终使用这个函数发送 Wire 消息。

    Args:
        msg: 要发送的消息（Event 类型）

    Raises:
        AssertionError: 如果 Wire 未设置（应该在 Soul 运行时才调用）

    使用示例：
        # 发送文本片段（流式输出）
        wire_send(ContentPart(text="你好"))

        # 发送步骤开始事件
        wire_send(StepBegin(n=1))

    对应源码：kimi-cli-fork/src/kimi_cli/soul/__init__.py:175-183
    """
    wire = get_wire_or_none()
    assert wire is not None, "Wire is expected to be set when soul is running"
    wire.soul_side.send(msg)


async def run_soul(
    soul: Soul,
    user_input: str | list[ContentPart],
    ui_loop_fn: UILoopFn,
    cancel_event: asyncio.Event,
) -> None:
    """
    运行 Soul 并连接到 UI Loop（通过 Wire）

    这是 Wire 机制的核心函数！
    它创建 Wire，启动 Soul 和 UI Loop，并处理取消事件。

    流程：
    1. 创建 Wire 并设置到 ContextVar
    2. 启动 UI Loop 任务（接收 Wire 消息）
    3. 启动 Soul 任务（处理用户输入）
    4. 等待 Soul 完成或取消事件
    5. 关闭 Wire 并等待 UI Loop 退出

    Args:
        soul: Soul 实例
        user_input: 用户输入（字符串或 ContentPart 列表）
        ui_loop_fn: UI Loop 函数（接收 WireUISide）
        cancel_event: 取消事件（用户按 Ctrl+C 时设置）

    Raises:
        LLMNotSet: LLM 未配置
        RunCancelled: 用户取消运行

    使用示例：
        # 创建取消事件
        cancel_event = asyncio.Event()

        # 定义 UI Loop
        async def print_ui_loop(wire_ui: WireUISide):
            while True:
                msg = await wire_ui.receive()
                # 渲染消息...

        # 运行 Soul
        await run_soul(soul, "你好", print_ui_loop, cancel_event)

    对应源码：kimi-cli-fork/src/kimi_cli/soul/__init__.py:101-161
    """
    # 1. 创建 Wire 并设置到 ContextVar
    wire = Wire()
    wire_token = _current_wire.set(wire)

    # 2. 启动 UI Loop 任务
    ui_task = asyncio.create_task(ui_loop_fn(wire.ui_side))

    # 3. 启动 Soul 任务
    soul_task = asyncio.create_task(soul.run(user_input)) #

    # 4. 等待 Soul 完成或取消事件（哪个先完成就处理哪个）
    cancel_event_task = asyncio.create_task(cancel_event.wait())
    await asyncio.wait(
        [soul_task, cancel_event_task],
        return_when=asyncio.FIRST_COMPLETED, #
    )

    try:
        # 5a. 如果是取消事件，取消 Soul 任务
        if cancel_event.is_set():
            soul_task.cancel()
            try:
                await soul_task
            except asyncio.CancelledError:
                raise RunCancelled from None
        # 5b. 如果 Soul 完成，取消取消事件任务
        else:
            assert soul_task.done()
            cancel_event_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await cancel_event_task
            soul_task.result()  # 如果 Soul 抛异常，这里会重新抛出
    finally:
        # 6. 关闭 Wire（会导致 UI Loop 退出）
        wire.shutdown()
        try:
            await asyncio.wait_for(ui_task, timeout=0.5)
        except asyncio.QueueShutDown:
            # UI Loop 正常退出
            pass
        except TimeoutError:
            # UI Loop 超时（可能卡住了）
            pass
        finally:
            # 7. 重置 ContextVar
            _current_wire.reset(wire_token)


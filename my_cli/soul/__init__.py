"""
阶段 4-5：Soul 模块 - Protocol 定义 + 便捷工厂函数

学习目标：
1. 理解 Protocol（接口）的设计思想
2. 理解为什么要分离接口和实现
3. 使用工厂函数简化创建流程
4. 使用配置文件管理多个 API Provider ⭐

对应源码：kimi-cli-main/src/kimi_cli/soul/__init__.py

阶段演进：
- Stage 4-5：基础 Soul 引擎 ✅
  * Soul Protocol 协议定义
  * create_soul() 工厂函数（使用配置文件）
  * Agent/Runtime/Context 基础组件
  * kosong.generate() 调用 LLM

- Stage 6：Wire 机制 + 流式输出（待实现）
  * 新增 wire_send() 全局函数
  * 修改 KimiSoul.run() 使用 on_message_part 回调
  * run_soul() 函数：连接 Soul 和 UI Loop
  * 新增 Wire 类（消息队列）

- Stage 7：工具系统（待实现）
  * Agent 集成 Toolset
  * 切换到 kosong.step() 支持工具调用
  * 实现 Shell/ReadFile/WriteFile 工具

- Stage 8+：高级特性（待实现）
  * Context 压缩（Compaction）
  * Checkpoint/Rollback 机制
  * 重试机制（tenacity）
  * Approval 系统
"""

from pathlib import Path
from typing import Protocol, runtime_checkable

from kosong.chat_provider.kimi import Kimi

from my_cli.config import get_provider_and_model, load_config
from my_cli.soul.agent import Agent
from my_cli.soul.kimisoul import KimiSoul
from my_cli.soul.runtime import Runtime

__all__ = [
    "Soul",
    "create_soul",
]


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

    - Stage 6+：扩展接口（待实现）
      * model_capabilities: 模型能力（image_in, thinking）
      * status: 运行状态（context_usage）
      * set_thinking(): 启用/禁用思考模式
    """

    @property
    def name(self) -> str:
        """Agent 的名称"""
        ...

    @property
    def model_name(self) -> str:
        """使用的 LLM 模型名称"""
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

    Stage 6+ 补充：
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

    对应源码：kimi-cli-main/src/kimi_cli/app.py:26-121
    """
    # ============================================================
    # Stage 4-5：基础实现 ✅
    # ============================================================

    # 1. 加载配置文件
    config = load_config(config_file)

    # 2. 获取 Provider 和 Model 配置
    provider, model = get_provider_and_model(config, model_name)

    # 3. 创建 Agent
    agent = Agent(
        name=agent_name,
        work_dir=work_dir,
    )

    # 4. 创建 ChatProvider
    # Stage 4-5: 只支持 Kimi Provider
    # Stage 6+: 根据 provider.type 选择不同的 ChatProvider
    chat_provider = Kimi(
        base_url=provider.base_url,
        api_key=provider.api_key.get_secret_value(),
        model=model.model,
    )

    # 5. 创建 Runtime
    runtime = Runtime(
        chat_provider=chat_provider,
        max_steps=20,
    )

    # 6. 创建 KimiSoul
    soul = KimiSoul(
        agent=agent,
        runtime=runtime,
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

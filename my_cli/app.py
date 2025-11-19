"""
App - 应用层框架

学习目标：
1. 理解应用类的职责（协调 Session、Runtime、Soul）
2. 理解配置管理
3. 理解依赖注入模式

对应源码：kimi-cli-fork/src/kimi_cli/app.py

阶段演进：
- Stage 2-3：基础应用框架 ✅
- Stage 4-5：Soul 引擎集成 ✅
- Stage 18：Session 管理集成 ⭐ 完整实现
- Stage 18+：完整应用层
"""

from __future__ import annotations

import contextlib
import os
import warnings
from collections.abc import Generator
from pathlib import Path
from typing import Any

from pydantic import SecretStr

from my_cli.agentspec import DEFAULT_AGENT_FILE
from my_cli.config import LLMModel, LLMProvider, load_config
from my_cli.llm import augment_provider_with_env_vars, create_llm
from my_cli.session import Session
from my_cli.share import get_share_dir
from my_cli.soul import LLMNotSet, LLMNotSupported
from my_cli.soul.context import Context
from my_cli.soul.kimisoul import KimiSoul
from my_cli.soul.runtime import Runtime
from my_cli.utils.logging import StreamToLogger, logger
from my_cli.utils.path import shorten_home


def enable_logging(debug: bool = False) -> None:
    """启用日志系统 ⭐ Stage 18

    Args:
        debug: 是否启用调试模式

    对应源码：kimi-cli-fork/src/kimi_cli/app.py:27-36
    """
    if debug:
        logger.enable("kosong")
    logger.add(
        get_share_dir() / "logs" / "kimi.log",
        level="TRACE" if debug else "INFO",
        rotation="06:00",
        retention="10 days",
    )


class MyCLI:
    """My CLI 应用类 ⭐ Stage 18 完整实现

    职责：
    - 管理 Session（会话持久化）
    - 协调 Runtime（运行时）
    - 管理 KimiSoul（AI 引擎）
    - 提供 UI 入口点

    对应源码：kimi-cli-fork/src/kimi_cli/app.py:39-116
    """

    @staticmethod
    async def create(
        session: Session,
        *,
        yolo: bool = False,
        mcp_configs: list[dict[str, Any]] | None = None,
        config_file: Path | None = None,
        model_name: str | None = None,
        thinking: bool = False,
        agent_file: Path | None = None,
    ) -> "MyCLI":
        """
        创建 MyCLI 实例 ⭐ Stage 18 完整实现

        这是应用的主要工厂方法，负责：
        1. 加载配置
        2. 创建 LLM 客户端
        3. 创建 Runtime
        4. 加载 Agent 规范
        5. 创建并恢复 Context
        6. 创建 KimiSoul

        Args:
            session: Session 实例（通过 Session.create() 或 Session.continue_() 创建）
            yolo: 是否自动批准所有操作（无确认模式）
            mcp_configs: MCP 工具配置列表
            config_file: 配置文件路径
            model_name: 模型名称
            thinking: 是否启用思考模式
            agent_file: Agent 规范文件路径

        Returns:
            MyCLI: 应用实例

        Raises:
            FileNotFoundError: Agent 文件不存在
            ConfigError: 配置无效
            AgentSpecError: Agent 规范无效

        对应源码：kimi-cli-fork/src/kimi_cli/app.py:40-116
        """
        # 1. 加载配置
        config = load_config(config_file)
        logger.info("Loaded config: {config}", config=config)

        model: LLMModel | None = None
        provider: LLMProvider | None = None

        # 尝试使用配置文件中的设置
        if not model_name and config.default_model:
            # 未指定 --model && 配置中有默认模型
            model = config.models[config.default_model]
            provider = config.providers[model.provider]
        if model_name and model_name in config.models:
            # 指定了 --model && 模型在配置中
            model = config.models[model_name]
            provider = config.providers[model.provider]

        if not model:
            # 使用默认的空配置（将抛出 LLMNotSet 异常）
            model = LLMModel(provider="", model="", max_context_size=100_000)
            provider = LLMProvider(type="kimi", base_url="", api_key=SecretStr(""))

        # 2. 环境变量覆盖
        assert provider is not None
        assert model is not None
        env_overrides = augment_provider_with_env_vars(provider, model)

        # 3. 创建 LLM 客户端
        if not provider.base_url or not model.model:
            llm = None
        else:
            logger.info("Using LLM provider: {provider}", provider=provider)
            logger.info("Using LLM model: {model}", model=model)
            llm = create_llm(provider, model, session_id=session.id)

        # 4. 创建 Runtime
        runtime = await Runtime.create(config, llm, session, yolo)

        # 5. 加载 Agent 规范
        # TODO: Stage 18+ 实现完整的 load_agent 函数
        # if agent_file is None:
        #     agent_file = DEFAULT_AGENT_FILE
        # from my_cli.soul.agent import load_agent
        # agent = await load_agent(agent_file, runtime, mcp_configs=mcp_configs or [])
        # 临时使用简化实现
        from my_cli.soul.agent import Agent
        agent = Agent(
            name="MyCLI Assistant",
            work_dir=runtime.session.work_dir,
        )

        # 6. 创建并恢复 Context
        context = Context(session.history_file)
        await context.restore()

        # 7. 创建 KimiSoul
        soul = KimiSoul(
            agent,
            runtime,
            context=context,
        )
        try:
            soul.set_thinking(thinking)
        except (LLMNotSet, LLMNotSupported) as e:
            logger.warning("Failed to enable thinking mode: {error}", error=e)

        return MyCLI(soul, runtime, env_overrides)

    def __init__(
        self,
        _soul: KimiSoul,
        _runtime: Runtime,
        _env_overrides: dict[str, str],
    ) -> None:
        """初始化 MyCLI 实例（私有）"""
        self._soul = _soul
        self._runtime = _runtime
        self._env_overrides = _env_overrides

    @property
    def soul(self) -> KimiSoul:
        """获取 KimiSoul 实例"""
        return self._soul

    @property
    def session(self) -> Session:
        """获取 Session 实例"""
        return self._runtime.session

    @contextlib.contextmanager
    def _app_env(self) -> Generator[None]:
        """应用环境上下文管理器

        负责：
        1. 切换到工作目录
        2. 重定向 stderr 到日志
        3. 忽略弃用警告

        对应源码：kimi-cli-fork/src/kimi_cli/app.py:138-148
        """
        original_cwd = Path.cwd()
        os.chdir(self._runtime.session.work_dir)
        try:
            # 忽略 dateparser 的弃用警告
            warnings.filterwarnings("ignore", category=DeprecationWarning)
            with contextlib.redirect_stderr(StreamToLogger()):
                yield
        finally:
            os.chdir(original_cwd)

    async def run_shell_mode(self, command: str | None = None) -> bool:
        """运行 Shell 模式 ⭐ Stage 18 简化版

        TODO Stage 19+: 添加 WelcomeInfoItem 支持

        对应源码：kimi-cli-fork/src/kimi_cli/app.py:150-201
        """
        from my_cli.ui.shell import ShellApp

        # TODO: Stage 19+ 添加欢迎信息（WelcomeInfoItem）
        # 目前简化版不显示欢迎信息

        # 运行 Shell App
        with self._app_env():
            app = ShellApp(self._soul)
            return await app.run(command)

    async def run_print_mode(self, command: str | None) -> None:
        """运行 Print 模式 ⭐ Stage 18

        对应源码：kimi-cli-fork/src/kimi_cli/app.py:150+
        """
        with self._app_env():
            await self._soul.run_print_mode(command)

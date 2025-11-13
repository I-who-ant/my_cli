"""
阶段 4-5：Soul 模块 - Protocol 定义 + 便捷工厂函数

学习目标：
1. 理解 Protocol（接口）的设计思想
2. 理解为什么要分离接口和实现
3. 使用工厂函数简化创建流程
4. 使用配置文件管理多个 API Provider ⭐

对应源码：kimi-cli-main/src/kimi_cli/soul/__init__.py
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

    对应源码：kimi-cli-main/src/kimi_cli/soul/__init__.py:52-86
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
        """运行 Agent，处理用户输入"""
        ...


def create_soul(
    work_dir: Path,
    agent_name: str = "MyCLI Assistant",
    model_name: str | None = None,
    config_file: Path | None = None,
) -> KimiSoul:
    """
    便捷工厂函数 - 创建 KimiSoul 实例（使用配置文件）

    Args:
        work_dir: 工作目录
        agent_name: Agent 名称
        model_name: 模型名称（None 则使用配置文件中的 default_model）
        config_file: 配置文件路径（None 则使用默认路径 .mycli_config.json）

    Returns:
        KimiSoul: 配置好的 Soul 实例

    Raises:
        ValueError: 如果配置文件无效或模型不存在
    """
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

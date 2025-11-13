"""
阶段 4-5：Runtime 类

学习目标：
1. 理解 Runtime 的职责（管理运行时配置）
2. 理解 ChatProvider 的封装

对应源码：kimi-cli-main/src/kimi_cli/soul/runtime.py
"""

from kosong.chat_provider import ChatProvider


class Runtime:
    """
    Runtime - 运行时配置和状态

    职责：
    - 管理 ChatProvider（LLM 客户端）
    - 管理运行时参数（max_steps 等）

    对应源码：kimi-cli-main/src/kimi_cli/soul/runtime.py
    """

    def __init__(
        self,
        chat_provider: ChatProvider,
        max_steps: int = 20,
    ):
        self.chat_provider = chat_provider
        self.max_steps = max_steps

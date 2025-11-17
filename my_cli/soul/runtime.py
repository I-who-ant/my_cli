"""
阶段 4-5：Runtime 类

学习目标：
1. 理解 Runtime 的职责（管理运行时配置）
2. 理解 ChatProvider 的封装

对应源码：kimi-cli-main/src/kimi_cli/soul/runtime.py

阶段演进：
- Stage 4-16：使用 ChatProvider ✅
- Stage 17：使用 LLM（封装 ChatProvider + max_context_size + capabilities）⭐ 当前
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from my_cli.llm import LLM


class Runtime:
    """
    Runtime - 运行时配置和状态 ⭐ Stage 17 更新

    职责：
    - 管理 LLM（统一的 LLM 接口）⭐ Stage 17
    - 管理运行时参数（max_steps 等）

    对应源码：kimi-cli-main/src/kimi_cli/soul/runtime.py
    """

    def __init__(
        self,
        llm: "LLM",  # ⭐ Stage 17：改为 LLM
        max_steps: int = 20,
    ):
        """
        初始化 Runtime

        Args:
            llm: LLM 实例（封装了 ChatProvider、max_context_size、capabilities）⭐ Stage 17
            max_steps: 最大步数
        """
        self.llm = llm
        self.max_steps = max_steps

    # ============================================================
    # Stage 17-：兼容性属性（保持向后兼容）
    # ============================================================
    # 官方参考：kimi-cli-fork/src/kimi_cli/soul/runtime.py
    #
    # 为了保持向后兼容，添加 chat_provider 属性：
    # @property
    # def chat_provider(self) -> ChatProvider:
    #     return self.llm.chat_provider
    # ============================================================

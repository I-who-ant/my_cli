"""
阶段 4-5：Context 类

学习目标：
1. 理解 Context 的职责（管理对话历史）
2. 理解 kosong.Message 的使用

对应源码：kimi-cli-main/src/kimi_cli/soul/context.py

阶段演进：
- Stage 4-5：基础 Context（消息历史管理）✅
- Stage 16：新增 token_count 属性 ⭐ 当前
"""

from kosong.message import Message


class Context:
    """
    Context - 对话上下文管理

    职责：
    - 管理消息历史
    - 提供格式化的消息列表
    - 追踪 token 使用量 ⭐ Stage 16 新增

    对应源码：kimi-cli-main/src/kimi_cli/soul/context.py
    """

    def __init__(self):
        self.messages: list[Message] = []
        self._token_count: int = 0  # ⭐ Stage 16: 追踪 token 数量

    async def append_message(self, message: Message) -> None:
        """添加消息到上下文"""
        self.messages.append(message)

    def get_messages(self) -> list[Message]:
        """获取所有消息"""
        return self.messages.copy()

    def clear(self) -> None:
        """清空上下文"""
        self.messages = []
        self._token_count = 0  # ⭐ Stage 16: 清空时重置 token 计数

    def __len__(self) -> int:
        """返回消息数量"""
        return len(self.messages)

    # ============================================================
    # Stage 16：Token 计数支持 ⭐
    # ============================================================

    @property
    def token_count(self) -> int:
        """
        获取当前 Context 的 token 数量 ⭐ Stage 16

        Returns:
            int: token 数量

        官方实现：
        - 从历史文件中读取 {"role": "_usage", "token_count": xxx}
        - 通过 LLM API 响应更新（kosong.StepResult.usage）

        简化版实现：
        - 初始为 0
        - 通过 update_token_count() 手动更新
        - 估算：每条消息约 500 tokens（简化）

        对应源码：kimi-cli-fork/src/kimi_cli/soul/context.py:57-58
        """
        return self._token_count

    async def update_token_count(self, token_count: int) -> None:
        """
        更新 token 计数 ⭐ Stage 16

        Args:
            token_count: 新的 token 计数

        官方实现：
        - 写入历史文件：{"role": "_usage", "token_count": xxx}
        - 由 LLM API 响应自动更新

        简化版实现：
        - 直接更新内存中的 _token_count
        - 不持久化（Stage 17+ 可扩展）

        对应源码：kimi-cli-fork/src/kimi_cli/soul/context.py:139-144
        """
        self._token_count = token_count

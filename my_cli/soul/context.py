"""
阶段 4-5：Context 类

学习目标：
1. 理解 Context 的职责（管理对话历史）
2. 理解 kosong.Message 的使用

对应源码：kimi-cli-main/src/kimi_cli/soul/context.py
"""

from kosong.message import Message


class Context:
    """
    Context - 对话上下文管理

    职责：
    - 管理消息历史
    - 提供格式化的消息列表

    对应源码：kimi-cli-main/src/kimi_cli/soul/context.py
    """

    def __init__(self):
        self.messages: list[Message] = []

    async def append_message(self, message: Message) -> None:
        """添加消息到上下文"""
        self.messages.append(message)

    def get_messages(self) -> list[Message]:
        """获取所有消息"""
        return self.messages.copy()

    def clear(self) -> None:
        """清空上下文"""
        self.messages = []

    def __len__(self) -> int:
        """返回消息数量"""
        return len(self.messages)

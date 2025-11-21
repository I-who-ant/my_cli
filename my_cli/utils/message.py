"""
阶段 28：消息工具函数

学习目标：
1. 理解 Message 对象的结构
2. 提取消息中的文本内容

对应源码：kimi-cli-fork/src/kimi_cli/utils/message.py
"""

from __future__ import annotations

from kosong.message import Message, TextPart


def message_extract_text(message: Message) -> str:
    """
    从 Message 中提取文本内容 ⭐ Stage 28

    Args:
        message: 消息对象

    Returns:
        str: 提取的文本内容

    对应源码：kimi-cli-fork/src/kimi_cli/utils/message.py:6-10
    """
    if isinstance(message.content, str):
        return message.content
    return "\n".join(part.text for part in message.content if isinstance(part, TextPart))


def message_stringify(message: Message) -> str:
    """
    获取消息的字符串表示 ⭐ Stage 28

    Args:
        message: 消息对象

    Returns:
        str: 消息的字符串表示

    对应源码：kimi-cli-fork/src/kimi_cli/utils/message.py:13-24
    """
    parts: list[str] = []
    if isinstance(message.content, str):
        parts.append(message.content)
    else:
        for part in message.content:
            if isinstance(part, TextPart):
                parts.append(part.text)
            else:
                parts.append(f"[{part.type}]")
    return "".join(parts)

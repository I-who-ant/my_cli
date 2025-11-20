"""
Context 压缩 - 减少 token 使用

学习目标：
1. 理解为什么需要 Context 压缩
2. 理解压缩策略（保留重要消息）
3. 理解如何使用 LLM 生成摘要

对应源码：kimi-cli-fork/src/kimi_cli/soul/compaction.py

阶段演进：
- Stage 8-18：不需要（简化版）✅
- Stage 19：实现 Context 压缩 ⭐

背景：
当 Context 中的消息过多时，token 使用量会快速增长。
Context 压缩通过：
1. 保留系统消息和最近的消息
2. 使用 LLM 生成中间消息的摘要
3. 用摘要替换原始消息
来减少 token 使用。
"""

from __future__ import annotations

from collections.abc import Sequence
from string import Template
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from kosong import generate
from kosong.message import ContentPart, Message, TextPart

import my_cli.prompts as prompts
from my_cli.llm import LLM
from my_cli.soul.message import system
from my_cli.utils.logging import logger


@runtime_checkable
class Compaction(Protocol):
    """压缩协议

    定义 Context 压缩的接口。

    对应源码：kimi-cli-fork/src/kimi_cli/soul/compaction.py:16-32
    """

    async def compact(self, messages: Sequence[Message], llm: LLM) -> Sequence[Message]:
        """
        压缩消息列表

        Args:
            messages (Sequence[Message]): 要压缩的消息列表
            llm (LLM): 用于压缩的 LLM 实例

        Returns:
            Sequence[Message]: 压缩后的消息列表

        Raises:
            ChatProviderError: LLM API 错误
        """
        ...


class SimpleCompaction(Compaction):
    """简单压缩策略

    保留最近 N 条消息，将旧消息压缩为摘要。

    对应源码：kimi-cli-fork/src/kimi_cli/soul/compaction.py:35-102
    """

    MAX_PRESERVED_MESSAGES = 2
    """保留的最近消息数量"""

    async def compact(self, messages: Sequence[Message], llm: LLM) -> Sequence[Message]:
        """压缩消息列表 ⭐ Stage 19

        流程：
        1. 从后往前查找，保留最近 MAX_PRESERVED_MESSAGES 条 user/assistant 消息
        2. 将之前的旧消息发送给 LLM 生成摘要
        3. 用摘要消息替换旧消息
        4. 返回：摘要消息 + 保留的最近消息

        Args:
            messages: 要压缩的消息列表
            llm: 用于生成摘要的 LLM

        Returns:
            压缩后的消息列表

        对应源码：kimi-cli-fork/src/kimi_cli/soul/compaction.py:38-102
        """
        history = list(messages)
        if not history:
            return history

        # 1. 从后往前找，保留最近的 user/assistant 消息
        preserve_start_index = len(history)
        n_preserved = 0
        for index in range(len(history) - 1, -1, -1):
            if history[index].role in {"user", "assistant"}:
                n_preserved += 1
                if n_preserved == self.MAX_PRESERVED_MESSAGES:
                    preserve_start_index = index
                    break

        if n_preserved < self.MAX_PRESERVED_MESSAGES:
            # 消息不够多，不需要压缩
            return history

        to_compact = history[:preserve_start_index]
        to_preserve = history[preserve_start_index:]

        if not to_compact:
            # 没有需要压缩的消息
            return to_preserve

        # 2. 将旧消息转换为字符串
        history_text = "\n\n".join(
            f"## Message {i + 1}\nRole: {msg.role}\nContent: {msg.content}"
            for i, msg in enumerate(to_compact)
        )

        # 3. 构建压缩提示词
        compact_template = Template(prompts.COMPACT)
        compact_prompt = compact_template.substitute(CONTEXT=history_text)

        # 4. 创建输入消息
        compact_message = Message(role="user", content=compact_prompt)

        # 5. 调用 LLM 生成摘要
        logger.debug("Compacting context...")
        result = await generate(
            chat_provider=llm.chat_provider,
            system_prompt="You are a helpful assistant that compacts conversation context.",
            tools=[],
            history=[compact_message],
        )
        if result.usage:
            logger.debug(
                "Compaction used {input} input tokens and {output} output tokens",
                input=result.usage.input,
                output=result.usage.output,
            )

        # 6. 构建压缩后的消息
        content: list[ContentPart] = [
            system("Previous context has been compacted. Here is the compaction output:")
        ]
        compacted_msg = result.message
        content.extend(
            [TextPart(text=compacted_msg.content)]
            if isinstance(compacted_msg.content, str)
            else compacted_msg.content
        )
        compacted_messages: list[Message] = [Message(role="assistant", content=content)]
        compacted_messages.extend(to_preserve)
        return compacted_messages


if TYPE_CHECKING:

    def type_check(simple: SimpleCompaction):
        _: Compaction = simple

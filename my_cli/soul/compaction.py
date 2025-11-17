"""
Context 压缩 - 减少 token 使用

学习目标：
1. 理解为什么需要 Context 压缩
2. 理解压缩策略（保留重要消息）
3. 理解如何使用 LLM 生成摘要

对应源码：kimi-cli-fork/src/kimi_cli/soul/compaction.py

阶段演进：
- Stage 8-18：不需要（简化版）✅
- Stage 19：实现 Context 压缩 ⭐ TODO

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

from kosong.message import Message


# ============================================================
# 压缩策略常量 ⭐ Stage 19
# ============================================================

# 压缩触发阈值（Context 使用率）
COMPACTION_THRESHOLD = 0.8  # 80%

# 压缩目标（压缩后的 Context 使用率）
COMPACTION_TARGET = 0.5  # 50%

# 保留最近的消息数量
KEEP_RECENT_MESSAGES = 10


# ============================================================
# 核心函数 ⭐ Stage 19
# ============================================================


async def compact_messages(
    messages: Sequence[Message],
    target_count: int,
) -> Sequence[Message]:
    """
    压缩消息列表 ⭐ Stage 19

    官方实现要点：
    1. 保留系统消息（第一条）
    2. 保留最近的 N 条消息
    3. 将中间的消息发送给 LLM 生成摘要
    4. 用摘要消息替换中间消息

    Args:
        messages: 原始消息列表
        target_count: 目标消息数量

    Returns:
        Sequence[Message]: 压缩后的消息列表

    对应源码：kimi-cli-fork/src/kimi_cli/soul/compaction.py
    """
    # ============================================================
    # TODO: Stage 19 完整实现（参考官方）
    # ============================================================
    # 官方实现伪代码：
    #
    # if len(messages) <= target_count:
    #     return messages
    #
    # # 1. 分离消息
    # system_messages = [messages[0]]  # 第一条系统消息
    # recent_messages = messages[-KEEP_RECENT_MESSAGES:]  # 最近的消息
    # middle_messages = messages[1:-KEEP_RECENT_MESSAGES]  # 中间的消息
    #
    # # 2. 使用 LLM 生成摘要
    # summary_prompt = f"Summarize the following messages:\n{middle_messages}"
    # summary = await llm.generate(summary_prompt)
    #
    # # 3. 创建摘要消息
    # summary_message = Message(
    #     role="assistant",
    #     content=[TextPart(text=f"<summary>{summary}</summary>")]
    # )
    #
    # # 4. 组合消息
    # return system_messages + [summary_message] + recent_messages
    # ============================================================

    # 简化版（Stage 8-18）：不压缩，直接返回
    return messages


# ============================================================
# TODO: Stage 19+ 完整功能（参考官方）
# ============================================================
# 官方参考：kimi-cli-fork/src/kimi_cli/soul/compaction.py
#
# Stage 19（Context 压缩）需要：
# 1. 在 KimiSoul 中添加 compact_context() 方法
# 2. 在 _agent_loop() 开始前检查 Context 使用率
# 3. 如果使用率超过阈值，调用 compact_context()
# 4. 发送 CompactionBegin 和 CompactionEnd Wire 事件
# 5. 在 Context 中实现 compact() 方法
#
# 压缩策略：
# - 保留系统消息（第一条）
# - 保留最近 N 条消息
# - 压缩中间消息为摘要
#
# Stage 20+ 扩展：
# - 更智能的压缩策略（保留重要工具调用）
# - 使用专门的摘要模型（更便宜）
# - 压缩历史持久化
# ============================================================

"""
异常定义

对应源码：kimi-cli-fork/src/kimi_cli/exception.py

阶段演进：
- Stage 16：基础异常（LLMNotSet, LLMNotSupported, MaxStepsReached）✅
- Stage 19：新增 BackToTheFuture（时间旅行）⭐ TODO
"""

from __future__ import annotations

# ============================================================
# Stage 16 已实现的异常（在 soul/__init__.py）
# ============================================================
# - LLMNotSet
# - LLMNotSupported
# - MaxStepsReached
# - RunCancelled

# ============================================================
# TODO: Stage 19+ 新增异常（参考官方）
# ============================================================
# 官方参考：kimi-cli-fork/src/kimi_cli/exception.py
#
# Stage 19（时间旅行）需要：
#
# from collections.abc import Sequence
# from kosong.message import Message
#
# class BackToTheFuture(Exception):
#     """时间旅行异常（D-Mail 触发的 Checkpoint 回滚）"""
#
#     def __init__(self, checkpoint_id: int, messages: Sequence[Message]):
#         self.checkpoint_id = checkpoint_id
#         self.messages = messages
#         super().__init__(f"Back to checkpoint {checkpoint_id}")
# ============================================================

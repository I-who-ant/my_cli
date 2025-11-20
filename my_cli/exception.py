"""
异常定义 ⭐ Stage 19.1 对齐官方

对应源码：kimi-cli-fork/src/kimi_cli/exception.py

阶段演进：
- Stage 16：基础异常（LLMNotSet, LLMNotSupported, MaxStepsReached）✅
- Stage 19.1：异常体系对齐官方（KimiCLIException, ConfigError）✅
- Stage 19+：新增 BackToTheFuture（时间旅行）⭐ TODO
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
# Stage 19.1：异常基类 ⭐ 对齐官方
# ============================================================


class KimiCLIException(Exception):
    """
    Kimi CLI 异常基类 ⭐ Stage 19.1

    所有自定义异常都继承此类

    对应源码：kimi-cli-fork/src/kimi_cli/exception.py:4-7
    """

    pass


class ConfigError(KimiCLIException):
    """
    配置错误 ⭐ Stage 19.1

    配置文件格式错误、验证失败等

    对应源码：kimi-cli-fork/src/kimi_cli/exception.py:10-13
    """

    pass


class AgentSpecError(KimiCLIException):
    """
    Agent 规范错误 ⭐ Stage 18

    Agent 规范文件格式错误、缺少必需字段等

    对应源码：kimi-cli-fork/src/kimi_cli/exception.py:16-19
    """

    pass


# ============================================================
# Stage 19：时间旅行异常 ⭐
# ============================================================

from collections.abc import Sequence

from kosong.message import Message


class BackToTheFuture(Exception):
    """时间旅行异常 ⭐ Stage 19

    当 D-Mail 被发送时抛出，触发 Context 回滚到指定检查点。

    Attributes:
        checkpoint_id: 目标检查点 ID
        messages: 要添加到目标检查点的消息列表

    对应源码：kimi-cli-fork/src/kimi_cli/exception.py（未找到官方实现，参考文档）
    """

    def __init__(self, checkpoint_id: int, messages: Sequence[Message]):
        self.checkpoint_id = checkpoint_id
        self.messages = messages
        super().__init__(f"Back to checkpoint {checkpoint_id}")

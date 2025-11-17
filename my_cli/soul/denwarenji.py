"""
DenwaRenji - 时间旅行 D-Mail 系统

学习目标：
1. 理解 D-Mail（时间旅行消息）机制
2. 理解 Checkpoint 和 D-Mail 的配合
3. 理解如何发送消息回到过去

对应源码：kimi-cli-fork/src/kimi_cli/soul/denwarenji.py

阶段演进：
- Stage 8-16：不需要（简化版）✅
- Stage 19：实现 DenwaRenji 系统 ⭐ TODO

背景故事：
DenwaRenji（電話レンジ，电话微波炉）来自动画《命运石之门》，
是可以向过去发送信息的装置。这里用于 Agent 向过去的 Checkpoint 发送消息。
"""

from __future__ import annotations

from pydantic import BaseModel, Field


# ============================================================
# DMail - 时间旅行消息 ⭐ Stage 19
# ============================================================


class DMail(BaseModel):
    """
    D-Mail - 发送到过去的消息 ⭐ Stage 19

    这个类定义了时间旅行消息的格式。
    Agent 可以通过 SendDMail 工具向过去的 Checkpoint 发送消息。

    属性：
        message: 要发送的消息内容
        checkpoint_id: 目标 Checkpoint 的 ID（从 0 开始）

    对应源码：kimi-cli-fork/src/kimi_cli/soul/denwarenji.py:6-10
    """

    message: str = Field(description="The message to send.")
    checkpoint_id: int = Field(description="The checkpoint to send the message back to.", ge=0)
    # TODO: Stage 20+ 扩展 - 支持恢复文件系统状态


# ============================================================
# DenwaRenjiError - 异常类 ⭐ Stage 19
# ============================================================


class DenwaRenjiError(Exception):
    """
    DenwaRenji 错误 ⭐ Stage 19

    当 D-Mail 发送失败时抛出。

    可能的错误：
    - 同时发送多个 D-Mail
    - Checkpoint ID 为负数
    - Checkpoint ID 超出范围

    对应源码：kimi-cli-fork/src/kimi_cli/soul/denwarenji.py:13-14
    """

    pass


# ============================================================
# DenwaRenji - 时间旅行管理器 ⭐ Stage 19
# ============================================================


class DenwaRenji:
    """
    DenwaRenji - 时间旅行 D-Mail 系统 ⭐ Stage 19

    这个类管理 D-Mail 的发送和接收。

    官方实现要点：
    1. 维护 _pending_dmail（待处理的 D-Mail）
    2. 维护 _n_checkpoints（Checkpoint 数量）
    3. send_dmail() - 发送 D-Mail（由 SendDMail 工具调用）
    4. fetch_pending_dmail() - 获取待处理的 D-Mail（由 Soul 调用）
    5. set_n_checkpoints() - 设置 Checkpoint 数量（由 Soul 调用）

    使用流程：
    1. Soul 创建 Checkpoint 时调用 set_n_checkpoints()
    2. Agent 调用 SendDMail 工具
    3. SendDMail 工具调用 denwa_renji.send_dmail()
    4. Soul 在 _step() 中调用 fetch_pending_dmail()
    5. 如果有待处理的 D-Mail，抛出 BackToTheFuture 异常
    6. Soul 回滚到目标 Checkpoint 并添加 D-Mail 消息

    对应源码：kimi-cli-fork/src/kimi_cli/soul/denwarenji.py:17-39
    """

    def __init__(self):
        """
        初始化 DenwaRenji

        官方实现：
        - _pending_dmail: DMail | None = None
        - _n_checkpoints: int = 0
        """
        self._pending_dmail: DMail | None = None
        self._n_checkpoints: int = 0

    def send_dmail(self, dmail: DMail):
        """
        发送 D-Mail ⭐ Stage 19

        这个方法由 SendDMail 工具调用。

        Args:
            dmail: 要发送的 D-Mail

        Raises:
            DenwaRenjiError: 如果已有待处理的 D-Mail
            DenwaRenjiError: 如果 checkpoint_id 无效

        对应源码：kimi-cli-fork/src/kimi_cli/soul/denwarenji.py:21-28
        """
        # ============================================================
        # TODO: Stage 19 完整实现（参考官方）
        # ============================================================
        # 官方实现：
        #
        # if self._pending_dmail is not None:
        #     raise DenwaRenjiError("Only one D-Mail can be sent at a time")
        # if dmail.checkpoint_id < 0:
        #     raise DenwaRenjiError("The checkpoint ID can not be negative")
        # if dmail.checkpoint_id >= self._n_checkpoints:
        #     raise DenwaRenjiError("There is no checkpoint with the given ID")
        # self._pending_dmail = dmail
        # ============================================================
        pass  # 简化版（Stage 8-18）：不实现

    def set_n_checkpoints(self, n_checkpoints: int):
        """
        设置 Checkpoint 数量 ⭐ Stage 19

        这个方法由 Soul 调用（在创建 Checkpoint 后）。

        Args:
            n_checkpoints: Checkpoint 数量

        对应源码：kimi-cli-fork/src/kimi_cli/soul/denwarenji.py:30-32
        """
        # ============================================================
        # TODO: Stage 19 完整实现（参考官方）
        # ============================================================
        # 官方实现：
        # self._n_checkpoints = n_checkpoints
        # ============================================================
        pass  # 简化版（Stage 8-18）：不实现

    def fetch_pending_dmail(self) -> DMail | None:
        """
        获取待处理的 D-Mail ⭐ Stage 19

        这个方法由 Soul 在 _step() 中调用。

        Returns:
            DMail | None: 待处理的 D-Mail，如果没有则返回 None

        对应源码：kimi-cli-fork/src/kimi_cli/soul/denwarenji.py:34-37
        """
        # ============================================================
        # TODO: Stage 19 完整实现（参考官方）
        # ============================================================
        # 官方实现：
        # pending_dmail = self._pending_dmail
        # self._pending_dmail = None
        # return pending_dmail
        # ============================================================
        return None  # 简化版（Stage 8-18）：永远返回 None


# ============================================================
# TODO: Stage 19+ 完整功能（参考官方）
# ============================================================
# 官方参考：kimi-cli-fork/src/kimi_cli/soul/denwarenji.py
#
# Stage 19（DenwaRenji 系统）需要：
# 1. 在 KimiSoul.__init__() 中创建 DenwaRenji 实例
# 2. 在 _checkpoint() 中调用 set_n_checkpoints()
# 3. 在 _step() 中调用 fetch_pending_dmail()
# 4. 如果有待处理的 D-Mail，抛出 BackToTheFuture 异常
# 5. 在 run() 中捕获 BackToTheFuture 异常并回滚
#
# Stage 20+ 扩展：
# - 支持恢复文件系统状态到 Checkpoint
# - SendDMail 工具实现（在 tools/ 目录）
# ============================================================

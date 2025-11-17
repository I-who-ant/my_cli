"""
阶段 6-7：Wire 消息类型定义

学习目标：
1. 理解 Wire 消息系统的类型设计
2. 理解控制流事件（Control Flow Events）
3. 理解工具调用消息流（ToolCall → ToolResult）

对应源码：kimi-cli-fork/src/kimi_cli/wire/message.py

阶段演进：
- Stage 6：基础消息类型 ✅
  * StepBegin/StepInterrupted（步骤控制）
  * ContentPart/ToolCall（来自 kosong）
  * Event 联合类型

- Stage 7：工具系统消息 ✅
  * ToolResult（工具返回结果）- 从 kosong.tooling 导入
  * ToolCallPart（工具调用片段）- 从 kosong.message 导入

- Stage 16：状态更新消息 ⭐ 当前
  * StatusUpdate（状态更新事件）

- Stage 17+：高级消息类型（待实现）
  * CompactionBegin/CompactionEnd（Context 压缩）
  * ApprovalRequest（批准请求）
  * SubagentEvent（子 Agent 事件）
"""

from __future__ import annotations

from kosong.message import ContentPart, ToolCall, ToolCallPart
from kosong.tooling import ToolResult
from pydantic import BaseModel

# ⭐ 官方实现：直接导入 StatusSnapshot（不使用 TYPE_CHECKING）
# 参考：kimi-cli-fork/src/kimi_cli/wire/message.py:13
from my_cli.soul import StatusSnapshot


# ============================================================
# Stage 6：基础控制流事件 ✅
# ============================================================


class StepBegin(BaseModel):
    """
    步骤开始事件

    在每个 Agent 步骤开始时发送。
    这是 Agent 循环的核心控制消息。

    对应源码：kimi-cli-fork/src/kimi_cli/wire/message.py:16-24
    """

    n: int
    """步骤编号（从 1 开始）"""


class StepInterrupted(BaseModel):
    """
    步骤中断事件

    在步骤被中断时发送（用户取消或发生错误）。
    UI 层收到此消息后应停止接收 Wire 消息。

    对应源码：kimi-cli-fork/src/kimi_cli/wire/message.py:26-29
    """

    pass


# ============================================================
# Stage 16：状态更新事件 ⭐
# ============================================================


class StatusUpdate(BaseModel):
    """
    状态更新事件 ⭐ Stage 16

    当 Soul 状态发生变化时发送（例如 token_count 更新后）。
    UI 层收到后可以更新状态栏显示。

    对应源码：kimi-cli-fork/src/kimi_cli/wire/message.py:52-54
    """

    status: StatusSnapshot  # ⭐ 官方：直接使用类型，不是字符串
    """Soul 的当前状态快照"""


# ============================================================
# Stage 16：事件类型定义扩展 ⭐
# ============================================================

# 控制流事件（Stage 16 新增 StatusUpdate）
type ControlFlowEvent = StepBegin | StepInterrupted | StatusUpdate  # ⭐ 新增 StatusUpdate
"""控制流事件：步骤控制、状态更新等"""

# Event 联合类型（Stage 6-7-16）
type Event = ControlFlowEvent | ContentPart | ToolCall | ToolCallPart | ToolResult
"""
所有事件类型的联合

Stage 6 包含：
- ControlFlowEvent: StepBegin, StepInterrupted
- ContentPart: 来自 kosong（文本、图片等内容片段）
- ToolCall: 来自 kosong（完整的工具调用）
- ToolCallPart: 来自 kosong（工具调用的流式片段）

Stage 7 新增：
- ToolResult: 工具执行结果 ⭐

Stage 16 新增：
- StatusUpdate: 状态更新（context_usage 等）⭐

Stage 17+ 扩展：
- CompactionBegin/CompactionEnd: Context 压缩控制
- SubagentEvent: 子 Agent 事件
"""

# WireMessage 联合类型（Stage 6 简化版）
type WireMessage = Event
"""
Wire 上传输的所有消息类型

Stage 6: 只包含 Event
Stage 8+: 添加 ApprovalRequest（批准请求）
"""


# ============================================================
# TODO: Stage 7+ 完整消息类型（参考官方）
# ============================================================
# 官方参考：kimi-cli-fork/src/kimi_cli/wire/message.py:32-201
#
# Stage 7（工具系统）需要添加：
#
# from kosong.tooling import ToolResult
#
# # 扩展 Event 类型
# type Event = ControlFlowEvent | ContentPart | ToolCall | ToolCallPart | ToolResult
#
#
# Stage 8+（高级特性）需要添加：
#
# import uuid
# from enum import Enum
# from typing import Any
# from pydantic import Field
# from kimi_cli.soul import StatusSnapshot
#
# class CompactionBegin(BaseModel):
#     """Context 压缩开始事件"""
#     pass
#
# class CompactionEnd(BaseModel):
#     """Context 压缩结束事件"""
#     pass
#
# class StatusUpdate(BaseModel):
#     """状态更新事件"""
#     status: StatusSnapshot
#
# class SubagentEvent(BaseModel):
#     """子 Agent 事件（Task 工具）"""
#     task_tool_call_id: str
#     event: Event
#
# type ControlFlowEvent = (
#     StepBegin | StepInterrupted |
#     CompactionBegin | CompactionEnd |
#     StatusUpdate
# )
#
# type Event = (
#     ControlFlowEvent |
#     ContentPart | ToolCall | ToolCallPart | ToolResult |
#     SubagentEvent
# )
#
# class ApprovalResponse(Enum):
#     """批准响应类型"""
#     APPROVE = "approve"
#     APPROVE_FOR_SESSION = "approve_for_session"
#     REJECT = "reject"
#
# class ApprovalRequest(BaseModel):
#     """批准请求（需要用户确认的操作）"""
#     id: str = Field(default_factory=lambda: str(uuid.uuid4()))
#     tool_call_id: str
#     sender: str
#     action: str
#     description: str
#
#     def __init__(self, **kwargs: Any) -> None:
#         super().__init__(**kwargs)
#         self._future = asyncio.Future[ApprovalResponse]()
#
#     async def wait(self) -> ApprovalResponse:
#         return await self._future
#
#     def resolve(self, response: ApprovalResponse) -> None:
#         self._future.set_result(response)
#
#     @property
#     def resolved(self) -> bool:
#         return self._future.done()
#
# type WireMessage = Event | ApprovalRequest
#
#
# def serialize_event(event: Event) -> dict[str, Any]:
#     """序列化事件为 JSON（用于 stream-json 输出格式）"""
#     # 详细实现见官方源码
#     pass
# ============================================================
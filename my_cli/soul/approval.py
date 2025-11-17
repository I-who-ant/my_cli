"""
Approval 系统 - 工具执行前的用户批准

学习目标：
1. 理解为什么需要 Approval 系统（安全性）
2. 理解 YOLO 模式（自动批准）
3. 理解批准请求队列和响应机制

对应源码：kimi-cli-fork/src/kimi_cli/soul/approval.py

��段演进：
- Stage 8-18：不需要（简化版）✅
- Stage 20：实现 Approval 系统 ⭐ TODO

背景：
某些工具操作可能有风险（删除文件、执行命令等），
需要在执行前获得用户批准。

Approval 系统提供：
1. 批准请求��列（工具请求批准）
2. 批准响应机制（用户批准/拒绝）
3. YOLO 模式（自动批准所有操作）
4. 会话级自动批准（同一会话中自动批准相同操作）
"""

from __future__ import annotations

import asyncio

from my_cli.soul.toolset import get_current_tool_call_or_none


# ============================================================
# Approval 类 ⭐ Stage 20
# ============================================================


class Approval:
    """
    Approval 系统 - 管理工具执行前的用户批准 ⭐ Stage 20

    官方实现要点：
    1. 维护批准请求队列（_request_queue）
    2. 支持 YOLO 模式（_yolo）
    3. 支持会话级自动批准（_auto_approve_actions）
    4. request() 方法（工具调用）
    5. fetch_request() 方法（Soul 调用）

    使用流程：
    1. 工具调用 approval.request(sender, action, description)
    2. Approval 将请求放入队列
    3. Soul 通过 _pipe_approval_to_wire() 将请求发送到 Wire
    4. UI 层显示批准请求并等待用户响应
    5. 用户批准/拒绝后，响应返回给工具
    6. 工具根据响应决定是否继续执行

    对应源码：kimi-cli-fork/src/kimi_cli/soul/approval.py:9-75
    """

    def __init__(self, yolo: bool = False):
        """
        初始化 Approval 系统

        Args:
            yolo: 是否启用 YOLO 模式（自动批准所有操作）

        官方实现：
        - _request_queue: asyncio.Queue[ApprovalRequest]
        - _yolo: bool
        - _auto_approve_actions: set[str]��会话级自动批准）
        """
        self._request_queue: asyncio.Queue = asyncio.Queue()
        self._yolo = yolo
        self._auto_approve_actions: set[str] = set()
        """会话级自动批准的操作集合（TODO: 持久化）"""

    def set_yolo(self, yolo: bool) -> None:
        """
        设置 YOLO 模式 ⭐ Stage 20

        Args:
            yolo: 是否启用 YOLO 模式

        对应源码：kimi-cli-fork/src/kimi_cli/soul/approval.py:15-16
        """
        self._yolo = yolo

    async def request(self, sender: str, action: str, description: str) -> bool:
        """
        请求批准 ⭐ Stage 20

        这个方法由工具调用（在 __call__ 方法中）。

        Args:
            sender: 发送者名称（工具名称）
            action: 操作名称（用于自动批准识别）
            description: 操作描述（显示给用户）

        Returns:
            bool: True 表示批准，False 表示拒绝

        Raises:
            RuntimeError: 如果不在工具调用上下文中

        使用示例：
            class DeleteFileTool:
                def __init__(self, approval: Approval):
                    self.approval = approval

                async def __call__(self, file_path: str) -> str:
                    approved = await self.approval.request(
                        sender="DeleteFile",
                        action="delete_file",
                        description=f"Delete file: {file_path}"
                    )
                    if not approved:
                        return "User rejected the operation"
                    # 执行删除操作...

        对应源码：kimi-cli-fork/src/kimi_cli/soul/approval.py:18-67
        """
        # ============================================================
        # TODO: Stage 20 完整实现（参考官方）
        # ============================================================
        # 官方实现：
        #
        # # 1. 获取当前��具调用
        # tool_call = get_current_tool_call_or_none()
        # if tool_call is None:
        #     raise RuntimeError("Approval must be requested from a tool call.")
        #
        # # 2. 检查 YOLO 模式
        # if self._yolo:
        #     return True
        #
        # # 3. 检查会话级自动批准
        # if action in self._auto_approve_actions:
        #     return True
        #
        # # 4. 创建批准请求
        # from my_cli.wire.message import ApprovalRequest
        # request = ApprovalRequest(
        #     tool_call_id=tool_call.id,
        #     sender=sender,
        #     action=action,
        #     description=description,
        # )
        #
        # # 5. 放入队列
        # self._request_queue.put_nowait(request)
        #
        # # 6. 等待响应
        # response = await request.wait()
        #
        # # 7. 处理响应
        # from my_cli.wire.message import ApprovalResponse
        # match response:
        #     case ApprovalResponse.APPROVE:
        #         return True
        #     case ApprovalResponse.APPROVE_FOR_SESSION:
        #         self._auto_approve_actions.add(action)
        #         return True
        #     case ApprovalResponse.REJECT:
        #         return False
        # ============================================================

        # 简化版（Stage 8-19）：永远批准
        return True

    async def fetch_request(self):
        """
        获取批准请求 ⭐ Stage 20

        这个方法由 Soul 在 _pipe_approval_to_wire() 中调用。

        Returns:
            ApprovalRequest: 批准请求

        对应源码：kimi-cli-fork/src/kimi_cli/soul/approval.py:69-72
        """
        # ============================================================
        # TODO: Stage 20 完整实现（参考官方）
        # ============================================================
        # 官方实现：
        # return await self._request_queue.get()
        # ============================================================

        # 简化版（Stage 8-19）：永远不返回请求
        await asyncio.sleep(float("inf"))  # 永远等待


# ============================================================
# TODO: Stage 20+ 完整功能（参考官方）
# ============================================================
# 官方参考：kimi-cli-fork/src/kimi_cli/soul/approval.py
#
# Stage 20（Approval 系统）需要：
# 1. 在 Runtime 中创建 Approval 实例
# 2. 在需要批准的工具中注入 Approval
# 3. 在 KimiSoul._agent_loop() 中启动 _pipe_approval_to_wire() 任务
# 4. 实现 ApprovalRequest 和 ApprovalResponse Wire 消息
# 5. 在 UI 层处理批准请求
#
# _pipe_approval_to_wire() 伪代码：
# async def _pipe_approval_to_wire():
#     while True:
#         request = await self._runtime.approval.fetch_request()
#         wire_send(request)
#
# Wire 消息类型（在 wire/message.py）：
# class ApprovalRequest(BaseModel):
#     id: str
#     tool_call_id: str
#     sender: str
#     action: str
#     description: str
#     _future: asyncio.Future[ApprovalResponse]
#
#     async def wait(self) -> ApprovalResponse:
#         return await self._future
#
#     def resolve(self, response: ApprovalResponse):
#         self._future.set_result(response)
#
# class ApprovalResponse(Enum):
#     APPROVE = "approve"
#     APPROVE_FOR_SESSION = "approve_for_session"
#     REJECT = "reject"
#
# Stage 21+ 扩展：
# - 持久化 _auto_approve_actions
# - 更细粒度的批准控制（基于参数）
# - 批准历史记录
# ============================================================

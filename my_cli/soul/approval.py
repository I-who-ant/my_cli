"""
Approval 系统 - 工具执行前的用户批准 ⭐ Stage 24

学习目标：
1. 理解为什么需要 Approval 系统（安全性）
2. 理解 YOLO 模式（自动批准）
3. 理解批准请求队列和响应机制

对应源码：kimi-cli-fork/src/kimi_cli/soul/approval.py

阶段演进：
- Stage 8-18：不需要（简化版）✅
- Stage 24：完整实现 Approval 系统 ⭐

背景：
某些工具操作可能有风险（删除文件、执行命令等），
需要在执行前获得用户批准。

Approval 系统提供：
1. 批准请求队列（工具请求批准）
2. 批准响应机制（用户批准/拒绝）
3. YOLO 模式（自动批准所有操作）
4. 会话级自动批准（同一会话中自动批准相同操作）
"""

from __future__ import annotations

import asyncio

from my_cli.soul.toolset import get_current_tool_call_or_none
from my_cli.utils.logging import logger
from my_cli.wire.message import ApprovalRequest, ApprovalResponse


class Approval:
    """
    Approval 系统 - 管理工具执行前的用户批准 ⭐ Stage 24

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

    对应源码：kimi-cli-fork/src/kimi_cli/soul/approval.py:10-76
    """

    def __init__(self, yolo: bool = False):
        """
        初始化 Approval 系统

        Args:
            yolo: 是否启用 YOLO 模式（自动批准所有操作）

        官方实现：
        - _request_queue: asyncio.Queue[ApprovalRequest]
        - _yolo: bool
        - _auto_approve_actions: set[str]（会话级自动批准）
        """
        self._request_queue: asyncio.Queue[ApprovalRequest] = asyncio.Queue()
        self._yolo = yolo
        self._auto_approve_actions: set[str] = set()
        """会话级自动批准的操作集合（TODO: 持久化）"""

    def set_yolo(self, yolo: bool) -> None:
        """
        设置 YOLO 模式 ⭐ Stage 24

        Args:
            yolo: 是否启用 YOLO 模式

        对应源码：kimi-cli-fork/src/kimi_cli/soul/approval.py:17-18
        """
        self._yolo = yolo

    async def request(self, sender: str, action: str, description: str) -> bool:
        """
        请求批准 ⭐ Stage 24 完整实现

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

        对应源码：kimi-cli-fork/src/kimi_cli/soul/approval.py:20-70
        """
        # 1. 获取当前工具调用
        tool_call = get_current_tool_call_or_none()
        if tool_call is None:
            raise RuntimeError("Approval must be requested from a tool call.")

        logger.debug(
            "{tool_name} ({tool_call_id}) requesting approval: {action} {description}",
            tool_name=tool_call.function.name,
            tool_call_id=tool_call.id,
            action=action,
            description=description,
        )

        # 2. 检查 YOLO 模式
        if self._yolo:
            return True

        # 3. 检查会话级自动批准
        if action in self._auto_approve_actions:
            return True

        # 4. 创建批准请求
        request = ApprovalRequest(
            tool_call_id=tool_call.id,
            sender=sender,
            action=action,
            description=description,
        )

        # 5. 放入队列
        self._request_queue.put_nowait(request)

        # 6. 等待响应
        response = await request.wait()
        logger.debug("Received approval response: {response}", response=response)

        # 7. 处理响应
        match response:
            case ApprovalResponse.APPROVE:
                return True
            case ApprovalResponse.APPROVE_FOR_SESSION:
                self._auto_approve_actions.add(action)
                return True
            case ApprovalResponse.REJECT:
                return False

        return False  # 默认拒绝（防御性编程）

    async def fetch_request(self) -> ApprovalRequest:
        """
        获取批准请求 ⭐ Stage 24 完整实现

        这个方法由 Soul 在 _pipe_approval_to_wire() 中调用。

        Returns:
            ApprovalRequest: 批准请求

        对应源码：kimi-cli-fork/src/kimi_cli/soul/approval.py:72-76
        """
        return await self._request_queue.get()
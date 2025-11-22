"""
阶段 6：Wire 消息队列系统

学习目标：
1. 理解 asyncio.Queue 的使用
2. 理解生产者-消费者模式
3. 理解 Soul 和 UI 的解耦设计

对应源码：kimi-cli-fork/src/kimi_cli/wire/__init__.py (83 行)

阶段演进：
- Stage 6：基础 Wire 系统 ✅
  * Wire 类（消息队列封装）
  * WireSoulSide（Soul 层发送消息）
  * WireUISide（UI 层接收消息）
  * 异步消息传递

Wire 机制的核心思想：
┌─────────────┐                    ┌─────────────┐
│   Soul 层   │                    │   UI 层     │
│             │                    │             │
│  kosong     │    Wire Queue      │  Shell UI   │
│  generate() │ ═══════════════>   │  Print UI   │
│             │  on_message_part   │  ACP Server │
│             │                    │             │
└─────────────┘                    └─────────────┘

优势：
1. 解耦：Soul 不需要知道 UI 的具体实现
2. 异步：UI 可以实时接收流式消息
3. 灵活：支持多种 UI（Shell/Print/ACP/Wire）
4. 中断：支持用户取消（Ctrl+C）
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from kosong.message import ContentPart, ToolCallPart

from my_cli.utils.logging import logger

if TYPE_CHECKING:
    from my_cli.wire.message import ApprovalRequest, Event

# WireMessage 类型定义（与 message.py 保持一致）
type WireMessage = Event | ApprovalRequest  # type: ignore

__all__ = [
    "Wire",
    "WireSoulSide",
    "WireUISide",
    "WireMessage",
]


class Wire:
    """
    Wire - Soul 和 UI 之间的通信通道

    Wire 使用 asyncio.Queue 实现异步消息传递：
    - Soul 层通过 soul_side.send() 发送消息
    - UI 层通过 ui_side.receive() 接收消息
    - 消息按发送顺序传递（FIFO）

    对应源码：kimi-cli-fork/src/kimi_cli/wire/__init__.py:18-39

    使用示例：
        wire = Wire()

        # Soul 层发送消息
        wire.soul_side.send(StepBegin(n=1))
        wire.soul_side.send(TextPart(text="你好"))

        # UI 层接收消息
        msg = await wire.ui_side.receive()
    """

    def __init__(self):
        """初始化 Wire（创建消息队列）"""
        self._queue = asyncio.Queue[WireMessage]()
        self._soul_side = WireSoulSide(self._queue)
        self._ui_side = WireUISide(self._queue)

    @property
    def soul_side(self) -> WireSoulSide:
        """获取 Soul 侧接口（用于发送消息）"""
        return self._soul_side

    @property
    def ui_side(self) -> WireUISide:
        """获取 UI 侧接口（用于接收消息）"""
        return self._ui_side

    def shutdown(self) -> None:
        """
        关闭 Wire（停止消息队列）

        调用后：
        - send() 会静默失败
        - receive() 会抛出 asyncio.QueueShutDown
        """
        self._queue.shutdown()


class WireSoulSide:
    """
    Wire 的 Soul 侧接口（生产者）

    Soul 层通过这个接口发送消息到 UI 层。

    对应源码：kimi-cli-fork/src/kimi_cli/wire/__init__.py:41-56
    """

    def __init__(self, queue: asyncio.Queue[WireMessage]):
        self._queue = queue

    def send(self, msg: WireMessage) -> None:
        """
        发送消息到 Wire

        Args:
            msg: 要发送的消息（Event 类型）

        注意：
        - 此方法是同步的（不阻塞）
        - 如果队列已关闭，静默失败（不抛异常）
        - ContentPart 和 ToolCallPart 不打印日志（数量太多）
        """
        if not isinstance(msg, ContentPart | ToolCallPart):
            logger.debug("Sending wire message: {msg}", msg=msg)
        try:
            self._queue.put_nowait(msg)
        except asyncio.QueueShutDown:
            logger.info("Failed to send wire message, queue is shut down: {msg}", msg=msg)


class WireUISide:
    """
    Wire 的 UI 侧接口（消费者）

    UI 层通过这个接口从 Soul 层接收消息。

    对应源码：kimi-cli-fork/src/kimi_cli/wire/__init__.py:58-83
    """

    def __init__(self, queue: asyncio.Queue[WireMessage]):
        self._queue = queue

    async def receive(self) -> WireMessage:
        """
        接收一条消息（异步等待）

        Returns:
            WireMessage: 接收到的消息

        Raises:
            asyncio.QueueShutDown: 如果队列已关闭

        注意：
        - 此方法会阻塞，直到有消息或队列关闭
        """
        msg = await self._queue.get()
        if not isinstance(msg, ContentPart | ToolCallPart):
            logger.debug("Receiving wire message: {msg}", msg=msg)
        return msg

    def receive_nowait(self) -> WireMessage | None:
        """
        尝试接收一条消息（不等待）

        Returns:
            WireMessage | None: 接收到的消息，或 None（无消息）

        注意：
        - 此方法不阻塞
        - 如果没有消息，立即返回 None
        """
        try:
            msg = self._queue.get_nowait()
        except asyncio.QueueEmpty:
            return None
        if not isinstance(msg, ContentPart | ToolCallPart):
            logger.debug("Receiving wire message: {msg}", msg=msg)
        return msg

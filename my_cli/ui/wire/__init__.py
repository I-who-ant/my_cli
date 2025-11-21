"""
Wire 协议 UI 层 ⭐ Stage 29

提供基于 JSON-RPC 的 stdio Wire 服务器，
用于 IDE 插件（如 VSCode、JetBrains）集成。

功能：
- JSON-RPC 2.0 协议通信
- Soul 运行管理（run/interrupt）
- 事件推送（event notification）
- Approval 请求/响应处理

对应源码：kimi-cli-fork/src/kimi_cli/ui/wire/__init__.py
"""

from __future__ import annotations

import asyncio
import contextlib
import json
from collections.abc import Awaitable, Callable
from typing import Any, Literal

import acp  # pyright: ignore[reportMissingTypeStubs]
from kosong.chat_provider import ChatProviderError
from pydantic import ValidationError

from my_cli.soul import LLMNotSet, LLMNotSupported, MaxStepsReached, RunCancelled, Soul, run_soul
from my_cli.utils.logging import logger
from my_cli.wire import WireUISide
from my_cli.wire.message import (
    ApprovalRequest,
    ApprovalResponse,
    Event,
    serialize_approval_request,
    serialize_event,
)

from .jsonrpc import (
    JSONRPC_MESSAGE_ADAPTER,
    JSONRPC_VERSION,
    JSONRPCErrorResponse,
    JSONRPCRequest,
    JSONRPCSuccessResponse,
)

_ResultKind = Literal["ok", "error"]


class _SoulRunner:
    """
    Soul 运行器 - 管理 Soul 的执行生命周期

    功能：
    - 启动/中断/关闭 Soul
    - 事件回调和 Approval 处理
    """

    def __init__(
        self,
        soul: Soul,
        send_event: Callable[[Event], Awaitable[None]],
        request_approval: Callable[[ApprovalRequest], Awaitable[ApprovalResponse]],
    ):
        self._soul = soul
        self._send_event = send_event
        self._request_approval = request_approval
        self._cancel_event: asyncio.Event | None = None
        self._task: asyncio.Task[tuple[_ResultKind, Any]] | None = None

    @property
    def is_running(self) -> bool:
        """检查 Soul 是否正在运行"""
        return self._task is not None and not self._task.done()

    async def run(self, user_input: str) -> tuple[_ResultKind, Any]:
        """
        运行 Soul 处理用户输入

        Args:
            user_input: 用户输入

        Returns:
            (结果类型, 结果数据)
        """
        if self.is_running:
            raise RuntimeError("Soul is already running")

        self._cancel_event = asyncio.Event()
        self._task = asyncio.create_task(self._run(user_input))
        try:
            return await self._task
        finally:
            self._task = None
            self._cancel_event = None

    async def interrupt(self) -> None:
        """中断当前运行"""
        if self._cancel_event is not None:
            self._cancel_event.set()

    async def shutdown(self) -> None:
        """关闭运行器"""
        await self.interrupt()
        if self._task is not None:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            self._task = None
            self._cancel_event = None

    async def _run(self, user_input: str) -> tuple[_ResultKind, Any]:
        """内部运行逻辑"""
        assert self._cancel_event is not None
        try:
            await run_soul(
                self._soul,
                user_input,
                self._ui_loop,
                self._cancel_event,
            )
        except LLMNotSet:
            return ("error", (-32001, "LLM is not configured"))
        except LLMNotSupported as e:
            return ("error", (-32003, f"LLM not supported: {e}"))
        except ChatProviderError as e:
            return ("error", (-32002, f"LLM provider error: {e}"))
        except MaxStepsReached as e:
            return ("ok", {"status": "max_steps_reached", "steps": e.n_steps})
        except RunCancelled:
            return ("ok", {"status": "cancelled"})
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.exception("Soul run failed:")
            return ("error", (-32099, f"Run failed: {e}"))
        return ("ok", {"status": "finished"})

    async def _ui_loop(self, wire: WireUISide) -> None:
        """UI 循环 - 处理 Wire 消息"""
        while True:
            message = await wire.receive()
            if isinstance(message, ApprovalRequest):
                response = await self._request_approval(message)
                message.resolve(response)
            else:
                # must be Event
                await self._send_event(message)


class WireServer:
    """
    Wire 服务器 - 基于 stdio 的 JSON-RPC 服务

    功能：
    - 通过 stdin/stdout 与 IDE 通信
    - 处理 run/interrupt 请求
    - 推送事件通知
    - 管理 Approval 请求/响应

    对应源码：kimi-cli-fork/src/kimi_cli/ui/wire/__init__.py:114-343
    """

    def __init__(self, soul: Soul):
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._write_task: asyncio.Task[None] | None = None
        self._send_queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self._pending_requests: dict[str, ApprovalRequest] = {}
        self._runner = _SoulRunner(
            soul,
            send_event=self._send_event,
            request_approval=self._request_approval,
        )

    async def run(self) -> bool:
        """启动 Wire 服务器"""
        logger.info("Starting Wire server on stdio")

        self._reader, self._writer = await acp.stdio_streams()
        self._write_task = asyncio.create_task(self._write_loop())
        try:
            await self._read_loop()
        finally:
            await self._shutdown()

        return True

    async def _read_loop(self) -> None:
        """读取循环 - 从 stdin 读取 JSON-RPC 消息"""
        assert self._reader is not None

        while True:
            line = await self._reader.readline()
            if not line:
                logger.info("stdin closed, Wire server exiting")
                break

            try:
                payload = json.loads(line.decode("utf-8"))
            except json.JSONDecodeError:
                logger.warning("Invalid JSON line: {line}", line=line)
                continue

            await self._dispatch(payload)

    async def _dispatch(self, payload: dict[str, Any]) -> None:
        """分发 JSON-RPC 消息"""
        version = payload.get("jsonrpc")
        if version != JSONRPC_VERSION:
            logger.warning("Unexpected jsonrpc version: {version}", version=version)
            return

        try:
            message = JSONRPC_MESSAGE_ADAPTER.validate_python(payload)
        except ValidationError as e:
            logger.warning(
                "Ignoring malformed JSON-RPC payload: {message}; error={error}",
                message=payload,
                error=str(e),
            )
            return

        match message:
            case JSONRPCRequest():
                await self._handle_request(message)
            case JSONRPCSuccessResponse() | JSONRPCErrorResponse():
                await self._handle_response(message)

    async def _handle_request(self, message: JSONRPCRequest) -> None:
        """处理 JSON-RPC 请求"""
        method = message.method
        msg_id = message.id
        params = message.params

        if method == "run":
            await self._handle_run(msg_id, params)
        elif method == "interrupt":
            await self._handle_interrupt(msg_id)
        else:
            logger.warning("Unknown method: {method}", method=method)
            if msg_id is not None:
                await self._send_error(msg_id, -32601, f"Unknown method: {method}")

    async def _handle_response(
        self,
        message: JSONRPCSuccessResponse | JSONRPCErrorResponse,
    ) -> None:
        """处理 JSON-RPC 响应（用于 Approval）"""
        msg_id = message.id
        if msg_id is None:
            logger.warning("Response without id: {message}", message=message.model_dump())
            return

        pending = self._pending_requests.get(msg_id)
        if pending is None:
            logger.warning("No pending request for response id={id}", id=msg_id)
            return

        try:
            if isinstance(message, JSONRPCErrorResponse):
                pending.resolve(ApprovalResponse.REJECT)
            else:
                response = self._parse_approval_response(message.result)
                pending.resolve(response)
        finally:
            self._pending_requests.pop(msg_id, None)

    async def _handle_run(self, msg_id: Any, params: dict[str, Any]) -> None:
        """处理 run 请求"""
        if msg_id is None:
            logger.warning("Run notification ignored")
            return

        if self._runner.is_running:
            await self._send_error(msg_id, -32000, "Run already in progress")
            return

        user_input = params.get("input")
        if not isinstance(user_input, str):
            user_input = params.get("prompt")
        if not isinstance(user_input, str):
            await self._send_error(msg_id, -32602, "`input` (or `prompt`) must be a string")
            return

        try:
            kind, payload = await self._runner.run(user_input)
        except RuntimeError:
            await self._send_error(msg_id, -32000, "Run already in progress")
            return

        if kind == "error":
            code, message = payload
            await self._send_error(msg_id, code, message)
        else:
            await self._send_response(msg_id, payload)

    async def _handle_interrupt(self, msg_id: Any) -> None:
        """处理 interrupt 请求"""
        if not self._runner.is_running:
            if msg_id is not None:
                await self._send_response(msg_id, {"status": "idle"})
            return

        await self._runner.interrupt()
        if msg_id is not None:
            await self._send_response(msg_id, {"status": "ok"})

    async def _send_event(self, event: Event) -> None:
        """发送事件通知"""
        await self._send_notification("event", serialize_event(event))

    async def _request_approval(self, request: ApprovalRequest) -> ApprovalResponse:
        """请求 Approval 并等待响应"""
        self._pending_requests[request.id] = request

        await self._send_request(
            request.id,
            "request",
            {"type": "approval", "payload": serialize_approval_request(request)},
        )

        try:
            return await request.wait()
        finally:
            self._pending_requests.pop(request.id, None)

    def _parse_approval_response(self, result: dict[str, Any]) -> ApprovalResponse:
        """解析 Approval 响应"""
        value = result.get("response")
        try:
            if isinstance(value, ApprovalResponse):
                return value
            return ApprovalResponse(str(value))
        except ValueError:
            logger.warning("Unknown approval response: {value}", value=value)
            return ApprovalResponse.REJECT

    async def _write_loop(self) -> None:
        """写入循环 - 向 stdout 发送 JSON-RPC 消息"""
        assert self._writer is not None

        try:
            while True:
                try:
                    payload = await self._send_queue.get()
                except asyncio.QueueShutDown:
                    logger.debug("Send queue shut down, stopping Wire server write loop")
                    break
                data = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
                self._writer.write(data.encode("utf-8") + b"\n")
                await self._writer.drain()
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Wire server write loop error:")
            raise

    async def _send_notification(self, method: str, params: Any) -> None:
        """发送 JSON-RPC 通知（无 id）"""
        await self._enqueue_payload(
            {"jsonrpc": JSONRPC_VERSION, "method": method, "params": params}
        )

    async def _send_request(self, msg_id: Any, method: str, params: Any) -> None:
        """发送 JSON-RPC 请求"""
        await self._enqueue_payload(
            {"jsonrpc": JSONRPC_VERSION, "id": msg_id, "method": method, "params": params}
        )

    async def _send_response(self, msg_id: Any, result: Any) -> None:
        """发送 JSON-RPC 成功响应"""
        await self._enqueue_payload({"jsonrpc": JSONRPC_VERSION, "id": msg_id, "result": result})

    async def _send_error(self, msg_id: Any, code: int, message: str) -> None:
        """发送 JSON-RPC 错误响应"""
        await self._enqueue_payload(
            {"jsonrpc": JSONRPC_VERSION, "id": msg_id, "error": {"code": code, "message": message}}
        )

    async def _enqueue_payload(self, payload: dict[str, Any]) -> None:
        """入队待发送的消息"""
        try:
            await self._send_queue.put(payload)
        except asyncio.QueueShutDown:
            logger.debug("Send queue shut down; dropping payload: {payload}", payload=payload)

    async def _shutdown(self) -> None:
        """关闭服务器"""
        await self._runner.shutdown()
        self._send_queue.shutdown()

        if self._write_task is not None:
            with contextlib.suppress(asyncio.CancelledError):
                await self._write_task

        for request in self._pending_requests.values():
            if not request.resolved:
                request.resolve(ApprovalResponse.REJECT)
        self._pending_requests.clear()

        if self._writer is not None:
            self._writer.close()
            with contextlib.suppress(Exception):
                await self._writer.wait_closed()
            self._writer = None

        self._reader = None


__all__ = ["WireServer"]

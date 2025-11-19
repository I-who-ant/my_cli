"""
消息显示模块 - 分离消息处理逻辑

参考官方架构：将消息显示逻辑从 __init__.py 分离到 visualize.py
官方的 visualize() 函数本身就是 UI loop 函数，包含完整的消息循环！
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Protocol

import rich
from kosong.message import ContentPart, MergeableMixin, Message, TextPart, ToolCall, ToolCallPart
from kosong.tooling import ToolResult

from my_cli.cli import OutputFormat
from my_cli.wire import WireMessage, WireUISide
from my_cli.wire.message import StepBegin, StepInterrupted


class Printer(Protocol):
    """打印器协议"""
    def feed(self, msg: WireMessage) -> None: ...
    def flush(self) -> None: ...


class TextPrinter(Printer):
    """文本打印机 - 使用 rich 显示消息"""
    def __init__(self) -> None:
        self._merge_buffer: MergeableMixin | None = None

    def feed(self, msg: WireMessage) -> None:
        match msg:
            case MergeableMixin():
                # 合并流式消息
                if self._merge_buffer is None:
                    self._merge_buffer = msg
                elif self._merge_buffer.merge_in_place(msg):
                    pass  # 成功合并，继续累积
                else:
                    # 合并失败，打印缓冲区
                    rich.print(self._merge_buffer)
                    self._merge_buffer = msg
            case _:
                # 非合并消息，先打印缓冲区
                self.flush()
                rich.print(msg)

    def flush(self) -> None:
        if self._merge_buffer is not None:
            rich.print(self._merge_buffer)
            self._merge_buffer = None


class JsonPrinter(Printer):
    """JSON 打印机 - 输出结构化数据"""
    @dataclass(slots=True)
    class _ToolCallState:
        tool_call: ToolCall
        tool_result: ToolResult | None

    def __init__(self) -> None:
        self._content_buffer: list[ContentPart] = []
        """内容缓冲区"""
        self._tool_call_buffer: dict[str, JsonPrinter._ToolCallState] = {}
        """工具调用缓冲区"""
        self._last_tool_call: ToolCall | None = None

    def feed(self, msg: WireMessage) -> None:
        match msg:
            case StepBegin() | StepInterrupted():
                # 步骤开始/中断：刷新缓冲区
                self.flush()
            case ContentPart() as part:
                # 合并内容片段
                if not self._content_buffer or not self._content_buffer[-1].merge_in_place(part):
                    self._content_buffer.append(part)
            case ToolCall() as call:
                # 记录工具调用
                self._tool_call_buffer[call.id] = JsonPrinter._ToolCallState(
                    tool_call=call, tool_result=None
                )
                self._last_tool_call = call
            case ToolCallPart() as part:
                # 合并工具调用参数
                if self._last_tool_call is None:
                    return
                assert self._last_tool_call.merge_in_place(part)
            case ToolResult() as result:
                # 记录工具结果
                state = self._tool_call_buffer.get(result.tool_call_id)
                if state is None:
                    return
                state.tool_result = result
            case _:
                # 忽略其他消息
                pass

    def flush(self) -> None:
        if not self._content_buffer and not self._tool_call_buffer:
            return

        # 收集工具调用和结果
        tool_calls: list[ToolCall] = []
        tool_results: list[ToolResult] = []
        for state in self._tool_call_buffer.values():
            if state.tool_result is None:
                continue
            tool_calls.append(state.tool_call)
            tool_results.append(state.tool_result)

        # 创建消息
        message = Message(
            role="assistant",
            content=self._content_buffer,
            tool_calls=tool_calls or None,
        )

        # 打印结构化 JSON
        import json
        message_dict = {
            "role": message.role,
            "content": [
                {
                    "type": part.__class__.__name__.lower(),
                    "data": part.model_dump() if hasattr(part, "model_dump") else str(part)
                }
                for part in message.content
            ],
        }
        if message.tool_calls:
            message_dict["tool_calls"] = [
                {
                    "id": call.id,
                    "type": "function",
                    "function": {
                        "name": call.function.name,
                        "arguments": call.function.arguments,
                    }
                }
                for call in message.tool_calls
            ]

        rich.print_json(data=json.dumps(message_dict, ensure_ascii=False))

        # 清空缓冲区
        self._content_buffer.clear()
        self._tool_call_buffer.clear()
        self._last_tool_call = None


async def visualize(
    output_format: OutputFormat,
    wire: WireUISide,
) -> None:
    """
    消息显示函数 - 官方架构：这就是 UI Loop 函数！

    官方的 visualize() 函数本身就是完整的 UI loop：
    1. 根据 output_format 创建合适的 Printer
    2. 在内部处理完整的消息循环
    3. 从 wire 接收消息并交给 Printer 处理
    4. 收到 StepInterrupted 时退出

    Args:
        output_format: 输出格式（"text" 或 "stream-json"）
        wire: Wire 的 UI 侧接口

    对应源码：kimi-cli-fork/src/kimi_cli/ui/print/visualize.py:112-130
    """
    # 1. 根据输出格式创建 Printer
    if output_format == "stream-json":
        handler = JsonPrinter()
    else:
        handler = TextPrinter()

    # 2. **完整的消息循环在这里！** （官方架构）
    while True:
        try:
            # 接收消息
            msg = await wire.receive()
        except asyncio.QueueShutDown:
            # 队列关闭，刷新并退出
            handler.flush()
            break

        # 交给 Printer 处理
        handler.feed(msg)

        # 收到中断信号，退出循环
        if isinstance(msg, StepInterrupted):
            break
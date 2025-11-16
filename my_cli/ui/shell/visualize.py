"""
Shell UI 可视化渲染模块

职责：
1. 处理 Wire 消息并渲染到终端
2. 工具调用显示
3. 流式文本输出
4. 步骤指示器

对应源码：kimi-cli-fork/src/kimi_cli/ui/shell/visualize.py

为什么单独分离？
1. 渲染逻辑独立于业务逻辑
2. 可以支持不同的输出格式（终端、JSON、HTML）
3. 易于扩展和定制样式
4. 符合单一职责原则（SRP）

Stage 11 实现：
- 基础版 UI Loop 渲染
- 彩色输出（使用 rich）
- 工具调用显示
"""

from __future__ import annotations

import asyncio
import json

from kosong.message import ContentPart, TextPart, ToolCall
from kosong.tooling import ToolError, ToolOk, ToolResult

from my_cli.ui.shell.console import console
from my_cli.wire import WireUISide
from my_cli.wire.message import StepBegin, StepInterrupted

__all__ = ["visualize"]


async def visualize(wire_ui: WireUISide) -> None:
    """
    UI Loop 函数 - 从 Wire 接收消息并渲染

    这是核心的渲染函数，负责：
    1. 循环接收 Wire 消息
    2. 根据消息类型渲染到终端
    3. 支持流式输出（逐字显示）
    4. 显示工具调用和结果

    Args:
        wire_ui: Wire 的 UI 侧接口
    """
    while True:
        msg = await wire_ui.receive()

        # 文本片段：实时打印
        if isinstance(msg, TextPart):
            if msg.text:
                console.print(msg.text, end="", markup=False)

        elif isinstance(msg, ContentPart):
            if hasattr(msg, "text") and msg.text:
                console.print(msg.text, end="", markup=False)

        # 步骤开始：显示步骤编号
        elif isinstance(msg, StepBegin):
            if msg.n > 1:
                console.print(f"\n\n[cyan]🔄 [Step {msg.n}][/cyan]")

        # 工具调用：显示工具名称和参数
        elif isinstance(msg, ToolCall):
            _render_tool_call(msg)

        # 工具结果：显示成功/失败状态
        elif isinstance(msg, ToolResult):
            _render_tool_result(msg)

        # 步骤中断：退出 UI Loop
        elif isinstance(msg, StepInterrupted):
            break


def _render_tool_call(tool_call: ToolCall) -> None:
    """渲染工具调用"""
    console.print(f"\n\n[yellow]🔧 调用工具: {tool_call.function.name}[/yellow]")

    try:
        arguments = (
            json.loads(tool_call.function.arguments)
            if tool_call.function.arguments
            else {}
        )
        args_str = json.dumps(arguments, ensure_ascii=False, indent=2)
        console.print(f"[grey50]   参数:\n{args_str}[/grey50]")
    except Exception:
        console.print(f"[grey50]   参数: {tool_call.function.arguments}[/grey50]")


def _render_tool_result(tool_result: ToolResult) -> None:
    """渲染工具执行结果"""
    if isinstance(tool_result.result, ToolOk):
        console.print(f"\n[green]✅ 工具成功[/green]")
        if tool_result.result.brief:
            console.print(f"[grey50]   {tool_result.result.brief}[/grey50]")
        output = str(tool_result.result.output)
        if len(output) > 500:
            output = output[:500] + "...(截断)"
        if output.strip():
            console.print(f"[grey50]   输出: {output}[/grey50]")

    elif isinstance(tool_result.result, ToolError):
        console.print(f"\n[red]❌ 工具失败: {tool_result.result.brief}[/red]")
        if tool_result.result.message:
            console.print(f"[grey50]   错误: {tool_result.result.message}[/grey50]")

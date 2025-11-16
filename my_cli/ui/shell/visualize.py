"""
Shell UI 可视化渲染模块 ⭐ Stage 12 Live 修复版

职责：
1. 处理 Wire 消息并渲染到终端
2. 工具调用显示
3. 流式文本输出
4. 步骤指示器
5. ⭐ 使用 rich.live.Live 隔离输出（彻底修复光标混乱 bug）

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

Stage 12 修复：
- ⭐ 使用 rich.live.Live 实现独立渲染区域
- ⭐ 彻底修复光标混乱 bug（Live 区域和输入区域完全隔离）
- ⭐ 累积文本内容，Live 实时刷新显示
- ⭐ 应用 utils.rich 全局配置（字符级换行）
"""

from __future__ import annotations

import asyncio
import json

# ⭐ Stage 12：导入 utils.rich 应用全局配置（字符级换行）
import my_cli.utils.rich  # noqa: F401
from kosong.message import ContentPart, TextPart, ToolCall
from kosong.tooling import ToolError, ToolOk, ToolResult
from rich.console import Group
from rich.live import Live
from rich.text import Text

from my_cli.ui.shell.console import console
from my_cli.wire import WireUISide
from my_cli.wire.message import StepBegin, StepInterrupted

__all__ = ["visualize"]


async def visualize(wire_ui: WireUISide) -> None:
    """
    UI Loop 函数 - 从 Wire 接收消息并渲染 ⭐ Stage 12 Live 修复版

    这是核心的渲染函数，负责：
    1. 循环接收 Wire 消息
    2. 根据消息类型渲染到终端
    3. 支持流式输出（逐字显示）
    4. 显示工具调用和结果
    5. ⭐ 使用 rich.live.Live 创建独立渲染区域

    Args:
        wire_ui: Wire 的 UI 侧接口

    关键修复：
        使用 rich.live.Live 创建独立的渲染区域：
        - Live 区域和 PromptSession 的输入区域完全隔离
        - Live 区域的内容实时刷新，不会影响输入
        - 光标始终在输入区域，不会出现在 LLM 输出中

        工作原理：
        1. 累积所有文本内容到 content_text
        2. 每次收到消息时，更新 content_text
        3. live.update() 刷新 Live 区域显示
        4. 输入区域完全独立，不受影响
    """
    # 累积的文本内容
    content_text = Text()

    # ⭐ 使用 Live 创建独立渲染区域
    with Live(
        content_text,
        console=console,
        refresh_per_second=10,  # 每秒刷新 10 次
        transient=False,  # 内容不是临时的，结束后保留
    ) as live:
        while True:
            msg = await wire_ui.receive()

            # 文本片段：累积并更新显示
            if isinstance(msg, TextPart):
                if msg.text:
                    content_text.append(msg.text)
                    live.update(content_text)  # ⭐ 实时刷新

            elif isinstance(msg, ContentPart):
                if hasattr(msg, "text") and msg.text:
                    content_text.append(msg.text)
                    live.update(content_text)

            # 步骤开始：显示步骤编号
            elif isinstance(msg, StepBegin):
                if msg.n > 1:
                    content_text.append(f"\n\n🔄 [Step {msg.n}]\n", style="cyan")
                    live.update(content_text)

            # 工具调用：显示工具名称和参数
            elif isinstance(msg, ToolCall):
                _render_tool_call_to_text(msg, content_text)
                live.update(content_text)

            # 工具结果：显示成功/失败状态
            elif isinstance(msg, ToolResult):
                _render_tool_result_to_text(msg, content_text)
                live.update(content_text)

            # 步骤中断：退出 UI Loop
            elif isinstance(msg, StepInterrupted):
                break


def _render_tool_call_to_text(tool_call: ToolCall, text: Text) -> None:
    """
    渲染工具调用到 Text 对象 ⭐ Stage 12 Live 修复版

    将工具调用信息追加到 Text 对象，而不是直接 console.print()。
    这样才能保证 Live 区域的完全隔离。

    Args:
        tool_call: 工具调用对象
        text: 累积的 Text 对象
    """
    # 添加工具调用标题
    text.append("\n\n🔧 调用工具: ", style="yellow")
    text.append(tool_call.function.name, style="yellow")
    text.append("\n")

    # 格式化参数
    try:
        arguments = (
            json.loads(tool_call.function.arguments)
            if tool_call.function.arguments
            else {}
        )
        args_str = json.dumps(arguments, ensure_ascii=False, indent=2)
        text.append(f"   参数:\n{args_str}\n", style="grey50")
    except Exception:
        text.append(f"   参数: {tool_call.function.arguments}\n", style="grey50")


def _render_tool_result_to_text(tool_result: ToolResult, text: Text) -> None:
    """
    渲染工具执行结果到 Text 对象 ⭐ Stage 12 Live 修复版

    将工具执行结果追加到 Text 对象，而不是直接 console.print()。
    这样才能保证 Live 区域的完全隔离。

    Args:
        tool_result: 工具执行结果对象
        text: 累积的 Text 对象
    """
    if isinstance(tool_result.result, ToolOk):
        # 成功情况
        text.append("\n✅ 工具成功\n", style="green")

        if tool_result.result.brief:
            text.append(f"   {tool_result.result.brief}\n", style="grey50")

        output = str(tool_result.result.output)
        if len(output) > 500:
            output = output[:500] + "...(截断)"
        if output.strip():
            text.append(f"   输出: {output}\n", style="grey50")

    elif isinstance(tool_result.result, ToolError):
        # 失败情况
        text.append(f"\n❌ 工具失败: {tool_result.result.brief}\n", style="red")

        if tool_result.result.message:
            text.append(f"   错误: {tool_result.result.message}\n", style="grey50")

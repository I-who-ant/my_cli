"""
调试命令 ⭐ Stage 30

显示当前 Context 的详细信息。

对应源码：kimi-cli-fork/src/kimi_cli/ui/shell/debug.py
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from kosong.message import (
    AudioURLPart,
    ContentPart,
    ImageURLPart,
    Message,
    TextPart,
    ThinkPart,
    ToolCall,
)
from rich.console import Group
from rich.panel import Panel
from rich.rule import Rule
from rich.syntax import Syntax
from rich.text import Text

from my_cli.soul.kimisoul import KimiSoul
from my_cli.ui.shell.console import console
from my_cli.ui.shell.metacmd import meta_command

if TYPE_CHECKING:
    from my_cli.ui.shell import ShellApp


def _format_content_part(part: ContentPart) -> Text | Panel | Group:
    """格式化单个内容部分"""
    match part:
        case TextPart(text=text):
            if text.strip().startswith("<system>") and text.strip().endswith("</system>"):
                return Panel(
                    text.strip()[8:-9].strip(),
                    title="[dim]system[/dim]",
                    border_style="dim yellow",
                    padding=(0, 1),
                )
            return Text(text, style="white")

        case ThinkPart(think=think):
            return Panel(
                think,
                title="[dim]thinking[/dim]",
                border_style="dim cyan",
                padding=(0, 1),
            )

        case ImageURLPart(image_url=img):
            url_display = img.url[:80] + "..." if len(img.url) > 80 else img.url
            id_text = f" (id: {img.id})" if img.id else ""
            return Text(f"[Image{id_text}] {url_display}", style="blue")

        case AudioURLPart(audio_url=audio):
            url_display = audio.url[:80] + "..." if len(audio.url) > 80 else audio.url
            id_text = f" (id: {audio.id})" if audio.id else ""
            return Text(f"[Audio{id_text}] {url_display}", style="blue")

        case _:
            return Text(f"[Unknown content type: {type(part).__name__}]", style="red")


def _format_tool_call(tool_call: ToolCall) -> Panel:
    """格式化工具调用"""
    args = tool_call.function.arguments or "{}"
    try:
        args_formatted = json.dumps(json.loads(args), indent=2)
        args_syntax = Syntax(args_formatted, "json", theme="monokai", padding=(0, 1))
    except json.JSONDecodeError:
        args_syntax = Text(args, style="red")

    content = Group(
        Text(f"Function: {tool_call.function.name}", style="bold cyan"),
        Text(f"Call ID: {tool_call.id}", style="dim"),
        Text("Arguments:", style="bold"),
        args_syntax,
    )

    return Panel(
        content,
        title="[bold yellow]Tool Call[/bold yellow]",
        border_style="yellow",
        padding=(0, 1),
    )


def _format_message(msg: Message, index: int) -> Panel:
    """格式化单条消息"""
    role_colors = {
        "system": "magenta",
        "developer": "magenta",
        "user": "green",
        "assistant": "blue",
        "tool": "yellow",
    }
    role_color = role_colors.get(msg.role, "white")
    role_text = f"[bold {role_color}]{msg.role.upper()}[/bold {role_color}]"

    if msg.name:
        role_text += f" [dim]({msg.name})[/dim]"

    if msg.tool_call_id:
        role_text += f" [dim]→ {msg.tool_call_id}[/dim]"

    content_items: list = []

    if isinstance(msg.content, str):
        content_items.append(Text(msg.content, style="white"))
    else:
        for part in msg.content:
            formatted = _format_content_part(part)
            content_items.append(formatted)

    if msg.tool_calls:
        if content_items:
            content_items.append(Text())
        for tool_call in msg.tool_calls:
            content_items.append(_format_tool_call(tool_call))

    if not content_items:
        content_items.append(Text("[empty message]", style="dim italic"))

    group = Group(*content_items)

    title = f"#{index + 1} {role_text}"
    if msg.partial:
        title += " [dim italic](partial)[/dim italic]"

    return Panel(
        group,
        title=title,
        border_style=role_color,
        padding=(0, 1),
    )


@meta_command(kimi_soul_only=True)
def debug(app: ShellApp, args: list[str]):
    """调试 Context 上下文信息"""
    assert isinstance(app.soul, KimiSoul)

    context = app.soul._context
    history = context.history

    if not history:
        console.print(
            Panel(
                "Context is empty - no messages yet",
                border_style="yellow",
                padding=(1, 2),
            )
        )
        return

    output_items = [
        Panel(
            Group(
                Text(f"Total messages: {len(history)}", style="bold"),
                Text(f"Token count: {context.token_count:,}", style="bold"),
                Text(f"Checkpoints: {context.n_checkpoints}", style="bold"),
                Text(f"Trajectory: {context._file_backend}", style="dim"),
            ),
            title="[bold]Context Info[/bold]",
            border_style="cyan",
            padding=(0, 1),
        ),
        Rule(style="dim"),
    ]

    for idx, msg in enumerate(history):
        output_items.append(_format_message(msg, idx))

    display_group = Group(*output_items)

    with console.pager(styles=True):
        console.print(display_group)


__all__ = ["debug"]

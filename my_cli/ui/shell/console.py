"""
Shell UI Console 模块

职责：提供全局 Console 单例和主题配置

对应源码：kimi-cli-fork/src/kimi_cli/ui/shell/console.py (32行)

为什么单独分离？
1. Console 是全局单例，所有模块都需要使用
2. 主题配置集中管理，避免重复定义
3. 符合单一职责原则（SRP）
"""

from __future__ import annotations

from rich.console import Console
from rich.theme import Theme

# 自定义主题：中性 Markdown 渲染
# 官方使用这个主题来避免 Markdown 自动高亮干扰输出
_NEUTRAL_MARKDOWN_THEME = Theme(
    {
        "markdown.paragraph": "none",
        "markdown.block_quote": "none",
        "markdown.hr": "none",
        "markdown.item": "none",
        "markdown.item.bullet": "none",
        "markdown.item.number": "none",
        "markdown.link": "none",
        "markdown.link_url": "none",
        "markdown.h1": "none",
        "markdown.h1.border": "none",
        "markdown.h2": "none",
        "markdown.h3": "none",
        "markdown.h4": "none",
        "markdown.h5": "none",
        "markdown.h6": "none",
        "markdown.em": "none",
        "markdown.strong": "none",
        "markdown.s": "none",
        "status.spinner": "none",
    },
    inherit=True,
)

# 全局 Console 单例
# highlight=False: 禁用自动语法高亮（避免误渲染用户输入）
# theme: 使用自定义主题
console = Console(highlight=False, theme=_NEUTRAL_MARKDOWN_THEME)

__all__ = ["console"]

"""
Prompts - 提示词模块

提供 LLM 提示词模板。

对应源码：kimi-cli-fork/src/kimi_cli/prompts/__init__.py
"""

from __future__ import annotations

from pathlib import Path

COMPACT = (Path(__file__).parent / "compact.md").read_text(encoding="utf-8")
"""上下文压缩提示词"""

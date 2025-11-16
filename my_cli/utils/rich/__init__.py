
"""
Rich 库全局配置和扩展 ⭐ Stage 12

职责：
1. Rich 全局配置（字符级换行）
2. 为未来的 Rich 组件扩展提供基础

对应源码：kimi-cli-fork/src/kimi_cli/utils/rich/__init__.py

为什么需要字符级换行？
- Rich 默认在空格处换行（保留完整单词）
- 但在显示代码、长 URL 时，可能超出终端宽度
- 字符级换行允许在任意字符处折行，避免溢出
"""

from __future__ import annotations

import re
from typing import Final

from rich import _wrap

# Rich 默认的换行正则（空格分词）
_DEFAULT_WRAP_PATTERN: Final[re.Pattern[str]] = re.compile(r"\s*\S+\s*")

# 字符级换行正则（任意字符）
_CHAR_WRAP_PATTERN: Final[re.Pattern[str]] = re.compile(r".", re.DOTALL)


def enable_character_wrap() -> None:
    """
    启用字符级换行 ⭐ Rich 全局配置

    Rich 默认尝试保留完整单词，我们覆盖内部正则，
    让 Markdown 渲染可以在任意列折叠文本，避免超出终端宽度。

    官方说明：
    "Switch Rich's wrapping logic to break on every character.
     Rich's default behavior tries to preserve whole words;
     we override the internal regex so markdown rendering can
     fold text at any column once it exceeds the terminal width."
    """
    _wrap.re_word = _CHAR_WRAP_PATTERN


def restore_word_wrap() -> None:
    """恢复 Rich 默认的单词级换行"""
    _wrap.re_word = _DEFAULT_WRAP_PATTERN


# ⭐ 应用字符级换行（全局生效）
# 只要 import my_cli.utils.rich，就会自动应用此配置
enable_character_wrap()

__all__ = ["enable_character_wrap", "restore_word_wrap"]

"""
字符串工具 ⭐ Stage 30

对应源码：kimi-cli-fork/src/kimi_cli/utils/string.py
"""

from __future__ import annotations

import random
import re
import string

_NEWLINE_RE = re.compile(r"[\r\n]+")


def shorten_middle(text: str, width: int, remove_newline: bool = True) -> str:
    """在中间插入省略号来缩短文本"""
    if len(text) <= width:
        return text
    if remove_newline:
        text = _NEWLINE_RE.sub(" ", text)
    return text[: width // 2] + "..." + text[-width // 2 :]


def random_string(length: int = 8) -> str:
    """生成指定长度的随机字符串"""
    letters = string.ascii_lowercase
    return "".join(random.choice(letters) for _ in range(length))


__all__ = ["shorten_middle", "random_string"]

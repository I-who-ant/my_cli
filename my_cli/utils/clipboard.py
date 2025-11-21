"""
剪贴板工具模块

对应源码：kimi-cli-fork/src/kimi_cli/utils/clipboard.py
"""

from __future__ import annotations


def is_clipboard_available() -> bool:
    """
    检查 Pyperclip 剪贴板是否可用

    Returns:
        True 如果剪贴板可用
    """
    try:
        import pyperclip
        pyperclip.paste()
        return True
    except Exception:
        return False

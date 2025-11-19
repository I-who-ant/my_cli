"""
Path Utils - 路径工具函数

学习目标：
1. 理解文件旋转（rotation）机制
2. 理解异步文件操作

对应源码：kimi-cli-fork/src/kimi_cli/utils/path.py

阶段演进：
- Stage 4-16：不需要
- Stage 18：为 Context.checkpoint() 提供文件旋转支持 ⭐
"""

from __future__ import annotations

import asyncio
import os
import re
import subprocess
import sys
from pathlib import Path

import aiofiles.os

_ROTATION_OPEN_FLAGS = os.O_CREAT | os.O_EXCL | os.O_WRONLY
_ROTATION_FILE_MODE = 0o600


async def _reserve_rotation_path(path: Path) -> bool:
    """原子性地创建空文件作为路径保留

    Args:
        path: 要保留的文件路径

    Returns:
        bool: 成功返回 True，文件已存在返回 False

    对应源码：kimi-cli-fork/src/kimi_cli/utils/path.py:16-27
    """
    def _create() -> None:
        fd = os.open(str(path), _ROTATION_OPEN_FLAGS, _ROTATION_FILE_MODE)
        os.close(fd)

    try:
        await asyncio.to_thread(_create)
    except FileExistsError:
        return False
    return True


async def next_available_rotation(path: Path) -> Path | None:
    """获取下一个可用的旋转文件路径

    文件旋转用于备份历史文件，命名格式为：原名_1.ext, 原名_2.ext 等

    Args:
        path: 原始文件路径

    Returns:
        Path | None: 下一个可用的旋转路径，如果父目录不存在返回 None

    对应源码：kimi-cli-fork/src/kimi_cli/utils/path.py:30-54

    Note:
        必须在返回路径后立即使用，因为它已经创建了占位文件
    """
    if not path.parent.exists():
        return None

    base_name = path.stem
    suffix = path.suffix
    pattern = re.compile(rf"^{re.escape(base_name)}_(\d+){re.escape(suffix)}$")
    max_num = 0
    for entry in await aiofiles.os.listdir(path.parent):
        if match := pattern.match(entry):
            max_num = max(max_num, int(match.group(1)))

    next_num = max_num + 1
    while True:
        next_path = path.parent / f"{base_name}_{next_num}{suffix}"
        if await _reserve_rotation_path(next_path):
            return next_path
        next_num += 1


def list_directory(work_dir: Path) -> str:
    """列出目录内容（跨平台）"""
    if sys.platform == "win32":
        ls = subprocess.run(
            ["cmd", "/c", "dir", work_dir],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    else:
        ls = subprocess.run(
            ["ls", "-la", work_dir],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    return ls.stdout.strip()


def shorten_home(path: Path) -> Path:
    """
    将绝对路径转换为使用 ~ 表示家目录

    Args:
        path: 要转换的路径

    Returns:
        Path: 如果路径在家目录下则使用 ~ 前缀，否则返回原路径

    对应源码：kimi-cli-fork/src/kimi_cli/utils/path.py:77-86
    """
    try:
        home = Path.home()
        p = path.relative_to(home)
        return Path("~") / p
    except ValueError:
        return path

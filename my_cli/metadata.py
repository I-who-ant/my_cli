"""
Metadata - 元数据管理

学习目标：
1. 理解元数据的作用（版本、构建信息等）
2. 理解如何在运行时获取元数据
3. 理解会话管理的元数据系统（WorkDirMeta, Metadata）

对应源码：kimi-cli-fork/src/kimi_cli/metadata.py

阶段演进：
- Stage 4-16：硬编码版本信息 ✅
- Stage 18：会话管理元数据系统 ⭐ 完整实现
- Stage 18+：从 package metadata 读取
"""

from __future__ import annotations

import json
import os
from hashlib import md5
from pathlib import Path

from pydantic import BaseModel, Field

# ============================================================
# Stage 18：动态版本读取 ⭐
# ============================================================

try:
    from importlib.metadata import version

    VERSION = version("my_cli")
except Exception:
    VERSION = "0.1.0"  # 开发模式降级

"""版本号"""

BUILD_COMMIT = os.getenv("BUILD_COMMIT", "unknown")
"""构建 commit"""

BUILD_TIME = os.getenv("BUILD_TIME", "unknown")
"""构建时间"""


# ============================================================
# Stage 18：会话管理元数据系统（参考官方）
# ============================================================
# 官方参考：kimi-cli-fork/src/kimi_cli/metadata.py


def get_share_dir() -> Path:
    """获取共享目录路径

    Returns:
        Path: 共享目录路径 (~/.kimi)

    对应源码：kimi-cli-fork/src/kimi_cli/share.py:6-10
    """
    from my_cli.share import get_share_dir as _get_share_dir
    return _get_share_dir()


def get_metadata_file() -> Path:
    """获取元数据文件路径

    Returns:
        Path: 元数据文件路径 (~/.mc/my_cli.json)

    对应源码：kimi-cli-fork/src/kimi_cli/metadata.py:13-14
    """
    return get_share_dir() / "my_cli.json"


class WorkDirMeta(BaseModel):
    """工作目录元数据

    Attributes:
        path: 工作目录完整路径
        last_session_id: 上次会话 ID

    对应源码：kimi-cli-fork/src/kimi_cli/metadata.py:17-31
    """

    path: str
    """工作目录完整路径"""

    last_session_id: str | None = None
    """上次会话 ID"""

    @property
    def sessions_dir(self) -> Path:
        """会话存储目录

        使用 MD5 哈希避免路径中的特殊字符问题

        Returns:
            Path: 会话存储目录路径

        对应源码：kimi-cli-fork/src/kimi_cli/metadata.py:26-30
        """
        path = get_share_dir() / "sessions" / md5(self.path.encode(encoding="utf-8")).hexdigest()
        path.mkdir(parents=True, exist_ok=True)
        return path


class Metadata(BaseModel):
    """Kimi CLI 元数据结构

    Attributes:
        work_dirs: 工作目录列表
        thinking: 上次会话是否开启思考模式

    对应源码：kimi-cli-fork/src/kimi_cli/metadata.py:33-41
    """

    work_dirs: list[WorkDirMeta] = Field(default_factory=list[WorkDirMeta])
    """工作目录列表"""

    thinking: bool = False
    """上次会话是否开启思考模式"""


def load_metadata() -> Metadata:
    """加载元数据

    Returns:
        Metadata: 元数据对象

    对应源码：kimi-cli-fork/src/kimi_cli/metadata.py:43-52
    """
    metadata_file = get_metadata_file()
    if not metadata_file.exists():
        return Metadata()

    with open(metadata_file, encoding="utf-8") as f:
        data = json.load(f)
        return Metadata(**data)


def save_metadata(metadata: Metadata):
    """保存元数据

    Args:
        metadata: 要保存的元数据对象

    对应源码：kimi-cli-fork/src/kimi_cli/metadata.py:54-59
    """
    metadata_file = get_metadata_file()
    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(metadata.model_dump(), f, indent=2, ensure_ascii=False)

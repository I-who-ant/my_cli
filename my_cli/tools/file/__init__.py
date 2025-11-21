"""
File 工具模块 ⭐ Stage 27

包含6个核心文件操作工具：
- ReadFile - 读取文件
- WriteFile - 写入文件
- Glob - 文件搜索（glob 模式）
- Grep - 内容搜索（正则表达式）
- StrReplaceFile - 内容替换
- PatchFile - 补丁式编辑

对应源码：kimi-cli-fork/src/kimi_cli/tools/file/__init__.py
"""

from enum import Enum


class FileOpsWindow:
    """维护文件操作窗口（未来功能）"""

    pass


class FileActions(str, Enum):
    """文件操作动作枚举（用于 Approval）"""

    READ = "read file"
    EDIT = "edit file"


# 导入所有工具
from .glob import Glob  # noqa: E402
from .grep import Grep  # noqa: E402
from .patch import PatchFile  # noqa: E402
from .read import ReadFile  # noqa: E402
from .replace import StrReplaceFile  # noqa: E402
from .write import WriteFile  # noqa: E402

__all__ = (
    "ReadFile",
    "Glob",
    "Grep",
    "WriteFile",
    "StrReplaceFile",
    "PatchFile",
    "FileActions",
    "FileOpsWindow",
)

"""
Glob 工具 ⭐ Stage 27

功能：使用 glob 模式搜索文件和目录
- 支持通配符模式（*, ?, [abc], **）
- 限制最大匹配数（1000 个）
- 安全检查（禁止 ** 开头，必须在工作目录内）
- 可选是否包含目录

对应源码：kimi-cli-fork/src/kimi_cli/tools/file/glob.py
"""

import asyncio
from pathlib import Path
from typing import Any, override

from kosong.tooling import CallableTool2, ToolError, ToolOk, ToolReturnType
from pydantic import BaseModel, Field

from my_cli.soul.runtime import BuiltinSystemPromptArgs
from my_cli.tools.utils import load_desc
from my_cli.utils.path import list_directory

MAX_MATCHES = 1000
"""最大匹配数"""


class Params(BaseModel):
    """Glob 工具参数"""

    pattern: str = Field(description="Glob pattern to match files/directories.")
    directory: str | None = Field(
        description="Absolute path to the directory to search in (defaults to working directory).",
        default=None,
    )
    include_dirs: bool = Field(
        description="Whether to include directories in results.",
        default=True,
    )


class Glob(CallableTool2[Params]):
    """
    Glob 工具 - 使用模式搜索文件 ⭐ Stage 27

    功能：
    - 支持 glob 模式（*, ?, [abc], **/*）
    - 返回相对路径列表
    - 限制最大匹配数
    - 安全检查（路径遍历保护）

    对应源码：kimi-cli-fork/src/kimi_cli/tools/file/glob.py:31-148
    """

    name: str = "Glob"
    description: str = load_desc(
        Path(__file__).parent / "glob.md",
        {
            "MAX_MATCHES": str(MAX_MATCHES),
        },
    )
    params: type[Params] = Params

    def __init__(self, builtin_args: BuiltinSystemPromptArgs, **kwargs: Any) -> None:
        """
        初始化 Glob 工具

        Args:
            builtin_args: 内置参数（用于获取工作目录）
            **kwargs: 其他参数
        """
        super().__init__(**kwargs)
        self._work_dir = builtin_args.MY_CLI_WORK_DIR

    async def _validate_pattern(self, pattern: str) -> ToolError | None:
        """
        验证模式安全性（禁止 ** 开头）

        Args:
            pattern: glob 模式

        Returns:
            ToolError: 模式不安全
            None: 模式安全
        """
        if pattern.startswith("**"):
            ls_result = await asyncio.to_thread(list_directory, self._work_dir)
            return ToolError(
                output=ls_result,
                message=(
                    f"Pattern `{pattern}` starts with '**' which is not allowed. "
                    "This would recursively search all directories and may include large "
                    "directories like `node_modules`. Use more specific patterns instead. "
                    "For your convenience, a list of all files and directories in the "
                    "top level of the working directory is provided below."
                ),
                brief="Unsafe pattern",
            )
        return None

    def _validate_directory(self, directory: Path) -> ToolError | None:
        """
        验证目录安全性（必须在工作目录内）

        Args:
            directory: 要验证的目录

        Returns:
            ToolError: 目录不安全
            None: 目录安全
        """
        resolved_dir = directory.resolve()
        resolved_work_dir = self._work_dir.resolve()

        # 确保目录在工作目录内
        if not str(resolved_dir).startswith(str(resolved_work_dir)):
            return ToolError(
                message=(
                    f"`{directory}` is outside the working directory. "
                    "You can only search within the working directory."
                ),
                brief="Directory outside working directory",
            )
        return None

    @override
    async def __call__(self, params: Params) -> ToolReturnType:
        """
        执行 glob 搜索

        Args:
            params: 工具参数

        Returns:
            ToolOk: 成功搜索
            ToolError: 搜索失败
        """
        try:
            # 1. 验证模式安全性
            pattern_error = await self._validate_pattern(params.pattern)
            if pattern_error:
                return pattern_error

            # 2. 确定搜索目录
            dir_path = Path(params.directory) if params.directory else self._work_dir

            if not dir_path.is_absolute():
                return ToolError(
                    message=(
                        f"`{params.directory}` is not an absolute path. "
                        "You must provide an absolute path to search."
                    ),
                    brief="Invalid directory",
                )

            # 3. 验证目录安全性
            dir_error = self._validate_directory(dir_path)
            if dir_error:
                return dir_error

            # 4. 检查目录是否存在
            if not dir_path.exists():
                return ToolError(
                    message=f"`{params.directory}` does not exist.",
                    brief="Directory not found",
                )

            if not dir_path.is_dir():
                return ToolError(
                    message=f"`{params.directory}` is not a directory.",
                    brief="Invalid directory",
                )

            # 5. 执行 glob 搜索
            def _glob(pattern: str) -> list[Path]:
                return list(dir_path.glob(pattern))

            matches = await asyncio.to_thread(_glob, params.pattern)

            # 6. 过滤目录（如果不包含目录）
            if not params.include_dirs:
                matches = [p for p in matches if p.is_file()]

            # 7. 排序（保证一致性）
            matches.sort()

            # 8. 限制匹配数
            message = (
                f"Found {len(matches)} matches for pattern `{params.pattern}`."
                if len(matches) > 0
                else f"No matches found for pattern `{params.pattern}`."
            )

            if len(matches) > MAX_MATCHES:
                matches = matches[:MAX_MATCHES]
                message += (
                    f" Only the first {MAX_MATCHES} matches are returned. "
                    "You may want to use a more specific pattern."
                )

            # 9. 返回相对路径
            return ToolOk(
                output="\n".join(str(p.relative_to(dir_path)) for p in matches),
                message=message,
            )

        except Exception as e:
            return ToolError(
                message=f"Failed to search for pattern {params.pattern}. Error: {e}",
                brief="Glob failed",
            )


__all__ = ["Glob"]

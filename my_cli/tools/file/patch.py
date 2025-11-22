"""
PatchFile 工具 ⭐ Stage 27

功能：应用 unified diff 格式的补丁到文件
- 支持标准 unified diff 格式
- 路径安全检查（必须在工作目录内）
- 集成 Approval 系统（需要用户批准）

对应源码：kimi-cli-fork/src/kimi_cli/tools/file/patch.py
"""
from pathlib import Path
from typing import Any, Literal, override

import aiofiles
import patch_ng  # pyright: ignore[reportMissingTypeStubs]
from kosong.tooling import CallableTool2, ToolError, ToolOk, ToolReturnType
from pydantic import BaseModel, Field

from my_cli.soul.approval import Approval
from my_cli.soul.runtime import BuiltinSystemPromptArgs
from my_cli.tools.file import FileActions
from my_cli.tools.utils import ToolRejectedError, load_desc


def _parse_patch(diff_bytes: bytes) -> patch_ng.PatchSet | None:
    """从字节解析补丁，返回 PatchSet 或 None（解析失败时）

    为无类型的 patch_ng.fromstring 函数提供类型提示。
    """
    result: patch_ng.PatchSet | Literal[False] = patch_ng.fromstring(diff_bytes)  # pyright: ignore[reportUnknownMemberType]
    return result if result is not False else None


def _count_hunks(patch_set: patch_ng.PatchSet) -> int:
    """统计 PatchSet 中所有项的 hunk 总数

    为无类型的 patch_ng 库提供类型提示。
    PatchSet.items 是 list[Patch]，Patch.hunks 是 list[Hunk]。
    """
    items: list[patch_ng.Patch] = patch_set.items  # pyright: ignore[reportUnknownMemberType]
    # Each Patch has a hunks attribute (list[Hunk])
    return sum(len(item.hunks) for item in items)  # pyright: ignore[reportUnknownArgumentType, reportUnknownMemberType]


def _apply_patch(patch_set: patch_ng.PatchSet, root: str) -> bool:
    """将补丁应用到指定根目录下的文件

    为无类型的 patch_ng.apply 方法提供类型提示。
    """
    success: Any = patch_set.apply(root=root)  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    return bool(success)  # pyright: ignore[reportUnknownArgumentType]


class Params(BaseModel):
    path: str = Field(description="The absolute path to the file to apply the patch to.")
    diff: str = Field(description="The diff content in unified format to apply.")


class PatchFile(CallableTool2[Params]):
    name: str = "PatchFile"
    description: str = load_desc(Path(__file__).parent / "patch.md")
    params: type[Params] = Params

    def __init__(self, builtin_args: BuiltinSystemPromptArgs, approval: Approval, **kwargs: Any):
        super().__init__(**kwargs)
        self._work_dir = builtin_args.MY_CLI_WORK_DIR
        self._approval = approval

    def _validate_path(self, path: Path) -> ToolError | None:
        """验证路径安全性（必须在工作目录内）"""
        # Check for path traversal attempts
        resolved_path = path.resolve()
        resolved_work_dir = Path(self._work_dir).resolve()

        # Ensure the path is within work directory
        if not str(resolved_path).startswith(str(resolved_work_dir)):
            return ToolError(
                message=(
                    f"`{path}` is outside the working directory. "
                    "You can only patch files within the working directory."
                ),
                brief="Path outside working directory",
            )
        return None

    @override
    async def __call__(self, params: Params) -> ToolReturnType:
        try:
            p = Path(params.path)

            if not p.is_absolute():
                return ToolError(
                    message=(
                        f"`{params.path}` is not an absolute path. "
                        "You must provide an absolute path to patch a file."
                    ),
                    brief="Invalid path",
                )

            # Validate path safety
            path_error = self._validate_path(p)
            if path_error:
                return path_error

            if not p.exists():
                return ToolError(
                    message=f"`{params.path}` does not exist.",
                    brief="File not found",
                )
            if not p.is_file():
                return ToolError(
                    message=f"`{params.path}` is not a file.",
                    brief="Invalid path",
                )

            # Request approval
            if not await self._approval.request(
                self.name,
                FileActions.EDIT,
                f"Patch file `{params.path}`",
            ):
                return ToolRejectedError()

            # Read the file content
            async with aiofiles.open(p, encoding="utf-8", errors="replace") as f:
                original_content = await f.read()

            # Create patch object directly from string (no temporary file needed!)
            patch_set = _parse_patch(params.diff.encode("utf-8"))

            # Handle case where parsing failed
            if patch_set is None:
                return ToolError(
                    message=(
                        "Failed to parse diff content: invalid patch format or no valid hunks found"
                    ),
                    brief="Invalid diff format",
                )

            # Count total hunks across all items
            total_hunks = _count_hunks(patch_set)

            if total_hunks == 0:
                return ToolError(
                    message="No valid hunks found in the diff content",
                    brief="No hunks found",
                )

            # Apply the patch
            success = _apply_patch(patch_set, str(p.parent))

            if not success:
                return ToolError(
                    message=(
                        "Failed to apply patch - patch may not be compatible with the file content"
                    ),
                    brief="Patch application failed",
                )

            # Read the modified content to check if changes were made
            async with aiofiles.open(p, encoding="utf-8", errors="replace") as f:
                modified_content = await f.read()

            # Check if any changes were made
            if modified_content == original_content:
                return ToolError(
                    message="No changes were made. The patch does not apply to the file.",
                    brief="No changes made",
                )

            return ToolOk(
                output="",
                message=(
                    f"File successfully patched. Applied {total_hunks} hunk(s) to {params.path}."
                ),
            )

        except Exception as e:
            return ToolError(
                message=f"Failed to patch file. Error: {e}",
                brief="Failed to patch file",
            )

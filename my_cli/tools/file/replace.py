"""
StrReplaceFile 工具 ⭐ Stage 27

功能：字符串替换编辑文件
- 支持单次替换和全局替换
- 支持批量编辑（多个替换操作）
- 路径安全检查（必须在工作目录内）
- 集成 Approval 系统（需要用户批准）

对应源码：kimi-cli-fork/src/kimi_cli/tools/file/replace.py
"""
from pathlib import Path
from typing import Any, override

import aiofiles
from kosong.tooling import CallableTool2, ToolError, ToolOk, ToolReturnType
from pydantic import BaseModel, Field

from my_cli.soul.approval import Approval
from my_cli.soul.runtime import BuiltinSystemPromptArgs
from my_cli.tools.file import FileActions
from my_cli.tools.utils import ToolRejectedError, load_desc


class Edit(BaseModel):
    old: str = Field(description="The old string to replace. Can be multi-line.")
    new: str = Field(description="The new string to replace with. Can be multi-line.")
    replace_all: bool = Field(description="Whether to replace all occurrences.", default=False)


class Params(BaseModel):
    path: str = Field(description="The absolute path to the file to edit.")
    edit: Edit | list[Edit] = Field(
        description=(
            "The edit(s) to apply to the file. "
            "You can provide a single edit or a list of edits here."
        )
    )


class StrReplaceFile(CallableTool2[Params]):
    name: str = "StrReplaceFile"
    description: str = load_desc(Path(__file__).parent / "replace.md")
    params: type[Params] = Params

    def __init__(self, builtin_args: BuiltinSystemPromptArgs, approval: Approval, **kwargs: Any):
        super().__init__(**kwargs)
        self._work_dir = builtin_args.MY_CLI_WORK_DIR
        self._approval = approval

    def _validate_path(self, path: Path) -> ToolError | None:
        """验证路径安全性（必须在工作目录内）"""
        # Check for path traversal attempts
        resolved_path = path.resolve()
        resolved_work_dir = self._work_dir.resolve()

        # Ensure the path is within work directory
        if not str(resolved_path).startswith(str(resolved_work_dir)):
            return ToolError(
                message=(
                    f"`{path}` is outside the working directory. "
                    "You can only edit files within the working directory."
                ),
                brief="Path outside working directory",
            )
        return None

    def _apply_edit(self, content: str, edit: Edit) -> str:
        """应用单个编辑到内容"""
        if edit.replace_all:
            return content.replace(edit.old, edit.new)
        else:
            return content.replace(edit.old, edit.new, 1)

    @override
    async def __call__(self, params: Params) -> ToolReturnType:
        try:
            p = Path(params.path)

            if not p.is_absolute():
                return ToolError(
                    message=(
                        f"`{params.path}` is not an absolute path. "
                        "You must provide an absolute path to edit a file."
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
                f"Edit file `{params.path}`",
            ):
                return ToolRejectedError()

            # Read the file content
            async with aiofiles.open(p, encoding="utf-8", errors="replace") as f:
                content = await f.read()

            original_content = content
            edits = [params.edit] if isinstance(params.edit, Edit) else params.edit

            # Apply all edits
            for edit in edits:
                content = self._apply_edit(content, edit)

            # Check if any changes were made
            if content == original_content:
                return ToolError(
                    message="No replacements were made. The old string was not found in the file.",
                    brief="No replacements made",
                )

            # Write the modified content back to the file
            async with aiofiles.open(p, mode="w", encoding="utf-8") as f:
                await f.write(content)

            # Count changes for success message
            total_replacements = 0
            for edit in edits:
                if edit.replace_all:
                    total_replacements += original_content.count(edit.old)
                else:
                    total_replacements += 1 if edit.old in original_content else 0

            return ToolOk(
                output="",
                message=(
                    f"File successfully edited. "
                    f"Applied {len(edits)} edit(s) with {total_replacements} total replacement(s)."
                ),
            )

        except Exception as e:
            return ToolError(
                message=f"Failed to edit. Error: {e}",
                brief="Failed to edit file",
            )

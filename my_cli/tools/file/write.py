"""
WriteFile 工具 ⭐ Stage 27

功能：写入内容到文件
- 支持两种模式：overwrite（覆盖）、append（追加）
- 路径安全检查（必须在工作目录内）
- 集成 Approval 系统（需要用户批准）

对应源码：kimi-cli-fork/src/kimi_cli/tools/file/write.py
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, override

import aiofiles
from kosong.tooling import CallableTool2, ToolError, ToolOk, ToolReturnType
from pydantic import BaseModel, Field

from my_cli.tools.utils import ToolRejectedError, load_desc

if TYPE_CHECKING:
    from my_cli.soul.approval import Approval
    from my_cli.soul.runtime import BuiltinSystemPromptArgs


class Params(BaseModel):
    """WriteFile 工具参数"""

    path: str = Field(description="The absolute path to the file to write")
    content: str = Field(description="The content to write to the file")
    mode: Literal["overwrite", "append"] = Field(
        description=(
            "The mode to use to write to the file. "
            "Two modes are supported: `overwrite` for overwriting the whole file and "
            "`append` for appending to the end of an existing file."
        ),
        default="overwrite",
    )


class WriteFile(CallableTool2[Params]):
    """
    WriteFile 工具 - 写入文件内容 ⭐ Stage 27

    功能：
    - 写入或追加内容到文件
    - 路径安全检查（必须在工作目录内）
    - 需要用户批准（Approval）

    对应源码：kimi-cli-fork/src/kimi_cli/tools/file/write.py:27-119
    """

    name: str = "WriteFile"
    description: str = load_desc(Path(__file__).parent / "write.md")
    params: type[Params] = Params

    def __init__(
        self, builtin_args: BuiltinSystemPromptArgs, approval: Approval, **kwargs: Any
    ):
        """
        初始化 WriteFile 工具

        Args:
            builtin_args: 内置参数（用于获取工作目录）
            approval: Approval 实例（用于请求用户批准）
            **kwargs: 其他参数
        """
        super().__init__(**kwargs)
        self._work_dir = builtin_args.KIMI_WORK_DIR
        self._approval = approval

    def _validate_path(self, path: Path) -> ToolError | None:
        """
        验证路径安全性（必须在工作目录内）

        Args:
            path: 要验证的路径

        Returns:
            ToolError: 路径不安全
            None: 路径安全
        """
        # 检查路径遍历攻击
        resolved_path = path.resolve()
        resolved_work_dir = self._work_dir.resolve()

        # 确保路径在工作目录内
        if not str(resolved_path).startswith(str(resolved_work_dir)):
            return ToolError(
                message=(
                    f"`{path}` is outside the working directory. "
                    "You can only write files within the working directory."
                ),
                brief="Path outside working directory",
            )

        return None

    @override
    async def __call__(self, params: Params) -> ToolReturnType:
        """
        写入文件内容

        Args:
            params: 工具参数

        Returns:
            ToolOk: 成功写入文件
            ToolError: 写入失败
        """
        # TODO: 未来功能
        # - 检查文件是否可能包含敏感信息（secrets）
        # - 检查文件格式是否可写

        try:
            p = Path(params.path)

            # 1. 验证路径
            if not p.is_absolute():
                return ToolError(
                    message=(
                        f"`{params.path}` is not an absolute path. "
                        "You must provide an absolute path to write a file."
                    ),
                    brief="Invalid path",
                )

            # 2. 路径安全检查
            path_error = self._validate_path(p)
            if path_error:
                return path_error

            # 3. 检查父目录是否存在
            if not p.parent.exists():
                return ToolError(
                    message=f"`{params.path}` parent directory does not exist.",
                    brief="Parent directory not found",
                )

            # 4. 验证模式参数
            if params.mode not in ["overwrite", "append"]:
                return ToolError(
                    message=(
                        f"Invalid write mode: `{params.mode}`. "
                        "Mode must be either `overwrite` or `append`."
                    ),
                    brief="Invalid write mode",
                )

            # 5. 请求用户批准
            # 导入 FileActions（延迟导入避免循环依赖）
            from my_cli.tools.file import FileActions

            if not await self._approval.request(
                self.name,
                FileActions.EDIT,
                f"Write file `{params.path}`",
            ):
                return ToolRejectedError()

            # 6. 确定文件打开模式
            file_mode = "w" if params.mode == "overwrite" else "a"

            # 7. 写入文件
            async with aiofiles.open(p, mode=file_mode, encoding="utf-8") as f:
                await f.write(params.content)

            # 8. 获取文件信息
            file_size = p.stat().st_size
            action = "overwritten" if params.mode == "overwrite" else "appended to"

            return ToolOk(
                output="",
                message=f"File successfully {action}. Current size: {file_size} bytes.",
            )

        except Exception as e:
            return ToolError(
                message=f"Failed to write to {params.path}. Error: {e}",
                brief="Failed to write file",
            )


__all__ = ["WriteFile"]

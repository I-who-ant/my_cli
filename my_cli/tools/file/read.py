"""
ReadFile 工具 ⭐ Stage 27

功能：从文件读取内容
- 支持分页读取（line_offset, n_lines）
- 限制最大行数（1000 行）
- 限制最大行长度（2000 字符）
- 限制最大字节数（100KB）
- 输出格式类似 `cat -n`（带行号）

对应源码：kimi-cli-fork/src/kimi_cli/tools/file/read.py
"""

from pathlib import Path
from typing import Any, override

import aiofiles
from kosong.tooling import CallableTool2, ToolError, ToolOk, ToolReturnType
from pydantic import BaseModel, Field

from my_cli.soul.runtime import BuiltinSystemPromptArgs
from my_cli.tools.utils import load_desc, truncate_line

# 读取限制
MAX_LINES = 1000
"""最大读取行数"""

MAX_LINE_LENGTH = 2000
"""最大行长度（字符）"""

MAX_BYTES = 100 << 10  # 100KB
"""最大读取字节数"""


class Params(BaseModel):
    """ReadFile 工具参数"""

    path: str = Field(description="The absolute path to the file to read")
    line_offset: int = Field(
        description=(
            "The line number to start reading from. "
            "By default read from the beginning of the file. "
            "Set this when the file is too large to read at once."
        ),
        default=1,
        ge=1,
    )
    n_lines: int = Field(
        description=(
            "The number of lines to read. "
            f"By default read up to {MAX_LINES} lines, which is the max allowed value. "
            "Set this value when the file is too large to read at once."
        ),
        default=MAX_LINES,
        ge=1,
    )


class ReadFile(CallableTool2[Params]):
    """
    ReadFile 工具 - 读取文件内容 ⭐ Stage 27

    功能：
    - 读取文件内容（支持分页）
    - 输出格式：行号 + Tab + 内容（类似 cat -n）
    - 自动截断过长的行
    - 限制最大读取量

    对应源码：kimi-cli-fork/src/kimi_cli/tools/file/read.py:38-140
    """

    name: str = "ReadFile"
    description: str = load_desc(
        Path(__file__).parent / "read.md",
        {
            "MAX_LINES": str(MAX_LINES),
            "MAX_LINE_LENGTH": str(MAX_LINE_LENGTH),
            "MAX_BYTES": str(MAX_BYTES),
        },
    )
    params: type[Params] = Params

    def __init__(self, builtin_args: BuiltinSystemPromptArgs, **kwargs: Any) -> None:
        """
        初始化 ReadFile 工具

        Args:
            builtin_args: 内置参数（用于获取工作目录）
            **kwargs: 其他参数
        """
        super().__init__(**kwargs)
        self._work_dir = builtin_args.MY_CLI_WORK_DIR

    @override
    async def __call__(self, params: Params) -> ToolReturnType:
        """
        读取文件内容

        Args:
            params: 工具参数

        Returns:
            ToolOk: 成功读取文件
            ToolError: 读取失败
        """
        # TODO: 未来功能
        # - 检查文件是否可能包含敏感信息（secrets）
        # - 检查文件格式是否可读

        try:
            p = Path(params.path)

            # 1. 验证路径
            if not p.is_absolute():
                return ToolError(
                    message=(
                        f"`{params.path}` is not an absolute path. "
                        "You must provide an absolute path to read a file."
                    ),
                    brief="Invalid path",
                )

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

            # 2. 验证参数
            assert params.line_offset >= 1
            assert params.n_lines >= 1

            # 3. 读取文件
            lines: list[str] = []
            n_bytes = 0
            truncated_line_numbers: list[int] = []
            max_lines_reached = False
            max_bytes_reached = False

            async with aiofiles.open(p, encoding="utf-8", errors="replace") as f:
                current_line_no = 0

                async for line in f:
                    current_line_no += 1

                    # 跳过偏移之前的行
                    if current_line_no < params.line_offset:
                        continue

                    # 截断过长的行
                    truncated = truncate_line(line, MAX_LINE_LENGTH)
                    if truncated != line:
                        truncated_line_numbers.append(current_line_no)

                    lines.append(truncated)
                    n_bytes += len(truncated.encode("utf-8"))

                    # 检查是否达到行数限制
                    if len(lines) >= params.n_lines:
                        break

                    # 检查是否达到最大行数
                    if len(lines) >= MAX_LINES:
                        max_lines_reached = True
                        break

                    # 检查是否达到最大字节数
                    if n_bytes >= MAX_BYTES:
                        max_bytes_reached = True
                        break

            # 4. 格式化输出（类似 cat -n）
            lines_with_no: list[str] = []
            for line_num, line in zip(
                range(params.line_offset, params.line_offset + len(lines)),
                lines,
                strict=True,
            ):
                # 6位行号，右对齐，Tab 分隔
                lines_with_no.append(f"{line_num:6d}\t{line}")

            # 5. 构建消息
            message = (
                f"{len(lines)} lines read from file starting from line {params.line_offset}."
                if len(lines) > 0
                else "No lines read from file."
            )

            if max_lines_reached:
                message += f" Max {MAX_LINES} lines reached."
            elif max_bytes_reached:
                message += f" Max {MAX_BYTES} bytes reached."
            elif len(lines) < params.n_lines:
                message += " End of file reached."

            if truncated_line_numbers:
                message += f" Lines {truncated_line_numbers} were truncated."

            return ToolOk(
                output="".join(lines_with_no),  # 行已包含 \n，直接拼接
                message=message,
            )

        except Exception as e:
            return ToolError(
                message=f"Failed to read {params.path}. Error: {e}",
                brief="Failed to read file",
            )


__all__ = ["ReadFile"]

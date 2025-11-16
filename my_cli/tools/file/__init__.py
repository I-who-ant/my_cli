"""
Stage 7 增强：File 工具实现

功能：
- ReadFile: 读取文件内容
- WriteFile: 写入文件内容

核心技术：
1. pathlib.Path - 路径操作
2. CallableTool2[Params] - 类型化工具基类
3. ToolResultBuilder - 输出限制（Stage 7 增强）⭐
4. load_desc() - 描述加载（Stage 7 增强）⭐

对应源码：kimi-cli-fork/src/kimi_cli/tools/file/__init__.py
"""

from __future__ import annotations

from pathlib import Path
from typing import override

from kosong.tooling import CallableTool2, ToolError, ToolReturnType
from pydantic import BaseModel, Field

from my_cli.tools.utils import ToolResultBuilder, load_desc

__all__ = ["ReadFile", "WriteFile"]


class ReadFileParams(BaseModel):
    """ReadFile 工具参数"""

    path: str = Field(description="The path to the file to read.")


class WriteFileParams(BaseModel):
    """WriteFile 工具参数"""

    path: str = Field(description="The path to the file to write.")
    content: str = Field(description="The content to write to the file.")


class ReadFile(CallableTool2[ReadFileParams]):
    """
    ReadFile 工具 - 读取文件内容

    Stage 7 增强：
    - ✅ 使用 ToolResultBuilder（输出限制）
    - ✅ 使用 load_desc()（描述管理）

    示例：
        read_file = ReadFile()
        result = await read_file.call({"path": "/path/to/file.txt"})
    """

    name: str = "ReadFile"
    description: str = load_desc(Path(__file__).parent / "readfile.md")  # ⭐ 从文件加载
    params: type[ReadFileParams] = ReadFileParams

    @override
    async def __call__(self, params: ReadFileParams) -> ToolReturnType:
        """读取文件内容（使用 ToolResultBuilder 限制输出）"""
        try:
            file_path = Path(params.path)

            # 检查文件是否存在
            if not file_path.exists():
                return ToolError(
                    message=f"File does not exist: {params.path}",
                    brief="File not found",
                )

            # 检查是否是文件
            if not file_path.is_file():
                return ToolError(
                    message=f"Path is not a file: {params.path}",
                    brief="Not a file",
                )

            # ⭐ 创建结果构建器
            builder = ToolResultBuilder()

            # 读取文件内容
            content = file_path.read_text(encoding="utf-8", errors="replace")

            # ⭐ 使用 builder 写入内容（自动截断）
            builder.write(content)

            # ⭐ 生成结果（自动添加截断提示）
            return builder.ok(
                message=f"File read successfully: {params.path}",
                brief=f"Read {builder.n_chars} chars",
            )

        except PermissionError:
            return ToolError(
                message=f"Permission denied: {params.path}",
                brief="Permission denied",
            )
        except Exception as e:
            return ToolError(
                message=f"Failed to read file: {e}",
                brief="Read failed",
            )


class WriteFile(CallableTool2[WriteFileParams]):
    """
    WriteFile 工具 - 写入文件内容

    Stage 7 增强：
    - ✅ 使用 load_desc()（描述管理）

    示例:
        write_file = WriteFile()
        result = await write_file.call({
            "path": "/path/to/file.txt",
            "content": "Hello, World!"
        })
    """

    name: str = "WriteFile"
    description: str = load_desc(Path(__file__).parent / "writefile.md")  # ⭐ 从文件加载
    params: type[WriteFileParams] = WriteFileParams

    @override
    async def __call__(self, params: WriteFileParams) -> ToolReturnType:
        """写入文件内容"""
        try:
            file_path = Path(params.path)

            # 创建父目录（如果不存在）
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # 写入文件内容
            file_path.write_text(params.content, encoding="utf-8")

            # ⭐ WriteFile 不需要 ToolResultBuilder（输出很小）
            from kosong.tooling import ToolOk
            return ToolOk(
                output=f"File written successfully: {params.path}",
                message=f"Wrote {len(params.content)} characters to {params.path}",
                brief=f"Wrote {len(params.content)} chars",
            )

        except PermissionError:
            return ToolError(
                message=f"Permission denied: {params.path}",
                brief="Permission denied",
            )
        except Exception as e:
            return ToolError(
                message=f"Failed to write file: {e}",
                brief="Write failed",
            )

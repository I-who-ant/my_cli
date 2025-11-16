"""
Stage 7 增强：Bash 工具实现

功能：执行 bash 命令并返回输出

核心技术：
1. asyncio.create_subprocess_shell - 异步子进程
2. asyncio.StreamReader - 流式读取输出
3. asyncio.wait_for - 超时控制
4. CallableTool2[Params] - 类型化工具基类
5. ToolResultBuilder - 输出限制（Stage 7 增强）⭐
6. load_desc() - 描述加载（Stage 7 增强）⭐

对应源码：kimi-cli-fork/src/kimi_cli/tools/bash/__init__.py
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from pathlib import Path
from typing import override

from kosong.tooling import CallableTool2, ToolReturnType
from pydantic import BaseModel, Field

from my_cli.tools.utils import ToolResultBuilder, load_desc

__all__ = ["Bash"]

# 最大超时时间（5分钟）
MAX_TIMEOUT = 5 * 60


class Params(BaseModel):
    """Bash 工具参数"""

    command: str = Field(description="The bash command to execute.")
    timeout: int = Field(
        description=(
            "The timeout in seconds for the command to execute. "
            "If the command takes longer than this, it will be killed."
        ),
        default=60,
        ge=1,
        le=MAX_TIMEOUT,
    )


class Bash(CallableTool2[Params]):
    """
    Bash 工具 - 执行 bash 命令

    Stage 7 增强：
    - ✅ 使用 ToolResultBuilder（输出限制）
    - ✅ 使用 load_desc()（描述管理）

    示例：
        bash = Bash()
        result = await bash.call({"command": "ls -la", "timeout": 30})
    """

    name: str = "Bash"
    description: str = load_desc(Path(__file__).parent / "bash.md")  # ⭐ 从文件加载
    params: type[Params] = Params

    @override
    async def __call__(self, params: Params) -> ToolReturnType:
        """执行 bash 命令（使用 ToolResultBuilder 限制输出）"""
        # ⭐ 创建结果构建器（自动限制输出大小）
        builder = ToolResultBuilder()

        def stdout_cb(line: bytes):
            """标准输出回调"""
            line_str = line.decode(encoding="utf-8", errors="replace")
            builder.write(line_str)  # ⭐ 使用 builder 而不是 append

        def stderr_cb(line: bytes):
            """标准错误回调"""
            line_str = line.decode(encoding="utf-8", errors="replace")
            builder.write(line_str)  # ⭐ 使用 builder

        try:
            # 执行命令并流式读取输出
            exitcode = await _stream_subprocess(
                params.command, stdout_cb, stderr_cb, params.timeout
            )

            # ⭐ 使用 builder 生成结果（自动添加截断提示）
            if exitcode == 0:
                return builder.ok(
                    message="Command executed successfully",
                    brief="Success"
                )
            else:
                return builder.error(
                    message=f"Command failed with exit code: {exitcode}",
                    brief=f"Failed (exit code: {exitcode})",
                )

        except TimeoutError:
            # ⭐ 超时也使用 builder（保留已有输出）
            return builder.error(
                message=f"Command killed by timeout ({params.timeout}s)",
                brief=f"Timeout ({params.timeout}s)",
            )




async def _stream_subprocess( #
    command: str,
    stdout_cb: Callable[[bytes], None],
    stderr_cb: Callable[[bytes], None],
    timeout: int,
) -> int:
    """
    异步执行子进程并流式读取输出

    Args:
        command: bash 命令
        stdout_cb: 标准输出回调
        stderr_cb: 标准错误回调
        timeout: 超时时间（秒）

    Returns:
        进程退出码

    Raises:
        TimeoutError: 超时
    """

    async def _read_stream(stream: asyncio.StreamReader, cb: Callable[[bytes], None]):
        """流式读取输出"""
        while True:
            line = await stream.readline()
            if line:
                cb(line)
            else:
                break

    # 创建子进程
    process = await asyncio.create_subprocess_shell(
        command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )

    assert process.stdout is not None, "stdout is None"
    assert process.stderr is not None, "stderr is None"

    try:
        # 并发读取 stdout 和 stderr
        await asyncio.wait_for(
            asyncio.gather(
                _read_stream(process.stdout, stdout_cb),
                _read_stream(process.stderr, stderr_cb),
            ),
            timeout,
        )
        return await process.wait()

    except TimeoutError:
        # 超时，杀死进程
        process.kill()
        await process.wait()
        raise
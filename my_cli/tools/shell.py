"""
Shell 工具 - 执行系统命令

学习目标：
1. 使用 asyncio 创建异步子进程
2. 捕获 stdout 和 stderr
3. 处理进程返回码

对应源码：kimi-cli-fork/src/kimi_cli/tools/bash.py
"""

import asyncio
from typing import Any


async def execute_shell(command: str, timeout: float = 30.0) -> dict[str, Any]:
    """执行 Shell 命令.

    Args:
        command: Shell 命令字符串
        timeout: 超时时间（秒），默认 30 秒

    Returns:
        包含执行结果的字典：
        {
            "stdout": str,      # 标准输出
            "stderr": str,      # 标准错误
            "return_code": int, # 返回码（0 表示成功）
            "success": bool,    # 是否成功执行
        }

    Raises:
        asyncio.TimeoutError: 执行超时
    """
    # 创建异步子进程
    # shell=True 允许执行 shell 命令（如管道、重定向等）
    proc = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,  # 捕获标准输出
        stderr=asyncio.subprocess.PIPE,  # 捕获标准错误
    )

    try:
        # 等待进程完成，设置超时
        stdout_bytes, stderr_bytes = await asyncio.wait_for(
            proc.communicate(), timeout=timeout
        )
    except asyncio.TimeoutError:
        # 超时，杀死进程
        proc.kill()
        await proc.wait()
        raise asyncio.TimeoutError(f"命令执行超时（{timeout}秒）: {command}")

    # 解码输出（处理可能的编码错误）
    stdout = stdout_bytes.decode("utf-8", errors="replace")
    stderr = stderr_bytes.decode("utf-8", errors="replace")

    return {
        "stdout": stdout,
        "stderr": stderr,
        "return_code": proc.returncode or 0,
        "success": proc.returncode == 0,
    }


# 测试代码
async def test_shell():
    """测试 Shell 工具."""
    print("测试 1: 简单命令")
    result = await execute_shell("echo 'Hello World'")
    print(f"  stdout: {result['stdout'].strip()}")
    print(f"  success: {result['success']}")
    print()

    print("测试 2: 列出文件")
    result = await execute_shell("ls -la | head -5")
    print(f"  stdout:\n{result['stdout']}")
    print()

    print("测试 3: 错误命令")
    result = await execute_shell("command_not_exist")
    print(f"  stderr: {result['stderr'].strip()}")
    print(f"  success: {result['success']}")
    print()


if __name__ == "__main__":
    # 运行测试
    asyncio.run(test_shell())
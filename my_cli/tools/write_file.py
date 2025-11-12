"""
WriteFile 工具 - 写入文件

学习目标：
1. 文件写入
2. 目录自动创建
3. 错误处理

对应源码：kimi-cli-fork/src/kimi_cli/tools/write_file.py
"""

from pathlib import Path


async def write_file(file_path: str, content: str) -> str:
    """写入文件.

    Args:
        file_path: 文件路径
        content: 文件内容

    Returns:
        成功消息

    Raises:
        ValueError: 文件路径无效
    """
    path = Path(file_path).expanduser().resolve()

    # 验证父目录
    if path.parent.exists() and not path.parent.is_dir():
        raise ValueError(f"父路径不是目录: {path.parent}")

    # 创建父目录（如果不存在）
    path.parent.mkdir(parents=True, exist_ok=True)

    # 写入文件
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception as e:
        raise ValueError(f"写入文件失败: {e}")

    # 统计信息
    lines = content.count("\n") + (1 if content and not content.endswith("\n") else 0)
    bytes_written = len(content.encode("utf-8"))

    return f"✅ 文件已写入: {file_path} ({lines} 行, {bytes_written} 字节)"


# 测试代码
async def test_write_file():
    """测试 WriteFile 工具."""
    import tempfile

    print("测试 1: 写入简单文件")
    temp_file = tempfile.mktemp(suffix=".txt")
    result = await write_file(temp_file, "Hello World\nLine 2\nLine 3")
    print(f"  {result}")
    print()

    print("测试 2: 验证写入内容")
    with open(temp_file, "r") as f:
        content = f.read()
    print(f"  内容: {content!r}")
    print()

    print("测试 3: 写入到不存在的目录")
    deep_path = f"{tempfile.gettempdir()}/test_dir/subdir/file.txt"
    result = await write_file(deep_path, "Deep file content")
    print(f"  {result}")
    print()

    # 清理
    import os

    os.remove(temp_file)
    os.remove(deep_path)
    os.removedirs(Path(deep_path).parent)


if __name__ == "__main__":
    import asyncio

    asyncio.run(test_write_file())
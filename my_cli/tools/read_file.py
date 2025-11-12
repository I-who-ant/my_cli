"""
ReadFile 工具 - 读取文件内容

学习目标：
1. 异步文件读取
2. 行号显示
3. 范围限制（offset + limit）

对应源码：kimi-cli-fork/src/kimi_cli/tools/read_file.py
"""

from pathlib import Path


async def read_file(
    file_path: str,
    offset: int = 0,
    limit: int = 2000,
) -> str:
    """读取文件内容（带行号）.

    Args:
        file_path: 文件路径
        offset: 起始行号（从 0 开始）
        limit: 最多读取多少行（默认 2000 行）

    Returns:
        文件内容，格式：
        ```
             1→第一行内容
             2→第二行内容
             3→第三行内容
        ```

    Raises:
        FileNotFoundError: 文件不存在
        ValueError: 不是文件
    """
    path = Path(file_path).expanduser().resolve()

    # 验证文件
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")

    if not path.is_file():
        raise ValueError(f"不是文件: {file_path}")

    # 读取文件
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            all_lines = f.readlines()
    except Exception as e:
        raise ValueError(f"读取文件失败: {e}")

    # 获取总行数
    total_lines = len(all_lines)

    # 范围检查
    if offset < 0:
        offset = 0
    if offset >= total_lines:
        return f"❌ 起始行号 {offset} 超出范围（总行数：{total_lines}）"

    # 截取指定范围
    end = min(offset + limit, total_lines)
    selected_lines = all_lines[offset:end]

    # 添加行号（格式：右对齐，固定宽度）
    result_lines = []
    for i, line in enumerate(selected_lines, start=offset + 1):
        # 去除行尾换行符
        line_content = line.rstrip("\n")
        # 格式：行号→内容
        result_lines.append(f"{i:6d}→{line_content}")

    # 添加提示信息
    if end < total_lines:
        result_lines.append("")
        result_lines.append(
            f"... ({total_lines - end} 行未显示，使用 offset={end} 继续读取)"
        )

    return "\n".join(result_lines)


# 测试代码
async def test_read_file():
    """测试 ReadFile 工具."""
    print("测试 1: 读取自己")
    result = await read_file(__file__, offset=0, limit=10)
    print(result)
    print()

    print("测试 2: 读取不存在的文件")
    try:
        await read_file("/tmp/not_exist.txt")
    except FileNotFoundError as e:
        print(f"  ✅ 正确捕获异常: {e}")
    print()

    print("测试 3: 读取大文件（带 offset）")
    result = await read_file(__file__, offset=20, limit=5)
    print(result)
    print()


if __name__ == "__main__":
    import asyncio

    asyncio.run(test_read_file())
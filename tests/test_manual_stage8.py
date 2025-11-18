"""
Stage 8 手动测试脚本

直接测试工具调用功能，无需 pytest
"""

import asyncio
from pathlib import Path

from my_cli.soul import create_soul, run_soul
from my_cli.ui.print import PrintUI


async def main():
    """手动测试 Stage 8 工具调用"""
    print("=" * 60)
    print("🧪 Stage 8 工具调用手动测试")
    print("=" * 60)

    # 创建 Print UI
    ui = PrintUI(verbose=True, work_dir=Path.cwd())

    # 测试 1：Bash 工具
    print("\n\n📝 测试 1: Bash 工具\n")
    print("-" * 60)
    await ui.run("请使用 Bash 工具执行命令: echo 'Hello Stage 8'")

    # 测试 2：ReadFile 工具
    print("\n\n📝 测试 2: ReadFile 工具\n")
    print("-" * 60)

    # 创建测试文件
    test_file = Path.cwd() / "test_stage8.txt"
    test_file.write_text("Stage 8 工具调用测试成功！\n这是第二行内容。")

    try:
        await ui.run(f"请使用 ReadFile 工具读取文件: {test_file}")
    finally:
        # 清理
        if test_file.exists():
            test_file.unlink()

    # 测试 3：组合工具调用
    print("\n\n📝 测试 3: 组合工具调用\n")
    print("-" * 60)
    await ui.run("请先用 Bash 列出当前目录的 .py 文件，然后读取 setup.py 的前 5 行")

    print("\n\n" + "=" * 60)
    print("✅ Stage 8 手动测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
"""
Stage 14 测试脚本：FileMentionCompleter @ 文件路径自动补全

测试目标：
1. ✅ @ 触发文件路径补全
2. ✅ 显示当前目录下的文件和目录
3. ✅ 目录添加 / 后缀
4. ✅ 忽略缓存目录（.git, node_modules, __pycache__ 等）
5. ✅ 支持子目录路径补全（@my_cli/<Tab>）

操作说明：
1. 运行脚本，在提示符处输入
2. 输入 @ 然后按 Tab 键，查看补全列表
3. 输入 @m 然后按 Tab 键，查看匹配 m 开头的文件
4. 输入 @my_cli/ 然后按 Tab 键，查看子目录内容
5. 输入 /help 然后按 Tab 键，测试命令补全仍然正常
6. 按 Ctrl+D 退出

预期结果：
- @ + Tab：显示所有文件和目录（排除 .git 等）
- @m + Tab：显示 m 开头的文件/目录
- @my_cli/ + Tab：显示 my_cli 目录下的内容
- /h + Tab：显示 /help 命令补全
"""

import asyncio
from pathlib import Path

from my_cli.ui.shell.prompt import CustomPromptSession


async def test_file_mention():
    """测试文件路径补全"""
    print("=" * 60)
    print("Stage 14 测试：FileMentionCompleter @ 文件路径补全")
    print("=" * 60)
    print("\n操作说明：")
    print("1. 输入 @ 然后按 Tab 键，查看所有文件/目录")
    print("2. 输入 @m 然后按 Tab 键，查看 m 开头的文件")
    print("3. 输入 @my_cli/ 然后按 Tab 键，查看子目录内容")
    print("4. 输入 /h 然后按 Tab 键，测试命令补全")
    print("5. 按 Ctrl+D 退出测试")
    print("\n预期效果：")
    print("- @ 触发文件路径补全")
    print("- 目录显示 / 后缀")
    print("- 忽略 .git、node_modules、__pycache__ 等")
    print("=" * 60)
    print()

    # 创建 CustomPromptSession
    work_dir = Path.cwd()
    session = CustomPromptSession(
        work_dir=work_dir,
        enable_file_history=False,  # 测试时不保存历史
        enable_completer=True,  # ⭐ 启用自动补全
    )

    print("✅ CustomPromptSession 已创建")
    print(f"📂 工作目录: {work_dir}")
    print(f"⚙️  自动补全: 已启用")
    print()

    # 循环输入，直到 Ctrl+D
    try:
        while True:
            # 获取用户输入
            user_input = await session.prompt()

            # 显示输入内容
            print(f"\n你输入了: {user_input.command}")
            print()

            # 如果输入是 /exit 或 /quit，退出
            if user_input.command.lower() in ["/exit", "/quit"]:
                print("👋 退出测试...")
                break

    except EOFError:
        # Ctrl+D 退出
        print("\n\n✅ 测试完成（Ctrl+D）")
    except KeyboardInterrupt:
        # Ctrl+C 退出
        print("\n\n✅ 测试完成（Ctrl+C）")

    print("\n" + "=" * 60)
    print("Stage 14 测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_file_mention())

#!/usr/bin/env python3
"""
Stage 13 测试脚本：状态栏和模式切换

测试目标：
1. ✅ 状态栏显示时间（HH:MM 格式）
2. ✅ 状态栏显示当前模式（agent/shell）
3. ✅ 状态栏显示快捷键提示
4. ✅ Ctrl+X 切换模式（agent ↔ shell）
5. ✅ 模式切换后状态栏实时更新

操作说明：
1. 运行脚本，观察底部状态栏
2. 按 Ctrl+X 切换模式，观察状态栏变化
3. 输入一些文本，确认输入功能正常
4. 按 Ctrl+D 退出

预期结果：
- 底部状态栏显示：[时间] [模式(背景色)] [快捷键提示]
- Agent 模式：青色背景 (bg:#4ecdc4)
- Shell 模式：红色背景 (bg:#ff6b6b)
- Ctrl+X 切换后，状态栏立即更新
"""

import asyncio
from pathlib import Path

from my_cli.ui.shell.prompt import CustomPromptSession


async def test_statusbar():
    """测试状态栏和模式切换"""
    print("=" * 60)
    print("Stage 13 测试：状态栏和模式切换")
    print("=" * 60)
    print("\n操作说明：")
    print("1. 观察底部状态栏（时间 + 模式 + 快捷键提示）")
    print("2. 按 Ctrl+X 切换模式（agent ↔ shell）")
    print("3. 观察模式切换后状态栏的颜色变化")
    print("4. 按 Ctrl+D 退出测试")
    print("\n预期效果：")
    print("- Agent 模式：青色背景 🟦")
    print("- Shell 模式：红色背景 🟥")
    print("- 时间每分钟自动更新")
    print("=" * 60)
    print()

    # 创建 CustomPromptSession
    work_dir = Path.cwd()
    session = CustomPromptSession(
        work_dir=work_dir,
        enable_file_history=False,  # 测试时不保存历史
        enable_completer=True,
    )

    print("✅ CustomPromptSession 已创建")
    print(f"📂 工作目录: {work_dir}")
    print(f"⚙️  初始模式: {session._mode}")
    print()

    # 循环输入，直到 Ctrl+D
    try:
        while True:
            # 获取用户输入
            user_input = await session.prompt()

            # 显示输入内容和当前模式
            print(f"\n你输入了: {user_input.command}")
            print(f"当前模式: {user_input.mode}")
            print(f"Session 模式: {session._mode}")
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
    print("Stage 13 测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_statusbar())

#!/usr/bin/env python3
"""
Stage 15 测试脚本：扩展状态栏信息

测试目标：
1. ✅ 显示时间（HH:MM 格式）
2. ✅ 显示模型名称 ⭐ Stage 15 新增
3. ✅ 显示当前模式（agent/shell）
4. ✅ 显示快捷键提示
5. ✅ 显示 Context 使用率（右对齐）⭐ Stage 15 新增
6. ✅ 模拟 Context 使用率动态更新

操作说明：
1. 运行脚本，观察底部状态栏
2. 状态栏显示：时间 + 模型 + 模式 + 快捷键 + Context使用率
3. 按 Ctrl+X 切换模式，观察状态栏变化
4. 输入 "update" 模拟 Context 使用率增加
5. 按 Ctrl+D 退出

预期结果：
- 状态栏格式：[时间]  [model:moonshot-v1]  [agent]  [快捷键提示]  ...  [context: 35.0%]
- Context 使用率右对齐显示
- 模式切换后，模式背景色变化
- 输入 "update" 后，Context 使用率增加 10%
"""

import asyncio
from pathlib import Path

from my_cli.ui.shell.prompt import CustomPromptSession


async def test_statusbar_enhanced():
    """测试扩展状态栏"""
    print("=" * 80)
    print("Stage 15 测试：扩展状态栏信息")
    print("=" * 80)
    print("\n操作说明：")
    print("1. 观察底部状态栏（时间 + 模型 + 模式 + 快捷键 + Context使用率）")
    print("2. 按 Ctrl+X 切换模式（agent ↔ shell）")
    print("3. 输入 'update' 模拟 Context 使用率增加 10%")
    print("4. 按 Ctrl+D 退出测试")
    print("\n预期效果：")
    print("- 状态栏左侧：时间、模型、模式、快捷键")
    print("- 状态栏右侧：Context 使用率（右对齐）")
    print("- 模式切换后，背景色变化")
    print("=" * 80)
    print()

    # 创建 CustomPromptSession ⭐ Stage 15: 传入模型名称
    work_dir = Path.cwd()
    session = CustomPromptSession(
        work_dir=work_dir,
        enable_file_history=False,  # 测试时不保存历史
        enable_completer=True,
        model_name="moonshot-v1-32k",  # ⭐ 自定义模型名称
    )

    print("✅ CustomPromptSession 已创建")
    print(f"📂 工作目录: {work_dir}")
    print(f"🤖 模型名称: {session.model_name}")
    print(f"📊 初始 Context 使用率: {session.context_usage:.1%}")
    print()

    # 设置初始 Context 使用率
    session.update_context_usage(0.35)  # 35%
    print(f"📊 设置 Context 使用率: {session.context_usage:.1%}")
    print()

    # 循环输入，直到 Ctrl+D
    try:
        while True:
            # 获取用户输入
            user_input = await session.prompt()

            # 显示输入内容
            print(f"\n你输入了: {user_input.command}")
            print(f"当前模式: {user_input.mode}")
            print(f"Session 模式: {session._mode}")
            print(f"Context 使用率: {session.context_usage:.1%}")

            # 特殊命令：更新 Context 使用率
            if user_input.command.lower() == "update":
                new_usage = min(session.context_usage + 0.1, 1.0)  # 增加 10%
                session.update_context_usage(new_usage)
                print(f"✅ Context 使用率更新为: {session.context_usage:.1%}")

            # 如果输入是 /exit 或 /quit，退出
            if user_input.command.lower() in ["/exit", "/quit"]:
                print("👋 退出测试...")
                break

            print()

    except EOFError:
        # Ctrl+D 退出
        print("\n\n✅ 测试完成（Ctrl+D）")
    except KeyboardInterrupt:
        # Ctrl+C 退出
        print("\n\n✅ 测试完成（Ctrl+C）")

    print("\n" + "=" * 80)
    print("Stage 15 测试完成！")
    print("=" * 80)
    print("\n状态栏包含：")
    print("- ✅ 时间（HH:MM）")
    print("- ✅ 模型名称（model:moonshot-v1-32k）")
    print("- ✅ 当前模式（agent/shell，带背景色）")
    print("- ✅ 快捷键提示（ctrl-x: 切换模式  ctrl-d: 退出）")
    print("- ✅ Context 使用率（右对齐显示，如 35.0%）")


if __name__ == "__main__":
    asyncio.run(test_statusbar_enhanced())

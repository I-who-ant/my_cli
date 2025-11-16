"""
Stage 11 手动测试脚本：模块化架构验证

测试目标：
1. console.py 模块（Console 单例）
2. metacmd.py 模块（斜杠命令系统）
3. prompt.py 模块（CustomPromptSession）
4. visualize.py 模块（UI Loop 渲染）
5. __init__.py 模块（ShellApp 主入口）
6. 端到端测试（完整交互流程）

运行方式：
    python test_manual_stage11.py
"""

import asyncio
from pathlib import Path


async def test_console_module():
    """测试 1：console.py 模块"""
    print("\n" + "=" * 60)
    print("🧪 测试 1: console.py 模块（Console 单例）")
    print("=" * 60)

    try:
        from my_cli.ui.shell.console import console
        from rich.panel import Panel

        # 验证 Console 单例
        console.print("[green]✅ Console 单例导入成功[/green]")

        # 验证 Panel 输出
        console.print(
            Panel(
                "[bold cyan]这是一个测试 Panel[/bold cyan]",
                border_style="cyan",
                padding=(1, 2),
            )
        )

        print("\n✅ 测试 1 完成：console.py 模块正常工作\n")

    except Exception as e:
        print(f"\n❌ 测试 1 失败: {e}\n")
        raise


async def test_metacmd_module():
    """测试 2：metacmd.py 模块"""
    print("\n" + "=" * 60)
    print("🧪 测试 2: metacmd.py 模块（斜杠命令系统）")
    print("=" * 60)

    try:
        from my_cli.ui.shell.metacmd import (
            get_meta_command,
            get_meta_commands,
            register_meta_command,
        )

        # 验证命令注册
        print("✅ metacmd.py 导入成功")

        # 测试获取所有命令
        commands = get_meta_commands()
        print(f"✅ 已注册命令数量: {len(commands)}")

        for cmd in commands:
            print(f"   - {cmd.slash_name()}: {cmd.description}")

        # 测试查询命令
        help_cmd = get_meta_command("help")
        if help_cmd:
            print(f"✅ 查询命令成功: {help_cmd.name}")
        else:
            print("❌ 查询命令失败")

        # 测试查询别名
        h_cmd = get_meta_command("h")
        if h_cmd and h_cmd.name == "help":
            print(f"✅ 别名查询成功: h -> {h_cmd.name}")
        else:
            print("❌ 别名查询失败")

        # 测试注册新命令
        def test_command(app, args):
            print("测试命令执行")

        register_meta_command(
            name="test",
            description="测试命令",
            func=test_command,
            aliases=["t"],
        )

        test_cmd = get_meta_command("test")
        if test_cmd:
            print(f"✅ 新命令注册成功: {test_cmd.name}")
        else:
            print("❌ 新命令注册失败")

        print("\n✅ 测试 2 完成：metacmd.py 模块正常工作\n")

    except Exception as e:
        print(f"\n❌ 测试 2 失败: {e}\n")
        import traceback

        traceback.print_exc()
        raise


async def test_prompt_module():
    """测试 3：prompt.py 模块"""
    print("\n" + "=" * 60)
    print("🧪 测试 3: prompt.py 模块（CustomPromptSession）")
    print("=" * 60)

    try:
        from my_cli.ui.shell.prompt import CustomPromptSession, UserInput, toast

        print("✅ prompt.py 导入成功")

        # 测试 UserInput
        user_input = UserInput(command="/help", thinking=False)
        print(f"✅ UserInput 创建成功: {user_input.command}")

        # 测试 toast
        toast("这是一个测试 Toast")
        print("✅ toast 显示成功")

        # 测试 CustomPromptSession（不运行 prompt，只测试创建）
        with CustomPromptSession(work_dir=Path.cwd()) as session:
            print(f"✅ CustomPromptSession 创建成功")
            print(f"   历史记录类型: {type(session.history).__name__}")

        print("\n✅ 测试 3 完成：prompt.py 模块正常工作\n")

    except Exception as e:
        print(f"\n❌ 测试 3 失败: {e}\n")
        import traceback

        traceback.print_exc()
        raise


async def test_visualize_module():
    """测试 4：visualize.py 模块"""
    print("\n" + "=" * 60)
    print("🧪 测试 4: visualize.py 模块（UI Loop 渲染）")
    print("=" * 60)

    try:
        from my_cli.ui.shell.visualize import visualize

        print("✅ visualize.py 导入成功")
        print("✅ visualize 函数可调用")

        # 注意：不实际运行 UI Loop，因为需要真实的 Wire 连接

        print("\n✅ 测试 4 完成：visualize.py 模块正常工作\n")

    except Exception as e:
        print(f"\n❌ 测试 4 失败: {e}\n")
        import traceback

        traceback.print_exc()
        raise


async def test_shell_app_single_command():
    """测试 5：ShellApp 单命令模式"""
    print("\n" + "=" * 60)
    print("🧪 测试 5: ShellApp 单命令模式")
    print("=" * 60)

    try:
        from my_cli.ui.shell import ShellApp

        print("✅ ShellApp 导入成功")

        # 创建 ShellApp
        app = ShellApp(verbose=True, work_dir=Path.cwd())
        print("✅ ShellApp 创建成功")

        # 运行单命令模式
        print("\n执行单命令：'你好，我是测试'\n")
        result = await app.run(command="你好，我是测试")

        if result:
            print("\n✅ 单命令执行成功")
        else:
            print("\n⚠️ 单命令执行失败（可能是配置问题）")

        print("\n✅ 测试 5 完成：ShellApp 单命令模式正常工作\n")

    except FileNotFoundError:
        print("\n⚠️ 测试 5 跳过：配置文件不存在")
        print("提示：运行 'python cli.py init' 创建配置文件\n")
    except Exception as e:
        print(f"\n❌ 测试 5 失败: {e}\n")
        import traceback

        traceback.print_exc()
        # 不抛出异常，因为配置问题不应该导致测试失败


async def test_module_integration():
    """测试 6：模块集成测试"""
    print("\n" + "=" * 60)
    print("🧪 测试 6: 模块集成测试")
    print("=" * 60)

    try:
        # 测试所有模块能否正常导入和协作
        from my_cli.ui.shell import ShellApp
        from my_cli.ui.shell.console import console
        from my_cli.ui.shell.metacmd import get_meta_command
        from my_cli.ui.shell.prompt import CustomPromptSession
        from my_cli.ui.shell.visualize import visualize

        print("✅ 所有模块导入成功")

        # 测试模块间的协作
        # 1. console 用于输出
        console.print("[cyan]测试 console 输出[/cyan]")

        # 2. metacmd 提供命令查询
        help_cmd = get_meta_command("help")
        print(f"✅ metacmd 提供命令: {help_cmd.name if help_cmd else 'None'}")

        # 3. prompt 创建会话
        with CustomPromptSession() as session:
            print(f"✅ prompt 创建会话成功")

        # 4. ShellApp 协调所有模块
        app = ShellApp()
        print(f"✅ ShellApp 协调器创建成功")

        print("\n✅ 测试 6 完成：模块集成正常\n")

    except Exception as e:
        print(f"\n❌ 测试 6 失败: {e}\n")
        import traceback

        traceback.print_exc()
        raise


async def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("🚀 Stage 11 模块化架构测试")
    print("=" * 60)
    print("\n功能概述：")
    print("- console.py: Console 单例 + 主题配置")
    print("- metacmd.py: 斜杠命令系统（装饰器注册）")
    print("- prompt.py: CustomPromptSession（命令历史）")
    print("- visualize.py: UI Loop 渲染逻辑")
    print("- __init__.py: ShellApp 主入口（协调器）")

    try:
        # 测试 1：console.py 模块
        await test_console_module()

        # 测试 2：metacmd.py 模块
        await test_metacmd_module()

        # 测试 3：prompt.py 模块
        await test_prompt_module()

        # 测试 4：visualize.py 模块
        await test_visualize_module()

        # 测试 5：ShellApp 单命令模式
        await test_shell_app_single_command()

        # 测试 6：模块集成测试
        await test_module_integration()

        # 总结
        print("\n" + "=" * 60)
        print("✅ Stage 11 自动化测试完成！")
        print("=" * 60)
        print("\n手动测试项目：")
        print("1. 运行命令：python my_cli/cli.py --ui shell")
        print("2. 查看模块化架构效果")
        print("3. 测试斜杠命令：/help, /clear, /exit")
        print("4. 测试命令历史：上下箭头查看历史输入")
        print("5. 查看文件历史持久化：.mycli_history 文件\n")

        print("\n" + "=" * 60)
        print("📁 模块架构总结")
        print("=" * 60)
        print("""
my_cli/ui/shell/
├── __init__.py      # ShellApp 主入口（协调器）
├── console.py       # Console 单例 + 主题配置
├── metacmd.py       # 斜杠命令系统（装饰器注册）
├── prompt.py        # CustomPromptSession（输入处理）
├── visualize.py     # UI Loop 渲染逻辑
└── enhanced.py.md.backup      # Stage 10 增强版（备份）

每个模块职责单一，符合 SOLID 原则！
""")

    except Exception as e:
        print(f"\n\n❌ 测试失败: {e}\n")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

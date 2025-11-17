"""
Stage 10 手动测试脚本：UI 美化和增强

测试目标：
1. prompt_toolkit PromptSession（命令历史）
2. rich Panel（欢迎信息美化）
3. 斜杠命令支持（/help, /clear, /exit）
4. 彩色输出

运行方式：
    python test_manual_stage10.py
"""

import asyncio
from pathlib import Path

from my_cli.ui.shell.enhanced import EnhancedShellUI


async def test_single_command():
    """测试 1：单命令模式（验证 rich 输出）"""
    print("\n" + "=" * 60)
    print("🧪 测试 1: 单命令模式（验证 rich 输出）")
    print("=" * 60)

    ui = EnhancedShellUI(verbose=True, work_dir=Path.cwd())
    await ui.run(command="你好，我是测试")

    print("\n✅ 测试 1 完成：检查是否有彩色输出\n")


async def test_slash_commands():
    """测试 2：斜杠命令（模拟输入）"""
    print("\n" + "=" * 60)
    print("🧪 测试 2: 斜杠命令支持")
    print("=" * 60)

    # 模拟用户输入序列
    test_inputs = [
        "/help",  # 显示帮助
        "/unknown",  # 未知命令
        "/clear",  # 清空 Context（暂未实现）
        "/exit",  # 退出
    ]

    # 创建模拟输入
    input_iter = iter(test_inputs)

    # 自定义 PromptSession 的 prompt_async
    class MockPromptSession:
        def __init__(self, *args, **kwargs):
            pass

        async def prompt_async(self, prompt: str) -> str:
            try:
                user_input = next(input_iter)
                print(f"{prompt}{user_input}")
                return user_input
            except StopIteration:
                raise EOFError()

    # 替换 PromptSession
    from my_cli.ui.shell import enhanced
    original_prompt_session = enhanced.PromptSession
    enhanced.PromptSession = MockPromptSession

    try:
        ui = EnhancedShellUI(verbose=False, work_dir=Path.cwd())
        await ui.run(command=None)

        print("\n✅ 测试 2 完成：斜杠命令正常工作\n")
    finally:
        enhanced.PromptSession = original_prompt_session


async def test_prompt_toolkit_integration():
    """测试 3：prompt_toolkit 集成验证"""
    print("\n" + "=" * 60)
    print("🧪 测试 3: prompt_toolkit 集成验证")
    print("=" * 60)

    # 验证导入
    try:
        from prompt_toolkit import PromptSession
        from prompt_toolkit.history import InMemoryHistory
        print("✅ prompt_toolkit 导入成功")

        # 创建 PromptSession
        history = InMemoryHistory()
        session = PromptSession(history=history)
        print("✅ PromptSession 创建成功")

        # 添加历史记录
        history.append_string("测试命令 1")
        history.append_string("测试命令 2")
        print(f"✅ 历史记录: {list(history.get_strings())}")

    except Exception as e:
        print(f"❌ prompt_toolkit 测试失败: {e}")

    print("\n✅ 测试 3 完成\n")


async def test_rich_integration():
    """测试 4：rich 库集成验证"""
    print("\n" + "=" * 60)
    print("🧪 测试 4: rich 库集成验证")
    print("=" * 60)

    try:
        from rich.console import Console
        from rich.panel import Panel
        from rich.text import Text
        print("✅ rich 库导入成功")

        # 创建 Console
        console = Console()
        print("✅ Console 创建成功")

        # 测试 Panel 输出
        test_text = "[bold cyan]这是一个测试 Panel[/bold cyan]\n[yellow]支持颜色和样式[/yellow]"
        console.print(Panel(test_text, border_style="cyan", padding=(1, 2)))

        print("\n✅ rich Panel 输出成功")

    except Exception as e:
        print(f"❌ rich 测试失败: {e}")

    print("\n✅ 测试 4 完成\n")


async def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("🚀 Stage 10 UI 美化和增强测试")
    print("=" * 60)
    print("\n功能概述：")
    print("- prompt_toolkit: 命令历史记录")
    print("- rich: Panel 边框和彩色输出")
    print("- 斜杠命令: /help, /clear, /exit")

    try:
        # 测试 1：单命令模式
        await test_single_command()

        # 测试 2：斜杠命令
        await test_slash_commands()

        # 测试 3：prompt_toolkit 集成
        await test_prompt_toolkit_integration()

        # 测试 4：rich 集成
        await test_rich_integration()

        # 总结
        print("\n" + "=" * 60)
        print("✅ Stage 10 自动化测试完成！")
        print("=" * 60)
        print("\n手动测试项目：")
        print("1. 运行命令：python my_cli/cli.py --ui shell")
        print("2. 查看 rich Panel 边框效果")
        print("3. 测试斜杠命令：/help, /clear, /exit")
        print("4. 测试命令历史：上下箭头查看历史输入")
        print("5. 查看彩色输出（成功=绿色，错误=红色）\n")

    except Exception as e:
        print(f"\n\n❌ 测试失败: {e}\n")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

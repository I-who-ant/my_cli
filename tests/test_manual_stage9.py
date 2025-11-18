"""
Stage 9 手动测试脚本：Shell 交互模式

测试目标：
1. Shell UI 基础功能
2. 多轮对话（Context 保持）
3. 工具调用在交互模式下的显示
4. 退出处理（exit 命令）

注意：
- 本测试脚本用于验证 Shell UI 的基本功能
- Ctrl+C 和 Ctrl+D 需要手动测试（无法自动化）
- 多轮对话需要手动验证 Context 是否保持

运行方式：
    python test_manual_stage9.py
"""

import asyncio
from pathlib import Path

from my_cli.ui.shell import ShellUI


async def test_shell_ui_single_command():
    """
    测试 1：单命令模式（Shell UI 支持）

    预期行为：
    - 执行一次命令后退出
    - 与 Print UI 行为相同
    """
    print("\n" + "=" * 60)
    print("🧪 测试 1: Shell UI 单命令模式")
    print("=" * 60)

    ui = ShellUI(verbose=True, work_dir=Path.cwd())

    # 执行单个命令（command 不为 None）
    await ui.run(command="请简单介绍一下你自己")

    print("\n✅ 测试 1 完成：单命令模式正常工作\n")


async def test_shell_ui_interactive_mode():
    """
    测试 2：交互式模式（自动化测试）

    预期行为：
    - 进入输入循环
    - 执行多轮对话
    - 使用 exit 命令退出

    注意：
    - 本测试通过模拟用户输入来自动化测试
    - 实际使用时需要手动输入
    """
    print("\n" + "=" * 60)
    print("🧪 测试 2: Shell UI 交互模式（模拟输入）")
    print("=" * 60)

    # 模拟用户输入序列
    test_inputs = [
        "你好，我是用户",  # 第一轮对话
        "请用 Bash 工具执行: echo 'Hello Stage 9'",  # 第二轮：测试工具调用
        "exit",  # 退出命令
    ]

    # 创建模拟输入迭代器
    input_iter = iter(test_inputs)

    def mock_input(prompt: str) -> str:
        """模拟 input() 函数"""
        try:
            user_input = next(input_iter)
            print(f"{prompt}{user_input}")  # 显示提示符和输入
            return user_input
        except StopIteration:
            # 输入结束，抛出 EOFError 模拟 Ctrl+D
            raise EOFError()

    # 替换 asyncio.to_thread 的 input 为 mock_input
    original_input = __builtins__.input
    __builtins__.input = mock_input

    try:
        ui = ShellUI(verbose=True, work_dir=Path.cwd())

        # 运行交互模式（command 为 None）
        await ui.run(command=None)

        print("\n✅ 测试 2 完成：交互模式正常工作\n")
    finally:
        # 恢复原始 input 函数
        __builtins__.input = original_input


async def test_context_persistence():
    """
    测试 3：Context 持久化（多轮对话）

    预期行为：
    - 第一轮：询问用户名称
    - 第二轮：LLM 应该记住用户名称
    - 验证 Context 是否保持
    """
    print("\n" + "=" * 60)
    print("🧪 测试 3: Context 持久化（多轮对话）")
    print("=" * 60)

    # 模拟用户输入序列
    test_inputs = [
        "我的名字是老王",  # 第一轮：告诉 LLM 名字
        "你还记得我的名字吗？",  # 第二轮：测试 Context 是否保持
        "exit",
    ]

    input_iter = iter(test_inputs)

    def mock_input(prompt: str) -> str:
        try:
            user_input = next(input_iter)
            print(f"{prompt}{user_input}")
            return user_input
        except StopIteration:
            raise EOFError()

    original_input = __builtins__.input
    __builtins__.input = mock_input

    try:
        ui = ShellUI(verbose=True, work_dir=Path.cwd())
        await ui.run(command=None)

        print("\n✅ 测试 3 完成：验证 LLM 是否记住了用户名称\n")
        print("   （检查 LLM 响应中是否提到 '老王'）\n")
    finally:
        __builtins__.input = original_input


async def main():
    """
    运行所有测试

    测试顺序：
    1. 单命令模式
    2. 交互模式
    3. Context 持久化
    """
    print("\n" + "=" * 60)
    print("🚀 Stage 9 Shell UI 手动测试")
    print("=" * 60)
    print("\n注意：")
    print("- 以下测试会自动模拟用户输入")
    print("- Ctrl+C 和 Ctrl+D 需要手动测试")
    print("- 手动测试命令：python -m my_cli --ui shell\n")

    try:
        # 测试 1：单命令模式
        await test_shell_ui_single_command()

        # 测试 2：交互模式
        await test_shell_ui_interactive_mode()

        # 测试 3：Context 持久化
        await test_context_persistence()

        # 总结
        print("\n" + "=" * 60)
        print("✅ Stage 9 自动化测试完成！")
        print("=" * 60)
        print("\n手动测试项目：")
        print("1. 运行命令：python -m my_cli --ui shell")
        print("2. 测试 Ctrl+C：在 LLM 响应时按 Ctrl+C（应显示提示而不退出）")
        print("3. 测试 Ctrl+D：按 Ctrl+D（应退出程序）")
        print("4. 测试 exit 命令：输入 'exit' 或 'quit'（应退出程序）")
        print("5. 测试多轮对话：连续输入多个问题（验证 Context 保持）\n")

    except KeyboardInterrupt:
        print("\n\n⚠️  测试被中断（Ctrl+C）\n")
    except Exception as e:
        print(f"\n\n❌ 测试失败: {e}\n")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

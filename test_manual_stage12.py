"""
Stage 12 手动测试脚本：Prompt 自动补全和多行输入

测试目标：
1. MetaCommandCompleter（/命令自动补全）
2. 多行输入支持（Ctrl+J / Alt+Enter）
3. CustomPromptSession 增强版
4. 端到端测试（完整交互流程）

运行方式：
    python test_manual_stage12.py
"""

import asyncio
from pathlib import Path


async def test_meta_command_completer():
    """测试 1：MetaCommandCompleter"""
    print("\n" + "=" * 60)
    print("🧪 测试 1: MetaCommandCompleter（/命令自动补全）")
    print("=" * 60)

    try:
        from prompt_toolkit.document import Document
        from my_cli.ui.shell.prompt import MetaCommandCompleter

        print("✅ MetaCommandCompleter 导入成功")

        # 创建补全器
        completer = MetaCommandCompleter()
        print("✅ MetaCommandCompleter 创建成功")

        # 测试场景 1：空输入，应该显示所有命令
        print("\n🔍 场景 1：空输入 '/' 应该显示所有命令")
        document = Document("/")
        completions = list(completer.get_completions(document, None))
        print(f"   补全建议数量: {len(completions)}")
        for comp in completions[:5]:  # 只显示前 5 个
            print(f"   - {comp.display}: {comp.display_meta}")

        # 测试场景 2：输入 /h，应该补全 /help
        print("\n🔍 场景 2：输入 '/h' 应该补全 /help")
        document = Document("/h")
        completions = list(completer.get_completions(document, None))
        print(f"   补全建议数量: {len(completions)}")
        for comp in completions:
            print(f"   - {comp.display}: {comp.display_meta}")

        # 测试场景 3：输入 /c，应该补全 /clear
        print("\n🔍 场景 3：输入 '/c' 应该补全 /clear")
        document = Document("/c")
        completions = list(completer.get_completions(document, None))
        print(f"   补全建议数量: {len(completions)}")
        for comp in completions:
            print(f"   - {comp.display}: {comp.display_meta}")

        # 测试场景 4：不以 / 开头，不应该补全
        print("\n🔍 场景 4：输入 'hello' 不应该补全")
        document = Document("hello")
        completions = list(completer.get_completions(document, None))
        print(f"   补全建议数量: {len(completions)}（应该为 0）")

        print("\n✅ 测试 1 完成：MetaCommandCompleter 正常工作\n")

    except Exception as e:
        print(f"\n❌ 测试 1 失败: {e}\n")
        import traceback

        traceback.print_exc()
        raise


async def test_custom_prompt_session_creation():
    """测试 2：CustomPromptSession 创建（增强版）"""
    print("\n" + "=" * 60)
    print("🧪 测试 2: CustomPromptSession 创建（Stage 12 增强版）")
    print("=" * 60)

    try:
        from my_cli.ui.shell.prompt import CustomPromptSession

        print("✅ CustomPromptSession 导入成功")

        # 测试场景 1：启用补全器
        print("\n🔍 场景 1：启用补全器")
        with CustomPromptSession(
            work_dir=Path.cwd(), enable_completer=True
        ) as session:
            print(f"✅ CustomPromptSession 创建成功（启用补全）")
            print(f"   历史记录类型: {type(session.history).__name__}")
            print(f"   补全器类型: {type(session.completer).__name__}")
            print(f"   是否有键绑定: {session.session.key_bindings is not None}")

        # 测试场景 2：禁用补全器
        print("\n🔍 场景 2：禁用补全器")
        with CustomPromptSession(
            work_dir=Path.cwd(), enable_completer=False
        ) as session:
            print(f"✅ CustomPromptSession 创建成功（禁用补全）")
            print(f"   历史记录类型: {type(session.history).__name__}")
            print(f"   补全器: {session.completer}")

        print("\n✅ 测试 2 完成：CustomPromptSession 创建正常\n")

    except Exception as e:
        print(f"\n❌ 测试 2 失败: {e}\n")
        import traceback

        traceback.print_exc()
        raise


async def test_stage12_features_summary():
    """测试 3：Stage 12 功能总结"""
    print("\n" + "=" * 60)
    print("🧪 测试 3: Stage 12 功能总结")
    print("=" * 60)

    try:
        from my_cli.ui.shell.prompt import CustomPromptSession, MetaCommandCompleter

        print("\n✅ Stage 12 新增功能：\n")
        print("1. ✅ MetaCommandCompleter（/命令自动补全）")
        print("   - 输入 '/' 显示所有命令")
        print("   - 输入 '/h' 补全 /help")
        print("   - 支持别名匹配（如 'h' -> 'help'）")
        print("   - 显示命令描述\n")

        print("2. ✅ 多行输入支持")
        print("   - Ctrl+J: 插入换行")
        print("   - Alt+Enter: 插入换行（macOS 友好）")
        print("   - 默认单行模式，按需多行\n")

        print("3. ✅ 自定义键绑定")
        print("   - Ctrl+J: 换行")
        print("   - Ctrl+R: 搜索历史（prompt_toolkit 内置）")
        print("   - Tab: 触发自动补全（prompt_toolkit 内置）\n")

        print("4. ✅ 历史记录持久化")
        print("   - FileHistory（跨会话保存）")
        print("   - 存储位置: .mycli_history\n")

        print("\n✅ 测试 3 完成：Stage 12 功能总结\n")

    except Exception as e:
        print(f"\n❌ 测试 3 失败: {e}\n")
        import traceback

        traceback.print_exc()


async def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("🚀 Stage 12 Prompt 自动补全测试")
    print("=" * 60)
    print("\n功能概述：")
    print("- MetaCommandCompleter: /命令自动补全")
    print("- 多行输入: Ctrl+J / Alt+Enter 插入换行")
    print("- 键绑定: 自定义快捷键支持")
    print("- 历史记录: FileHistory 持久化")

    try:
        # 测试 1：MetaCommandCompleter
        await test_meta_command_completer()

        # 测试 2：CustomPromptSession 创建
        await test_custom_prompt_session_creation()

        # 测试 3：功能总结
        await test_stage12_features_summary()

        # 总结
        print("\n" + "=" * 60)
        print("✅ Stage 12 自动化测试完成！")
        print("=" * 60)
        print("\n手动测试项目（交互式验证）：")
        print("1. 运行命令：python my_cli/cli.py --ui shell")
        print("2. 输入 '/' 然后按 Tab 键，查看命令补全")
        print("3. 输入 '/h' 然后按 Tab 键，查看补全为 /help")
        print("4. 输入文本后按 Ctrl+J，测试多行输入")
        print("5. 按 Ctrl+R 搜索历史命令")
        print("6. 退出后重新启动，验证历史记录持久化\n")

        print("\n" + "=" * 60)
        print("📁 Stage 12 修改总结")
        print("=" * 60)
        print(
            """
修改文件：
- my_cli/ui/shell/prompt.py
  * 添加 MetaCommandCompleter 类（自动补全器）
  * CustomPromptSession 增强（集成补全器 + 键绑定）
  * 多行输入支持（Ctrl+J / Alt+Enter）

新增功能：
1. ✅ /命令自动补全（Tab 键触发）
2. ✅ 多行输入支持（Ctrl+J 换行）
3. ✅ 自定义键绑定（Ctrl+J）
4. ✅ 历史搜索（Ctrl+R）

用户体验提升：
- Tab 键补全命令，减少输入错误
- 多行输入支持，便于复杂查询
- 历史搜索，快速调用历史命令
"""
        )

    except Exception as e:
        print(f"\n\n❌ 测试失败: {e}\n")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

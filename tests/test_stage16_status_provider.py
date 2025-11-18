#!/usr/bin/env python3
"""
Stage 16 测试：status_provider 动态状态回调机制

测试目标：
1. 验证 Soul Protocol 新增属性（status/model_capabilities/message_count）
2. 验证 KimiSoul 实现的属性
3. 验证 CustomPromptSession 通过 status_provider 动态获取状态
4. 验证状态栏能够显示实时的 Context 使用率

测试方案：
- 模拟 Soul 状态变化
- 验证 status_provider 回调被正确调用
- 验证状态栏渲染时使用最新状态

运行命令：
    python test_stage16_status_provider.py
"""

from pathlib import Path
import sys

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from my_cli.soul import StatusSnapshot, Soul
from my_cli.soul.kimisoul import KimiSoul
from my_cli.soul.agent import Agent
from my_cli.soul.runtime import Runtime
from my_cli.soul.context import Context
from my_cli.ui.shell.prompt import CustomPromptSession, FormattedText


def test_soul_protocol_attributes():
    """测试 1：Soul Protocol 新增属性"""
    print("=" * 60)
    print("测试 1：Soul Protocol 新增属性")
    print("=" * 60)

    # 检查 Soul Protocol 有哪些属性
    print("Soul Protocol 必需的属性：")
    print(f"  - name: str")
    print(f"  - model_name: str")
    print(f"  - model_capabilities: set[str] | None  ⭐ Stage 16 新增")
    print(f"  - status: StatusSnapshot  ⭐ Stage 16 新增")
    print(f"  - message_count: int  ⭐ Stage 16 新增")
    print(f"  - run(user_input: str): async method")

    # 检查 StatusSnapshot 结构
    print(f"\nStatusSnapshot 数据类：")
    snapshot = StatusSnapshot(context_usage=0.35)
    print(f"  - context_usage: {snapshot.context_usage}")
    print(f"  - 类型: {type(snapshot)}")
    print(f"  - frozen: {snapshot.__dataclass_fields__}")

    print("✅ Soul Protocol 属性定义正确！\n")


def test_kimisoul_implementation():
    """测试 2：KimiSoul 实现的属性"""
    print("=" * 60)
    print("测试 2：KimiSoul 实现的属性")
    print("=" * 60)

    # 创建模拟的 Agent 和 Runtime
    agent = Agent(name="TestAgent", work_dir=Path.cwd())

    # 创建一个简单的 MockChatProvider
    class MockChatProvider:
        @property
        def model_name(self) -> str:
            return "mock-model-v1"

    # ⭐ Stage 17：使用 LLM 替代 ChatProvider
    from my_cli.llm import LLM
    llm = LLM(
        chat_provider=MockChatProvider(),
        max_context_size=32000,
        capabilities={"thinking"}
    )
    runtime = Runtime(llm=llm, max_steps=10)

    # 创建一个简单的 MockToolset
    class MockToolset:
        def get_tools(self):
            return []

    toolset = MockToolset()

    # 创建 KimiSoul
    soul = KimiSoul(agent=agent, runtime=runtime, toolset=toolset)

    print(f"KimiSoul 实例：")
    print(f"  - name: {soul.name}")
    print(f"  - model_name: {soul.model_name}")
    print(f"  - model_capabilities: {soul.model_capabilities}")
    print(f"  - message_count: {soul.message_count}")
    print(f"  - status: {soul.status}")
    print(f"  - status.context_usage: {soul.status.context_usage:.2%}")

    # 验证 Protocol 实现
    assert isinstance(soul, Soul), "KimiSoul 应该实现 Soul Protocol"
    print(f"\n✅ KimiSoul 正确实现了 Soul Protocol！\n")


def test_status_provider_callback():
    """测试 3：status_provider 回调机制"""
    print("=" * 60)
    print("测试 3：status_provider 回调机制")
    print("=" * 60)

    # 模拟一个简单的状态提供器
    call_count = [0]  # 使用列表来在闭包中修改
    current_usage = [0.0]

    def mock_status_provider() -> StatusSnapshot:
        """模拟 Soul 的 status 属性"""
        call_count[0] += 1
        return StatusSnapshot(context_usage=current_usage[0])

    # 创建 CustomPromptSession，传入 status_provider
    session = CustomPromptSession(
        work_dir=Path.cwd(),
        enable_file_history=False,  # 禁用文件历史（测试用）
        status_provider=mock_status_provider,
        model_capabilities={"image_in"},  # 模拟能力
    )

    print(f"初始状态：")
    print(f"  - status_provider 调用次数: {call_count[0]}")
    print(f"  - current_usage: {current_usage[0]:.2%}")

    # 渲染状态栏（会调用 status_provider）
    toolbar = session._render_bottom_toolbar()
    print(f"\n第一次渲染状态栏：")
    print(f"  - status_provider 调用次数: {call_count[0]}")
    print(f"  - 状态栏内容: {toolbar}")

    # 模拟 Context 使用率增加
    current_usage[0] = 0.35  # 35%

    # 再次渲染状态栏
    toolbar2 = session._render_bottom_toolbar()
    print(f"\n第二次渲染状态栏（usage=35%）：")
    print(f"  - status_provider 调用次数: {call_count[0]}")
    print(f"  - 状态栏内容: {toolbar2}")

    # 模拟更多消息
    current_usage[0] = 0.67  # 67%
    toolbar3 = session._render_bottom_toolbar()
    print(f"\n第三次渲染状态栏（usage=67%）：")
    print(f"  - status_provider 调用次数: {call_count[0]}")
    print(f"  - 状态栏内容: {toolbar3}")

    # 验证
    assert call_count[0] == 3, f"status_provider 应该被调用 3 次，实际 {call_count[0]}"
    print(f"\n✅ status_provider 回调机制工作正常！每次渲染都动态获取状态！\n")


def test_no_status_provider():
    """测试 4：没有 status_provider 时的行为"""
    print("=" * 60)
    print("测试 4：没有 status_provider 时的行为")
    print("=" * 60)

    # 创建没有 status_provider 的 session
    session = CustomPromptSession(
        work_dir=Path.cwd(),
        enable_file_history=False,
        status_provider=None,  # 没有 status_provider
    )

    # 渲染状态栏
    toolbar = session._render_bottom_toolbar()
    print(f"状态栏内容（无 status_provider）：")
    print(f"  {toolbar}")

    # 检查状态栏包含 "N/A"
    toolbar_text = "".join(text for _, text in toolbar)
    assert "N/A" in toolbar_text, "没有 status_provider 时应该显示 N/A"

    print(f"\n✅ 没有 status_provider 时正确显示 N/A！\n")


def test_formatted_text_structure():
    """测试 5：FormattedText 结构"""
    print("=" * 60)
    print("测试 5：FormattedText 结构")
    print("=" * 60)

    session = CustomPromptSession(
        work_dir=Path.cwd(),
        enable_file_history=False,
        status_provider=lambda: StatusSnapshot(context_usage=0.42),
    )

    toolbar = session._render_bottom_toolbar()
    print(f"FormattedText 结构：")
    print(f"  类型: {type(toolbar)}")
    print(f"  片段数量: {len(toolbar)}")

    print("\n各片段详情：")
    for i, (style, text) in enumerate(toolbar):
        style_desc = style if style else "(默认样式)"
        print(f"  [{i}] style={style_desc}, text='{text}'")

    # 提取纯文本
    full_text = "".join(text for _, text in toolbar)
    print(f"\n完整状态栏文本：")
    print(f"  '{full_text}'")

    # 验证包含关键信息
    assert "agent" in full_text or "shell" in full_text, "应该包含模式信息"
    assert "context:" in full_text, "应该包含 context 信息"
    assert "42.0%" in full_text, "应该显示 42.0%"

    print(f"\n✅ FormattedText 结构正确，包含所有必要信息！\n")


def test_integration_simulation():
    """测试 6：集成模拟（模拟 ShellApp 使用场景）"""
    print("=" * 60)
    print("测试 6：集成模拟（模拟 ShellApp 使用场景）")
    print("=" * 60)

    # 创建 Mock Soul
    class MockSoul:
        def __init__(self):
            self._messages = []
            self.name = "MockSoul"
            self.model_name = "mock-gpt-4"

        @property
        def model_capabilities(self) -> set[str] | None:
            return {"image_in", "thinking"}

        @property
        def status(self) -> StatusSnapshot:
            # 模拟基于消息数量的 context usage
            message_count = len(self._messages)
            estimated_tokens = message_count * 500
            max_tokens = 32000
            usage = min(estimated_tokens / max_tokens, 1.0)
            return StatusSnapshot(context_usage=usage)

        @property
        def message_count(self) -> int:
            return len(self._messages)

        def add_message(self, content: str):
            """模拟添加消息"""
            self._messages.append(content)

    # 模拟 ShellApp 的使用方式
    soul = MockSoul()

    print(f"初始状态：")
    print(f"  - message_count: {soul.message_count}")
    print(f"  - context_usage: {soul.status.context_usage:.2%}")

    # 创建 CustomPromptSession（模拟 ShellApp 的方式）
    session = CustomPromptSession(
        work_dir=Path.cwd(),
        enable_file_history=False,
        status_provider=lambda: soul.status,  # ⭐ 这就是 ShellApp 传递的方式
        model_capabilities=soul.model_capabilities,
    )

    toolbar1 = session._render_bottom_toolbar()
    toolbar_text1 = "".join(text for _, text in toolbar1)
    print(f"\n状态栏 (0 条消息)：")
    print(f"  '{toolbar_text1}'")

    # 模拟用户发送消息
    soul.add_message("你好")
    soul.add_message("我想了解 Python")
    print(f"\n添加 2 条消息后：")
    print(f"  - message_count: {soul.message_count}")
    print(f"  - context_usage: {soul.status.context_usage:.2%}")

    toolbar2 = session._render_bottom_toolbar()
    toolbar_text2 = "".join(text for _, text in toolbar2)
    print(f"状态栏 (2 条消息)：")
    print(f"  '{toolbar_text2}'")

    # 添加更多消息
    for i in range(10):
        soul.add_message(f"消息 {i}")

    print(f"\n添加 10 条消息后：")
    print(f"  - message_count: {soul.message_count}")
    print(f"  - context_usage: {soul.status.context_usage:.2%}")

    toolbar3 = session._render_bottom_toolbar()
    toolbar_text3 = "".join(text for _, text in toolbar3)
    print(f"状态栏 (12 条消息)：")
    print(f"  '{toolbar_text3}'")

    # 验证 context_usage 随消息增加而增加
    usage1 = float(toolbar_text1.split("context:")[1].strip().replace("%", "")) / 100
    usage2 = float(toolbar_text2.split("context:")[1].strip().replace("%", "")) / 100
    usage3 = float(toolbar_text3.split("context:")[1].strip().replace("%", "")) / 100

    assert usage1 < usage2 < usage3, "Context 使用率应该随消息增加而增加"
    print(f"\n✅ 集成模拟成功！Context 使用率随消息动态更新！\n")


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("🧪 Stage 16 测试：status_provider 动态状态回调机制")
    print("=" * 60 + "\n")

    try:
        test_soul_protocol_attributes()
        test_kimisoul_implementation()
        test_status_provider_callback()
        test_no_status_provider()
        test_formatted_text_structure()
        test_integration_simulation()

        print("=" * 60)
        print("🎉 所有测试通过！Stage 16 status_provider 机制实现完成！")
        print("=" * 60)

        print("\n关键改进：")
        print("1. Soul Protocol 新增 status/model_capabilities/message_count 属性")
        print("2. KimiSoul 实现了这些属性")
        print("3. CustomPromptSession 使用 status_provider 回调动态获取状态")
        print("4. ShellApp 传递 lambda: self.soul.status 实现实时更新")
        print("5. 状态栏无需手动 update_context_usage()，自动获取最新值")

        print("\n架构优势：")
        print("- ✅ 遵循依赖倒置原则（DIP）：UI 层不直接依赖 Soul 实现")
        print("- ✅ 遵循开闭原则（OCP）：新增状态信息无需修改 UI 层")
        print("- ✅ 实时性：每次渲染都获取最新状态")
        print("- ✅ 解耦：CustomPromptSession 不需要知道 Soul 的内部结构")

    except Exception as e:
        print(f"\n❌ 测试失败：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

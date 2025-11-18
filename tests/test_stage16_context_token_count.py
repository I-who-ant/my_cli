#!/usr/bin/env python3
"""
Stage 16 测试：Context.token_count 和 _context_usage 最小实现

测试目标：
1. 验证 Context.token_count 属性
2. 验证 Context.update_token_count() 方法
3. 验证 KimiSoul._context_usage 使用 token_count 计算
4. 验证估算机制（token_count=0 时）

运行命令：
    python test_stage16_context_token_count.py
"""

from pathlib import Path
import sys
import asyncio

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from my_cli.soul.context import Context
from my_cli.soul.kimisoul import KimiSoul
from my_cli.soul.agent import Agent
from my_cli.soul.runtime import Runtime
from kosong.message import Message


def test_context_token_count():
    """测试 1：Context.token_count 基础功能"""
    print("=" * 60)
    print("测试 1：Context.token_count 基础功能")
    print("=" * 60)

    context = Context()

    print(f"初始状态：")
    print(f"  - token_count: {context.token_count}")
    print(f"  - 类型: {type(context.token_count)}")

    assert context.token_count == 0, "初始 token_count 应该为 0"
    print("✅ 初始 token_count = 0\n")


async def test_update_token_count():
    """测试 2：Context.update_token_count() 方法"""
    print("=" * 60)
    print("测试 2：Context.update_token_count() 方法")
    print("=" * 60)

    context = Context()

    print(f"更新前: token_count = {context.token_count}")

    # 更新 token_count
    await context.update_token_count(1000)
    print(f"更新为 1000: token_count = {context.token_count}")
    assert context.token_count == 1000

    # 再次更新
    await context.update_token_count(5000)
    print(f"更新为 5000: token_count = {context.token_count}")
    assert context.token_count == 5000

    # 清空 context
    context.clear()
    print(f"清空后: token_count = {context.token_count}")
    assert context.token_count == 0, "清空后 token_count 应该重置为 0"

    print("✅ update_token_count() 方法工作正常\n")


def test_context_usage_calculation():
    """测试 3：KimiSoul._context_usage 计算"""
    print("=" * 60)
    print("测试 3：KimiSoul._context_usage 计算")
    print("=" * 60)

    # 创建模拟的 ChatProvider
    class MockChatProvider:
        @property
        def model_name(self) -> str:
            return "mock-model-v1"

    # 创建 Mock Toolset
    class MockToolset:
        def get_tools(self):
            return []

    # 创建 Agent 和 Runtime
    agent = Agent(name="TestAgent", work_dir=Path.cwd())
    runtime = Runtime(chat_provider=MockChatProvider(), max_steps=10)
    toolset = MockToolset()

    # 创建 KimiSoul
    soul = KimiSoul(agent=agent, runtime=runtime, toolset=toolset)

    print(f"初始状态（token_count=0）：")
    print(f"  - context.token_count: {soul._context.token_count}")
    print(f"  - _context_usage: {soul._context_usage:.2%}")
    print(f"  - status.context_usage: {soul.status.context_usage:.2%}")

    # token_count = 0 时，应该使用估算（message_count * 500）
    assert soul._context_usage == 0.0, "没有消息时应该是 0%"

    print("✅ token_count=0 时使用估算\n")


async def test_context_usage_with_real_token_count():
    """测试 4：使用真实 token_count 的 _context_usage 计算"""
    print("=" * 60)
    print("测试 4：使用真实 token_count 的 _context_usage 计算")
    print("=" * 60)

    # 创建模拟的 ChatProvider
    class MockChatProvider:
        @property
        def model_name(self) -> str:
            return "mock-model-v1"

    class MockToolset:
        def get_tools(self):
            return []

    agent = Agent(name="TestAgent", work_dir=Path.cwd())
    runtime = Runtime(chat_provider=MockChatProvider(), max_steps=10)
    toolset = MockToolset()
    soul = KimiSoul(agent=agent, runtime=runtime, toolset=toolset)

    # 手动设置 token_count
    await soul._context.update_token_count(3200)  # 10% of 32000

    print(f"设置 token_count=3200 后：")
    print(f"  - context.token_count: {soul._context.token_count}")
    print(f"  - _context_usage: {soul._context_usage:.2%}")
    print(f"  - status.context_usage: {soul.status.context_usage:.2%}")

    assert soul._context_usage == 0.1, f"3200/32000 应该是 10%，实际 {soul._context_usage}"

    # 更新为 50%
    await soul._context.update_token_count(16000)

    print(f"\n设置 token_count=16000 后：")
    print(f"  - context.token_count: {soul._context.token_count}")
    print(f"  - _context_usage: {soul._context_usage:.2%}")
    print(f"  - status.context_usage: {soul.status.context_usage:.2%}")

    assert soul._context_usage == 0.5, f"16000/32000 应该是 50%，实际 {soul._context_usage}"

    # 更新为超过 100%（应该限制在 1.0）
    await soul._context.update_token_count(35000)

    print(f"\n设置 token_count=35000 后（超过最大值）：")
    print(f"  - context.token_count: {soul._context.token_count}")
    print(f"  - _context_usage: {soul._context_usage:.2%}")
    print(f"  - status.context_usage: {soul.status.context_usage:.2%}")

    assert soul._context_usage == 1.0, f"超过 max_context_size 应该限制在 100%，实际 {soul._context_usage}"

    print("✅ 使用真实 token_count 的计算正确\n")


async def test_estimation_fallback():
    """测试 5：估算机制（token_count=0 时）"""
    print("=" * 60)
    print("测试 5：估算机制（token_count=0 时）")
    print("=" * 60)

    class MockChatProvider:
        @property
        def model_name(self) -> str:
            return "mock-model-v1"

    class MockToolset:
        def get_tools(self):
            return []

    agent = Agent(name="TestAgent", work_dir=Path.cwd())
    runtime = Runtime(chat_provider=MockChatProvider(), max_steps=10)
    toolset = MockToolset()
    soul = KimiSoul(agent=agent, runtime=runtime, toolset=toolset)

    # 添加消息（但不设置 token_count）
    msg1 = Message(role="user", content="你好")
    await soul._context.append_message(msg1)

    print(f"添加 1 条消息后（token_count=0）：")
    print(f"  - message_count: {len(soul._context.messages)}")
    print(f"  - token_count: {soul._context.token_count}")
    print(f"  - _context_usage: {soul._context_usage:.2%}")
    print(f"  - 估算 tokens: {len(soul._context.messages) * 500}")

    # token_count=0 时，应该估算为 1 * 500 = 500
    expected_usage = min((1 * 500) / 32000, 1.0)
    assert abs(soul._context_usage - expected_usage) < 0.0001, \
        f"应该估算为 {expected_usage:.2%}，实际 {soul._context_usage:.2%}"

    # 添加更多消息
    for i in range(10):
        msg = Message(role="user", content=f"消息 {i}")
        await soul._context.append_message(msg)

    print(f"\n添加 10 条消息后（总计 11 条，token_count=0）：")
    print(f"  - message_count: {len(soul._context.messages)}")
    print(f"  - token_count: {soul._context.token_count}")
    print(f"  - _context_usage: {soul._context_usage:.2%}")
    print(f"  - 估算 tokens: {len(soul._context.messages) * 500}")

    # token_count=0 时，应该估算为 11 * 500 = 5500
    expected_usage = min((11 * 500) / 32000, 1.0)
    assert abs(soul._context_usage - expected_usage) < 0.0001, \
        f"应该估算为 {expected_usage:.2%}，实际 {soul._context_usage:.2%}"

    print("✅ token_count=0 时正确使用估算机制\n")


async def test_integration():
    """测试 6：集成测试（真实 token_count + 估算混合）"""
    print("=" * 60)
    print("测试 6：集成测试（真实 token_count + 估算混合）")
    print("=" * 60)

    class MockChatProvider:
        @property
        def model_name(self) -> str:
            return "mock-model-v1"

    class MockToolset:
        def get_tools(self):
            return []

    agent = Agent(name="TestAgent", work_dir=Path.cwd())
    runtime = Runtime(chat_provider=MockChatProvider(), max_steps=10)
    toolset = MockToolset()
    soul = KimiSoul(agent=agent, runtime=runtime, toolset=toolset)

    # 场景 1：没有消息，没有 token_count
    print(f"场景 1：初始状态")
    print(f"  - _context_usage: {soul._context_usage:.2%}")
    assert soul._context_usage == 0.0

    # 场景 2：有消息，但 token_count=0（使用估算）
    msg = Message(role="user", content="你好")
    await soul._context.append_message(msg)
    print(f"\n场景 2：1 条消息，token_count=0（估算）")
    print(f"  - _context_usage: {soul._context_usage:.2%}")
    assert soul._context_usage > 0.0

    # 场景 3：更新 token_count（使用真实值）
    await soul._context.update_token_count(6400)  # 20%
    print(f"\n场景 3：设置 token_count=6400（真实值）")
    print(f"  - _context_usage: {soul._context_usage:.2%}")
    assert soul._context_usage == 0.2

    # 场景 4：清空后重新开始
    soul._context.clear()
    print(f"\n场景 4：清空后")
    print(f"  - _context_usage: {soul._context_usage:.2%}")
    assert soul._context_usage == 0.0

    print("✅ 集成测试通过\n")


async def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("🧪 Stage 16 测试：Context.token_count 最小实现")
    print("=" * 60 + "\n")

    try:
        test_context_token_count()
        await test_update_token_count()
        test_context_usage_calculation()
        await test_context_usage_with_real_token_count()
        await test_estimation_fallback()
        await test_integration()

        print("=" * 60)
        print("🎉 所有测试通过！Context.token_count 最小实现完成！")
        print("=" * 60)

        print("\n关键改进：")
        print("1. Context 新增 token_count 属性（初始为 0）")
        print("2. Context 新增 update_token_count() 方法")
        print("3. KimiSoul._context_usage 使用 token_count / max_context_size 计算")
        print("4. token_count=0 时使用估算机制（message_count * 500）")
        print("5. 遵循官方实现模式（status -> _context_usage）")

        print("\n官方对照：")
        print("- 官方: self._context.token_count / self._runtime.llm.max_context_size")
        print("- 简化版: self._context.token_count / 32000（固定）")
        print("- 估算: message_count * 500（token_count=0 时）")

        print("\nStage 17+ 扩展方向：")
        print("- 集成 LLM API 响应自动更新 token_count")
        print("- 持久化 token_count 到历史文件")
        print("- 从 Runtime.llm.max_context_size 动态获取最大值")
        print("- 使用更精确的 token 计算（tiktoken）")

    except Exception as e:
        print(f"\n❌ 测试失败：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

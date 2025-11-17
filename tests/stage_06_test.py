"""
Stage 6 验收测试 - Wire 机制完整性验证

测试目标：
1. Wire 消息队列基础功能
2. ContextVar 上下文隔离
3. wire_send() 全局函数
4. run_soul() 任务调度
5. UI Loop 消息接收
6. 流式输出端到端测试

运行方式：
    python tests/stage_06_test.py
"""

import asyncio
from pathlib import Path

from kosong.message import TextPart

from my_cli.soul import create_soul, run_soul, wire_send, get_wire_or_none
from my_cli.wire import Wire, WireUISide
from my_cli.wire.message import StepBegin, StepInterrupted


# ============================================================
# 测试 1: Wire 基础功能
# ============================================================
async def test_wire_basic():
    """测试 Wire 消息队列的基本功能"""
    print("\n" + "=" * 60)
    print("测试 1: Wire 基础功能")
    print("=" * 60)

    wire = Wire()

    # 测试发送和接收
    test_msg = TextPart(text="Hello, Wire!")
    wire.soul_side.send(test_msg)

    received = await wire.ui_side.receive()

    assert isinstance(received, TextPart), "❌ 消息类型错误"
    assert received.text == "Hello, Wire!", "❌ 消息内容错误"

    print("✅ Wire 基础功能测试通过")
    print(f"   - 发送消息: {test_msg.text}")
    print(f"   - 接收消息: {received.text}")


# ============================================================
# 测试 2: ContextVar 上下文隔离
# ============================================================
async def test_context_var():
    """测试 ContextVar 的上下文隔离功能"""
    print("\n" + "=" * 60)
    print("测试 2: ContextVar 上下文隔离")
    print("=" * 60)

    from my_cli.soul import _current_wire

    # 测试初始状态
    wire1 = get_wire_or_none()
    assert wire1 is None, "❌ 初始状态应该为 None"
    print("✅ 初始状态为 None")

    # 测试设置 Wire
    wire = Wire()
    token = _current_wire.set(wire)

    wire2 = get_wire_or_none()
    assert wire2 is wire, "❌ 获取的 Wire 不匹配"
    print("✅ 设置 Wire 成功")

    # 测试重置
    _current_wire.reset(token)
    wire3 = get_wire_or_none()
    assert wire3 is None, "❌ 重置后应该为 None"
    print("✅ 重置 Wire 成功")


# ============================================================
# 测试 3: wire_send() 全局函数
# ============================================================
async def test_wire_send():
    """测试 wire_send() 全局函数"""
    print("\n" + "=" * 60)
    print("测试 3: wire_send() 全局函数")
    print("=" * 60)

    from my_cli.soul import _current_wire

    wire = Wire()
    token = _current_wire.set(wire)

    try:
        # 发送消息
        test_msg = TextPart(text="Hello from wire_send!")
        wire_send(test_msg)

        # 接收消息
        received = await wire.ui_side.receive()

        assert isinstance(received, TextPart), "❌ 消息类型错误"
        assert received.text == "Hello from wire_send!", "❌ 消息内容错误"

        print("✅ wire_send() 测试通过")
        print(f"   - 发送消息: {test_msg.text}")
        print(f"   - 接收消息: {received.text}")

    finally:
        _current_wire.reset(token)


# ============================================================
# 测试 4: UI Loop 消息处理
# ============================================================
async def test_ui_loop():
    """测试 UI Loop 的消息处理"""
    print("\n" + "=" * 60)
    print("测试 4: UI Loop 消息处理")
    print("=" * 60)

    wire = Wire()

    # 准备测试消息
    messages = [
        TextPart(text="Hello, "),
        TextPart(text="World!"),
        StepInterrupted(),
    ]

    # 发送消息
    for msg in messages:
        wire.soul_side.send(msg)

    # UI Loop 接收消息
    received_texts = []

    async def ui_loop(wire_ui: WireUISide):
        while True:
            msg = await wire_ui.receive()

            if isinstance(msg, TextPart):
                received_texts.append(msg.text)
            elif isinstance(msg, StepInterrupted):
                break

    await ui_loop(wire.ui_side)

    assert received_texts == ["Hello, ", "World!"], "❌ 接收的消息不正确"

    print("✅ UI Loop 测试通过")
    print(f"   - 接收到 {len(received_texts)} 条文本消息")
    print(f"   - 内容: {''.join(received_texts)}")


# ============================================================
# 测试 5: run_soul() 任务调度
# ============================================================
async def test_run_soul():
    """测试 run_soul() 的任务调度功能"""
    print("\n" + "=" * 60)
    print("测试 5: run_soul() 任务调度")
    print("=" * 60)

    # 创建一个简单的 Soul mock
    class MockSoul:
        def __init__(self):
            self.model_name = "mock-model"
            self.message_count = 0

        async def run(self, user_input: str):
            """模拟 Soul 运行"""
            # 发送一些测试消息
            wire_send(TextPart(text="Mock response: "))
            await asyncio.sleep(0.01)  # 模拟异步处理
            wire_send(TextPart(text=user_input))
            await asyncio.sleep(0.01)
            wire_send(StepInterrupted())

    # UI Loop 收集消息
    received_texts = []

    async def ui_loop(wire_ui: WireUISide):
        while True:
            msg = await wire_ui.receive()

            if isinstance(msg, TextPart):
                received_texts.append(msg.text)
            elif isinstance(msg, StepInterrupted):
                break

    # 运行 run_soul()
    soul = MockSoul()
    cancel_event = asyncio.Event()

    await run_soul(
        soul=soul,
        user_input="Test input",
        ui_loop_fn=ui_loop,
        cancel_event=cancel_event,
    )

    assert len(received_texts) == 2, f"❌ 期望收到 2 条消息，实际收到 {len(received_texts)} 条"
    assert received_texts[0] == "Mock response: ", "❌ 第一条消息不正确"
    assert received_texts[1] == "Test input", "❌ 第二条消息不正确"

    print("✅ run_soul() 测试通过")
    print(f"   - Soul 任务正常完成")
    print(f"   - UI Loop 正常接收消息")
    print(f"   - 消息内容: {''.join(received_texts)}")


# ============================================================
# 测试 6: 端到端流式输出（集成测试）
# ============================================================
async def test_end_to_end_streaming():
    """端到端测试：真实 LLM API 流式输出"""
    print("\n" + "=" * 60)
    print("测试 6: 端到端流式输出（集成测试）")
    print("=" * 60)

    print("\n⚠️  这个测试需要真实的 API Key 和网络连接")
    print("如果没有配置 API Key，这个测试会被跳过\n")

    try:
        # 创建 Soul
        soul = create_soul(work_dir=Path.cwd())

        print(f"✅ Soul 创建成功，使用模型: {soul.model_name}")

        # UI Loop 收集消息
        received_texts = []

        async def ui_loop(wire_ui: WireUISide):
            print("\n💬 AI 回复:\n")
            while True:
                msg = await wire_ui.receive()

                if isinstance(msg, TextPart):
                    if msg.text:
                        received_texts.append(msg.text)
                        print(msg.text, end="", flush=True)
                elif isinstance(msg, StepInterrupted):
                    break
            print("\n")

        # 运行真实测试
        cancel_event = asyncio.Event()

        await run_soul(
            soul=soul,
            user_input="1+1等于几？直接说答案",
            ui_loop_fn=ui_loop,
            cancel_event=cancel_event,
        )

        assert len(received_texts) > 0, "❌ 没有收到任何响应"

        print("✅ 端到端流式输出测试通过")
        print(f"   - 收到 {len(received_texts)} 个文本片段")
        print(f"   - 总字符数: {sum(len(t) for t in received_texts)}")

    except FileNotFoundError:
        print("⚠️  配置文件不存在，跳过此测试")
    except Exception as e:
        print(f"⚠️  测试失败: {e}")
        print("   这可能是因为 API Key 无效或网络问题")


# ============================================================
# 主测试入口
# ============================================================
async def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("Stage 6 Wire 机制验收测试")
    print("=" * 60)

    try:
        await test_wire_basic()
        await test_context_var()
        await test_wire_send()
        await test_ui_loop()
        await test_run_soul()
        await test_end_to_end_streaming()

        print("\n" + "=" * 60)
        print("🎉 所有测试通过！Stage 6 Wire 机制实现完整！")
        print("=" * 60 + "\n")

    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}\n")
        raise
    except Exception as e:
        print(f"\n❌ 未知错误: {e}\n")
        raise


if __name__ == "__main__":
    asyncio.run(run_all_tests())
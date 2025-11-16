"""
Stage 8 测试：工具调用集成测试

测试目标：
1. 验证 kosong.step() API 正常工作
2. 验证 Agent 循环正常运行
3. 验证工具调用成功执行
4. 验证 UI 正确显示工具调用过程

对应源码：kimi-cli-fork/tests/test_soul.py
"""

import asyncio
from pathlib import Path

import pytest

from my_cli.soul import create_soul, run_soul
from my_cli.wire import WireUISide


@pytest.mark.asyncio
async def test_stage8_tool_calling():
    """
    Stage 8 端到端测试：工具调用

    测试流程：
    1. 创建 Soul（带 Toolset）
    2. 让 LLM 调用 ReadFile 工具读取文件
    3. 验证工具成功调用并返回结果
    """
    # 1. 创建 Soul
    work_dir = Path(__file__).parent.parent
    soul = create_soul(work_dir=work_dir)

    # 2. 创建测试文件
    test_file = work_dir / "test_file.txt"
    test_file.write_text("Hello from Stage 8!")

    try:
        # 3. 准备测试输入（让 LLM 读取文件）
        user_input = f"请使用 ReadFile 工具读取文件：{test_file}"

        # 4. 收集 UI 消息（用于验证）
        received_messages = []

        async def test_ui_loop(wire_ui: WireUISide):
            """测试 UI Loop - 收集所有消息"""
            while True:
                msg = await wire_ui.receive()
                received_messages.append(msg)

                # 检查是否结束
                from my_cli.wire.message import StepInterrupted

                if isinstance(msg, StepInterrupted):
                    break

        # 5. 运行 Soul
        cancel_event = asyncio.Event()
        await run_soul(
            soul=soul,
            user_input=user_input,
            ui_loop_fn=test_ui_loop,
            cancel_event=cancel_event,
        )

        # 6. 验证结果
        from kosong.message import ToolCall
        from kosong.tooling import ToolResult, ToolOk

        # 验证是否有工具调用
        tool_calls = [msg for msg in received_messages if isinstance(msg, ToolCall)]
        assert len(tool_calls) > 0, "应该至少有一次工具调用"

        # 验证是否调用了 ReadFile
        read_file_calls = [tc for tc in tool_calls if tc.name == "ReadFile"]
        assert len(read_file_calls) > 0, "应该调用了 ReadFile 工具"

        # 验证工具结果
        tool_results = [msg for msg in received_messages if isinstance(msg, ToolResult)]
        assert len(tool_results) > 0, "应该至少有一个工具结果"

        # 验证 ReadFile 成功
        read_file_results = [
            tr
            for tr in tool_results
            if any(tc.id == tr.tool_call_id for tc in read_file_calls)
        ]
        assert len(read_file_results) > 0, "应该有 ReadFile 的结果"
        assert isinstance(
            read_file_results[0].result, ToolOk
        ), "ReadFile 应该成功"

        # 验证读取的内容正确
        output = read_file_results[0].result.output
        assert "Hello from Stage 8!" in str(output), "应该读取到文件内容"

        print("\n✅ Stage 8 工具调用测试通过！")

    finally:
        # 7. 清理测试文件
        if test_file.exists():
            test_file.unlink()


@pytest.mark.asyncio
async def test_stage8_bash_tool():
    """
    Stage 8 测试：Bash 工具调用

    测试 Bash 工具是否正常工作
    """
    work_dir = Path(__file__).parent.parent
    soul = create_soul(work_dir=work_dir)

    user_input = "请使用 Bash 工具执行命令：echo 'Stage 8 Bash Test'"

    received_messages = []

    async def test_ui_loop(wire_ui: WireUISide):
        """测试 UI Loop"""
        while True:
            msg = await wire_ui.receive()
            received_messages.append(msg)

            from my_cli.wire.message import StepInterrupted

            if isinstance(msg, StepInterrupted):
                break

    cancel_event = asyncio.Event()
    await run_soul(
        soul=soul,
        user_input=user_input,
        ui_loop_fn=test_ui_loop,
        cancel_event=cancel_event,
    )

    # 验证 Bash 工具调用
    from kosong.message import ToolCall
    from kosong.tooling import ToolResult, ToolOk

    tool_calls = [msg for msg in received_messages if isinstance(msg, ToolCall)]
    bash_calls = [tc for tc in tool_calls if tc.name == "Bash"]
    assert len(bash_calls) > 0, "应该调用了 Bash 工具"

    tool_results = [msg for msg in received_messages if isinstance(msg, ToolResult)]
    bash_results = [
        tr
        for tr in tool_results
        if any(tc.id == tr.tool_call_id for tc in bash_calls)
    ]
    assert len(bash_results) > 0, "应该有 Bash 的结果"
    assert isinstance(bash_results[0].result, ToolOk), "Bash 应该成功"

    output = str(bash_results[0].result.output)
    assert "Stage 8 Bash Test" in output, "应该有 echo 的输出"

    print("\n✅ Stage 8 Bash 工具测试通过！")


if __name__ == "__main__":
    # 直接运行测试（用于调试）
    print("🧪 运行 Stage 8 工具调用测试...\n")
    asyncio.run(test_stage8_tool_calling())
    asyncio.run(test_stage8_bash_tool())
    print("\n✅ 所有 Stage 8 测试通过！")

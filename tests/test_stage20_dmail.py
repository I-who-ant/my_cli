"""
Stage 20 测试：D-Mail 系统完整功能测试

测试内容：
1. DenwaRenji 基础功能（send_dmail, fetch_pending_dmail）
2. SendDMail 工具（工具调用）
3. BackToTheFuture 异常处理
4. Context 回滚和消息添加
"""

import asyncio
from pathlib import Path

from kosong.message import Message

from my_cli.soul.context import Context
from my_cli.soul.denwarenji import DenwaRenji, DMail, DenwaRenjiError
from my_cli.soul.kimisoul import BackToTheFuture
from my_cli.tools.dmail import SendDMail


async def test_denwa_renji_basic():
    """测试 DenwaRenji 基础功能"""
    print("\n=== 测试 1: DenwaRenji 基础功能 ===")

    denwa_renji = DenwaRenji()
    assert denwa_renji._n_checkpoints == 0
    assert denwa_renji._pending_dmail is None

    # 设置 checkpoint 数量
    denwa_renji.set_n_checkpoints(3)
    assert denwa_renji._n_checkpoints == 3

    # 发送 D-Mail
    dmail = DMail(message="Test message to the past", checkpoint_id=1)
    denwa_renji.send_dmail(dmail)
    assert denwa_renji._pending_dmail == dmail

    # 获取 D-Mail
    fetched = denwa_renji.fetch_pending_dmail()
    assert fetched == dmail
    assert denwa_renji._pending_dmail is None  # 已清空

    print("✅ DenwaRenji 基础功能测试通过")


async def test_denwa_renji_errors():
    """测试 DenwaRenji 错误处理"""
    print("\n=== 测试 2: DenwaRenji 错误处理 ===")

    denwa_renji = DenwaRenji()
    denwa_renji.set_n_checkpoints(2)

    # 测试：一次只能发送一个 D-Mail
    dmail1 = DMail(message="First", checkpoint_id=0)
    denwa_renji.send_dmail(dmail1)

    try:
        dmail2 = DMail(message="Second", checkpoint_id=1)
        denwa_renji.send_dmail(dmail2)
        assert False, "应该抛出异常"
    except DenwaRenjiError as e:
        assert "Only one D-Mail" in str(e)
        print("✅ 检测到重复发送 D-Mail 错误")

    # 清空
    denwa_renji.fetch_pending_dmail()

    # 测试：checkpoint_id 为负数（Pydantic 会在创建对象时验证）
    try:
        from pydantic import ValidationError
        dmail = DMail(message="Test", checkpoint_id=-1)
        assert False, "应该抛出异常"
    except ValidationError as e:
        assert "greater than or equal to 0" in str(e)
        print("✅ 检测到负数 checkpoint_id 错误（Pydantic 验证）")

    # 测试：checkpoint_id 超出范围
    try:
        dmail = DMail(message="Test", checkpoint_id=5)
        denwa_renji.send_dmail(dmail)
        assert False, "应该抛出异常"
    except DenwaRenjiError as e:
        assert "no checkpoint" in str(e)
        print("✅ 检测到 checkpoint_id 超出范围错误")

    print("✅ DenwaRenji 错误处理测试通过")


async def test_send_dmail_tool():
    """测试 SendDMail 工具"""
    print("\n=== 测试 3: SendDMail 工具 ===")

    denwa_renji = DenwaRenji()
    denwa_renji.set_n_checkpoints(2)

    tool = SendDMail(denwa_renji=denwa_renji)
    assert tool.name == "SendDMail"
    assert tool.params == DMail

    # 测试成功发送
    dmail = DMail(message="Test from tool", checkpoint_id=0)
    result = await tool(dmail)

    # SendDMail 永远返回 ToolError（因为成功会触发异常）
    assert result.output == ""
    assert "not sent successfully" in result.message

    # 验证 D-Mail 已经在 denwa_renji 中
    fetched = denwa_renji.fetch_pending_dmail()
    assert fetched.message == "Test from tool"
    assert fetched.checkpoint_id == 0

    print("✅ SendDMail 工具测试通过")


async def test_back_to_the_future_exception():
    """测试 BackToTheFuture 异常"""
    print("\n=== 测试 4: BackToTheFuture 异常 ===")

    messages = [Message(role="user", content="D-Mail content")]
    exception = BackToTheFuture(checkpoint_id=1, messages=messages)

    assert exception.checkpoint_id == 1
    assert len(exception.messages) == 1
    assert exception.messages[0].content == "D-Mail content"

    print("✅ BackToTheFuture 异常测试通过")


async def test_context_revert_with_dmail():
    """测试 Context 回滚与 D-Mail 集成"""
    print("\n=== 测试 5: Context 回滚与 D-Mail 集成（简化版）===")

    # 简化测试：只验证核心 API 存在，不深度测试 revert_to
    # （revert_to 在 Stage 18 已经测试过，这里只需要验证能调用即可）

    work_dir = Path("/tmp/test_dmail_context")
    work_dir.mkdir(parents=True, exist_ok=True)

    file_backend = work_dir / "history.jsonl"
    context = Context(file_backend=file_backend)

    # 验证 API 存在
    await context.append_message(Message(role="user", content="Message 1"))
    await context.checkpoint(add_user_message=False)
    assert context.n_checkpoints == 1

    await context.append_message(Message(role="assistant", content="Response 1"))
    assert hasattr(context, "revert_to")  # 验证 revert_to 方法存在

    print("✅ Context 回滚与 D-Mail 集成测试通过（API 验证）")

    # 清理
    import shutil
    shutil.rmtree(work_dir, ignore_errors=True)


async def main():
    """运行所有测试"""
    print("🧪 开始 Stage 20 D-Mail 系统测试...")

    await test_denwa_renji_basic()
    await test_denwa_renji_errors()
    await test_send_dmail_tool()
    await test_back_to_the_future_exception()
    await test_context_revert_with_dmail()

    print("\n✨ 所有测试通过！D-Mail 系统实现完成！")


if __name__ == "__main__":
    asyncio.run(main())

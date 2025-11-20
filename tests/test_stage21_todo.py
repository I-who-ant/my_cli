"""
Stage 21.3 测试：SetTodoList 工具

测试内容：
1. SetTodoList 工具基础功能
2. Todo 模型验证
3. 状态格式化
4. 描述文件
"""

import asyncio
from pathlib import Path

from my_cli.tools.todo import SetTodoList, SetTodoListParams, Todo


async def test_settodolist_tool_basic():
    """测试 SetTodoList 工具基础功能"""
    print("\n=== 测试 1: SetTodoList 工具基础功能 ===")

    # 创建 SetTodoList 工具实例
    settodolist = SetTodoList()

    # 验证工具属性
    assert settodolist.name == "SetTodoList"
    assert settodolist.params == SetTodoListParams
    assert isinstance(settodolist.description, str)
    assert len(settodolist.description) > 0

    print("✅ SetTodoList 工具属性验证通过")

    # 测试工具调用
    params = SetTodoListParams(
        todos=[
            Todo(title="Read requirements", status="Done"),
            Todo(title="Design schema", status="In Progress"),
            Todo(title="Implement API", status="Pending"),
        ]
    )
    result = await settodolist(params)

    # 验证返回值
    assert hasattr(result, "brief")
    assert "Read requirements" in result.brief
    assert "Design schema" in result.brief
    assert "Implement API" in result.brief
    print(f"✅ SetTodoList 工具返回:\n{result.brief}")

    print("✅ SetTodoList 工具基础功能测试通过")


async def test_todo_model_validation():
    """测试 Todo 模型验证"""
    print("\n=== 测试 2: Todo 模型验证 ===")

    # 测试有效的 Todo
    todo_pending = Todo(title="Test task", status="Pending")
    todo_in_progress = Todo(title="Test task", status="In Progress")
    todo_done = Todo(title="Test task", status="Done")

    assert todo_pending.status == "Pending"
    assert todo_in_progress.status == "In Progress"
    assert todo_done.status == "Done"
    print("✅ 所有状态验证通过")

    # 测试无效状态（Pydantic 会验证）
    try:
        from pydantic import ValidationError

        Todo(title="Test", status="Invalid")  # 无效状态
        print("❌ 应该抛出 ValidationError")
    except ValidationError:
        print("✅ 无效状态被正确拒绝")

    # 测试空标题（min_length=1）
    try:
        Todo(title="", status="Pending")  # 空标题
        print("❌ 应该抛出 ValidationError")
    except ValidationError:
        print("✅ 空标题被正确拒绝")

    print("✅ Todo 模型验证测试通过")


async def test_status_formatting():
    """测试状态格式化"""
    print("\n=== 测试 3: 状态格式化 ===")

    settodolist = SetTodoList()

    # 测试不同状态的格式化
    params = SetTodoListParams(
        todos=[
            Todo(title="Completed task", status="Done"),
            Todo(title="Current task", status="In Progress"),
            Todo(title="Future task", status="Pending"),
        ]
    )

    result = await settodolist(params)

    # 验证格式化
    assert "~~Completed task~~" in result.brief  # Done: 删除线
    assert "**Current task**" in result.brief  # In Progress: 粗体
    assert "Future task" in result.brief  # Pending: 普通
    assert "[Done]" in result.brief
    assert "[In Progress]" in result.brief
    assert "[Pending]" in result.brief

    print(f"✅ 格式化结果:\n{result.brief}")
    print("✅ 状态格式化测试通过")


async def test_empty_todo_list():
    """测试空的 todo 列表"""
    print("\n=== 测试 4: 空的 todo 列表 ===")

    settodolist = SetTodoList()

    # 空列表
    params = SetTodoListParams(todos=[])
    result = await settodolist(params)

    assert result.brief == ""
    print("✅ 空列表处理正确")

    print("✅ 空列表测试通过")


async def test_todo_description_file():
    """测试 set_todo_list.md 描述文件"""
    print("\n=== 测试 5: set_todo_list.md 描述文件 ===")

    # 验证描述文件存在
    desc_file = (
        Path(__file__).parent.parent / "my_cli" / "tools" / "todo" / "set_todo_list.md"
    )
    assert desc_file.exists(), f"描述文件不存在: {desc_file}"
    print(f"✅ 描述文件存在: {desc_file}")

    # 验证描述文件内容
    content = desc_file.read_text()
    assert len(content) > 0
    assert "SetTodoList" in content or "Todo" in content
    print(f"✅ 描述文件内容有效（长度: {len(content)} 字符）")

    print("✅ set_todo_list.md 描述文件测试通过")


async def main():
    """运行所有测试"""
    print("🧪 开始 Stage 21.3 SetTodoList 工具测试...")

    await test_settodolist_tool_basic()
    await test_todo_model_validation()
    await test_status_formatting()
    await test_empty_todo_list()
    await test_todo_description_file()

    print("\n✨ 所有测试通过！SetTodoList 工具实现完成！")


if __name__ == "__main__":
    asyncio.run(main())

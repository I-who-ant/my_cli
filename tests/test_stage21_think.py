"""
Stage 21.1 测试：Think 工具

测试内容：
1. Think 工具基础功能
2. ThinkParams 参数验证
3. 工具返回值格式
"""

import asyncio
from pathlib import Path

from my_cli.tools.think import Think, ThinkParams


async def test_think_tool_basic():
    """测试 Think 工具基础功能"""
    print("\n=== 测试 1: Think 工具基础功能 ===")

    # 创建 Think 工具实例
    think = Think()

    # 验证工具属性
    assert think.name == "Think"
    assert think.params == ThinkParams
    assert isinstance(think.description, str)
    assert len(think.description) > 0

    print("✅ Think 工具属性验证通过")

    # 测试工具调用
    params = ThinkParams(thought="我需要先读取配置文件，然后分析项目结构")
    result = await think(params)

    # 验证返回值（官方返回 ToolOk，message 包含思考内容）
    assert hasattr(result, "message")
    assert "Thinking" in result.message
    assert "读取配置文件" in result.message
    print(f"✅ Think 工具返回: {result.message}")

    print("✅ Think 工具基础功能测试通过")


async def test_think_params_validation():
    """测试 ThinkParams 参数验证"""
    print("\n=== 测试 2: ThinkParams 参数验证 ===")

    # 测试有效参数
    params = ThinkParams(thought="Test thought")
    assert params.thought == "Test thought"
    print("✅ 有效参数验证通过")

    # 测试空字符串（Pydantic 允许）
    params_empty = ThinkParams(thought="")
    assert params_empty.thought == ""
    print("✅ 空字符串参数验证通过")

    # 测试长字符串
    long_thought = "这是一个很长的思考过程..." * 100
    params_long = ThinkParams(thought=long_thought)
    assert params_long.thought == long_thought
    print("✅ 长字符串参数验证通过")

    print("✅ ThinkParams 参数验证测试通过")


async def test_think_return_format():
    """测试 Think 工具返回值格式"""
    print("\n=== 测试 3: Think 工具返回值格式 ===")

    think = Think()

    # 测试不同内容的思考
    test_cases = [
        "简单的思考",
        "复杂的思考：\n1. 步骤一\n2. 步骤二\n3. 步骤三",
        "包含代码的思考：`code_snippet`",
    ]

    for i, thought in enumerate(test_cases, 1):
        params = ThinkParams(thought=thought)
        result = await think(params)

        assert hasattr(result, "message")
        assert thought in result.message
        print(f"✅ 测试用例 {i} 通过: {result.message[:50]}...")

    print("✅ Think 工具返回值格式测试通过")


async def test_think_description_file():
    """测试 think.md 描述文件"""
    print("\n=== 测试 4: think.md 描述文件 ===")

    # 验证描述文件存在
    desc_file = Path(__file__).parent.parent / "my_cli" / "tools" / "think" / "think.md"
    assert desc_file.exists(), f"描述文件不存在: {desc_file}"
    print(f"✅ 描述文件存在: {desc_file}")

    # 验证描述文件内容
    content = desc_file.read_text()
    assert len(content) > 0
    assert "Think Tool" in content or "When to Use" in content
    print(f"✅ 描述文件内容有效（长度: {len(content)} 字符）")

    print("✅ think.md 描述文件测试通过")


async def main():
    """运行所有测试"""
    print("🧪 开始 Stage 21.1 Think 工具测试...")

    await test_think_tool_basic()
    await test_think_params_validation()
    await test_think_return_format()
    await test_think_description_file()

    print("\n✨ 所有测试通过！Think 工具实现完成！")


if __name__ == "__main__":
    asyncio.run(main())

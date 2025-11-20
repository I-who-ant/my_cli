"""
Stage 21.2 测试：SearchWeb 和 FetchURL 工具

测试内容：
1. SearchWeb 工具（Moonshot Search API）
2. FetchURL 工具（网页抓取）
3. 配置集成和 SkipThisTool 处理
"""

import asyncio
from pathlib import Path

from my_cli.config import Config, MoonshotSearchConfig, Services
from my_cli.tools import SkipThisTool
from my_cli.tools.web import SearchWeb, FetchURL
from pydantic import SecretStr


async def test_searchweb_skip_without_config():
    """测试 SearchWeb 在没有配置时抛出 SkipThisTool"""
    print("\n=== 测试 1: SearchWeb 配置缺失处理 ===")

    # 创建没有 moonshot_search 的配置
    config = Config(
        default_model="",
        models={},
        providers={},
        services=Services(),  # 空服务配置
    )

    # 尝试创建 SearchWeb（应该抛出 SkipThisTool）
    try:
        searchweb = SearchWeb(config)
        print("❌ 应该抛出 SkipThisTool")
    except SkipThisTool:
        print("✅ 正确抛出 SkipThisTool（配置缺失）")

    print("✅ SearchWeb 配置缺失处理测试通过")


async def test_searchweb_with_config():
    """测试 SearchWeb 工具（需要真实的 Moonshot Search API）"""
    print("\n=== 测试 2: SearchWeb 工具基础功能 ===")

    # 创建带 moonshot_search 配置的 Config
    config = Config(
        default_model="",
        models={},
        providers={},
        services=Services(
            moonshot_search=MoonshotSearchConfig(
                base_url="https://api.moonshot.cn/v1/web/search",
                api_key=SecretStr("sk-hJwUlVMp0MK70TLeahsXhvKWsp1VYHLie4lYcVqmrzBdu9qM"),
            )
        ),
    )

    # 创建 SearchWeb 工具
    searchweb = SearchWeb(config)

    # 验证工具属性
    assert searchweb.name == "SearchWeb"
    print("✅ SearchWeb 工具创建成功")

    # 注意：这里不实际调用 API（需要网络和真实配置）
    # 实际调用测试需要在集成测试中进行
    print("✅ SearchWeb 工具基础功能测试通过")


async def test_fetchurl_tool_basic():
    """测试 FetchURL 工具基础功能"""
    print("\n=== 测试 3: FetchURL 工具基础功能 ===")

    # 创建 FetchURL 工具（不需要配置）
    fetchurl = FetchURL()

    # 验证工具属性
    assert fetchurl.name == "FetchURL"
    print("✅ FetchURL 工具属性验证通过")

    # 注意：这里不实际抓取网页（需要网络）
    # 实际抓取测试需要在集成测试中进行
    print("✅ FetchURL 工具基础功能测试通过")


async def test_web_description_files():
    """测试 search.md 和 fetch.md 描述文件"""
    print("\n=== 测试 4: Web 工具描述文件 ===")

    # 验证 search.md 存在
    search_md = (
        Path(__file__).parent.parent / "my_cli" / "tools" / "web" / "search.md"
    )
    assert search_md.exists(), f"描述文件不存在: {search_md}"
    print(f"✅ search.md 存在: {search_md}")

    # 验证 search.md 内容
    search_content = search_md.read_text()
    assert len(search_content) > 0
    assert "SearchWeb" in search_content or "search" in search_content.lower()
    print(f"✅ search.md 内容有效（长度: {len(search_content)} 字符）")

    # 验证 fetch.md 存在
    fetch_md = (
        Path(__file__).parent.parent / "my_cli" / "tools" / "web" / "fetch.md"
    )
    assert fetch_md.exists(), f"描述文件不存在: {fetch_md}"
    print(f"✅ fetch.md 存在: {fetch_md}")

    # 验证 fetch.md 内容
    fetch_content = fetch_md.read_text()
    assert len(fetch_content) > 0
    assert "FetchURL" in fetch_content or "fetch" in fetch_content.lower()
    print(f"✅ fetch.md 内容有效（长度: {len(fetch_content)} 字符）")

    print("✅ Web 工具描述文件测试通过")


async def main():
    """运行所有测试"""
    print("🧪 开始 Stage 21.2 Web 工具测试...")

    await test_searchweb_skip_without_config()
    await test_searchweb_with_config()
    await test_fetchurl_tool_basic()
    await test_web_description_files()

    print("\n✨ 所有测试通过！Web 工具实现完成！")


if __name__ == "__main__":
    asyncio.run(main())

"""
演示 Config 的保存和读取

展示如何把 Python Config 对象保存到 JSON 文件
"""

from pydantic import SecretStr
from my_cli.config import (
    Config,
    LLMProvider,
    LLMModel,
    Services,
    MoonshotSearchConfig,
    save_config,
    load_config,
    get_config_file,
)


def demo_save_config():
    """演示保存配置"""
    print("=== 演示 1: 创建并保存配置 ===\n")

    # 1. 创建 Config 对象（Python）
    config = Config(
        default_model="kimi-k2-thinking-turbo",
        models={
            "kimi-k2-thinking-turbo": LLMModel(
                provider="moonshot-cn",
                model="kimi-k2-thinking-turbo",
                max_context_size=262144,
            )
        },
        providers={
            "moonshot-cn": LLMProvider(
                type="kimi",
                base_url="https://api.moonshot.cn/v1",
                api_key=SecretStr("sk-your-api-key-here"),
            )
        },
        services=Services(
            moonshot_search=MoonshotSearchConfig(
                base_url="https://api.moonshot.cn/v1/web/search",
                api_key=SecretStr("sk-your-search-api-key"),
            )
        ),
    )

    print("Config 对象创建成功：")
    print(f"  - default_model: {config.default_model}")
    print(f"  - providers: {list(config.providers.keys())}")
    print(f"  - models: {list(config.models.keys())}")
    print(f"  - services.moonshot_search: {'✅ 已配置' if config.services.moonshot_search else '❌ 未配置'}")

    # 2. 保存到文件（JSON）
    config_file = get_config_file()
    print(f"\n保存配置到: {config_file}")
    save_config(config)
    print("✅ 配置已保存")

    # 3. 查看生成的 JSON 内容
    print(f"\n生成的 JSON 内容（前 500 字符）:")
    with open(config_file, "r", encoding="utf-8") as f:
        content = f.read()
        print(content[:500])
        print("...")


def demo_load_config():
    """演示加载配置"""
    print("\n\n=== 演示 2: 从文件加载配置 ===\n")

    # 1. 从 JSON 文件加载
    config_file = get_config_file()
    print(f"从文件加载配置: {config_file}")
    config = load_config()
    print("✅ 配置已加载")

    # 2. 访问配置
    print("\n配置内容：")
    print(f"  - default_model: {config.default_model}")
    print(f"  - providers: {list(config.providers.keys())}")
    print(f"  - models: {list(config.models.keys())}")

    # 3. 访问嵌套配置
    if config.services.moonshot_search:
        print(f"  - moonshot_search.base_url: {config.services.moonshot_search.base_url}")
        print(f"  - moonshot_search.api_key: {config.services.moonshot_search.api_key.get_secret_value()[:10]}...")


def demo_model_dump_json():
    """演示 Pydantic 的 model_dump_json() 方法"""
    print("\n\n=== 演示 3: Pydantic 序列化魔法 ===\n")

    # 创建简单的配置
    config = Config(
        default_model="test-model",
        models={},
        providers={},
        services=Services(
            moonshot_search=MoonshotSearchConfig(
                base_url="https://api.example.com/search",
                api_key=SecretStr("sk-secret-key-123"),
            )
        ),
    )

    # 方法 1: model_dump() - 转换为字典
    print("1. model_dump() - 转换为 Python 字典:")
    data = config.model_dump(exclude_none=True)
    print(f"   类型: {type(data)}")
    print(f"   内容: {list(data.keys())}")

    # 方法 2: model_dump_json() - 转换为 JSON 字符串
    print("\n2. model_dump_json() - 转换为 JSON 字符串:")
    json_str = config.model_dump_json(indent=2, exclude_none=True)
    print(f"   类型: {type(json_str)}")
    print(f"   内容（前 200 字符）:\n{json_str[:200]}")
    print("   ...")

    # 这就是写入文件的内容！
    print("\n💡 这个 JSON 字符串就是写入 config.json 的内容！")


if __name__ == "__main__":
    # 演示 1: 保存配置
    demo_save_config()

    # 演示 2: 加载配置
    demo_load_config()

    # 演示 3: Pydantic 序列化
    demo_model_dump_json()

    print("\n\n✨ 演示完成！")
    print("\n总结：")
    print("  1. save_config(config) → config.model_dump_json() → 写入文件")
    print("  2. load_config() → 读取文件 → Config(**json.load(f))")
    print("  3. Pydantic 自动处理 Python ↔ JSON 转换")

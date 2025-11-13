"""
阶段 4-5：配置管理模块

学习目标：
1. 理解配置文件的作用
2. 实现多 Provider 和 Model 配置
3. 支持环境变量覆盖（官方 kimi-cli 的核心特性）

对应源码：kimi-cli-main/src/kimi_cli/config.py (156 行)

阶段演进：
- Stage 4-5：基础配置系统 ✅
  * LLMProvider 配置（type, base_url, api_key）
  * LLMModel 配置（provider, model, max_context_size）
  * 配置文件加载/保存
  * 环境变量覆盖（KIMI_API_KEY, KIMI_BASE_URL）

- Stage 6+：完整配置系统（待实现）
  * LoopControl 配置（max_steps_per_run, max_retries_per_step）
  * Services 配置（moonshot_search 等外部服务）
  * 多 Provider 类型支持（openai_legacy, openai_responses, anthropic）
  * ModelCapability 配置（image_in, thinking）
  * custom_headers 支持
"""

import json
import os
from pathlib import Path

from pydantic import BaseModel, Field, SecretStr, field_serializer


class LLMProvider(BaseModel):
    """
    LLM Provider 配置

    Stage 4-5 实现：
    - type: Provider 类型（目前只支持 "kimi"）
    - base_url: API 基础 URL
    - api_key: API 密钥

    Stage 6+ 补充：
    - custom_headers: 自定义请求头（用于特殊认证）

    对应源码：kimi-cli-main/src/kimi_cli/config.py:13-23
    """

    type: str  # Stage 4-5: 只支持 "kimi"，Stage 6+: 支持 "openai_legacy", "anthropic" 等
    base_url: str
    api_key: SecretStr
    # custom_headers: dict[str, str] | None = None  # Stage 6+ 实现

    @field_serializer("api_key", when_used="json")
    def dump_secret(self, v: SecretStr):
        """序列化时保留完整 API Key（用于保存配置文件）"""
        return v.get_secret_value()


class LLMModel(BaseModel):
    """
    LLM Model 配置

    Stage 4-5 实现：
    - provider: 关联的 Provider 名称
    - model: 模型名称（如 "moonshot-v1-8k"）
    - max_context_size: 最大上下文长度

    Stage 6+ 补充：
    - capabilities: 模型能力（image_in, thinking）

    对应源码：kimi-cli-main/src/kimi_cli/config.py:30-40
    """

    provider: str  # provider 名称（对应 providers 中的 key）
    model: str  # 模型名称
    max_context_size: int = 128000
    # capabilities: set[ModelCapability] | None = None  # Stage 6+ 实现


# ============================================================
# Stage 6+ 待实现的配置类
# ============================================================

# class LoopControl(BaseModel):
#     """
#     Agent 循环控制配置（Stage 7+ 实现）
#
#     用途：
#     - 限制单次运行的最大步数（防止死循环）
#     - 限制单步的最大重试次数（处理临时错误）
#     """
#     max_steps_per_run: int = 100
#     max_retries_per_step: int = 3

# class MoonshotSearchConfig(BaseModel):
#     """
#     Moonshot Search 服务配置（Stage 8+ 实现）
#
#     用途：
#     - 集成 Moonshot 的搜索服务
#     - 为 LLM 提供实时网络搜索能力
#     """
#     base_url: str
#     api_key: SecretStr
#     custom_headers: dict[str, str] | None = None

# class Services(BaseModel):
#     """外部服务配置（Stage 8+ 实现）"""
#     moonshot_search: MoonshotSearchConfig | None = None


class Config(BaseModel):
    """
    主配置结构

    Stage 4-5 实现：
    - default_model: 默认使用的模型
    - providers: Provider 配置字典
    - models: Model 配置字典

    Stage 6+ 补充：
    - loop_control: Agent 循环控制配置
    - services: 外部服务配置

    对应源码：kimi-cli-main/src/kimi_cli/config.py:74-92
    """

    default_model: str = Field(default="", description="默认使用的模型")
    providers: dict[str, LLMProvider] = Field(
        default_factory=dict, description="Provider 配置列表"
    )
    models: dict[str, LLMModel] = Field(default_factory=dict, description="Model 配置列表")

    # Stage 6+ 补充：
    # loop_control: LoopControl = Field(default_factory=LoopControl)
    # services: Services = Field(default_factory=Services)

    # @model_validator(mode="after")
    # def validate_model(self) -> Self:
    #     """Stage 6+ 补充：验证配置的一致性"""
    #     if self.default_model and self.default_model not in self.models:
    #         raise ValueError(f"Default model {self.default_model} not found in models")
    #     for model in self.models.values():
    #         if model.provider not in self.providers:
    #             raise ValueError(f"Provider {model.provider} not found in providers")
    #     return self


# ============================================================
# 配置文件管理
# ============================================================


def get_config_file() -> Path:
    """
    获取配置文件路径

    Stage 4-5 实现：
    - 配置文件放在项目根目录: .mycli_config.json

    Stage 6+ 改进：
    - 使用系统级配置目录（参考官方实现）
    - Linux: ~/.config/my_cli/config.json
    - macOS: ~/Library/Application Support/my_cli/config.json
    - Windows: %APPDATA%/my_cli/config.json

    对应源码：kimi-cli-main/src/kimi_cli/config.py:95-97
    """
    # Stage 4-5: 简化版，直接放在项目根目录
    return Path.cwd() / ".mycli_config.json"


def get_default_config() -> Config:
    """
    获取默认配置（空配置）

    Stage 4-5 实现：
    - 返回空配置（没有任何 provider 和 model）

    对应源码：kimi-cli-main/src/kimi_cli/config.py:100-107
    """
    return Config(
        default_model="",
        providers={},
        models={},
    )


def get_example_config() -> Config:
    """
    获取示例配置

    Stage 4-5 实现：
    - 包含两个 Provider（moonshot 和 kimi）
    - 包含两个 Model（moonshot-k2 和 kimi-coding）
    - 使用用户提供的 API Key

    用途：
    - 首次运行时创建示例配置文件
    - 让用户知道如何配置

    注意：
    - API Key 是占位符，用户需要替换为真实的 Key
    """
    return Config(
        default_model="moonshot-k2",  # 默认使用 Moonshot
        providers={
            "moonshot": LLMProvider(
                type="kimi",
                base_url="https://api.moonshot.cn/v1",
                api_key=SecretStr("your-moonshot-api-key-here"),
            ),
            "kimi": LLMProvider(
                type="kimi",
                base_url="https://api.kimi.com/coding/",
                api_key=SecretStr("your-kimi-api-key-here"),
            ),
        },
        models={
            "moonshot-k2": LLMModel(
                provider="moonshot",
                model="moonshot-v1-8k",
                max_context_size=128000,
            ),
            "kimi-coding": LLMModel(
                provider="kimi",
                model="kimi-k2-turbo-preview",
                max_context_size=128000,
            ),
        },
    )


def load_config(config_file: Path | None = None) -> Config:
    """
    加载配置文件

    Stage 4-5 实现：
    - 如果配置文件不存在，创建示例配置文件
    - 读取 JSON 文件并解析为 Config 对象
    - 基础错误处理

    Stage 6+ 改进：
    - 更详细的错误提示和修复建议
    - 配置文件迁移（版本升级）
    - 配置验证（使用 model_validator）

    Args:
        config_file: 配置文件路径（None 则使用默认路径）

    Returns:
        Config: 配置对象

    对应源码：kimi-cli-main/src/kimi_cli/config.py:110-141
    """
    config_file = config_file or get_config_file()

    if not config_file.exists():
        print(f"⚠️  配置文件不存在: {config_file}")
        print("💡 正在创建示例配置文件...")
        config = get_example_config()
        save_config(config, config_file)
        print(f"✅ 示例配置文件已创建: {config_file}")
        print()
        print("📝 请编辑配置文件，填入你的 API Key：")
        print(f"   {config_file}")
        print()
        return config

    try:
        with open(config_file, encoding="utf-8") as f:
            data = json.load(f)
        return Config(**data)
    except json.JSONDecodeError as e:
        raise ValueError(f"配置文件 JSON 格式错误: {e}") from e
    except Exception as e:
        raise ValueError(f"配置文件加载失败: {e}") from e


def save_config(config: Config, config_file: Path | None = None) -> None:
    """
    保存配置到文件

    Stage 4-5 实现：
    - 序列化 Config 对象为 JSON
    - 自动创建父目录
    - 格式化输出（indent=2）

    Args:
        config: 配置对象
        config_file: 配置文件路径（None 则使用默认路径）

    对应源码：kimi-cli-main/src/kimi_cli/config.py:144-155
    """
    config_file = config_file or get_config_file()
    config_file.parent.mkdir(parents=True, exist_ok=True)

    with open(config_file, "w", encoding="utf-8") as f:
        f.write(config.model_dump_json(indent=2, exclude_none=True))


# ============================================================
# 环境变量覆盖（官方核心特性）
# ============================================================


def augment_provider_with_env(provider: LLMProvider) -> dict[str, str]:
    """
    使用环境变量覆盖 Provider 配置

    Stage 4-5 实现：
    - 支持 KIMI_API_KEY 覆盖 api_key
    - 支持 KIMI_BASE_URL 覆盖 base_url
    - 环境变量优先级 > 配置文件

    Stage 6+ 补充：
    - 支持 KIMI_MODEL_NAME 覆盖 model
    - 支持 KIMI_MODEL_MAX_CONTEXT_SIZE 覆盖 max_context_size
    - 支持 KIMI_MODEL_CAPABILITIES 覆盖 capabilities
    - 支持其他 Provider 的环境变量（OPENAI_*, ANTHROPIC_*）

    用途：
    - CI/CD 环境中动态配置
    - 临时测试不同的 API Key
    - 不修改配置文件的情况下切换配置

    Args:
        provider: Provider 配置对象（会被修改）

    Returns:
        dict: 应用的环境变量映射（用于日志）

    对应源码：kimi-cli-main/src/kimi_cli/llm.py:30-68
    """
    applied: dict[str, str] = {}

    if provider.type == "kimi":
        # 环境变量覆盖 API Key
        if api_key := os.getenv("KIMI_API_KEY"):
            provider.api_key = SecretStr(api_key)
            applied["KIMI_API_KEY"] = "******"  # 日志中隐藏真实 Key

        # 环境变量覆盖 Base URL
        if base_url := os.getenv("KIMI_BASE_URL"):
            provider.base_url = base_url
            applied["KIMI_BASE_URL"] = base_url

    # Stage 6+ 补充：
    # elif provider.type == "openai_legacy":
    #     if api_key := os.getenv("OPENAI_API_KEY"):
    #         provider.api_key = SecretStr(api_key)
    #         applied["OPENAI_API_KEY"] = "******"
    #     if base_url := os.getenv("OPENAI_BASE_URL"):
    #         provider.base_url = base_url
    #         applied["OPENAI_BASE_URL"] = base_url

    return applied


def get_provider_and_model(
    config: Config, model_name: str | None = None
) -> tuple[LLMProvider, LLMModel]:
    """
    根据 model_name 获取对应的 Provider 和 Model 配置

    Stage 4-5 实现：
    - 查找指定的 model（或使用 default_model）
    - 查找 model 关联的 provider
    - 应用环境变量覆盖
    - 基础错误处理

    Args:
        config: 配置对象
        model_name: 模型名称（None 则使用 default_model）

    Returns:
        tuple[LLMProvider, LLMModel]: Provider 和 Model 配置

    Raises:
        ValueError: 如果 model 或 provider 不存在
    """
    # 1. 确定使用哪个 model
    model_name = model_name or config.default_model
    if not model_name:
        raise ValueError("❌ 没有指定模型，且配置文件中没有 default_model")

    # 2. 查找 model 配置
    if model_name not in config.models:
        raise ValueError(f"❌ 模型不存在: {model_name}")

    model = config.models[model_name]

    # 3. 查找 provider 配置
    if model.provider not in config.providers:
        raise ValueError(f"❌ Provider 不存在: {model.provider}")

    provider = config.providers[model.provider]

    # 4. 应用环境变量覆盖
    applied = augment_provider_with_env(provider)
    if applied:
        print("🔧 使用环境变量覆盖配置:")
        for key, value in applied.items():
            print(f"   {key} = {value}")

    return provider, model


# ============================================================
# 示例用法
# ============================================================

if __name__ == "__main__":
    # 创建示例配置
    config = get_example_config()
    print("示例配置：")
    print(config.model_dump_json(indent=2))

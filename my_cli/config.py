"""
配置管理模块 ⭐ Stage 19.1 对齐官方

学习目标：
1. 理解配置文件的作用
2. 实现多 Provider 和 Model 配置
3. 支持环境变量覆盖
4. 完整的配置验证

对应源码：kimi-cli-fork/src/kimi_cli/config.py

阶段演进：
- Stage 4-5：基础配置系统 ✅
- Stage 19.1：完整对齐官方实现 ✅
  * LoopControl 配置
  * MoonshotSearchConfig 配置（TODO）
  * Services 配置（TODO）
  * model_validator 验证
  * 使用 logger 替代 print
  * 使用 get_share_dir() 获取配置路径
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Self

from pydantic import BaseModel, Field, SecretStr, ValidationError, field_serializer, model_validator

from my_cli.exception import ConfigError
from my_cli.llm import ModelCapability, ProviderType
from my_cli.share import get_share_dir
from my_cli.utils.logging import logger


class LLMProvider(BaseModel):
    """
    LLM Provider 配置 ⭐ Stage 19.1 对齐官方

    对应源码：kimi-cli-fork/src/kimi_cli/config.py:15-30
    """

    type: ProviderType
    """Provider 类型"""
    base_url: str
    """API 基础 URL"""
    api_key: SecretStr
    """API 密钥"""
    custom_headers: dict[str, str] | None = None
    """自定义请求头（用于特殊认证）"""

    @field_serializer("api_key", when_used="json")
    def dump_secret(self, v: SecretStr):
        """序列化时保留完整 API Key（用于保存配置文件）"""
        return v.get_secret_value()


class LLMModel(BaseModel):
    """
    LLM Model 配置 ⭐ Stage 19.1 对齐官方

    对应源码：kimi-cli-fork/src/kimi_cli/config.py:32-43
    """

    provider: str
    """Provider 名称"""
    model: str
    """模型名称"""
    max_context_size: int
    """最大上下文长度（单位：tokens）"""
    capabilities: set[ModelCapability] | None = None
    """模型能力"""


class LoopControl(BaseModel):
    """
    Agent 循环控制配置 ⭐ Stage 19.1 对齐官方

    用途：
    - 限制单次运行的最大步数（防止死循环）
    - 限制单步的最大重试次数（处理临时错误）

    对应源码：kimi-cli-fork/src/kimi_cli/config.py:45-52
    """

    max_steps_per_run: int = 100
    """单次运行的最大步数"""
    max_retries_per_step: int = 3
    """单步的最大重试次数"""


class MoonshotSearchConfig(BaseModel):
    """
    Moonshot Search 配置 ⭐ Stage 19.1 对齐官方

    TODO: Stage 20+ 实现搜索服务集成

    用途：
    - 集成 Moonshot 的搜索服务
    - 为 LLM 提供实时网络搜索能力

    对应源码：kimi-cli-fork/src/kimi_cli/config.py:54-67
    """

    base_url: str
    """Moonshot Search 服务基础 URL"""
    api_key: SecretStr
    """Moonshot Search API 密钥"""
    custom_headers: dict[str, str] | None = None
    """自定义请求头"""

    @field_serializer("api_key", when_used="json")
    def dump_secret(self, v: SecretStr):
        return v.get_secret_value()


class Services(BaseModel):
    """
    外部服务配置 ⭐ Stage 19.1 对齐官方

    TODO: Stage 20+ 实现完整的服务集成

    对应源码：kimi-cli-fork/src/kimi_cli/config.py:69-74
    """

    moonshot_search: MoonshotSearchConfig | None = None
    """Moonshot Search 配置"""


class Config(BaseModel):
    """
    主配置结构 ⭐ Stage 19.1 对齐官方

    对应源码：kimi-cli-fork/src/kimi_cli/config.py:76-95
    """

    default_model: str = Field(default="", description="默认使用的模型")
    models: dict[str, LLMModel] = Field(default_factory=dict, description="模型配置列表")
    providers: dict[str, LLMProvider] = Field(default_factory=dict, description="Provider 配置列表")
    loop_control: LoopControl = Field(default_factory=LoopControl, description="Agent 循环控制")
    services: Services = Field(default_factory=Services, description="外部服务配置")

    @model_validator(mode="after")
    def validate_model(self) -> Self:
        """
        验证配置的一致性 ⭐ Stage 19.1 对齐官方

        检查：
        1. default_model 是否存在于 models 中
        2. 每个 model 的 provider 是否存在于 providers 中

        对应源码：kimi-cli-fork/src/kimi_cli/config.py:87-94
        """
        if self.default_model and self.default_model not in self.models:
            raise ValueError(f"Default model {self.default_model} not found in models")
        for model in self.models.values():
            if model.provider not in self.providers:
                raise ValueError(f"Provider {model.provider} not found in providers")
        return self


# ============================================================
# 配置文件管理 ⭐ Stage 19.1 对齐官方
# ============================================================


def get_config_file() -> Path:
    """
    获取配置文件路径 ⭐ Stage 19.1 对齐官方

    使用系统级配置目录：
    - Linux: ~/.kimi/config.json
    - macOS: ~/Library/Application Support/kimi/config.json
    - Windows: %APPDATA%/kimi/config.json

    对应源码：kimi-cli-fork/src/kimi_cli/config.py:97-99
    """
    return get_share_dir() / "config.json"


def get_default_config() -> Config:
    """
    获取默认配置 ⭐ Stage 19.1 对齐官方

    返回空配置（没有任何 provider 和 model）

    对应源码：kimi-cli-fork/src/kimi_cli/config.py:102-109
    """
    return Config(
        default_model="",
        models={},
        providers={},
        services=Services(),
    )


def load_config(config_file: Path | None = None) -> Config:
    """
    加载配置文件 ⭐ Stage 19.1 对齐官方

    如果配置文件不存在，创建默认配置文件。

    Args:
        config_file: 配置文件路径（None 则使用默认路径）

    Returns:
        验证后的 Config 对象

    Raises:
        ConfigError: 如果配置文件无效

    对应源码：kimi-cli-fork/src/kimi_cli/config.py:112-144
    """
    config_file = config_file or get_config_file()
    logger.debug("Loading config from file: {file}", file=config_file)

    if not config_file.exists():
        config = get_default_config()
        logger.debug("No config file found, creating default config: {config}", config=config)
        config_file.parent.mkdir(parents=True, exist_ok=True)  # ⭐ 确保父目录存在
        with open(config_file, "w", encoding="utf-8") as f:
            f.write(config.model_dump_json(indent=2, exclude_none=True))
        return config

    try:
        with open(config_file, encoding="utf-8") as f:
            data = json.load(f)
        return Config(**data)
    except json.JSONDecodeError as e:
        raise ConfigError(f"Invalid JSON in configuration file: {e}") from e
    except ValidationError as e:
        raise ConfigError(f"Invalid configuration file: {e}") from e


def save_config(config: Config, config_file: Path | None = None):
    """
    保存配置到文件 ⭐ Stage 19.1 对齐官方

    Args:
        config: 配置对象
        config_file: 配置文件路径（None 则使用默认路径）

    对应源码：kimi-cli-fork/src/kimi_cli/config.py:146-158
    """
    config_file = config_file or get_config_file()
    logger.debug("Saving config to file: {file}", file=config_file)
    config_file.parent.mkdir(parents=True, exist_ok=True)  # ⭐ 确保父目录存在
    with open(config_file, "w", encoding="utf-8") as f:
        f.write(config.model_dump_json(indent=2, exclude_none=True))


# ============================================================
# 示例用法
# ============================================================

if __name__ == "__main__":
    # 创建示例配置
    config = get_default_config()
    print("默认配置：")
    print(config.model_dump_json(indent=2))
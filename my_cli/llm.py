"""
LLM 管理 - 统一的 LLM 接口

学习目标：
1. 理解 LLM 类的作用（封装 ChatProvider）
2. 理解 ModelCapability 枚举
3. 理解 create_llm() 工厂函数

对应源码：kimi-cli-fork/src/kimi_cli/llm.py

阶段演进：
- Stage 4-16：使用 ChatProvider 直接访问 ✅
- Stage 17：实现 LLM 类（封装 ChatProvider + max_context_size + capabilities）⭐ TODO
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, get_args

from kosong.chat_provider import ChatProvider

if TYPE_CHECKING:
    from my_cli.config import LLMModel, LLMProvider

# ============================================================
# 类型定义 ⭐ Stage 17
# ============================================================

type ProviderType = Literal["kimi", "openai_legacy", "openai_responses", "anthropic"]
"""支持的 LLM Provider 类型"""

type ModelCapability = Literal["image_in", "thinking"]
"""模型能力枚举"""

ALL_MODEL_CAPABILITIES: set[ModelCapability] = set(get_args(ModelCapability))


# ============================================================
# LLM 类 ⭐ Stage 17
# ============================================================


@dataclass(slots=True)
class LLM:
    """
    LLM - 统一的 LLM 接口 ⭐ Stage 17

    这个类封装了 ChatProvider 并添加了额外信息：
    - chat_provider: kosong 的 ChatProvider
    - max_context_size: 最大 Context 大小
    - capabilities: 模型能力集合

    对应源码：kimi-cli-fork/src/kimi_cli/llm.py:17-26
    """

    chat_provider: ChatProvider
    max_context_size: int
    capabilities: set[ModelCapability]

    @property
    def model_name(self) -> str:
        """获取模型名称"""
        return self.chat_provider.model_name


# ============================================================
# TODO: Stage 17+ 完整实现（参考官方）
# ============================================================
# 官方参考：kimi-cli-fork/src/kimi_cli/llm.py
#
# Stage 17（LLM 类）需要：
# 1. 实现 create_llm() 工厂函数
# 2. 实现 augment_provider_with_env_vars() 环境变量覆盖
# 3. 在 Runtime 中使用 LLM 替代 ChatProvider
# 4. 在 KimiSoul 中使用 self._runtime.llm
#
# create_llm() 伪代码：
# def create_llm(
#     provider: LLMProvider,
#     model: LLMModel,
#     *,
#     stream: bool = True,
#     session_id: str | None = None,
# ) -> LLM:
#     match provider.type:
#         case "kimi":
#             from kosong.chat_provider.kimi import Kimi
#             chat_provider = Kimi(...)
#         case "openai_legacy":
#             from kosong.contrib.chat_provider.openai_legacy import OpenAILegacy
#             chat_provider = OpenAILegacy(...)
#         ...
#
#     return LLM(
#         chat_provider=chat_provider,
#         max_context_size=model.max_context_size,
#         capabilities=model.capabilities,
#     )
#
# Stage 8-16 简化版：
# - 直接使用 ChatProvider
# - 固定 max_context_size = 32000
# - 不检查 capabilities
# ============================================================

# ============================================================
# create_llm() 工厂函数 ⭐ Stage 17 实现
# ============================================================


def create_llm(
    provider: "LLMProvider",
    model: "LLMModel",
    *,
    stream: bool = True,
    session_id: str | None = None,
) -> LLM:
    """
    创建 LLM 实例（工厂函数）⭐ Stage 17

    根据 Provider 类型创建对应的 ChatProvider，然后封装成 LLM。

    Args:
        provider: LLM Provider 配置
        model: LLM Model 配置
        stream: 是否使用流式输出
        session_id: 会话 ID（用于 prompt cache）

    Returns:
        LLM: 封装了 ChatProvider、max_context_size、capabilities 的 LLM 实例

    对应源码：kimi-cli-fork/src/kimi_cli/llm.py:73-141
    """
    # 根据 provider 类型创建 ChatProvider
    match provider.type:
        case "kimi":
            from kosong.chat_provider.kimi import Kimi

            from my_cli.constant import USER_AGENT

            chat_provider = Kimi(
                model=model.model,
                base_url=provider.base_url,
                api_key=provider.api_key.get_secret_value(),
                stream=stream,
                default_headers={
                    "User-Agent": USER_AGENT,
                    **(provider.custom_headers or {}),
                },
            )
            # 如果有 session_id，使用 prompt cache
            if session_id:
                chat_provider = chat_provider.with_generation_kwargs(prompt_cache_key=session_id)

        case "openai_legacy":
            from kosong.contrib.chat_provider.openai_legacy import OpenAILegacy

            chat_provider = OpenAILegacy(
                model=model.model,
                base_url=provider.base_url,
                api_key=provider.api_key.get_secret_value(),
                stream=stream,
            )

        case "openai_responses":
            from kosong.contrib.chat_provider.openai_responses import OpenAIResponses

            chat_provider = OpenAIResponses(
                model=model.model,
                base_url=provider.base_url,
                api_key=provider.api_key.get_secret_value(),
                stream=stream,
            )

        case "anthropic":
            from kosong.contrib.chat_provider.anthropic import Anthropic

            chat_provider = Anthropic(
                model=model.model,
                base_url=provider.base_url,
                api_key=provider.api_key.get_secret_value(),
                stream=stream,
                default_max_tokens=50000,
            )

        case "_chaos":
            # 测试用的混沌 ChatProvider（模拟错误）
            from kosong.chat_provider.chaos import ChaosChatProvider, ChaosConfig

            chat_provider = ChaosChatProvider(
                model=model.model,
                base_url=provider.base_url,
                api_key=provider.api_key.get_secret_value(),
                chaos_config=ChaosConfig(
                    error_probability=0.8,
                    error_types=[429, 500, 503],
                ),
            )

        case _:
            raise ValueError(f"Unsupported provider type: {provider.type}")

    # 封装成 LLM
    return LLM(
        chat_provider=chat_provider,
        max_context_size=model.max_context_size,
        capabilities=_derive_capabilities(provider, model),
    )


def _derive_capabilities(provider: "LLMProvider", model: "LLMModel") -> set[ModelCapability]:
    """
    推导模型能力 ⭐ Stage 17

    根据 Provider 类型和 Model 名称推导额外的能力。

    Args:
        provider: LLM Provider 配置
        model: LLM Model 配置

    Returns:
        set[ModelCapability]: 模型能力集合

    对应源码：kimi-cli-fork/src/kimi_cli/llm.py:144-151
    """
    capabilities = model.capabilities or set()

    # Kimi 特殊处理：自动添加 thinking 能力
    if provider.type != "kimi":
        return capabilities

    if model.model == "kimi-for-coding" or "thinking" in model.model:
        capabilities.add("thinking")

    return capabilities


def augment_provider_with_env_vars(provider: "LLMProvider", model: "LLMModel") -> dict[str, str]:
    """
    从环境变量覆盖 Provider/Model 设置 ⭐ Stage 17

    这允许用户通过环境变量临时覆盖配置文件中的设置。

    Args:
        provider: LLM Provider 配置（会被修改）
        model: LLM Model 配置（会被修改）

    Returns:
        dict[str, str]: 应用的环境变量映射

    对应源码：kimi-cli-fork/src/kimi_cli/llm.py:32-70
    """
    import os

    from typing import cast

    from pydantic import SecretStr

    applied: dict[str, str] = {}

    match provider.type:
        case "kimi":
            if base_url := os.getenv("KIMI_BASE_URL"):
                provider.base_url = base_url
                applied["KIMI_BASE_URL"] = base_url
            if api_key := os.getenv("KIMI_API_KEY"):
                provider.api_key = SecretStr(api_key)
                applied["KIMI_API_KEY"] = "******"
            if model_name := os.getenv("KIMI_MODEL_NAME"):
                model.model = model_name
                applied["KIMI_MODEL_NAME"] = model_name
            if max_context_size := os.getenv("KIMI_MODEL_MAX_CONTEXT_SIZE"):
                model.max_context_size = int(max_context_size)
                applied["KIMI_MODEL_MAX_CONTEXT_SIZE"] = max_context_size
            if capabilities := os.getenv("KIMI_MODEL_CAPABILITIES"):
                caps_lower = (cap.strip().lower() for cap in capabilities.split(",") if cap.strip())
                model.capabilities = set(
                    cast(ModelCapability, cap) for cap in caps_lower if cap in get_args(ModelCapability)
                )
                applied["KIMI_MODEL_CAPABILITIES"] = capabilities

        case "openai_legacy" | "openai_responses":
            if base_url := os.getenv("OPENAI_BASE_URL"):
                provider.base_url = base_url
                applied["OPENAI_BASE_URL"] = base_url
            if api_key := os.getenv("OPENAI_API_KEY"):
                provider.api_key = SecretStr(api_key)
                applied["OPENAI_API_KEY"] = "******"

        case _:
            pass

    return applied

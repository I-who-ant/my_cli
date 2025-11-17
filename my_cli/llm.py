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

"""
Setup - 交互式配置 MyCLI

学习目标：
1. 理解 /setup 元命令的实现
2. 理解交互式配置流程
3. 理解 config.json 的保存机制

对应源码：kimi-cli-fork/src/kimi_cli/ui/shell/setup.py

阶段演进：
- Stage 19.2：简化版 /setup 命令 ⭐
- Stage 20+：完整版（API 模型列表拉取、平台选择）
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, NamedTuple

import aiohttp
from prompt_toolkit import PromptSession
from prompt_toolkit.shortcuts.choice_input import ChoiceInput
from pydantic import SecretStr

from my_cli.config import LLMModel, LLMProvider, MoonshotSearchConfig, load_config, save_config
from my_cli.ui.shell.console import console
from my_cli.ui.shell.metacmd import meta_command
from my_cli.utils.aiohttp import new_client_session

if TYPE_CHECKING:
    from my_cli.ui.shell import ShellApp


# ============================================================
# 平台定义 ⭐ Stage 19.3
# ============================================================


class _Platform(NamedTuple):
    """API 平台配置"""

    id: str  # Provider ID
    name: str  # 显示名称
    base_url: str  # API Base URL
    search_url: str | None = None  # ⭐ 搜索服务 URL（可选）
    allowed_prefixes: list[str] | None = None  # ⭐ 允许的模型前缀


# 支持的平台列表
_PLATFORMS = [
    _Platform(
        id="kimi-for-coding",
        name="Kimi For Coding",
        base_url="https://api.kimi.com/coding/v1",
        search_url="https://api.kimi.com/coding/v1/search",  # ⭐ 有搜索服务
    ),
    _Platform(
        id="moonshot-cn",
        name="Moonshot AI 开放平台 (moonshot.cn)",
        base_url="https://api.moonshot.cn/v1",
        allowed_prefixes=["kimi-k2-"],  # ⭐ 只允许 kimi-k2-* 模型
    ),
    _Platform(
        id="moonshot-ai",
        name="Moonshot AI Open Platform (moonshot.ai)",
        base_url="https://api.moonshot.ai/v1",
        allowed_prefixes=["kimi-k2-"],  # ⭐ 只允许 kimi-k2-* 模型
    ),
]


class _SetupResult(NamedTuple):
    """配置结果 ⭐ 对齐官方"""

    platform: _Platform
    api_key: SecretStr
    model_id: str
    max_context_size: int


@meta_command
async def setup(app: "ShellApp", args: list[str]):
    """
    交互式配置 MyCLI ⭐ 完全对齐官方实现

    官方流程：
    1. 选择平台（Kimi For Coding / Moonshot CN / Moonshot AI）
    2. 输入 API Key
    3. 自动拉取可用模型列表（API 调用）⭐ 关键改进
    4. 选择模型（从列表中）⭐ 关键改进
    5. 自动读取模型的 context_length ⭐ 关键改进
    6. 保存配置
    7. Reload

    对应源码：kimi-cli-fork/src/kimi_cli/ui/shell/setup.py:50-84
    """
    console.print("\n[bold cyan]MyCLI 配置向导[/bold cyan]\n")

    result = await _setup()
    if not result:
        # 用户取消或错误
        return

    # 加载现有配置
    config = load_config()

    # 添加 Provider
    config.providers[result.platform.id] = LLMProvider(
        type="kimi",
        base_url=result.platform.base_url,
        api_key=result.api_key,
    )

    # 添加 Model
    config.models[result.model_id] = LLMModel(
        provider=result.platform.id,
        model=result.model_id,
        max_context_size=result.max_context_size,
    )

    # 设置为默认模型
    config.default_model = result.model_id

    # ⭐ 如果平台有 search_url，自动配置 moonshot_search
    if result.platform.search_url:
        config.services.moonshot_search = MoonshotSearchConfig(
            base_url=result.platform.search_url,
            api_key=result.api_key,  # 复用同一个 API Key
        )

    # 保存配置
    save_config(config)

    console.print("\n[green]✓[/green] MyCLI 配置完成！正在重新加载...\n")
    await asyncio.sleep(1)
    console.clear()

    # 触发 Reload（重新加载配置）
    from my_cli.cli import Reload

    raise Reload


async def _setup() -> _SetupResult | None:
    """
    交互式配置流程 ⭐ 完全对齐官方实现

    流程：
    1. 选择平台
    2. 输入 API Key
    3. 调用 API 拉取模型列表 ⭐ 关键改进
    4. 从列表中选择模型 ⭐ 关键改进
    5. 返回配置结果（包含 context_length）⭐ 关键改进

    Returns:
        _SetupResult | None: 配置结果，None 表示用户取消或失败

    对应源码：kimi-cli-fork/src/kimi_cli/ui/shell/setup.py:94-159
    """
    # 1. 选择平台
    platform_name = await _prompt_choice(
        header="Select the API platform",
        choices=[platform.name for platform in _PLATFORMS],
    )
    if not platform_name:
        console.print("[red]未选择平台[/red]")
        return None

    platform = next(p for p in _PLATFORMS if p.name == platform_name)

    # 2. 输入 API Key
    api_key = await _prompt_text("Enter your API key", is_password=True)
    if not api_key:
        return None

    # 3. 调用 API 拉取模型列表 ⭐ 关键改进
    models_url = f"{platform.base_url}/models"
    try:
        async with (
            new_client_session() as session,
            session.get(
                models_url,
                headers={
                    "Authorization": f"Bearer {api_key}",
                },
                raise_for_status=True,
            ) as response,
        ):
            resp_json = await response.json()
    except aiohttp.ClientError as e:
        console.print(f"[red]获取模型列表失败: {e}[/red]")
        return None

    model_dict = {model["id"]: model for model in resp_json["data"]}

    # 4. 过滤模型（根据 allowed_prefixes）
    model_ids: list[str] = [model["id"] for model in resp_json["data"]]
    if platform.allowed_prefixes is not None:
        model_ids = [
            model_id
            for model_id in model_ids
            if model_id.startswith(tuple(platform.allowed_prefixes))
        ]

    if not model_ids:
        console.print("[red]该平台没有可用模型[/red]")
        return None

    # 5. 选择模型 ⭐ 关键改进
    model_id = await _prompt_choice(
        header="Select the model",
        choices=model_ids,
    )
    if not model_id:
        console.print("[red]未选择模型[/red]")
        return None

    model = model_dict[model_id]

    # 6. 返回配置结果（自动读取 context_length）⭐ 关键改进
    return _SetupResult(
        platform=platform,
        api_key=SecretStr(api_key),
        model_id=model_id,
        max_context_size=model["context_length"],  # ⭐ 从 API 响应中读取
    )


async def _prompt_choice(*, header: str, choices: list[str]) -> str | None:
    """
    选择菜单 ⭐ 对齐官方实现

    Args:
        header: 提示标题
        choices: 选项列表

    Returns:
        str | None: 选中的选项，None 表示用户取消

    对应源码：kimi-cli-fork/src/kimi_cli/ui/shell/setup.py:162-173
    """
    if not choices:
        return None

    try:
        return await ChoiceInput(
            message=header,
            options=[(choice, choice) for choice in choices],
            default=choices[0],
        ).prompt_async()
    except (EOFError, KeyboardInterrupt):
        return None


async def _prompt_text(prompt: str, *, is_password: bool = False) -> str | None:
    """
    文本输入 ⭐ 对齐官方实现

    Args:
        prompt: 提示文本
        is_password: 是否为密码输入（隐藏输入内容）

    Returns:
        str | None: 用户输入，None 表示用户取消

    对应源码：kimi-cli-fork/src/kimi_cli/ui/shell/setup.py:176-186
    """
    session = PromptSession()
    try:
        return str(
            await session.prompt_async(
                f" {prompt}: ",
                is_password=is_password,
            )
        ).strip()
    except (EOFError, KeyboardInterrupt):
        return None


@meta_command
def reload(app: "ShellApp", args: list[str]):
    """
    重新加载配置 ⭐ Stage 19.2

    触发 Reload 异常，CLI 会捕获并重新初始化。

    对应源码：kimi-cli-fork/src/kimi_cli/ui/shell/setup.py:189-194
    """
    from my_cli.cli import Reload

    raise Reload

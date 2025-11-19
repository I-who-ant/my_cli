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

from prompt_toolkit import PromptSession
from prompt_toolkit.shortcuts.choice_input import ChoiceInput
from pydantic import SecretStr

from my_cli.config import LLMModel, LLMProvider, load_config, save_config
from my_cli.ui.shell.console import console
from my_cli.ui.shell.metacmd import meta_command

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


# 支持的平台列表
_PLATFORMS = [
    _Platform(
        id="kimi-for-coding",
        name="Kimi For Coding",
        base_url="https://api.kimi.com/coding/v1",
    ),
    _Platform(
        id="moonshot-cn",
        name="Moonshot AI 开放平台 (moonshot.cn)",
        base_url="https://api.moonshot.cn/v1",
    ),
    _Platform(
        id="moonshot-ai",
        name="Moonshot AI Open Platform (moonshot.ai)",
        base_url="https://api.moonshot.ai/v1",
    ),
]


class _SetupResult(NamedTuple):
    """配置结果"""

    api_key: SecretStr
    model_name: str
    base_url: str
    provider_name: str  # ⭐ 添加provider名称
    max_context_size: int  # ⭐ 添加max_context_size


@meta_command
async def setup(app: "ShellApp", args: list[str]):
    """
    交互式配置 MyCLI ⭐ Stage 19.2 简化版

    流程：
    1. 输入 API Key
    2. 输入模型名称
    3. 输入 Base URL
    4. 保存到 ~/.mc/config.json
    5. Reload 重新加载

    官方完整流程：
    1. 选择平台（Kimi For Coding / Moonshot CN / Moonshot AI）
    2. 输入 API Key
    3. 自动拉取可用模型列表（API 调用）
    4. 选择模型
    5. 保存配置
    6. Reload

    简化版（Stage 19.2）：
    - 跳过平台选择
    - 跳过模型列表拉取
    - 手动输入所有配置

    对应源码：kimi-cli-fork/src/kimi_cli/ui/shell/setup.py:50-84
    """
    console.print("\n[bold cyan]MyCLI 配置向导[/bold cyan]\n")

    result = await _setup()
    if not result:
        # 用户取消或错误
        console.print("[yellow]配置已取消[/yellow]")
        return

    # 加载现有配置
    config = load_config()

    # 添加 Provider（使用用户提供的名称）⭐
    config.providers[result.provider_name] = LLMProvider(
        type="kimi",
        base_url=result.base_url,
        api_key=result.api_key,
    )

    # 添加 Model（使用用户提供的max_context_size）⭐
    config.models[result.model_name] = LLMModel(
        provider=result.provider_name,
        model=result.model_name,
        max_context_size=result.max_context_size,
    )

    # 设置为默认模型
    config.default_model = result.model_name

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
    交互式配置流程 ⭐ Stage 19.3

    流程更新：
    1. 选择平台（使用 button_dialog）
    2. 输入 API Key
    3. 输入模型名称
    4. 输入 max_context_size

    Returns:
        _SetupResult | None: 配置结果，None 表示用户取消

    对应源码：kimi-cli-fork/src/kimi_cli/ui/shell/setup.py:94-159
    """
    # 1. 选择平台 ⭐ Stage 19.3
    platform = await _prompt_platform()
    if not platform:
        return None

    console.print(f"\n[green]✓[/green] 已选择: {platform.name}\n")

    # 2. 输入 API Key
    api_key = await _prompt_text("API Key", is_password=True)
    if not api_key:
        return None

    # 3. 输入模型名称
    model_name = await _prompt_text(
        "模型名称",
        default="moonshot-v1-8k",
    )
    if not model_name:
        return None

    # 4. 输入 max_context_size
    max_context_size_str = await _prompt_text(
        "Max Context Size",
        default="128000",
    )
    if not max_context_size_str:
        return None

    try:
        max_context_size = int(max_context_size_str)
    except ValueError:
        console.print("[red]错误：Max Context Size 必须是数字[/red]")
        return None

    return _SetupResult(
        api_key=SecretStr(api_key),
        model_name=model_name,
        base_url=platform.base_url,  # ⭐ 使用平台的 base_url
        provider_name=platform.id,  # ⭐ 使用平台的 id
        max_context_size=max_context_size,
    )


async def _prompt_platform() -> _Platform | None:
    """
    平台选择对话框 ⭐ Stage 19.3

    使用 ChoiceInput 实现官方的选择菜单：
    Select the API platform
    > 1. Kimi For Coding
      2. Moonshot AI 开放平台 (moonshot.cn)
      3. Moonshot AI Open Platform (moonshot.ai)

    Returns:
        _Platform | None: 选择的平台，None 表示用户取消

    对应源码：kimi-cli-fork/src/kimi_cli/ui/shell/setup.py:162-173
    """
    try:
        # ✅ 官方方式：choices 是纯字符串列表
        platform_names = [platform.name for platform in _PLATFORMS]

        # ✅ ChoiceInput 的 options 是 (name, name)，显示和返回值相同
        selected_name = await ChoiceInput(
            message="Select the API platform",
            options=[(name, name) for name in platform_names],
            default=platform_names[0],
        ).prompt_async()

        # ✅ 根据名称查找平台对象
        for platform in _PLATFORMS:
            if platform.name == selected_name:
                return platform

        return None

    except (EOFError, KeyboardInterrupt):
        return None


async def _prompt_text(
    prompt: str,
    *,
    is_password: bool = False,
    default: str | None = None,
) -> str | None:
    """
    交互式文本输入 ⭐ Stage 19.2

    Args:
        prompt: 提示文本
        is_password: 是否为密码输入（隐藏输入内容）
        default: 默认值

    Returns:
        str | None: 用户输入，None 表示用户取消

    对应源码：kimi-cli-fork/src/kimi_cli/ui/shell/setup.py:176-186
    """
    session = PromptSession()

    # 构建提示文本
    prompt_text = f" {prompt}"
    if default:
        prompt_text += f" (默认: {default})"
    prompt_text += ": "

    try:
        result = str(
            await session.prompt_async(
                prompt_text,
                is_password=is_password,
            )
        ).strip()

        # 如果用户没有输入，使用默认值
        if not result and default:
            return default

        return result if result else None

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

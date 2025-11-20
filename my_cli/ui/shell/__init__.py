"""
Stage 11：Shell UI 模块化重构

学习目标：
1. 理解官方的模块化架构设计
2. 单一职责原则（SRP）在实践中的应用
3. 模块间的依赖和协作关系
4. 如何设计可扩展的命令系统

对应源码：kimi-cli-fork/src/kimi_cli/ui/shell/__init__.py

模块架构（Stage 11）：
- ✅ console.py    - Console 单例 + 主题配置
- ✅ metacmd.py    - 斜杠命令系统（装饰器注册）
- ✅ prompt.py     - CustomPromptSession（输入处理）
- ✅ visualize.py  - UI Loop 渲染逻辑
- ✅ __init__.py   - ShellApp 主入口（协调器）

核心特性（保留 Stage 9/10 功能）：
- 多轮对话（复用同一个 Soul 实例）
- Context 自动保持
- 优雅退出处理
- prompt_toolkit 命令历史
- rich 彩色输出
- 斜杠命令支持

使用示例：
    python cli.py --ui shell
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from kosong.chat_provider import ChatProviderError
from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from my_cli.soul import LLMNotSet, RunCancelled, run_soul
from my_cli.ui.shell.console import console
from my_cli.ui.shell.metacmd import get_meta_command
from my_cli.ui.shell.prompt import CustomPromptSession, PromptMode, UserInput
from my_cli.ui.shell.visualize import visualize

__all__ = ["ShellApp", "WelcomeInfoItem"]


class ShellApp:
    """
    Shell App - 模块化的交互式 UI（Stage 11 重构版）

    这是官方架构的简化版实现：
    - 使用模块化设计（console、metacmd、prompt、visualize）
    - 符合单一职责原则（SRP）
    - 易于扩展和维护

    对应源码：kimi-cli-fork/src/kimi_cli/ui/shell/__init__.py:29-92

    架构演进：
    - Stage 9：Shell 交互模式（基础版）✅
    - Stage 10：UI 美化和增强（enhanced.py.md.backup）✅
    - Stage 11：模块化重构（按官方架构分层）✅
    """

    def __init__(self, soul, welcome_info: list[WelcomeInfoItem] | None = None):
        """
        初始化 ShellApp ⭐ Stage 19.3

        Args:
            soul: Soul 实例（由 MyCLI.create() 创建）
            welcome_info: 欢迎信息列表（WelcomeInfoItem 对象）

        对应源码：kimi-cli-fork/src/kimi_cli/ui/shell/__init__.py:30-33
        """
        self.soul = soul
        self._welcome_info = list(welcome_info or [])  # ⭐ Stage 19.3: 使用官方命名

    async def run(self, command: str | None = None) -> bool:
        """
        运行 Shell App ⭐ Stage 18 修复

        支持两种模式：
        1. 单命令模式（command 不为 None）：执行一次后退出
        2. 交互模式（command 为 None）：进入输入循环

        Args:
            command: 用户命令（None 则进入交互模式）

        Returns:
            是否成功执行

        对应源码：kimi-cli-fork/src/kimi_cli/ui/shell/__init__.py:36-93
        """
        # soul 已经在 __init__ 中传入，不需要再创建！
        # (soul 由 MyCLI.create() 创建并传入)

        # ============================================================
        # 模式 1：单命令模式
        # ============================================================
        if command is not None:
            return await self._run_single_command(command)

        # ============================================================
        # 模式 2：交互循环模式 ⭐ Stage 11 模块化版
        # ============================================================

        # 2. 显示欢迎信息 ⭐ Stage 19.3: 使用 WelcomeInfoItem
        _print_welcome_info(self.soul.name or "MyCLI Assistant", self._welcome_info)

        # 3. 创建 CustomPromptSession（模块化）⭐ Stage 19.1: 对齐官方签名
        with CustomPromptSession(
            status_provider=lambda: self.soul.status,  # ⭐ Stage 16: 动态状态回调
            model_capabilities=self.soul.model_capabilities or set(),  # ⭐ Stage 16: 模型能力
            initial_thinking=self.soul.thinking,  # ⭐ Stage 19.1: 初始 thinking 模式
        ) as prompt_session:
            # 4. 进入输入循环
            while True:
                try:
                    # 获取用户输入（使用模块化的 prompt.py）
                    user_input: UserInput = await prompt_session.prompt()

                    # 跳过空输入
                    if not user_input.command:
                        continue

                    # 处理退出命令
                    if user_input.command.lower() in ["exit", "quit", "/exit", "/quit"]:
                        console.print("[yellow]👋 再见！[/yellow]")
                        break

                    # ⭐ Stage 19.4: Shell 模式处理
                    if user_input.mode == PromptMode.SHELL:
                        await self._run_shell_command(user_input.command)
                        continue

                    # Stage 11：斜杠命令处理 ⭐
                    if user_input.command.startswith("/"):
                        await self._run_meta_command(user_input.command[1:])
                        continue

                    # 普通命令：发送到 LLM
                    await self._run_soul_command(user_input.content)

                except KeyboardInterrupt:
                    # Ctrl+C：取消当前请求，继续循环
                    console.print("\n\n[grey50]⚠️  提示: 输入 'exit' 或按 Ctrl+D 退出[/grey50]\n")
                    continue

                except EOFError:
                    # Ctrl+D：优雅退出
                    console.print("\n\n[yellow]👋 再见！[/yellow]\n")
                    break

                except Exception as e:
                    # 其他错误：打印错误但继续循环
                    console.print(f"\n[red]❌ 未知错误: {e}[/red]\n")
                    # TODO: Stage 19+ 添加 verbose 模式支持
                    import traceback
                    traceback.print_exc()
                    continue

        return True

    async def _run_single_command(self, command: str) -> bool:
        """单命令模式：执行一次命令后退出 ⭐ Stage 18 修复"""
        console.print("\n[bold cyan]💬 AI 回复:[/bold cyan]\n")
        try:
            await self._run_soul_command(command)
            console.print("\n")
            return True

        except Exception as e:
            console.print(f"\n[red]❌ 错误: {e}[/red]\n")
            return False

    async def _run_shell_command(self, command: str) -> None:
        """
        运行 Shell 命令（直接执行系统命令）⭐ Stage 19.4

        在 Shell 模式下（Ctrl+X 切换），用户输入会直接作为系统命令执行。

        Args:
            command: 要执行的 Shell 命令

        对应源码：kimi-cli-fork/src/kimi_cli/ui/shell/__init__.py:95-130
        """
        import shlex

        if not command.strip():
            return

        # 检查 cd 命令（目录切换不会跨命令保持）
        stripped_cmd = command.strip()
        try:
            split_cmd = shlex.split(stripped_cmd)
            if len(split_cmd) >= 1 and split_cmd[0] == "cd":
                console.print(
                    "[yellow]⚠️  注意：目录切换不会跨命令保持[/yellow]"
                )
                return
        except ValueError:
            pass  # shlex 解析失败，继续执行

        # 执行命令
        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=None,  # 直接输出到终端
                stderr=None,
            )
            await proc.wait()
        except Exception as e:
            console.print(f"[red]❌ Shell 命令执行失败: {e}[/red]")

    async def _run_meta_command(self, command_name: str) -> None:
        """
        运行斜杠命令 ⭐ Stage 11 模块化版

        使用 metacmd.py 的命令注册表查询和执行命令

        Args:
            command_name: 命令名称（不包含 / 前缀）
        """
        # 解析命令名和参数
        parts = command_name.strip().split()
        cmd_name = parts[0] if parts else ""
        cmd_args = parts[1:] if len(parts) > 1 else []

        # 从注册表查询命令
        cmd = get_meta_command(cmd_name)

        if cmd is None:
            console.print(f"[red]❌ 未知命令: /{cmd_name}[/red]")
            console.print("[grey50]输入 /help 查看可用命令[/grey50]")
            return

        # 执行命令
        try:
            result = cmd.func(self, cmd_args)
            # 支持同步和异步命令
            if asyncio.iscoroutine(result):
                await result
        except Exception as e:
            console.print(f"[red]❌ 命令执行失败: {e}[/red]")
            # TODO: Stage 19+ 添加 verbose 模式支持
            import traceback
            traceback.print_exc()

    async def _run_soul_command(self, user_input: str) -> None:
        """
        运行 Soul 命令（核心执行逻辑）

        流程：
        1. 创建取消事件（用于 Ctrl+C）
        2. 调用 run_soul() 连接 Soul 和 UI Loop
        3. UI Loop（visualize.py）接收 Wire 消息并渲染

        Args:
            user_input: 用户输入
        """
        cancel_event = asyncio.Event()

        try:
            await run_soul(
                soul=self.soul,
                user_input=user_input,
                ui_loop_fn=visualize,  # 使用模块化的 visualize.py ⭐
                cancel_event=cancel_event,
            )

        except LLMNotSet:
            console.print("\n[red]❌ LLM 未设置（需要配置 API Key）[/red]\n")
        except ChatProviderError as e:
            console.print(f"\n[red]❌ LLM API 错误: {e}[/red]\n")
        except RunCancelled:
            # Ctrl+C 取消运行（不打印错误，已在外层处理）
            pass
        except Exception as e:
            console.print(f"\n[red]❌ 未知错误: {e}[/red]\n")
            # TODO: Stage 19+ 添加 verbose 模式支持
            import traceback
            traceback.print_exc()


# ============================================================
# WelcomeInfoItem - 欢迎信息数据类 ⭐ Stage 19.3
# ============================================================


_MY_CLI_CYAN = "cyan"
# ⭐ Arch Linux 官方完整 Logo
_LOGO = f"""\
[{_MY_CLI_CYAN}]\
                   ▄
                  ▟█▙
                 ▟███▙
                ▟█████▙
               ▟███████▙
              ▂▔▀▜██████▙
             ▟██▅▂▝▜█████▙
            ▟█████████████▙
           ▟███████████████▙
          ▟█████████████████▙
         ▟███████████████████▙
        ▟█████████▛▀▀▜████████▙
       ▟████████▛      ▜███████▙
      ▟█████████        ████████▙
     ▟██████████        █████▆▅▄▃▂
    ▟██████████▛        ▜█████████▙
   ▟██████▀▀▀              ▀▀██████▙
  ▟███▀▘                       ▝▀███▙
 ▟▛▀                               ▀▜▙\
[/{_MY_CLI_CYAN}]\
"""


@dataclass(slots=True)
class WelcomeInfoItem:
    """
    欢迎信息条目 ⭐ Stage 19.3

    用于在启动时显示配置信息，如模型、目录、环境变量覆盖等。

    对应源码：kimi-cli-fork/src/kimi_cli/ui/shell/__init__.py:282-291
    """

    class Level(Enum):
        """信息级别（影响颜色）"""

        INFO = "grey50"  # 普通信息
        WARN = "yellow"  # 警告（如环境变量覆盖）
        ERROR = "red"  # 错误

    name: str  # 信息名称（如 "Model"）
    value: str  # 信息值（如 "kimi-k2-thinking-turbo"）
    level: Level = Level.INFO  # 信息级别


def _print_welcome_info(name: str, info_items: list[WelcomeInfoItem]) -> None:
    """
    打印欢迎信息 ⭐ Stage 19.3 官方版

    使用 rich Table + Panel 显示：
    - Logo + 标题
    - 帮助提示
    - 信息列表（带颜色）

    Args:
        name: 应用名称（如 "MyCLI Assistant"）
        info_items: 信息列表

    对应源码：kimi-cli-fork/src/kimi_cli/ui/shell/__init__.py:294-330
    """
    head = Text.from_markup(f"[bold]Welcome to {name}![/bold]")
    help_text = Text.from_markup("[grey50]Send /help for help information.[/grey50]")

    # 使用 Table 实现 Logo + 标题的并排布局
    logo = Text.from_markup(_LOGO)
    table = Table(show_header=False, show_edge=False, box=None, padding=(0, 1), expand=False)
    table.add_column(justify="left")
    table.add_column(justify="left")
    table.add_row(logo, Group(head, help_text))

    rows: list[RenderableType] = [table]

    # 添加空行
    rows.append(Text(""))

    # 添加信息条目（带颜色）
    for item in info_items:
        rows.append(Text(f"{item.name}: {item.value}", style=item.level.value))

    # 使用 Panel 显示
    console.print(
        Panel(
            Group(*rows),
            border_style=_MY_CLI_CYAN,
            expand=False,
            padding=(1, 2),
        )
    )


# ============================================================
# 旧版 _print_welcome_info（已废弃）
# ============================================================


def _print_welcome_info_old(name: str, model: str) -> None:
    """
    打印欢迎信息 ⭐ Stage 11 rich 美化版

    使用 rich Panel 边框和颜色
    """
    welcome_text = f"""[bold cyan]欢迎使用 {name}![/bold cyan]

[grey50]模型:[/grey50] [yellow]{model}[/yellow]
[grey50]输入 [/grey50][cyan]/help[/cyan][grey50] 查看可用命令[/grey50]
[grey50]输入 [/grey50][cyan]exit[/cyan][grey50] 或按 [/grey50][cyan]Ctrl+D[/cyan][grey50] 退出[/grey50]
[grey50]按 [/grey50][cyan]Ctrl+C[/cyan][grey50] 可以取消当前请求[/grey50]
"""

    console.print(
        Panel(
            welcome_text,
            border_style="cyan",
            padding=(1, 2),
            expand=False,
        )
    )
    console.print()  # 空行


# ============================================================
# TODO: Stage 12+ 更多功能（参考官方）
# ============================================================
# 官方参考：kimi-cli-fork/src/kimi_cli/ui/shell/
#
# Stage 12+ 需要添加的模块和功能：
#
# 1. keyboard.py（键盘事件监听）：
#    - 跨平台键盘监听（Unix/Windows）
#    - 异步事件流
#    - 热键支持
#
# 2. debug.py（调试功能）：
#    - 调试模式切换
#    - Wire 消息日志
#    - 性能分析
#
# 3. replay.py（历史回放）：
#    - 重放最近的对话
#    - 会话恢复
#
# 4. setup.py（配置向导）：
#    - 交互式配置 LLM
#    - API Key 管理
#    - 模型选择
#
# 5. update.py（自动更新）：
#    - 检查更新
#    - 版本提示
#    - 后台任务
#
# 6. prompt.py 增强：
#    - FileMentionCompleter（@文件路径补全）
#    - MetaCommandCompleter（/命令补全）
#    - 多模式切换（Normal/Shell/Thinking）
#    - 状态栏显示
#    - 剪贴板集成
#
# 7. metacmd.py 增强：
#    - @meta_command 装饰器（简化注册）
#    - 命令参数解析
#    - Kimi Soul 专属命令
#    - 帮助系统自动生成
# ============================================================

# ============================================================
# Stage 19.2：导入 setup 模块（注册 /setup 元命令）⭐
# ============================================================
from my_cli.ui.shell import setup  # noqa: F401


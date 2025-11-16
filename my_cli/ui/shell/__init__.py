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
from pathlib import Path

from kosong.chat_provider import ChatProviderError
from rich.panel import Panel

from my_cli.soul import LLMNotSet, RunCancelled, create_soul, run_soul
from my_cli.ui.shell.console import console
from my_cli.ui.shell.metacmd import get_meta_command
from my_cli.ui.shell.prompt import CustomPromptSession, UserInput
from my_cli.ui.shell.visualize import visualize

__all__ = ["ShellApp"]


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

    def __init__(self, verbose: bool = False, work_dir: Path | None = None):
        """
        初始化 ShellApp

        Args:
            verbose: 是否显示详细日志
            work_dir: 工作目录（默认当前目录）
        """
        self.verbose = verbose
        self.work_dir = work_dir or Path.cwd()
        self.soul = None  # Soul 实例（在 run() 中创建）

    async def run(self, command: str | None = None) -> bool:
        """
        运行 Shell App

        支持两种模式：
        1. 单命令模式（command 不为 None）：执行一次后退出
        2. 交互模式（command 为 None）：进入输入循环

        Args:
            command: 用户命令（None 则进入交互模式）

        Returns:
            是否成功执行
        """
        # 1. 创建 Soul（只创建一次，复用于所有对话）⭐
        try:
            self.soul = create_soul(work_dir=self.work_dir)
        except FileNotFoundError as e:
            console.print(f"\n[red]❌ 配置文件错误: {e}[/red]\n")
            console.print("请先运行 'mycli init' 创建配置文件")
            return False
        except ValueError as e:
            console.print(f"\n[red]❌ 配置错误: {e}[/red]\n")
            return False

        if self.verbose:
            console.print(f"\n[cyan]🤖 使用模型: {self.soul.model_name}[/cyan]\n")

        # ============================================================
        # 模式 1：单命令模式
        # ============================================================
        if command is not None:
            return await self._run_single_command(command)

        # ============================================================
        # 模式 2：交互循环模式 ⭐ Stage 11 模块化版
        # ============================================================

        # 2. 显示欢迎信息
        _print_welcome_info(self.soul.name, self.soul.model_name)

        # 3. 创建 CustomPromptSession（模块化）
        with CustomPromptSession(work_dir=self.work_dir) as prompt_session:
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
                    if self.verbose:
                        import traceback

                        traceback.print_exc()
                    continue

        return True

    async def _run_single_command(self, command: str) -> bool:
        """单命令模式：执行一次命令后退出"""
        if self.verbose:
            console.print(f"[grey50]📝 用户输入: {command}[/grey50]\n")

        console.print("\n[bold cyan]💬 AI 回复:[/bold cyan]\n")
        try:
            await self._run_soul_command(command)
            console.print("\n")

            if self.verbose:
                console.print(f"\n[green]✅ 对话轮次: {self.soul.message_count}[/green]")

            return True

        except Exception as e:
            console.print(f"\n[red]❌ 错误: {e}[/red]\n")
            return False

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
            if self.verbose:
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
            if self.verbose:
                import traceback

                traceback.print_exc()


def _print_welcome_info(name: str, model: str) -> None:
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

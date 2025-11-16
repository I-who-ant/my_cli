"""
Stage 9：Shell 交互模式 - 多轮对话 CLI

学习目标：
1. 理解交互式 UI 的实现
2. 理解如何复用 Soul 实例实现多轮对话
3. 理解输入循环和退出信号处理
4. 理解 KeyboardInterrupt 和 EOFError 的区别

对应源码：kimi-cli-fork/src/kimi_cli/ui/shell/__init__.py

核心特性：
- 多轮对话（复用同一个 Soul 实例）
- Context 自动保持（无需手动管理）
- 优雅退出（Ctrl+C 取消当前请求，Ctrl+D/exit 退出）
- 实时流式输出（复用 Print UI 的 _ui_loop）

使用示例：
    python cli.py shell
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from kosong.chat_provider import ChatProviderError
from kosong.message import ContentPart, TextPart, ToolCall
from kosong.tooling import ToolResult, ToolError, ToolOk

from my_cli.soul import LLMNotSet, RunCancelled, create_soul, run_soul
from my_cli.wire import WireUISide
from my_cli.wire.message import StepBegin, StepInterrupted

__all__ = ["ShellUI"]


class ShellUI:
    """
    Shell UI - 交互式多轮对话模式

    这是一个交互式 UI 实现，支持多轮对话：
    - 进入输入循环（while True）
    - 复用同一个 Soul 实例（Context 自动保持）
    - 处理退出信号（Ctrl+C, Ctrl+D, exit 命令）
    - 复用 Print UI 的流式输出逻辑

    对应源码：kimi-cli-fork/src/kimi_cli/ui/shell/__init__.py:23-230

    阶段演进：
    - Stage 9：Shell 交互模式 ✅
      * 多轮对话支持
      * Context 自动保持
      * 优雅退出处理
    """

    def __init__(self, verbose: bool = False, work_dir: Path | None = None):
        """
        初始化 Shell UI

        Args:
            verbose: 是否显示详细日志
            work_dir: 工作目录（默认当前目录）
        """
        self.verbose = verbose
        self.work_dir = work_dir or Path.cwd()

    async def run(self, command: str | None = None) -> None:
        """
        运行 Shell UI（支持两种模式）

        模式 1：单命令模式（command 不为 None）
            - 执行一次命令后退出
            - 与 Print UI 行为相同

        模式 2：交互循环模式（command 为 None）⭐ Stage 9 核心
            - 进入 while True 输入循环
            - 复用同一个 Soul 实例（Context 保持）
            - 支持多轮对话
            - 优雅处理退出信号

        Args:
            command: 用户输入（None 则进入交互模式）
        """
        # 1. 创建 Soul（只创建一次，复用于所有对话）⭐
        try:
            soul = create_soul(work_dir=self.work_dir)
        except FileNotFoundError as e:
            print(f"\n❌ 配置文件错误: {e}\n")
            print("请先运行 'mycli init' 创建配置文件")
            return
        except ValueError as e:
            print(f"\n❌ 配置错误: {e}\n")
            return

        if self.verbose:
            print(f"\n🤖 使用模型: {soul.model_name}\n")

        # ============================================================
        # 模式 1：单命令模式
        # ============================================================
        if command is not None:
            await self._run_single_command(soul, command)
            return

        # ============================================================
        # 模式 2：交互循环模式 ⭐ Stage 9 核心
        # ============================================================
        self._print_welcome(soul.name, soul.model_name)

        # 进入输入循环
        while True:
            try:
                # 2. 获取用户输入
                user_input = await self._get_user_input()

                # 3. 跳过空输入（提前检查）⭐
                if not user_input or not user_input.strip():
                    continue

                # 4. 处理退出命令
                if user_input.strip().lower() in ["exit", "quit", "q"]:
                    print("\n👋 再见！\n")
                    break

                # 5. 运行 Soul（复用同一个实例）⭐
                await self._run_soul_command(soul, user_input)

            except KeyboardInterrupt:
                # Ctrl+C：取消当前请求，继续循环 ⭐
                print("\n\n⚠️  提示: 输入 'exit' 或按 Ctrl+D 退出\n")
                continue

            except EOFError:
                # Ctrl+D：优雅退出 ⭐
                print("\n\n👋 再见！\n")
                break

            except UnicodeDecodeError as e:
                # 编码错误：友好提示
                print(f"\n❌ 编码错误: {e}\n")
                print("提示：请确保终端使用 UTF-8 编码")
                print("检查命令：echo $LANG（应该包含 UTF-8）\n")
                if self.verbose:
                    import traceback
                    traceback.print_exc()
                continue

            except Exception as e:
                # 其他错误：打印错误但继续循环
                print(f"\n❌ 未知错误: {e}\n")
                if self.verbose:
                    import traceback
                    traceback.print_exc()
                continue

    async def _get_user_input(self) -> str:
        """
        获取用户输入（异步包装）

        Stage 9 简化版：使用 asyncio.to_thread 包装同步的 input()
        官方使用 prompt_toolkit 的 PromptSession（支持历史记录、自动补全等）

        TODO: Stage 10+ 优化：使用 prompt_toolkit
        - 官方实现：kimi-cli-fork/src/kimi_cli/ui/shell/__init__.py:CustomPromptSession
        - 优化点：
          * 命令历史记录（上下箭头）
          * 自动补全（Tab 键）
          * 多行输入支持
          * 自定义提示符样式

        Returns:
            用户输入的字符串
        """
        # 使用 asyncio.to_thread 让同步的 input() 不阻塞事件循环
        return await asyncio.to_thread(input, "You: ")

    async def _run_single_command(self, soul, command: str) -> None:
        """
        单命令模式：执行一次命令后退出

        这个模式与 Print UI 行为相同

        Args:
            soul: Soul 实例
            command: 用户命令
        """
        if self.verbose:
            print(f"📝 用户输入: {command}\n")

        print("\n💬 AI 回复:\n")
        try:
            await self._run_soul_command(soul, command)
            print("\n")

            if self.verbose:
                print(f"\n✅ 对话轮次: {soul.message_count}")

        except Exception as e:
            print(f"\n❌ 错误: {e}\n")
            raise

    async def _run_soul_command(self, soul, user_input: str) -> None:
        """
        运行 Soul 命令（核心执行逻辑）

        流程：
        1. 创建取消事件（用于 Ctrl+C）
        2. 调用 run_soul() 连接 Soul 和 UI Loop
        3. UI Loop 接收 Wire 消息并实时显示
        4. 处理各种异常（LLMNotSet, ChatProviderError 等）

        Args:
            soul: Soul 实例
            user_input: 用户输入
        """
        # 1. 创建取消事件
        cancel_event = asyncio.Event()

        # 2. 调用 run_soul()
        try:
            await run_soul(
                soul=soul,
                user_input=user_input,
                ui_loop_fn=self._ui_loop,  # 复用 _ui_loop
                cancel_event=cancel_event,
            )

        except LLMNotSet:
            print("\n❌ LLM 未设置（需要配置 API Key）\n")
        except ChatProviderError as e:
            print(f"\n❌ LLM API 错误: {e}\n")
        except RunCancelled:
            # Ctrl+C 取消运行（不打印错误，已在外层处理）
            pass
        except Exception as e:
            print(f"\n❌ 未知错误: {e}\n")
            raise

    async def _ui_loop(self, wire_ui: WireUISide) -> None:
        """
        UI Loop 函数 - 从 Wire 接收消息并打印

        复用 Print UI 的 _ui_loop 逻辑（完全相同）

        流程：
        1. 循环接收 Wire 消息
        2. 根据消息类型渲染输出：
           - TextPart: 打印文本（逐字输出）
           - StepBegin: 显示步骤编号
           - ToolCall: 显示工具调用信息
           - ToolResult: 显示工具执行结果
           - StepInterrupted: 退出循环

        Args:
            wire_ui: Wire 的 UI 侧接口
        """
        import json

        while True:
            msg = await wire_ui.receive()

            # 文本片段：实时打印
            if isinstance(msg, TextPart):
                if msg.text:
                    print(msg.text, end="", flush=True)

            elif isinstance(msg, ContentPart):
                if hasattr(msg, "text") and msg.text:
                    print(msg.text, end="", flush=True)

            # 步骤开始：显示步骤编号
            elif isinstance(msg, StepBegin):
                if msg.n > 1:
                    print(f"\n\n🔄 [Step {msg.n}]", flush=True)

            # 工具调用：显示工具名称和参数
            elif isinstance(msg, ToolCall):
                print(f"\n\n🔧 调用工具: {msg.function.name}", flush=True)
                try:
                    arguments = json.loads(msg.function.arguments) if msg.function.arguments else {}
                    args_str = json.dumps(arguments, ensure_ascii=False, indent=2)
                    print(f"   参数:\n{args_str}", flush=True)
                except Exception:
                    print(f"   参数: {msg.function.arguments}", flush=True)

            # 工具结果：显示成功/失败状态
            elif isinstance(msg, ToolResult):
                if isinstance(msg.result, ToolOk):
                    print(f"\n✅ 工具成功", flush=True)
                    if msg.result.brief:
                        print(f"   {msg.result.brief}", flush=True)
                    output = str(msg.result.output)
                    if len(output) > 500:
                        output = output[:500] + "...(截断)"
                    if output.strip():
                        print(f"   输出: {output}", flush=True)
                elif isinstance(msg.result, ToolError):
                    print(f"\n❌ 工具失败: {msg.result.brief}", flush=True)
                    if msg.result.message:
                        print(f"   错误: {msg.result.message}", flush=True)

            # 步骤中断：退出 UI Loop
            elif isinstance(msg, StepInterrupted):
                break

    def _print_welcome(self, name: str, model: str) -> None:
        """
        打印欢迎信息

        Stage 9 简化版：纯文本欢迎信息
        官方使用 rich 库的 Panel 和 Table（漂亮的 UI）

        TODO: Stage 10+ 优化：使用 rich 库
        - 官方实现：kimi-cli-fork/src/kimi_cli/ui/shell/__init__.py:_print_welcome_info()
        - 优化点：
          * 使用 Panel 边框
          * 显示 KIMI logo
          * 显示版本更新信息
          * 颜色和样式美化

        Args:
            name: Agent 名称
            model: 模型名称
        """
        print("\n" + "=" * 60)
        print(f"  欢迎使用 {name}!")
        print(f"  模型: {model}")
        print("  输入 'exit' 或按 Ctrl+D 退出")
        print("  按 Ctrl+C 可以取消当前请求")
        print("=" * 60 + "\n")


# ============================================================
# TODO: Stage 10+ 扩展（参考官方）
# ============================================================
# 官方参考：kimi-cli-fork/src/kimi_cli/ui/shell/__init__.py
#
# Stage 10+ 需要添加的功能：
#
# 1. 使用 prompt_toolkit 的 PromptSession：
#    - 命令历史记录（上下箭头）
#    - 自动补全（Tab 键）
#    - 多行输入支持（Shift+Enter）
#    - 自定义提示符样式
#
# 2. 使用 rich 库美化输出：
#    - Panel 边框
#    - 颜色和样式
#    - KIMI logo
#    - 版本更新提示
#
# 3. 支持特殊命令（斜杠命令）：
#    - /help: 显示帮助信息
#    - /clear: 清空 Context
#    - /setup: 配置 LLM
#    - /thinking: 启用思考模式
#
# 4. 支持更多错误类型：
#    - MaxStepsReached: 达到最大步数
#    - LLMNotSupported: 模型不支持某些功能
#    - APIStatusError: API 状态错误（401, 402, 403 等）
#
# 5. 支持后台任务：
#    - 自动更新检查
#    - 异步任务管理
#
# 6. 支持信号处理：
#    - install_sigint_handler(): 自定义 SIGINT 处理
#    - 取消事件传递到 Soul
# ============================================================

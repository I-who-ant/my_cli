"""
阶段 3-8：Print UI 模式 + Wire 机制集成 + 工具调用显示

学习目标：
1. 理解非交互式 UI 的实现
2. 理解 create_soul() 工厂函数的使用
3. 理解 Wire 机制的 UI Loop 实现 ⭐
4. 理解 run_soul() 函数的调用模式 ⭐
5. 理解工具调用的 UI 显示 ⭐ Stage 8

对应源码：kimi-cli-fork/src/kimi_cli/ui/print/__init__.py

阶段演进：
- Stage 3：基础 Print UI ✅
  * 非交互式 CLI
  * 单次对话

- Stage 4-5：Soul 引擎集成 ✅
  * 使用 create_soul() 工厂函数
  * 从配置文件加载 LLM 配置

- Stage 6：Wire 机制 + 真正的流式输出 ✅
  * 使用 run_soul() 函数连接 Soul 和 UI
  * 使用 Wire 接收流式消息
  * 实时显示 LLM 响应（逐字输出）
  * 处理用户取消（Ctrl+C）

- Stage 8：工具调用显示 ✅ ⭐
  * 显示工具调用信息（名称、参数）
  * 显示工具执行结果（成功/失败）
  * 显示步骤编号（StepBegin）

使用示例：
    python cli.py print "你好，世界"
"""

from __future__ import annotations

import asyncio
from functools import partial
from pathlib import Path

from kosong.chat_provider import ChatProviderError

from my_cli.cli import OutputFormat, InputFormat
from my_cli.soul import LLMNotSet, RunCancelled, create_soul, run_soul
from my_cli.ui.print.visualize import visualize

__all__ = ["PrintUI"]


class PrintUI:
    """
    Print UI - 非交互式打印模式（支持 Wire 流式输出）

    这是一个简单的 UI 实现，用于演示 Wire 机制：
    - 接收用户输入
    - 调用 run_soul() 连接 Soul 和 UI Loop
    - UI Loop 从 Wire 接收消息并打印

    对应源码：kimi-cli-fork/src/kimi_cli/ui/print/__init__.py:23-156

    阶段演进：
    - Stage 3-5：基础 Print UI（非流式输出）✅
    - Stage 6：Wire 机制 + 流式输出 ✅
    """

    def __init__(
        self,
        verbose: bool = False,
        work_dir: Path | None = None,
        input_format: InputFormat = "text",
        output_format: OutputFormat = "text",
    ):
        """
        初始化 Print UI ⭐ Stage 33.5

        Args:
            verbose: 是否显示详细日志
            work_dir: 工作目录（默认当前目录）
            input_format: 输入格式（text 或 stream-json）
            output_format: 输出格式（text 或 stream-json）

        对应官方：kimi-cli-fork/src/kimi_cli/ui/print/__init__.py:32-42
        """
        self.verbose = verbose
        self.work_dir = work_dir or Path.cwd()
        self.input_format = input_format
        self.output_format = output_format

    async def run(self, command: str | None = None) -> None:
        """
        运行 Print UI

        Stage 6 流程：
        1. 创建 Soul（使用 create_soul 工厂函数）
        2. 创建取消事件（用于 Ctrl+C）
        3. 调用 run_soul() 连接 Soul 和 UI Loop
        4. UI Loop 从 Wire 接收消息并打印

        Args:
            command: 用户输入（None 则跳过）
        """
        # ============================================================
        # Stage 6: Wire 机制 + 流式输出 ✅
        # ============================================================

        # 1. 创建 Soul
        try:
            soul = await create_soul(work_dir=self.work_dir)
        except FileNotFoundError as e:
            print(f"\n❌ 配置文件错误: {e}\n")
            print("请先运行 'mycli init' 创建配置文件")
            return
        except ValueError as e:
            print(f"\n❌ 配置错误: {e}\n")
            return

        # 2. 处理用户输入
        if not command:
            print("\n⚠️  没有提供命令\n")
            return

        if self.verbose:
            print(f"\n🤖 使用模型: {soul.model_name}")
            print(f"📝 用户输入: {command}\n")

        # 3. 创建取消事件（用于 Ctrl+C）
        cancel_event = asyncio.Event()

        # 4. 调用 run_soul() 连接 Soul 和 UI Loop（⭐ 官方架构）
        print("\n💬 AI 回复:\n")
        try:
            await run_soul(
                soul=soul,
                user_input=command,
                ui_loop_fn=partial(visualize, self.output_format),  # ⭐ 官方做法：传递 output_format！
                cancel_event=cancel_event,
            )

            print("\n")

            if self.verbose:
                print(f"\n✅ 对话轮次: {soul.message_count}")

        except LLMNotSet:
            print("\n❌ LLM 未设置（需要配置 API Key）\n")
        except ChatProviderError as e:
            print(f"\n❌ LLM API 错误: {e}\n")
        except RunCancelled:
            print("\n\n⚠️  用户取消运行\n")
        except Exception as e:
            print(f"\n❌ 未知错误: {e}\n")
            raise


# ============================================================
# TODO: Stage 7+ 扩展（参考官方）
# ============================================================
# 官方参考：kimi-cli-fork/src/kimi_cli/ui/print/__init__.py
#
# Stage 7+ 需要添加的功能：
#
# 1. 支持多种输入/输出格式：
#    - input_format: "text" | "stream-json"
#    - output_format: "text" | "stream-json"
#
# 2. 支持从 stdin 读取命令：
#    if not sys.stdin.isatty() and self.input_format == "text":
#        command = sys.stdin.read().strip()
#
# 3. 支持 SIGINT 处理（Ctrl+C）：
#    from kimi_cli.utils.signals import install_sigint_handler
#    remove_sigint = install_sigint_handler(loop, _handler)
#
# 4. 支持更多消息类型渲染：
#    - ToolCall: 显示工具调用
#    - ToolResult: 显示工具结果
#    - StepBegin: 显示步骤开始
#
# 5. 支持 stream-json 输出格式：
#    async def _visualize_stream_json(self, wire: WireUISide, start_position: int):
#        # 从 context 文件读取并输出 JSON
#
# 6. 支持异常处理：
#    - MaxStepsReached: 达到最大步数
#    - BaseException: 其他未知错误
# ============================================================

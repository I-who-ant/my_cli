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
import json
from pathlib import Path

from kosong.chat_provider import ChatProviderError
from kosong.message import ContentPart, TextPart, ToolCall
from kosong.tooling import ToolResult, ToolError, ToolOk

from my_cli.soul import LLMNotSet, RunCancelled, create_soul, run_soul
from my_cli.wire import WireUISide
from my_cli.wire.message import StepBegin, StepInterrupted

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

    def __init__(self, verbose: bool = False, work_dir: Path | None = None):
        """
        初始化 Print UI

        Args:
            verbose: 是否显示详细日志
            work_dir: 工作目录（默认当前目录）
        """
        self.verbose = verbose
        self.work_dir = work_dir or Path.cwd()

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
            soul = create_soul(work_dir=self.work_dir)
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

        # 4. 调用 run_soul() 连接 Soul 和 UI Loop
        print("\n💬 AI 回复:\n")
        try:
            await run_soul(
                soul=soul,
                user_input=command,
                ui_loop_fn=self._ui_loop,  # UI Loop 函数
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

    async def _ui_loop(self, wire_ui: WireUISide) -> None:
        """
        UI Loop 函数 - 从 Wire 接收消息并打印（支持工具调用显示）

        这是 Wire 机制的关键部分！
        UI Loop 不断从 Wire 接收消息，直到收到 StepInterrupted 为止。

        流程：
        1. 循环接收 Wire 消息
        2. 根据消息类型渲染输出：
           - TextPart: 打印文本（flush=True 实现逐字输出）
           - ContentPart: 打印内容片段
           - StepBegin: 显示步骤编号 ⭐ Stage 8
           - ToolCall: 显示工具调用信息 ⭐ Stage 8
           - ToolResult: 显示工具执行结果 ⭐ Stage 8
           - StepInterrupted: 退出循环

        Args:
            wire_ui: Wire 的 UI 侧接口

        对应源码：kimi-cli-fork/src/kimi_cli/ui/print/__init__.py:129-134
        """
        # ⭐ 关键：循环接收 Wire 消息
        while True:
            # 接收一条消息（异步等待）
            msg = await wire_ui.receive()

            # ============================================================
            # Stage 6：基础消息处理 ✅
            # ============================================================
            if isinstance(msg, TextPart):
                # 文本片段：实时打印（逐字输出效果）
                if msg.text:
                    print(msg.text, end="", flush=True)

            elif isinstance(msg, ContentPart):
                # 内容片段（可能包含图片、文件等）
                # Stage 6 简化版：只处理文本
                if hasattr(msg, "text") and msg.text:
                    print(msg.text, end="", flush=True)

            # ============================================================
            # Stage 8：工具调用显示 ⭐
            # ============================================================
            elif isinstance(msg, StepBegin):
                # 步骤开始：显示步骤编号
                if msg.n > 1:  # 第一步不显示（避免干扰）
                    print(f"\n\n🔄 [Step {msg.n}]", flush=True)

            elif isinstance(msg, ToolCall):
                # 工具调用：显示工具名称和参数
                # ⭐ 修复：ToolCall 是嵌套结构 msg.function.name
                print(f"\n\n🔧 调用工具: {msg.function.name}", flush=True)
                # 格式化参数（缩进显示）
                try:
                    # ⭐ 修复：参数是 JSON 字符串 msg.function.arguments
                    arguments = json.loads(msg.function.arguments) if msg.function.arguments else {}
                    args_str = json.dumps(arguments, ensure_ascii=False, indent=2)
                    print(f"   参数:\n{args_str}", flush=True)
                except Exception:
                    print(f"   参数: {msg.function.arguments}", flush=True)

            elif isinstance(msg, ToolResult):
                # 工具结果：显示成功/失败状态
                if isinstance(msg.result, ToolOk):
                    print(f"\n✅ 工具成功", flush=True)
                    if msg.result.brief:
                        print(f"   {msg.result.brief}", flush=True)
                    # 显示输出（截断显示，避免过长）
                    output = str(msg.result.output)
                    if len(output) > 500:
                        output = output[:500] + "...(截断)"
                    if output.strip():
                        print(f"   输出: {output}", flush=True)
                elif isinstance(msg.result, ToolError):
                    print(f"\n❌ 工具失败: {msg.result.brief}", flush=True)
                    if msg.result.message:
                        print(f"   错误: {msg.result.message}", flush=True)

            # ============================================================
            # Stage 6：控制流消息 ✅
            # ============================================================
            elif isinstance(msg, StepInterrupted):
                # 步骤中断：退出 UI Loop
                break

            # 其他消息类型（Stage 8 暂时忽略）
            # Stage 9+ 需要处理：
            # - StatusUpdate: 状态更新
            # - CompactionBegin/End: Context 压缩


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

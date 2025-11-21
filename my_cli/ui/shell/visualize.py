"""
Shell UI 可视化渲染模块 ⭐ Stage 12 Live 修复版

职责：
1. 处理 Wire 消息并渲染到终端
2. 工具调用显示
3. 流式文本输出
4. 步骤指示器
5. ⭐ 使用 rich.live.Live 隔离输出（彻底修复光标混乱 bug）

对应源码：kimi-cli-fork/src/kimi_cli/ui/shell/visualize.py

为什么单独分离？
1. 渲染逻辑独立于业务逻辑
2. 可以支持不同的输出格式（终端、JSON、HTML）
3. 易于扩展和定制样式
4. 符合单一职责原则（SRP）

Stage 11 实现：
- 基础版 UI Loop 渲染
- 彩色输出（使用 rich）
- 工具调用显示

Stage 12 修复：
- ⭐ 使用 rich.live.Live 实现独立渲染区域
- ⭐ 彻底修复光标混乱 bug（Live 区域和输入区域完全隔离）
- ⭐ 累积文本内容，Live 实时刷新显示
- ⭐ 应用 utils.rich 全局配置（字符级换行）
"""

from __future__ import annotations

import asyncio
import json

# ⭐ Stage 12：导入 utils.rich 应用全局配置（字符级换行）
import my_cli.utils.rich  # noqa: F401
from kosong.message import ContentPart, TextPart, ToolCall, ToolCallPart
from kosong.tooling import ToolError, ToolOk, ToolResult
from rich.console import Group
from rich.live import Live
from rich.text import Text

from my_cli.ui.shell.console import console
from my_cli.wire import WireUISide
from my_cli.wire.message import ApprovalRequest, ApprovalResponse, StepBegin, StepInterrupted

__all__ = ["visualize"]


async def visualize(wire_ui: WireUISide) -> None:
    """
    UI Loop 函数 - 从 Wire 接收消息并渲染 ⭐ Stage 17 集成 extract_key_argument

    这是核心的渲染函数，负责：
    1. 循环接收 Wire 消息
    2. 根据消息类型渲染到终端
    3. 支持流式输出（逐字显示）
    4. 显示工具调用和结果
    5. ⭐ 使用 rich.live.Live 创建独立渲染区域
    6. ⭐ 支持 ToolCallPart 流式参数增量更新

    Args:
        wire_ui: Wire 的 UI 侧接口

    关键修复：
        使用 rich.live.Live 创建独立的渲染区域：
        - Live 区域和 PromptSession 的输入区域完全隔离
        - Live 区域的内容实时刷新，不会影响输入
        - 光标始终在输入区域，不会出现在 LLM 输出中

        工作原理：
        1. 累积所有文本内容到 content_text
        2. 每次收到消息时，更新 content_text
        3. live.update() 刷新 Live 区域显示
        4. 输入区域完全独立，不受影响

    Stage 17 新增：
        - 支持 ToolCallPart 累积参数增量
        - 使用 _ToolCallManager 管理活跃的工具调用
        - 实时更新工具参数显示
    """
    # 累积的文本内容
    content_text = Text()

    # ⭐ Stage 17：工具调用管理器（累积 ToolCallPart 增量）
    tool_call_manager = _ToolCallManager(content_text, live=None)

    # ⭐ 使用 Live 创建独立渲染区域
    with Live(
        content_text,
        console=console,
        refresh_per_second=10,  # 每秒刷新 10 次
        transient=False,  # 内容不是临时的，结束后保留
    ) as live:
        # 传递 live 实例给管理器
        tool_call_manager._live = live

        while True:
            msg = await wire_ui.receive()

            # 文本片段：累积并更新显示
            if isinstance(msg, TextPart):
                if msg.text:
                    content_text.append(msg.text)
                    live.update(content_text)  # ⭐ 实时刷新

            elif isinstance(msg, ContentPart):
                if hasattr(msg, "text") and msg.text:
                    content_text.append(msg.text)
                    live.update(content_text)

            # 步骤开始：显示步骤编号
            elif isinstance(msg, StepBegin):
                if msg.n > 1:
                    content_text.append(f"\n\n🔄 [Step {msg.n}]\n", style="cyan")
                    live.update(content_text)

            # ⭐ Stage 17：工具调用（支持 ToolCallPart 增量）
            elif isinstance(msg, ToolCall):
                tool_call_manager.start_tool_call(msg)

            # ⭐ Stage 17：工具调用增量参数更新
            elif isinstance(msg, ToolCallPart):
                tool_call_manager.append_args_part(msg)

            # 工具结果：显示成功/失败状态
            elif isinstance(msg, ToolResult):
                tool_call_manager.finish_tool_call(msg)
                _render_tool_result_to_text(msg, content_text)
                live.update(content_text)

            # ⭐ Stage 25：批准请求处理
            elif isinstance(msg, ApprovalRequest):
                await _handle_approval_request(msg, content_text, live)

            # 步骤中断：退出 UI Loop
            elif isinstance(msg, StepInterrupted):
                break


def _render_tool_result_to_text(tool_result: ToolResult, text: Text) -> None:
    """
    渲染工具执行结果到 Text 对象 ⭐ Stage 17 更新 extract_key_argument

    将工具执行结果追加到 Text 对象，而不是直接 console.print()。
    这样才能保证 Live 区域的完全隔离。

    Args:
        tool_result: 工具执行结果对象
        text: 累积的 Text 对象
    """
    if isinstance(tool_result.result, ToolOk):
        # 成功情况
        text.append("\n✅ 工具成功\n", style="green")

        if tool_result.result.brief:
            text.append(f"   {tool_result.result.brief}\n", style="grey50")

        output = str(tool_result.result.output)
        if len(output) > 500:
            output = output[:500] + "...(截断)"
        if output.strip():
            text.append(f"   输出: {output}\n", style="grey50")

    elif isinstance(tool_result.result, ToolError):
        # 失败情况
        text.append(f"\n❌ 工具失败: {tool_result.result.brief}\n", style="red")

        if tool_result.result.message:
            text.append(f"   错误: {tool_result.result.message}\n", style="grey50")


# ⭐ Stage 17：工具调用管理器（仿官方 _ToolCallBlock 的简化版）
class _ToolCallManager:
    """
    管理工具调用的流式更新（累积 ToolCallPart 增量）

    工作原理：
    1. 接收 ToolCall 后，显示工具名称
    2. 累积 ToolCallPart 的 arguments_part 增量
    3. 每次收到增量后，重新提取关键参数并更新显示
    4. ToolResult 到达后完成显示

    参考：kimi-cli-fork/src/kimi_cli/ui/shell/visualize.py:_ToolCallBlock
    """

    def __init__(self, text: Text, live):
        self._text = text
        self._live = live

        # 当前活跃的工具调用
        self._current_tool_call: ToolCall | None = None
        self._current_arguments: str = ""

    def start_tool_call(self, tool_call: ToolCall):
        """开始显示工具调用"""
        self._current_tool_call = tool_call
        self._current_arguments = tool_call.function.arguments or ""

        # 显示工具调用标题
        self._text.append("\n\n🔧 调用工具: ", style="yellow")
        self._text.append(tool_call.function.name, style="yellow")
        self._text.append("\n")

        # 立即尝试显示参数（如果有的话）
        self._update_arguments_display()

    def append_args_part(self, tool_call_part: ToolCallPart):
        """接收参数增量并更新显示"""
        if not self._current_tool_call:
            return

        # 累积参数增量
        if tool_call_part.arguments_part:
            self._current_arguments += tool_call_part.arguments_part

        # 更新显示
        self._update_arguments_display()

    def finish_tool_call(self, tool_result: ToolResult):
        """工具调用完成清理"""
        self._current_tool_call = None
        self._current_arguments = ""

    def _update_arguments_display(self):
        """更新参数显示"""
        if not self._current_tool_call:
            return

        from my_cli.tools import extract_key_argument

        # 提取关键参数
        key_arg = extract_key_argument(self._current_arguments, self._current_tool_call.function.name)

        if key_arg:
            # 显示关键参数（简洁版）
            self._text.append(f"   参数: {key_arg}\n", style="grey50")
        else:
            # 如果没有关键参数，尝试显示完整 JSON（但可能不完整）
            try:
                if self._current_arguments.strip():
                    arguments = json.loads(self._current_arguments)
                    args_str = json.dumps(arguments, ensure_ascii=False, indent=2)
                    self._text.append(f"   参数:\n{args_str}\n", style="grey50")
                else:
                    self._text.append(f"   参数:\n{{}}\n", style="grey50")
            except json.JSONDecodeError:
                # JSON 还没完整，先显示原始内容
                self._text.append(f"   参数: {self._current_arguments}", style="grey50")
                # 添加换行为下一个增量做准备
                self._text.append("\n", style="grey50")

        # 刷新显示
        if self._live:
            self._live.update(self._text)


# ============================================================
# Stage 25：批准请求处理 ⭐
# ============================================================


async def _handle_approval_request(
    request: ApprovalRequest, content_text: Text, live: Live
) -> None:
    """
    处理批准请求 ⭐ Stage 25

    当工具需要用户批准时（如执行危险操作），显示批准提示并等待用户输入。

    Args:
        request: 批准请求对象
        content_text: 累积的 Text 对象
        live: Live 渲染实例

    对应源码：kimi-cli-fork/src/kimi_cli/ui/shell/visualize.py:212-261
    """
    from rich.panel import Panel

    # 1. 在 Live 区域显示批准请求
    content_text.append("\n")
    content_text.append("⚠️ 批准请求\n", style="yellow bold")
    content_text.append(f"   工具: ", style="grey50")
    content_text.append(f"{request.sender}\n", style="blue")
    content_text.append(f"   操作: ", style="grey50")
    content_text.append(f"{request.description}\n", style="white")
    content_text.append("\n")
    content_text.append("   请选择:\n", style="grey50")
    content_text.append("   [y] 批准本次\n", style="cyan")
    content_text.append("   [a] 批准本会话所有同类操作\n", style="cyan")
    content_text.append("   [n] 拒绝\n", style="cyan")
    content_text.append("\n")
    live.update(content_text)

    # 2. 暂停 Live 渲染，获取用户输入
    live.stop()

    try:
        # 使用简单的 input 获取用户选择
        while True:
            try:
                choice = input("   你的选择 [y/a/n]: ").strip().lower()
            except EOFError:
                choice = "n"

            if choice in ("y", "yes", "是"):
                response = ApprovalResponse.APPROVE
                content_text.append("   ✅ 已批准\n\n", style="green")
                break
            elif choice in ("a", "all", "全部"):
                response = ApprovalResponse.APPROVE_FOR_SESSION
                content_text.append("   ✅ 已批准（本会话自动批准同类操作）\n\n", style="green")
                break
            elif choice in ("n", "no", "否", ""):
                response = ApprovalResponse.REJECT
                content_text.append("   ❌ 已拒绝\n\n", style="red")
                break
            else:
                print("   无效输入，请输入 y/a/n")

        # 3. 调用 request.resolve() 返回响应
        request.resolve(response)

    finally:
        # 4. 恢复 Live 渲染
        live.start()
        live.update(content_text)

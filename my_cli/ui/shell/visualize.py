"""
可视化模块 ⭐ Stage 33.2: 完全重构为 Compose 架构

学习目标：
1. 理解官方的 Compose 架构（vs 累积 Append 架构）
2. 理解 Block 模式（ContentBlock, ToolCallBlock, StatusBlock）
3. 理解流式 JSON 解析（streamingjson.Lexer）
4. 理解 refresh_soon() + compose() 刷新机制

对应源码：kimi-cli-fork/src/kimi_cli/ui/shell/visualize.py

核心改进：
- ❌ 旧架构：累积式 append() 到 Text 对象
- ✅ 新架构：compose() 重新组合所有 Block

架构对比：
# 旧架构（Stage 25）：
text.append("工具调用")  # 累积，无法清除
text.append("参数增量1")  # 重复显示
text.append("参数增量2")  # 重复显示

# 新架构（Stage 33.2）：
class Block:
    def compose() -> Renderable:  # 根据状态生成渲染内容
        return build_from_current_state()

live.update(view.compose())  # 每次刷新都重新组合

重构原因：
1. 流式参数显示导致重复输出（每个增量都 append 一行）
2. 无法根据状态更新显示（Text 只能累积，不能清除）
3. 与官方架构差异太大，维护困难

阶段演进：
- Stage 17：基础流式显示 ✅
- Stage 25：批准请求处理 ✅
- Stage 33.1：Future Annotations Bug 修复 ✅
- Stage 33.2：Compose 架构重构 ⭐ 当前
"""

import asyncio
from collections import deque
from collections.abc import Callable
from contextlib import asynccontextmanager, suppress
from typing import AsyncIterator, NamedTuple

import streamingjson  # pyright: ignore[reportMissingTypeStubs]
from kosong.message import ContentPart, TextPart, ToolCall, ToolCallPart
from kosong.tooling import ToolOk, ToolResult, ToolReturnType
from rich.console import Group, RenderableType
from rich.live import Live
from rich.markup import escape
from rich.panel import Panel
from rich.spinner import Spinner
from rich.text import Text

from my_cli.soul import StatusSnapshot
from my_cli.tools import extract_key_argument

from my_cli.ui.shell.console import console
from my_cli.ui.shell.keyboard import KeyEvent, listen_for_keyboard
from my_cli.utils.rich.columns import BulletColumns
from my_cli.utils.rich.markdown import Markdown
from my_cli.wire import WireMessage, WireUISide
from my_cli.wire.message import (
    ApprovalRequest,
    ApprovalResponse,
    CompactionBegin,
    CompactionEnd,
    StepBegin,
    StepInterrupted,
    StatusUpdate,
)

# ============================================================
# 常量定义
# ============================================================

MAX_SUBAGENT_TOOL_CALLS_TO_SHOW = 3
"""子任务工具调用最大显示数量"""


# ============================================================
# Block 类：_ContentBlock
# ============================================================


class _ContentBlock:
    """
    内容块：管理文本和思考内容 ⭐ Stage 33.2

    设计：
    - 流式接收文本内容（append）
    - compose() 时显示 spinner
    - compose_final() 时渲染为 Markdown

    对应源码：kimi-cli-fork/src/kimi_cli/ui/shell/visualize.py:_ContentBlock
    """

    def __init__(self, is_think: bool):
        self.is_think = is_think
        self._spinner = Spinner("dots", "Thinking..." if is_think else "Composing...")
        self.raw_text = ""

    def compose(self) -> RenderableType:
        """compose 时返回 spinner（进行中）"""
        return self._spinner

    def compose_final(self) -> RenderableType:
        """compose_final 时返回最终渲染的 Markdown"""
        return BulletColumns(
            Markdown(
                self.raw_text,
                style="grey50 italic" if self.is_think else "",
            ),
            bullet_style="grey50",
        )

    def append(self, content: str) -> None:
        """追加文本内容"""
        self.raw_text += content


# ============================================================
# Block 类：_ToolCallBlock
# ============================================================


class _ToolCallBlock:
    """
    工具调用块：管理单个工具调用的流式显示 ⭐ Stage 33.2

    设计：
    - 使用 streamingjson.Lexer 累积流式 JSON 参数
    - 参数变化时更新 _renderable（不是 append）
    - compose() 返回缓存的 _renderable
    - 支持子任务工具调用显示

    关键：
    - append_args_part() 只更新状态，不直接显示
    - _compose() 根据状态重新生成渲染内容
    - 每次状态变化时，调用 _compose() 更新 _renderable

    对应源码：kimi-cli-fork/src/kimi_cli/ui/shell/visualize.py:_ToolCallBlock
    """

    class FinishedSubCall(NamedTuple):
        """已完成的子工具调用"""

        call: ToolCall
        result: ToolReturnType

    def __init__(self, tool_call: ToolCall):
        self._tool_name = tool_call.function.name

        # 使用 streamingjson.Lexer 累积流式 JSON 参数
        self._lexer = streamingjson.Lexer()
        if tool_call.function.arguments is not None:
            self._lexer.append_string(tool_call.function.arguments)

        # 提取关键参数
        self._argument = extract_key_argument(self._lexer, self._tool_name)
        self._result: ToolReturnType | None = None

        # 子任务工具调用管理
        self._ongoing_subagent_tool_calls: dict[str, ToolCall] = {}
        self._last_subagent_tool_call: ToolCall | None = None
        self._n_finished_subagent_tool_calls = 0
        self._finished_subagent_tool_calls = deque[_ToolCallBlock.FinishedSubCall](
            maxlen=MAX_SUBAGENT_TOOL_CALLS_TO_SHOW
        )

        # Spinner 和渲染内容
        self._spinning_dots = Spinner("dots", text="")
        self._renderable: RenderableType = self._compose()

    def compose(self) -> RenderableType:
        """返回缓存的渲染内容"""
        return self._renderable

    @property
    def finished(self) -> bool:
        """工具调用是否已完成"""
        return self._result is not None

    def append_args_part(self, args_part: str):
        """
        追加参数增量 ⭐ 关键：只更新状态，不追加显示

        流程：
        1. 增量添加到 lexer
        2. 提取关键参数
        3. 如果参数变化，重新 compose _renderable
        """
        if self.finished:
            return

        self._lexer.append_string(args_part)

        # TODO: 优化：如果参数已稳定，不重复提取
        argument = extract_key_argument(self._lexer, self._tool_name)
        if argument and argument != self._argument:
            self._argument = argument
            # 🔑 关键：更新 _renderable，而不是 append
            self._renderable = BulletColumns(
                Text.from_markup(self._get_headline_markup()),
                bullet=self._spinning_dots,
            )

    def finish(self, result: ToolReturnType):
        """工具调用完成"""
        self._result = result
        self._renderable = self._compose()

    def append_sub_tool_call(self, tool_call: ToolCall):
        """添加子任务工具调用"""
        self._ongoing_subagent_tool_calls[tool_call.id] = tool_call
        self._last_subagent_tool_call = tool_call

    def append_sub_tool_call_part(self, tool_call_part: ToolCallPart):
        """追加子任务工具调用参数增量"""
        if self._last_subagent_tool_call is None:
            return
        if not tool_call_part.arguments_part:
            return

        # 累积参数
        if self._last_subagent_tool_call.function.arguments is None:
            self._last_subagent_tool_call.function.arguments = tool_call_part.arguments_part
        else:
            self._last_subagent_tool_call.function.arguments += tool_call_part.arguments_part

    def finish_sub_tool_call(self, tool_result: ToolResult):
        """子任务工具调用完成"""
        self._last_subagent_tool_call = None
        sub_tool_call = self._ongoing_subagent_tool_calls.pop(tool_result.tool_call_id, None)
        if sub_tool_call is None:
            return

        self._finished_subagent_tool_calls.append(
            _ToolCallBlock.FinishedSubCall(
                call=sub_tool_call,
                result=tool_result.result,
            )
        )
        self._n_finished_subagent_tool_calls += 1
        self._renderable = self._compose()

    def _compose(self) -> RenderableType:
        """
        根据当前状态组合渲染内容 ⭐ 核心方法

        组成：
        1. 标题行（工具名 + 关键参数）
        2. 子任务工具调用列表（如果有）
        3. 结果摘要（如果有）
        4. Spinner 或 check mark
        """
        lines: list[RenderableType] = [
            Text.from_markup(self._get_headline_markup()),
        ]

        # 如果子任务工具调用过多，显示省略提示
        if self._n_finished_subagent_tool_calls > MAX_SUBAGENT_TOOL_CALLS_TO_SHOW:
            n_hidden = self._n_finished_subagent_tool_calls - MAX_SUBAGENT_TOOL_CALLS_TO_SHOW
            lines.append(
                BulletColumns(
                    Text(
                        f"{n_hidden} more tool call{'s' if n_hidden > 1 else ''} ...",
                        style="grey50 italic",
                    ),
                    bullet_style="grey50",
                )
            )

        # 显示已完成的子任务工具调用
        for sub_call, sub_result in self._finished_subagent_tool_calls:
            argument = extract_key_argument(
                sub_call.function.arguments or "", sub_call.function.name
            )
            lines.append(
                BulletColumns(
                    Text.from_markup(
                        f"Used [blue]{sub_call.function.name}[/blue]"
                        + (f" [grey50]({argument})[/grey50]" if argument else "")
                    ),
                    bullet_style="green" if isinstance(sub_result, ToolOk) else "red",
                )
            )

        # 显示结果摘要
        if self._result is not None and self._result.brief:
            lines.append(
                Markdown(
                    self._result.brief,
                    style="grey50" if isinstance(self._result, ToolOk) else "red",
                )
            )

        # 返回组合的内容（带 spinner 或 check mark）
        if self.finished:
            return BulletColumns(
                Group(*lines),
                bullet_style="green" if isinstance(self._result, ToolOk) else "red",
            )
        else:
            return BulletColumns(
                Group(*lines),
                bullet=self._spinning_dots,
            )

    def _get_headline_markup(self) -> str:
        """生成标题行 Markup"""
        return f"{'Used' if self.finished else 'Using'} [blue]{self._tool_name}[/blue]" + (
            f" [grey50]({escape(self._argument)})[/grey50]" if self._argument else ""
        )


# ============================================================
# Block 类：_StatusBlock
# ============================================================


class _ApprovalRequestPanel:
    """批准请求面板 ⭐ Stage 33.11 对齐官方"""

    def __init__(self, request: ApprovalRequest):
        self.request = request
        self.options = [
            ("Approve", ApprovalResponse.APPROVE),
            ("Approve for this session", ApprovalResponse.APPROVE_FOR_SESSION),
            ("Reject, tell Kimi CLI what to do instead", ApprovalResponse.REJECT),
        ]
        self.selected_index = 0

    def render(self) -> RenderableType:
        """渲染批准菜单面板"""
        lines: list[RenderableType] = []

        # 添加请求详情
        lines.append(
            Text.assemble(
                Text.from_markup(f"[blue]{self.request.sender}[/blue]"),
                Text(f' is requesting approval to "{self.request.description}".'),
            )
        )

        lines.append(Text(""))  # 空行

        # 添加菜单选项
        for i, (option_text, _) in enumerate(self.options):
            if i == self.selected_index:
                lines.append(Text(f"→ {option_text}", style="cyan"))
            else:
                lines.append(Text(f"  {option_text}", style="grey50"))

        content = Group(*lines)
        return Panel.fit(
            content,
            title="[yellow]⚠ Approval Requested[/yellow]",
            border_style="yellow",
            padding=(1, 2),
        )

    def move_up(self):
        """向上移动选择"""
        self.selected_index = (self.selected_index - 1) % len(self.options)

    def move_down(self):
        """向下移动选择"""
        self.selected_index = (self.selected_index + 1) % len(self.options)

    def get_selected_response(self) -> ApprovalResponse:
        """根据选中选项获取批准响应"""
        return self.options[self.selected_index][1]


class _StatusBlock:
    """
    状态块：显示上下文使用情况 ⭐ Stage 33.2

    设计：
    - 显示 token 使用百分比和进度条
    - 根据使用率改变颜色

    对应源码：kimi-cli-fork/src/kimi_cli/ui/shell/visualize.py:_StatusBlock
    """

    def __init__(self, initial_status: StatusSnapshot):
        self._status = initial_status

    def update_status(self, status: StatusSnapshot):
        """更新状态"""
        self._status = status

    def render(self) -> RenderableType:
        """渲染状态块 ⭐ Stage 33.9 对齐官方（简化版）"""
        # ⭐ 对齐官方：直接创建 Text 并设置 plain 属性，避免 markup 解析错误
        text = Text("", justify="right", style="grey50")
        text.plain = f"context: {self._status.context_usage:.1%}"
        return text


# ============================================================
# 主视图：_LiveView
# ============================================================


class _LiveView:
    """
    主视图：组合所有 Block 并管理状态 ⭐ Stage 33.2

    设计：
    - 维护所有 Block 实例
    - dispatch_wire_message() 分发消息到各个 Block
    - compose() 组合所有 Block 的渲染内容
    - refresh_soon() 标记需要刷新

    刷新机制：
    1. Block 状态变化 → refresh_soon() → 设置 _need_recompose = True
    2. 主循环检测到 _need_recompose → live.update(self.compose())
    3. compose() 调用所有 Block 的 compose() 方法

    对应源码：kimi-cli-fork/src/kimi_cli/ui/shell/visualize.py:_LiveView
    """

    def __init__(self, initial_status: StatusSnapshot, cancel_event: asyncio.Event | None = None):
        self._cancel_event = cancel_event

        # Spinners
        self._mooning_spinner: Spinner | None = None  # StepBegin spinner
        self._compacting_spinner: Spinner | None = None  # CompactionBegin spinner

        # Blocks
        self._current_content_block: _ContentBlock | None = None
        self._tool_call_blocks: dict[str, _ToolCallBlock] = {}
        self._last_tool_call_block: _ToolCallBlock | None = None

        # 批准请求
        self._approval_request_queue = deque[ApprovalRequest]()
        self._current_approval_request_panel: _ApprovalRequestPanel | None = None
        self._reject_all_following = False

        # 状态块
        self._status_block = _StatusBlock(initial_status)

        # 刷新标记
        self._need_recompose = False

    async def visualize_loop(self, wire: WireUISide):
        """
        主可视化循环 ⭐ Stage 33.2

        流程：
        1. 创建 Live 实例
        2. 循环接收 Wire 消息
        3. dispatch_wire_message() 分发消息
        4. 如果 _need_recompose，调用 live.update(self.compose())
        """
        with Live(
            self.compose(),
            console=console,
            refresh_per_second=10,
            transient=True,
            vertical_overflow="visible",
        ) as live:

            # 键盘事件处理（ESC 取消等）
            def keyboard_handler(event: KeyEvent) -> None:
                self.dispatch_keyboard_event(event)
                if self._need_recompose:
                    live.update(self.compose())
                    self._need_recompose = False

            async with _keyboard_listener(keyboard_handler):
                while True:
                    try:
                        msg = await wire.receive()
                    except asyncio.QueueShutDown:
                        self.cleanup(is_interrupt=False)
                        live.update(self.compose())
                        break

                    if isinstance(msg, StepInterrupted):
                        self.cleanup(is_interrupt=True)
                        live.update(self.compose())
                        break

                    # 分发消息到各个 Block
                    self.dispatch_wire_message(msg)

                    # 如果需要刷新，更新显示
                    if self._need_recompose:
                        live.update(self.compose())
                        self._need_recompose = False

    def refresh_soon(self) -> None:
        """标记需要刷新"""
        self._need_recompose = True

    def compose(self) -> RenderableType:
        """
        组合所有 Block 的渲染内容 ⭐ 核心方法

        组成：
        1. Spinner（如果有）
        2. 内容块（如果有）
        3. 所有工具调用块
        4. 批准请求面板（如果有）
        5. 状态块
        """
        blocks: list[RenderableType] = []

        # Spinners 优先显示
        if self._mooning_spinner is not None:
            blocks.append(self._mooning_spinner)
        elif self._compacting_spinner is not None:
            blocks.append(self._compacting_spinner)
        else:
            # 内容块
            if self._current_content_block is not None:
                blocks.append(self._current_content_block.compose())

            # 工具调用块
            for tool_call in self._tool_call_blocks.values():
                blocks.append(tool_call.compose())

        # 批准请求面板
        if self._current_approval_request_panel:
            blocks.append(self._current_approval_request_panel.render())

        # 状态块
        blocks.append(self._status_block.render())

        return Group(*blocks)

    def dispatch_wire_message(self, msg: WireMessage) -> None:
        """
        分发 Wire 消息到各个 Block ⭐ 核心方法

        根据消息类型，调用相应的处理方法
        """
        assert not isinstance(msg, StepInterrupted)  # handled in visualize_loop

        if isinstance(msg, StepBegin):
            self.cleanup(is_interrupt=False)
            self._mooning_spinner = Spinner("moon", "")
            self.refresh_soon()
            return

        if self._mooning_spinner is not None:
            self._mooning_spinner = None
            self.refresh_soon()

        if isinstance(msg, ContentPart):
            self.append_content(msg)
        elif isinstance(msg, ToolCall):
            self.append_tool_call(msg)
        elif isinstance(msg, ToolCallPart):
            self.append_tool_call_part(msg)
        elif isinstance(msg, ToolResult):
            self.append_tool_result(msg)
        elif isinstance(msg, ApprovalRequest):
            self.request_approval(msg)
        elif isinstance(msg, CompactionBegin):
            self.begin_compaction(msg)
        elif isinstance(msg, CompactionEnd):
            self.end_compaction(msg)
        elif isinstance(msg, StatusUpdate):
            self._status_block.update_status(msg.status)
            self.refresh_soon()

    def append_content(self, msg: ContentPart) -> None:
        """追加内容"""
        if isinstance(msg, TextPart):
            # 开始新的内容块（如果需要）
            if self._current_content_block is None:
                self._current_content_block = _ContentBlock(is_think=False)
                self.refresh_soon()

            # 追加文本
            self._current_content_block.append(msg.text)
            self.refresh_soon()

    def append_tool_call(self, tool_call: ToolCall) -> None:
        """添加工具调用"""
        block = _ToolCallBlock(tool_call)
        self._tool_call_blocks[tool_call.id] = block
        self._last_tool_call_block = block
        self.refresh_soon()

    def append_tool_call_part(self, part: ToolCallPart) -> None:
        """追加工具调用参数增量"""
        if not part.arguments_part:
            return
        if self._last_tool_call_block is None:
            return

        self._last_tool_call_block.append_args_part(part.arguments_part)
        self.refresh_soon()

    def append_tool_result(self, result: ToolResult) -> None:
        """工具调用完成"""
        if block := self._tool_call_blocks.get(result.tool_call_id):
            block.finish(result.result)
            self.flush_finished_tool_calls()
            self.refresh_soon()

    def flush_finished_tool_calls(self) -> None:
        """清理所有已完成的工具调用块"""
        tool_call_ids = list(self._tool_call_blocks.keys())
        for tool_call_id in tool_call_ids:
            block = self._tool_call_blocks[tool_call_id]
            if not block.finished:
                break

            self._tool_call_blocks.pop(tool_call_id)
            console.print(block.compose())
            if self._last_tool_call_block == block:
                self._last_tool_call_block = None
            self.refresh_soon()

    def flush_content(self) -> None:
        """刷新当前内容块（输出最终渲染）"""
        if self._current_content_block is not None:
            console.print(self._current_content_block.compose_final())
            self._current_content_block = None
            self.refresh_soon()

    def request_approval(self, request: ApprovalRequest) -> None:
        """请求批准"""
        # 如果已设置拒绝所有后续请求，立即拒绝
        if self._reject_all_following:
            request.resolve(ApprovalResponse.REJECT)
            return

        # 加入队列
        self._approval_request_queue.append(request)

        # 如果没有正在处理的批准请求，处理新请求
        if self._current_approval_request_panel is None:
            console.bell()  # 响铃提示用户
            self._process_next_approval_request()

    def _process_next_approval_request(self):
        """处理下一个批准请求 ⭐ Stage 33.11 对齐官方"""
        if not self._approval_request_queue:
            return

        request = self._approval_request_queue[0]

        # ⭐ 对齐官方：使用 _ApprovalRequestPanel 类
        self._current_approval_request_panel = _ApprovalRequestPanel(request)
        self.refresh_soon()

    def show_next_approval_request(self):
        """显示下一个批准请求 ⭐ Stage 33.11 对齐官方"""
        # 从队列中移除当前请求
        if self._approval_request_queue:
            self._approval_request_queue.popleft()

        # 处理下一个请求
        if self._approval_request_queue:
            self._process_next_approval_request()
        else:
            # 队列为空，清除当前面板
            self._current_approval_request_panel = None
            self.refresh_soon()

    def dispatch_keyboard_event(self, event: KeyEvent) -> None:
        """处理键盘事件 ⭐ Stage 33.10 对齐官方"""
        # ⭐ 对齐官方：直接比较枚举值，不需要解析 key_sequence
        # 处理 ESC 键取消
        if event == KeyEvent.ESCAPE and self._cancel_event is not None:
            self._cancel_event.set()
            return

        # ⭐ 对齐官方：没有批准请求时忽略键盘事件
        if not self._current_approval_request_panel:
            return

        # ⭐ 对齐官方：处理批准面板的键盘导航
        match event:
            case KeyEvent.UP:
                self._current_approval_request_panel.move_up()
                self.refresh_soon()
            case KeyEvent.DOWN:
                self._current_approval_request_panel.move_down()
                self.refresh_soon()
            case KeyEvent.ENTER:
                resp = self._current_approval_request_panel.get_selected_response()
                self._current_approval_request_panel.request.resolve(resp)
                # 处理"本次会话批准"选项
                if resp == ApprovalResponse.APPROVE_FOR_SESSION:
                    to_remove_from_queue: list[ApprovalRequest] = []
                    for request in self._approval_request_queue:
                        # 批准所有队列中相同操作的请求
                        if request.action == self._current_approval_request_panel.request.action:
                            request.resolve(ApprovalResponse.APPROVE_FOR_SESSION)
                            to_remove_from_queue.append(request)
                    for request in to_remove_from_queue:
                        self._approval_request_queue.remove(request)
                # 处理"拒绝"选项
                elif resp == ApprovalResponse.REJECT:
                    # 拒绝应该立即停止步骤
                    while self._approval_request_queue:
                        self._approval_request_queue.popleft().resolve(ApprovalResponse.REJECT)
                    self._reject_all_following = True
                # 显示下一个批准请求
                self.show_next_approval_request()
            case _:
                # 其他键盘事件忽略
                return

    def begin_compaction(self, msg: CompactionBegin) -> None:
        """开始压缩"""
        # 将内容块转换为最终渲染
        if self._current_content_block is not None:
            # 简化版：直接保留 spinner 版本
            # 官方版本会调用 compose_final()
            pass

        self._compacting_spinner = Spinner("dots", "Compacting...")
        self.refresh_soon()

    def end_compaction(self, msg: CompactionEnd) -> None:
        """结束压缩"""
        self._compacting_spinner = None
        self.refresh_soon()

    def cleanup(self, is_interrupt: bool) -> None:
        """清理所有 Block"""
        self._mooning_spinner = None
        self._compacting_spinner = None
        self._current_content_block = None
        self._tool_call_blocks.clear()
        self._last_tool_call_block = None
        self._approval_request_queue.clear()
        self._current_approval_request_panel = None


# ============================================================
# 键盘监听器
# ============================================================


@asynccontextmanager
async def _keyboard_listener(
    handler: Callable[[KeyEvent], None]
) -> AsyncIterator[None]:
    """键盘监听器 ⭐ Stage 33.10 对齐官方"""
    # ⭐ 对齐官方：使用 listen_for_keyboard()，不要用 prompt_toolkit
    async def _keyboard():
        async for event in listen_for_keyboard():
            handler(event)

    task = asyncio.create_task(_keyboard())
    try:
        yield
    finally:
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task


# ============================================================
# 公开 API
# ============================================================


async def visualize(
    wire: WireUISide,
    *,
    initial_status: StatusSnapshot,
    cancel_event: asyncio.Event | None = None,
):
    """
    可视化 Agent 行为 ⭐ Stage 33.2

    Args:
        wire: Wire UI 侧通信通道
        initial_status: 初始状态快照
        cancel_event: 取消事件（按 ESC 触发）

    对应源码：kimi-cli-fork/src/kimi_cli/ui/shell/visualize.py:visualize
    """
    view = _LiveView(initial_status, cancel_event)
    await view.visualize_loop(wire)


__all__ = ["visualize"]

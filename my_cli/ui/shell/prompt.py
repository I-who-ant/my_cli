"""
Shell UI Prompt 模块（输入处理）⭐ Stage 12 增强版

职责：
1. CustomPromptSession - 自定义输入会话
2. 命令历史记录（FileHistory 持久化）
3. 自动补全系统（MetaCommandCompleter + FileMentionCompleter）
4. 多行输入支持（Ctrl+J / Alt+Enter）
5. 状态栏显示（可选）

对应源码：kimi-cli-fork/src/kimi_cli/ui/shell/prompt.py (793行)

阶段演进：
- Stage 11：基础 PromptSession + 历史记录 ✅
- Stage 12：自动补全 + 多行输入 ⭐ 当前
- Stage 13+：状态栏 + 剪贴板 + 键绑定

为什么单独分离？
1. 输入处理是独立的复杂子系统
2. 涉及 prompt_toolkit 的深度定制
3. 包含多种补全器、键绑定、状态管理
4. 代码量大（官方 793 行），拆分利于维护
"""

from __future__ import annotations

import asyncio
import contextlib
import getpass
import json
import os
import re
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from hashlib import md5
from pathlib import Path
from typing import TYPE_CHECKING, override

from kosong.message import ContentPart, ImageURLPart, TextPart
from prompt_toolkit import PromptSession
from prompt_toolkit.application import get_app_or_none
from prompt_toolkit.completion import Completer, Completion, DummyCompleter, merge_completers
from prompt_toolkit.document import Document
from prompt_toolkit.filters import Condition, has_completions
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.key_binding import KeyBindings, KeyPressEvent
from pydantic import BaseModel, ValidationError

from my_cli.utils.logging import logger

if TYPE_CHECKING:
    from prompt_toolkit.completion import CompleteEvent

    from my_cli.soul import StatusSnapshot  # ⭐ Stage 16: 类型提示

# Prompt 符号
PROMPT_SYMBOL = "✨"
PROMPT_SYMBOL_SHELL = "$"
PROMPT_SYMBOL_THINKING = "💫"

# 状态栏刷新间隔（秒）
_REFRESH_INTERVAL = 1.0

# ⭐ 附件占位符正则（对齐官方 line 461-463）
_ATTACHMENT_PLACEHOLDER_RE = re.compile(
    r"\[(?P<type>image):(?P<id>[a-zA-Z0-9_\-\.]+)(?:,(?P<width>\d+)x(?P<height>\d+))?\]"
)


# ============================================================
# Toast 通知系统 ⭐ 对齐官方实现
# ============================================================


@dataclass(slots=True)
class _ToastEntry:
    """Toast 条目"""
    topic: str | None
    """相同 topic 的 Toast 只保留一个"""
    message: str
    duration: float


_toast_queue: deque[_ToastEntry] = deque()
"""Toast 队列，第一个是当前正在显示的"""


def toast(
    message: str,
    duration: float = 5.0,
    topic: str | None = None,
    immediate: bool = False,
) -> None:
    """
    显示 Toast 通知 ⭐ 对齐官方实现

    Args:
        message: 通知消息
        duration: 显示时长（秒）
        topic: 主题（相同主题的 Toast 会被替换）
        immediate: 是否立即显示（插入队列头部）

    对应源码：kimi-cli-fork/src/kimi_cli/ui/shell/prompt.py:427-443
    """
    duration = max(duration, _REFRESH_INTERVAL)
    entry = _ToastEntry(topic=topic, message=message, duration=duration)

    # 移除相同 topic 的现有 Toast
    if topic is not None:
        for existing in list(_toast_queue):
            if existing.topic == topic:
                _toast_queue.remove(existing)

    # 添加到队列
    if immediate:
        _toast_queue.appendleft(entry)
    else:
        _toast_queue.append(entry)


def _current_toast() -> _ToastEntry | None:
    """获取当前正在显示的 Toast"""
    if not _toast_queue:
        return None
    return _toast_queue[0]


def _toast_thinking(thinking: bool) -> None:
    """显示 thinking 状态的 Toast ⭐ 对齐官方"""
    toast(
        f"thinking {'on' if thinking else 'off'}, tab to toggle",
        duration=3.0,
        topic="thinking",
        immediate=True,
    )


# ============================================================
# Prompt 模式 ⭐ Stage 13 新增
# ============================================================


class PromptMode(Enum):
    """
    Prompt 模式枚举 ⭐ Stage 13

    支持的模式：
    - AGENT: LLM 对话模式（默认）
    - SHELL: Shell 命令模式

    对应源码：kimi-cli-fork/src/kimi_cli/ui/shell/prompt.py:386-391
    """

    AGENT = "agent"
    SHELL = "shell"

    def toggle(self) -> "PromptMode":
        """切换模式"""
        return PromptMode.SHELL if self == PromptMode.AGENT else PromptMode.AGENT

    def __str__(self) -> str:
        return self.value


# ============================================================
# 自动补全器 ⭐ Stage 12 新增
# ============================================================


class MetaCommandCompleter(Completer):
    """
    斜杠命令自动补全器 ⭐ Stage 12

    功能：
    1. 当输入以 '/' 开头时触发补全
    2. 匹配命令名称和别名
    3. 显示命令描述

    对应源码：kimi-cli-fork/src/kimi_cli/ui/shell/prompt.py:57-93

    使用示例：
        输入: /h<Tab>
        补全: /help
        描述: 显示此帮助信息
    """

    @override
    def get_completions(
        self, document: Document, complete_event: CompleteEvent
    ) -> iter[Completion]:
        """
        获取补全建议

        Args:
            document: 当前文档
            complete_event: 补全事件

        Yields:
            Completion 对象
        """
        # 导入命令注册表（延迟导入避免循环依赖）
        from my_cli.ui.shell.metacmd import get_meta_commands

        text = document.text_before_cursor

        # 只在输入缓冲区没有其他内容时自动补全
        if document.text_after_cursor.strip():
            return

        # 只考虑最后一个 token（允许未来在空格后添加参数）
        last_space = text.rfind(" ")
        token = text[last_space + 1 :]
        prefix = text[: last_space + 1] if last_space != -1 else ""

        # 如果有前缀，说明不是第一个词，不补全
        if prefix.strip():
            return

        # 必须以 / 开头才补全
        if not token.startswith("/"):
            return

        # 去掉 / 前缀
        typed = token[1:]
        typed_lower = typed.lower()

        # 遍历所有命令
        for cmd in sorted(get_meta_commands(), key=lambda c: c.name):
            # 命令名 + 别名
            names = [cmd.name] + list(cmd.aliases)

            # 如果输入为空或匹配任何名称
            if typed == "" or any(n.lower().startswith(typed_lower) for n in names):
                yield Completion(
                    text=f"/{cmd.name}",  # 补全文本
                    start_position=-len(token),  # 替换位置
                    display=cmd.slash_name(),  # 显示文本（如 "/help (h, ?)"）
                    display_meta=cmd.description,  # 描述
                )


class FileMentionCompleter(Completer):
    """
    文件路径自动补全器 ⭐ Stage 14

    功能：
    1. 当输入包含 '@' 时触发补全
    2. 匹配工作目录下的文件和目录
    3. 忽略常见的缓存目录（.git, node_modules, __pycache__ 等）

    对应源码：kimi-cli-fork/src/kimi_cli/ui/shell/prompt.py:96-342

    使用示例：
        输入: @my_cli<Tab>
        补全: @my_cli/
        描述: 目录

    简化版实现（Stage 14）：
    - ✅ @ 触发补全
    - ✅ 忽略常见缓存目录
    - ✅ 目录添加 / 后缀
    - ❌ 缓存机制（Stage 15+）
    - ❌ 模糊匹配（Stage 15+）
    - ❌ 路径排序优化（Stage 15+）

    TODO (Stage 15+):
    - 添加文件索引缓存（2 秒刷新间隔）
    - 集成 FuzzyCompleter 模糊匹配
    - 路径排序优化（basename 优先）
    - 深度路径索引（os.walk）
    """

    # 忽略的目录列表（简化版）
    _IGNORED_DIRS = {
        ".git",
        ".hg",
        ".svn",
        "node_modules",
        "__pycache__",
        ".pytest_cache",
        ".venv",
        "venv",
        ".idea",
        ".vscode",
        "dist",
        "build",
        ".next",
        ".nuxt",
    }

    def __init__(self, root: Path):
        """
        初始化文件补全器

        Args:
            root: 工作目录根路径
        """
        self._root = root

    @staticmethod
    def _extract_fragment(text: str) -> str | None:
        """
        提取 @ 后的文件路径片段

        Args:
            text: 输入文本

        Returns:
            路径片段，如果没有 @ 或格式不正确则返回 None

        示例：
            "hello @my_cli" -> "my_cli"
            "@docs/README" -> "docs/README"
            "no at sign" -> None
        """
        index = text.rfind("@")
        if index == -1:
            return None

        # 确保 @ 前面不是字母或数字（避免匹配 email）
        if index > 0:
            prev = text[index - 1]
            if prev.isalnum():
                return None

        # 提取 @ 后的片段
        fragment = text[index + 1 :]
        if not fragment:
            return ""

        # 如果包含空格，不补全
        if any(ch.isspace() for ch in fragment):
            return None

        return fragment

    def _is_ignored(self, name: str) -> bool:
        """
        判断文件/目录是否应该被忽略

        Args:
            name: 文件/目录名称

        Returns:
            True 如果应该忽略
        """
        return name in self._IGNORED_DIRS

    def _get_matching_paths(self, fragment: str) -> list[tuple[str, bool]]:
        """
        获取匹配的文件路径

        Args:
            fragment: 路径片段

        Returns:
            (路径, 是否为目录) 的列表

        简化版实现：
        - 只搜索根目录和一级子目录
        - 忽略常见缓存目录
        - 最多返回 50 个结果
        """
        matches: list[tuple[str, bool]] = []

        try:
            # 如果片段包含 /，分解为目录和文件名
            if "/" in fragment:
                parts = fragment.split("/")
                search_dir = self._root / "/".join(parts[:-1])
                prefix = parts[-1].lower()
            else:
                search_dir = self._root
                prefix = fragment.lower()

            # 如果目录不存在，返回空
            if not search_dir.exists() or not search_dir.is_dir():
                return matches

            # 遍历目录
            for entry in sorted(search_dir.iterdir(), key=lambda p: p.name):
                name = entry.name

                # 跳过隐藏文件（以 . 开头）
                if name.startswith(".") and prefix and not prefix.startswith("."):
                    continue

                # 跳过忽略目录
                if self._is_ignored(name):
                    continue

                # 检查是否匹配前缀
                if not name.lower().startswith(prefix):
                    continue

                # 计算相对路径
                rel_path = entry.relative_to(self._root).as_posix()
                is_dir = entry.is_dir()

                matches.append((rel_path, is_dir))

                # 限制返回数量
                if len(matches) >= 50:
                    break

        except OSError:
            # 忽略权限错误等
            pass

        return matches

    @override
    def get_completions(
        self, document: Document, complete_event: CompleteEvent
    ) -> iter[Completion]:
        """
        获取补全建议

        Args:
            document: 当前文档
            complete_event: 补全事件

        Yields:
            Completion 对象
        """
        # 提取 @ 后的片段
        fragment = self._extract_fragment(document.text_before_cursor)
        if fragment is None:
            return

        # 获取匹配的路径
        matches = self._get_matching_paths(fragment)

        # 生成补全建议
        for path, is_dir in matches:
            # 目录添加 / 后缀
            display = f"{path}/" if is_dir else path

            # 计算替换位置（从 @ 之后开始）
            at_index = document.text_before_cursor.rfind("@")
            start_position = -(len(document.text_before_cursor) - at_index - 1)

            yield Completion(
                text=display,  # 补全文本
                start_position=start_position,  # 替换位置
                display=display,  # 显示文本
                display_meta="目录" if is_dir else "文件",  # 描述
            )


# ============================================================
# 历史记录系统 ⭐ 对齐官方实现
# ============================================================


class _HistoryEntry(BaseModel):
    """历史记录条目"""
    content: str


def _load_history_entries(history_file: Path) -> list[_HistoryEntry]:
    """
    加载历史记录文件 ⭐ 对齐官方实现

    Args:
        history_file: 历史记录文件路径（JSONL 格式）

    Returns:
        历史记录条目列表

    对应源码：kimi-cli-fork/src/kimi_cli/ui/shell/prompt.py:348-383
    """
    entries: list[_HistoryEntry] = []
    if not history_file.exists():
        return entries

    try:
        with history_file.open(encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    logger.warning(
                        "Failed to parse user history line; skipping: {line}",
                        line=line,
                    )
                    continue
                try:
                    entry = _HistoryEntry.model_validate(record)
                    entries.append(entry)
                except ValidationError:
                    logger.warning(
                        "Failed to validate user history entry; skipping: {line}",
                        line=line,
                    )
                    continue
    except OSError as exc:
        logger.warning(
            "Failed to load user history file: {file} ({error})",
            file=history_file,
            error=exc,
        )

    return entries


# ============================================================
# 输入封装 ⭐ Stage 12
# ============================================================


class UserInput(BaseModel):
    """
    用户输入封装 ⭐ 对齐官方实现

    对应源码：kimi-cli-fork/src/kimi_cli/ui/shell/prompt.py:397-409
    """
    mode: PromptMode
    thinking: bool
    command: str
    """用户输入的纯文本表示"""
    content: list[ContentPart]
    """富文本内容（包含文本和附件）"""

    def __str__(self) -> str:
        return self.command

    def __bool__(self) -> bool:
        return bool(self.command)


class CustomPromptSession:
    """
    自定义 PromptSession ⭐ Stage 12 增强版

    新增特性：
    - ✅ 命令历史记录（FileHistory 持久化）
    - ✅ MetaCommandCompleter（/命令补全）⭐ Stage 12
    - ✅ 多行输入支持（Ctrl+J 插入换行）⭐ Stage 12
    - ✅ 自定义键绑定（Ctrl+J 换行）⭐ Stage 12
    - ❌ FileMentionCompleter（@文件补全）Stage 13+
    - ❌ 状态栏显示（Model、Thinking）Stage 13+
    - ❌ 剪贴板集成（图片粘贴）Stage 13+

    对应源码：kimi-cli-fork/src/kimi_cli/ui/shell/prompt.py:466-687
    """

    def __init__(
        self,
        *,
        status_provider: Callable[[], "StatusSnapshot"],  # ⭐ Stage 19.1: 必需参数
        model_capabilities: set[str],  # ⭐ Stage 19.1: 必需参数
        initial_thinking: bool = False,  # ⭐ Stage 19.1: 初始 thinking 模式
    ):
        """
        初始化 CustomPromptSession ⭐ Stage 19.1 对齐官方签名

        Args:
            status_provider: 状态提供器回调函数（必需）
            model_capabilities: 模型能力集合（必需）
            initial_thinking: 初始 thinking 模式（默认 False）

        对应源码：kimi-cli-fork/src/kimi_cli/ui/shell/prompt.py:469-485
        """
        self.work_dir = Path.cwd()  # ⭐ Stage 19.1: 始终使用当前目录
        self._status_provider = status_provider
        self._model_capabilities = model_capabilities
        self._initial_thinking = initial_thinking  # ⭐ Stage 19.1: 存储初始状态

        # ============================================================
        # Stage 13：初始化模式状态 ⭐
        # ============================================================
        self._mode = PromptMode.AGENT  # 默认 Agent 模式
        self._thinking = initial_thinking  # ⭐ Thinking 模式状态

        # 状态刷新任务（用于 Toast 超时）
        self._status_refresh_task: asyncio.Task | None = None

        # ⭐ 附件占位符映射（用于图片粘贴）
        self._attachment_parts: dict[str, ContentPart] = {}  # attachment_id -> ContentPart

        # ============================================================
        # 历史记录 ⭐ 对齐官方：JSONL 格式 + InMemoryHistory
        # ============================================================
        from my_cli.share import get_share_dir

        history_dir = get_share_dir() / "user-history"
        history_dir.mkdir(parents=True, exist_ok=True)
        work_dir_id = md5(str(self.work_dir).encode(encoding="utf-8")).hexdigest()
        self._history_file = (history_dir / work_dir_id).with_suffix(".jsonl")
        self._last_history_content: str | None = None

        # 加载历史记录到 InMemoryHistory
        history_entries = _load_history_entries(self._history_file)
        self.history = InMemoryHistory()
        for entry in history_entries:
            self.history.append_string(entry.content)

        # 记录最后一条历史（用于去重）
        if history_entries:
            self._last_history_content = history_entries[-1].content

        # ============================================================
        # Stage 14：创建自动补全器（命令 + 文件）⭐ Stage 19.1: 始终启用
        # ============================================================
        # 合并多个补全器
        self._agent_mode_completer = merge_completers(
            [
                MetaCommandCompleter(),  # 斜杠命令补全
                FileMentionCompleter(self.work_dir),  # ⭐ Stage 14: 文件路径补全
            ],
            deduplicate=True,
        )
        self.completer = self._agent_mode_completer  # 兼容旧代码

        # ============================================================
        # Stage 13：创建自定义键绑定（多行 + 模式切换）⭐
        # ============================================================
        kb = KeyBindings()
        shortcut_hints: list[str] = []  # ⭐ 对齐官方：动态收集快捷键提示

        # ⭐ Stage 22.2: Enter 接受补全（对齐官方 line 508-517）
        @kb.add("enter", filter=has_completions)
        def _accept_completion(event: KeyPressEvent) -> None:
            """当有补全菜单显示时，Enter 接受第一个补全"""
            buff = event.current_buffer
            if buff.complete_state and buff.complete_state.completions:
                # 获取当前选中的补全，如果没有选中则使用第一个
                completion = buff.complete_state.current_completion
                if not completion:
                    completion = buff.complete_state.completions[0]
                buff.apply_completion(completion)

        @kb.add("c-j", eager=True)
        @kb.add("escape", "enter", eager=True)
        def _insert_newline(event: KeyPressEvent) -> None:
            """
            插入换行符（多行输入）⭐ Stage 12

            快捷键：
            - Ctrl+J: 插入换行
            - Alt+Enter: 插入换行（macOS 友好）
            """
            event.current_buffer.insert_text("\n")

        shortcut_hints.append("ctrl-j: newline")

        @kb.add("c-x", eager=True)
        def _toggle_mode(event: KeyPressEvent) -> None:
            """
            切换模式（Agent/Shell）⭐ Stage 13

            快捷键：
            - Ctrl+X: 切换模式
            """
            self._mode = self._mode.toggle()
            # ⭐ 应用模式切换（取消补全菜单等）
            self._apply_mode(event)
            # 重绘 UI（更新状态栏）
            event.app.invalidate()

        shortcut_hints.append("ctrl-x: switch mode")

        # ⭐ Stage 22.2: 剪贴板图片粘贴（对齐官方 line 537-547）
        from my_cli.utils.clipboard import is_clipboard_available

        if is_clipboard_available():
            from prompt_toolkit.clipboard.pyperclip import PyperclipClipboard

            @kb.add("c-v", eager=True)
            def _paste(event: KeyPressEvent) -> None:
                """粘贴剪贴板内容，支持图片"""
                if self._try_paste_image(event):
                    return
                clipboard_data = event.app.clipboard.get_data()
                event.current_buffer.paste_clipboard_data(clipboard_data)

            shortcut_hints.append("ctrl-v: paste")
            clipboard = PyperclipClipboard()
        else:
            clipboard = None

        # ============================================================
        # Stage 21：TAB 切换 Thinking 模式 ⭐ 对齐官方
        # ============================================================
        # 定义条件：当前是 Agent 模式
        is_agent_mode = Condition(lambda: self._mode == PromptMode.AGENT)

        # ⭐ 初始化时显示 thinking 状态（对齐官方 line 555）
        _toast_thinking(self._thinking)

        @kb.add("tab", filter=~has_completions & is_agent_mode, eager=True)
        def _switch_thinking(event: KeyPressEvent) -> None:
            """
            切换 Thinking 模式 ⭐ 对齐官方实现

            快捷键：
            - TAB: 切换 thinking（仅在没有补全菜单且为 Agent 模式时）

            对应源码：kimi-cli-fork/src/kimi_cli/ui/shell/prompt.py:557-567
            """
            from my_cli.ui.shell.console import console

            # 检查模型是否支持 thinking
            if "thinking" not in self._model_capabilities:
                console.print(
                    "[yellow]Thinking mode is not supported by the selected LLM model[/yellow]"
                )
                return

            # 切换 thinking 状态
            self._thinking = not self._thinking

            # 显示 Toast 通知
            _toast_thinking(self._thinking)

            # 重绘 UI
            event.app.invalidate()

        # ⭐ 保存快捷键提示到实例变量（对齐官方 line 569）
        self._shortcut_hints = shortcut_hints

        # ============================================================
        # Stage 14：创建 PromptSession（集成补全优化）⭐
        # ============================================================
        self.session = PromptSession(
            message=self._render_message,  # ⭐ 对齐官方：动态提示符
            history=self.history,
            completer=self._agent_mode_completer,  # ⭐ 自动补全
            complete_while_typing=Condition(
                lambda: self._mode == PromptMode.AGENT
            ),  # ⭐ Stage 14: 只在 AGENT 模式下自动补全
            key_bindings=kb,  # ⭐ 自定义键绑定（多行 + 模式切换）
            clipboard=clipboard,  # ⭐ 对齐官方：剪贴板支持
            multiline=False,  # 默认单行（Ctrl+J 换行）
            enable_history_search=True,  # 启用历史搜索
            bottom_toolbar=self._render_bottom_toolbar,  # ⭐ Stage 13: 状态栏
        )

    def _render_message(self) -> FormattedText:
        """
        渲染提示符 ⭐ 对齐官方实现

        根据模式和 thinking 状态显示不同提示符：
        - Agent 模式: ✨
        - Agent + Thinking: 💫
        - Shell 模式: $

        对应源码：kimi-cli-fork/src/kimi_cli/ui/shell/prompt.py:590-594
        """
        symbol = PROMPT_SYMBOL if self._mode == PromptMode.AGENT else PROMPT_SYMBOL_SHELL
        if self._mode == PromptMode.AGENT and self._thinking:
            symbol = PROMPT_SYMBOL_THINKING
        return FormattedText([("bold", f"{getpass.getuser()}@{Path.cwd().name}{symbol} ")])

    def _append_history_entry(self, text: str) -> None:
        """
        追加历史记录 ⭐ 对齐官方实现

        Args:
            text: 用户输入文本

        对应源码：kimi-cli-fork/src/kimi_cli/ui/shell/prompt.py:724-743
        """
        entry = _HistoryEntry(content=text.strip())
        if not entry.content:
            return

        # 跳过与上一条相同的记录（去重）
        if entry.content == self._last_history_content:
            return

        try:
            self._history_file.parent.mkdir(parents=True, exist_ok=True)
            with self._history_file.open("a", encoding="utf-8") as f:
                f.write(entry.model_dump_json(ensure_ascii=False) + "\n")
            self._last_history_content = entry.content
        except OSError as exc:
            logger.warning(
                "Failed to append user history entry: {file} ({error})",
                file=self._history_file,
                error=exc,
            )

    def _try_paste_image(self, event: KeyPressEvent) -> bool:
        """
        尝试从剪贴板粘贴图片 ⭐ 对齐官方实现

        Args:
            event: 键盘事件

        Returns:
            True 如果成功粘贴图片

        对应源码：kimi-cli-fork/src/kimi_cli/ui/shell/prompt.py:646-687

        注意：需要安装 Pillow 库
        """
        try:
            from PIL import Image, ImageGrab
        except ImportError:
            # PIL 未安装，返回 False 让普通文本粘贴生效
            return False

        # 尝试从剪贴板获取图片
        image = ImageGrab.grabclipboard()
        if isinstance(image, list):
            # 某些平台返回文件路径列表
            for item in image:
                try:
                    with Image.open(item) as img:
                        image = img.copy()
                    break
                except Exception:
                    continue
            else:
                image = None

        if image is None:
            return False

        # 检查模型是否支持图片输入
        if "image_in" not in self._model_capabilities:
            from my_cli.ui.shell.console import console
            console.print("[yellow]Image input is not supported by the selected LLM model[/yellow]")
            return False

        # 生成附件 ID 和占位符
        try:
            from my_cli.utils.string import random_string
        except ImportError:
            import random
            import string
            random_string = lambda n: ''.join(random.choices(string.ascii_letters + string.digits, k=n))

        import base64
        from io import BytesIO

        attachment_id = f"{random_string(8)}.png"
        png_bytes = BytesIO()
        image.save(png_bytes, format="PNG")
        png_base64 = base64.b64encode(png_bytes.getvalue()).decode("ascii")

        # 创建 ImageURLPart（对齐官方）
        from kosong.message import ImageURLPart

        image_part = ImageURLPart(
            image_url=ImageURLPart.ImageURL(
                url=f"data:image/png;base64,{png_base64}",
                id=attachment_id,
            )
        )
        self._attachment_parts[attachment_id] = image_part

        logger.debug(
            "Pasted image from clipboard: {attachment_id}, {image_size}",
            attachment_id=attachment_id,
            image_size=image.size,
        )

        # 插入占位符
        placeholder = f"[image:{attachment_id},{image.width}x{image.height}]"
        event.current_buffer.insert_text(placeholder)
        event.app.invalidate()
        return True

    def _apply_mode(self, event: KeyPressEvent | None = None) -> None:
        """
        应用模式切换 ⭐ 对齐官方实现

        在 Agent/Shell 模式切换时：
        - Shell 模式：取消补全菜单，使用 DummyCompleter
        - Agent 模式：恢复 agent_mode_completer

        对应源码：kimi-cli-fork/src/kimi_cli/ui/shell/prompt.py:596-612
        """
        # 获取当前 buffer
        try:
            buff = event.current_buffer if event is not None else self.session.default_buffer
        except Exception:
            buff = None

        if self._mode == PromptMode.SHELL:
            # Shell 模式：取消补全菜单
            with contextlib.suppress(Exception):
                if buff is not None:
                    buff.cancel_completion()
            if buff is not None:
                buff.completer = DummyCompleter()
        else:
            # Agent 模式：恢复补全器
            if buff is not None:
                buff.completer = self._agent_mode_completer

    def _render_bottom_toolbar(self) -> FormattedText:
        """
        渲染底部状态栏 ⭐ 对齐官方实现

        显示内容：
        - 当前时间（HH:MM 格式）
        - 当前模式（agent/shell）+ thinking 状态
        - Toast 通知或快捷键提示
        - Context 使用率（右对齐）

        Returns:
            FormattedText 对象

        对应源码：kimi-cli-fork/src/kimi_cli/ui/shell/prompt.py:745-788
        """
        # 获取终端宽度
        app = get_app_or_none()
        if app is not None:
            columns = app.output.get_size().columns
        else:
            columns = 80  # 默认宽度

        fragments: list[tuple[str, str]] = []

        # 添加时间
        now_text = datetime.now().strftime("%H:%M")
        fragments.extend([("", now_text), ("", " " * 2)])
        columns -= len(now_text) + 2

        # 添加模式（带 thinking 状态）
        mode_text = str(self._mode).lower()
        if self._mode == PromptMode.AGENT and self._thinking:
            mode_text += " (thinking)"
        fragments.extend([("", mode_text), ("", " " * 2)])
        columns -= len(mode_text) + 2

        # 获取 Context 使用率
        if self._status_provider:
            status = self._status_provider()
            bounded = max(0.0, min(status.context_usage, 1.0))
            status_text = f"context: {bounded:.1%}"
        else:
            status_text = "context: N/A"

        # 显示 Toast 或快捷键提示
        current_toast = _current_toast()
        if current_toast is not None:
            # 显示 Toast 消息
            fragments.extend([("", current_toast.message), ("", " " * 2)])
            columns -= len(current_toast.message) + 2

            # 递减 Toast 时长
            current_toast.duration -= _REFRESH_INTERVAL
            if current_toast.duration <= 0.0:
                _toast_queue.popleft()
        else:
            # 显示快捷键提示（对齐官方：使用 _shortcut_hints + ctrl-d: exit）
            shortcuts = [
                *self._shortcut_hints,
                "ctrl-d: exit",
            ]
            for shortcut in shortcuts:
                if columns - len(status_text) > len(shortcut) + 2:
                    fragments.extend([("", shortcut), ("", " " * 2)])
                    columns -= len(shortcut) + 2
                else:
                    break

        # 右对齐 Context 使用率
        padding = max(1, columns - len(status_text))
        fragments.append(("", " " * padding))
        fragments.append(("", status_text))

        return FormattedText(fragments)

    async def prompt(self) -> UserInput:
        """
        获取用户输入 ⭐ Stage 12 增强版

        新特性：
        - ✅ 支持 Tab 键触发自动补全
        - ✅ 支持 Ctrl+J 插入换行（多行输入）
        - ✅ 支持 Ctrl+R 搜索历史
        - ✅ 支持 Ctrl+X 切换模式 ⭐ Stage 13

        Returns:
            UserInput 对象
        """
        # 获取输入（使用动态提示符）
        user_input = await self.session.prompt_async()
        command = str(user_input).strip()
        command = command.replace("\x00", "")  # ⭐ 对齐官方：移除空字节

        # ⭐ 追加到历史记录（对齐官方）
        self._append_history_entry(command)

        # ⭐ Stage 22.2: 解析附件占位符（对齐官方 line 695-716）
        from kosong.message import ContentPart, TextPart

        content: list[ContentPart] = []
        remaining_command = command

        while match := _ATTACHMENT_PLACEHOLDER_RE.search(remaining_command):
            start, end = match.span()

            # 添加占位符前的文本
            if start > 0:
                content.append(TextPart(text=remaining_command[:start]))

            # 查找附件
            attachment_id = match.group("id")
            part = self._attachment_parts.get(attachment_id)

            if part is not None:
                content.append(part)
            else:
                # 找不到附件，保留占位符文本
                logger.warning(
                    "Attachment placeholder found but no matching attachment part: {placeholder}",
                    placeholder=match.group(0),
                )
                content.append(TextPart(text=match.group(0)))

            remaining_command = remaining_command[end:]

        # 添加剩余文本
        if remaining_command.strip():
            content.append(TextPart(text=remaining_command.strip()))

        # 封装为 UserInput（包含模式、thinking 和富文本内容）
        return UserInput(
            mode=self._mode,
            thinking=self._thinking,
            command=command,
            content=content,
        )

    def __enter__(self):
        """
        上下文管理器：进入 ⭐ 对齐官方实现

        启动状态刷新任务，用于 Toast 超时和状态栏更新。

        对应源码：kimi-cli-fork/src/kimi_cli/ui/shell/prompt.py:614-638
        """
        if self._status_refresh_task is not None and not self._status_refresh_task.done():
            return self

        async def _refresh(interval: float) -> None:
            """定时刷新 UI（用于 Toast 超时）"""
            try:
                while True:
                    app = get_app_or_none()
                    if app is not None:
                        app.invalidate()

                    try:
                        asyncio.get_running_loop()
                    except RuntimeError:
                        self._status_refresh_task = None
                        break

                    await asyncio.sleep(interval)
            except asyncio.CancelledError:
                # 优雅退出
                pass

        self._status_refresh_task = asyncio.create_task(_refresh(_REFRESH_INTERVAL))
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        上下文管理器：退出 ⭐ 对齐官方实现

        取消状态刷新任务。

        对应源码：kimi-cli-fork/src/kimi_cli/ui/shell/prompt.py:640-644
        """
        if self._status_refresh_task is not None and not self._status_refresh_task.done():
            self._status_refresh_task.cancel()
        self._status_refresh_task = None
        self._attachment_parts.clear()  # ⭐ 对齐官方：清理附件


__all__ = [
    "CustomPromptSession",
    "UserInput",
    "PromptMode",
    "MetaCommandCompleter",  # ⭐ Stage 12 新增
    "toast",
    "PROMPT_SYMBOL",
    "PROMPT_SYMBOL_SHELL",
    "PROMPT_SYMBOL_THINKING",
]

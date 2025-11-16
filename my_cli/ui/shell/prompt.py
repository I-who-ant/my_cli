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

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, override

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.document import Document
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.history import FileHistory, InMemoryHistory
from prompt_toolkit.key_binding import KeyBindings, KeyPressEvent

if TYPE_CHECKING:
    from prompt_toolkit.completion import CompleteEvent

# Prompt 符号
PROMPT_SYMBOL = "✨"
PROMPT_SYMBOL_SHELL = "$"
PROMPT_SYMBOL_THINKING = "💫"


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


# ============================================================
# 输入封装 ⭐ Stage 12
# ============================================================


class UserInput:
    """用户输入封装"""

    def __init__(
        self,
        command: str,
        mode: PromptMode = PromptMode.AGENT,  # ⭐ Stage 13: 使用新的 PromptMode
        thinking: bool = False,
    ):
        self.command = command
        self.mode = mode
        self.thinking = thinking

    @property
    def content(self) -> str:
        """获取实际内容（去除特殊前缀）"""
        return self.command


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
        work_dir: Path | None = None,
        enable_file_history: bool = True,
        enable_completer: bool = True,
    ):
        """
        初始化 CustomPromptSession

        Args:
            work_dir: 工作目录（用于历史文件）
            enable_file_history: 是否启用文件历史记录
            enable_completer: 是否启用自动补全 ⭐ Stage 12 新增
        """
        self.work_dir = work_dir or Path.cwd()

        # ============================================================
        # Stage 13：初始化模式状态 ⭐
        # ============================================================
        self._mode = PromptMode.AGENT  # 默认 Agent 模式

        # 创建历史记录
        if enable_file_history:
            # 文件历史（持久化）
            history_file = self.work_dir / ".mycli_history"
            self.history = FileHistory(str(history_file))
        else:
            # 内存历史（临时）
            self.history = InMemoryHistory()

        # ============================================================
        # Stage 12：创建自动补全器 ⭐
        # ============================================================
        if enable_completer:
            # 斜杠命令补全
            self.completer = MetaCommandCompleter()
        else:
            self.completer = None

        # ============================================================
        # Stage 13：创建自定义键绑定（多行 + 模式切换）⭐
        # ============================================================
        kb = KeyBindings()

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

        @kb.add("c-x", eager=True)
        def _toggle_mode(event: KeyPressEvent) -> None:
            """
            切换模式（Agent/Shell）⭐ Stage 13

            快捷键：
            - Ctrl+X: 切换模式
            """
            self._mode = self._mode.toggle()
            # 重绘 UI（更新状态栏）
            event.app.invalidate()

        # ============================================================
        # Stage 13：创建 PromptSession（集成状态栏）⭐
        # ============================================================
        self.session = PromptSession(
            history=self.history,
            completer=self.completer,  # ⭐ 自动补全
            key_bindings=kb,  # ⭐ 自定义键绑定（多行 + 模式切换）
            multiline=False,  # 默认单行（Ctrl+J 换行）
            enable_history_search=True,  # 启用历史搜索
            bottom_toolbar=self._render_bottom_toolbar,  # ⭐ Stage 13: 状态栏
        )

    def _render_bottom_toolbar(self) -> FormattedText:
        """
        渲染底部状态栏 ⭐ Stage 13

        显示内容：
        - 当前时间（HH:MM 格式）
        - 当前模式（agent/shell）
        - 快捷键提示

        Returns:
            FormattedText 对象

        TODO (Stage 14+):
        - 添加 Thinking 状态显示
        - 添加 Context 使用率
        - 添加当前模型名称
        - 支持自定义主题颜色
        """
        fragments: list[tuple[str, str]] = []

        # 添加时间
        now_text = datetime.now().strftime("%H:%M")
        fragments.extend([("", now_text), ("", " " * 2)])

        # 添加模式（颜色区分）
        mode_text = str(self._mode).lower()
        mode_style = "bg:#ff6b6b" if self._mode == PromptMode.SHELL else "bg:#4ecdc4"
        fragments.extend([(mode_style, f" {mode_text} "), ("", " " * 2)])

        # 添加快捷键提示
        fragments.append(("class:bottom-toolbar.text", "ctrl-x: 切换模式  ctrl-d: 退出"))

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
        # 获取输入（支持自动补全）
        user_input = await self.session.prompt_async(
            f"{PROMPT_SYMBOL} You: ",
            # enable_suspend=True,  # 允许 Ctrl+Z 挂起（可选）
        )

        # 封装为 UserInput
        return UserInput(command=user_input.strip())

    def __enter__(self):
        """上下文管理器：进入"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器：退出"""
        # 清理资源（如果需要）
        pass


def toast(message: str) -> None:
    """
    显示 Toast 通知

    Stage 11：简化版，直接打印
    官方版：使用 rich 的 Live 显示临时消息
    """
    from my_cli.ui.shell.console import console

    console.print(f"[grey50]💡 {message}[/grey50]")


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

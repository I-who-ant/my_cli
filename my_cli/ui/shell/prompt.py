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

import os
import re
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, override

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion, merge_completers
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
        # Stage 14：创建自动补全器（命令 + 文件）⭐
        # ============================================================
        if enable_completer:
            # 合并多个补全器
            self.completer = merge_completers(
                [
                    MetaCommandCompleter(),  # 斜杠命令补全
                    FileMentionCompleter(self.work_dir),  # ⭐ Stage 14: 文件路径补全
                ]
            )
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

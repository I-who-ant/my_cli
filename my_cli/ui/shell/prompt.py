"""
Shell UI Prompt 模块（输入处理）

职责：
1. CustomPromptSession - 自定义输入会话
2. 命令历史记录
3. 输入模式切换（Normal/Shell/Thinking）
4. 状态栏显示

对应源码：kimi-cli-fork/src/kimi_cli/ui/shell/prompt.py (600+行)

为什么单独分离？
1. 输入处理是独立的复杂子系统
2. 涉及 prompt_toolkit 的深度定制
3. 包含多种补全器、键绑定、状态管理
4. 代码量大（600+ 行），拆分利于维护

Stage 11 实现：
- 简化版，基础 PromptSession + 历史记录
- 官方版还包括：
  * FileMentionCompleter（文件路径补全）
  * MetaCommandCompleter（斜杠命令补全）
  * 多模式切换（Normal/Shell/Thinking）
  * 状态栏显示（Model、Thinking、Status）
  * 剪贴板集成（图片粘贴）
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory, InMemoryHistory

if TYPE_CHECKING:
    pass

# Prompt 符号
PROMPT_SYMBOL = "✨"
PROMPT_SYMBOL_SHELL = "$"
PROMPT_SYMBOL_THINKING = "💫"


class PromptMode(Enum):
    """输入模式"""

    NORMAL = "normal"  # 普通模式（发送到 LLM）
    SHELL = "shell"  # Shell 模式（执行 Shell 命令）
    THINKING = "thinking"  # 思考模式（启用 Thinking）


class UserInput:
    """用户输入封装"""

    def __init__(
        self,
        command: str,
        mode: PromptMode = PromptMode.NORMAL,
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
    自定义 PromptSession

    Stage 11 简化版特性：
    - ✅ 命令历史记录（FileHistory）
    - ✅ 基础输入处理
    - ❌ 自动补全（Stage 12+）
    - ❌ 多模式切换（Stage 12+）
    - ❌ 状态栏显示（Stage 12+）
    """

    def __init__(
        self,
        work_dir: Path | None = None,
        enable_file_history: bool = True,
    ):
        """
        初始化 CustomPromptSession

        Args:
            work_dir: 工作目录（用于历史文件）
            enable_file_history: 是否启用文件历史记录
        """
        self.work_dir = work_dir or Path.cwd()

        # 创建历史记录
        if enable_file_history:
            # 文件历史（持久化）
            history_file = self.work_dir / ".mycli_history"
            self.history = FileHistory(str(history_file))
        else:
            # 内存历史（临时）
            self.history = InMemoryHistory()

        # 创建 PromptSession
        self.session = PromptSession(history=self.history)

    async def prompt(self) -> UserInput:
        """
        获取用户输入

        Returns:
            UserInput 对象
        """
        # 获取输入
        user_input = await self.session.prompt_async(f"{PROMPT_SYMBOL} You: ")

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
    "toast",
    "PROMPT_SYMBOL",
    "PROMPT_SYMBOL_SHELL",
    "PROMPT_SYMBOL_THINKING",
]

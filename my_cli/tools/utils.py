"""
Stage 7 增强：工具辅助函数

功能：
1. load_desc() - 从 Markdown 文件加载工具描述
2. ToolResultBuilder - 工具结果构建器（输出限制）
3. ToolRejectedError - 用户拒绝错误
4. truncate_line() - 行截断工具

对应源码：kimi-cli-fork/src/kimi_cli/tools/utils.py
"""

import re
import string
from pathlib import Path

from kosong.tooling import ToolError, ToolOk

__all__ = [
    "load_desc",
    "truncate_line",
    "ToolResultBuilder",
    "ToolRejectedError",
    "DEFAULT_MAX_CHARS",
    "DEFAULT_MAX_LINE_LENGTH",
]

# ============================================================
# 默认输出限制
# ============================================================

DEFAULT_MAX_CHARS = 50_000
"""默认最大字符数（50K）"""

DEFAULT_MAX_LINE_LENGTH = 2000
"""默认最大行长度（2000字符）"""


# ============================================================
# 工具描述加载器
# ============================================================


def load_desc(path: Path, substitutions: dict[str, str] | None = None) -> str:
    """
    从文件加载工具描述（支持模板替换）

    Args:
        path: 描述文件路径（通常是 .md 文件）
        substitutions: 模板变量替换字典（可选）

    Returns:
        工具描述字符串

    示例：
        # bash.md 内容：
        # Execute a bash command.
        # Timeout: $timeout seconds

        desc = load_desc(
            Path("bash.md"),
            substitutions={"timeout": "60"}
        )
        # → "Execute a bash command.\nTimeout: 60 seconds"
    """
    description = path.read_text(encoding="utf-8")

    # 如果提供了替换字典，执行模板替换
    if substitutions:
        description = string.Template(description).substitute(substitutions)

    return description


# ============================================================
# 行截断工具
# ============================================================


def truncate_line(line: str, max_length: int, marker: str = "...") -> str:
    """
    截断过长的行（保留开头和换行符）

    Args:
        line: 要截断的行
        max_length: 最大长度
        marker: 截断标记（默认 "..."）

    Returns:
        截断后的行

    示例：
        truncate_line("very long line\\n", 10, "...")
        # → "very l...\\n"
    """
    if len(line) <= max_length:
        return line

    # 查找行尾的换行符
    m = re.search(r"[\r\n]+$", line)
    linebreak = m.group(0) if m else ""

    # 构建截断后的结尾
    end = marker + linebreak
    max_length = max(max_length, len(end))

    # 截断并添加标记
    return line[: max_length - len(end)] + end


# ============================================================
# 工具结果构建器
# ============================================================


class ToolResultBuilder:
    """
    工具结果构建器 - 自动限制输出大小

    功能：
    - 限制总字符数（默认 50K）
    - 限制单行长度（默认 2K）
    - 自动截断过长内容
    - 添加截断提示

    示例：
        builder = ToolResultBuilder(max_chars=10_000)

        # 写入输出
        for line in output_lines:
            builder.write(line)

        # 生成结果（自动添加截断提示）
        if success:
            return builder.ok("Command executed.")
        else:
            return builder.error("Command failed.", brief="Failed")
    """

    def __init__(
        self,
        max_chars: int = DEFAULT_MAX_CHARS,
        max_line_length: int | None = DEFAULT_MAX_LINE_LENGTH,
    ):
        """
        初始化构建器

        Args:
            max_chars: 最大字符数（默认 50K）
            max_line_length: 最大行长度（默认 2K，None 表示不限制）
        """
        self.max_chars = max_chars
        self.max_line_length = max_line_length
        self._marker = "[...truncated]"

        if max_line_length is not None:
            assert max_line_length > len(
                self._marker
            ), "max_line_length must be greater than marker length"

        self._buffer: list[str] = []
        self._n_chars = 0
        self._n_lines = 0
        self._truncation_happened = False

    def write(self, text: str) -> int:
        """
        写入文本到输出缓冲区（自动截断）

        Args:
            text: 要写入的文本

        Returns:
            实际写入的字符数

        示例：
            builder.write("line 1\\n")
            builder.write("line 2\\n")
        """
        if self.is_full:
            return 0

        lines = text.splitlines(keepends=True)
        if not lines:
            return 0

        chars_written = 0

        for line in lines:
            if self.is_full:
                break

            original_line = line

            # 计算剩余字符数
            remaining_chars = self.max_chars - self._n_chars

            # 计算行长度限制
            limit = (
                min(remaining_chars, self.max_line_length)
                if self.max_line_length is not None
                else remaining_chars
            )

            # 截断行
            line = truncate_line(line, limit, self._marker)

            if line != original_line:
                self._truncation_happened = True

            # 写入缓冲区
            self._buffer.append(line)
            chars_written += len(line)
            self._n_chars += len(line)

            if line.endswith("\n"):
                self._n_lines += 1

        return chars_written

    def ok(self, message: str = "", *, brief: str = "") -> ToolOk:
        """
        生成 ToolOk 结果（自动添加截断提示）

        Args:
            message: 给 LLM 的消息
            brief: 给用户的简短消息

        Returns:
            ToolOk 结果

        示例:
            return builder.ok("File read successfully.", brief="Read 1024 bytes")
        """
        output = "".join(self._buffer)

        # 自动添加句号
        final_message = message
        if final_message and not final_message.endswith("."):
            final_message += "."

        # 添加截断提示
        truncation_msg = "Output is truncated to fit in the message."
        if self._truncation_happened:
            if final_message:
                final_message += f" {truncation_msg}"
            else:
                final_message = truncation_msg

        return ToolOk(output=output, message=final_message, brief=brief)

    def error(self, message: str, *, brief: str) -> ToolError:
        """
        生成 ToolError 结果（自动添加截断提示）

        Args:
            message: 错误消息（给 LLM）
            brief: 简短错误消息（给用户）

        Returns:
            ToolError 结果

        示例:
            return builder.error("Command failed with exit code 1", brief="Failed")
        """
        output = "".join(self._buffer)

        # 添加截断提示
        final_message = message
        if self._truncation_happened:
            truncation_msg = "Output is truncated to fit in the message."
            if final_message:
                final_message += f" {truncation_msg}"
            else:
                final_message = truncation_msg

        return ToolError(output=output, message=final_message, brief=brief)

    @property
    def is_full(self) -> bool:
        """检查缓冲区是否已满"""
        return self._n_chars >= self.max_chars

    @property
    def n_chars(self) -> int:
        """获取当前字符数"""
        return self._n_chars

    @property
    def n_lines(self) -> int:
        """获取当前行数"""
        return self._n_lines


# ============================================================
# 用户拒绝错误
# ============================================================


class ToolRejectedError(ToolError):
    """
    工具被用户拒绝的错误

    用于 Stage 8+ 的批准机制：

    示例：
        # 请求用户批准
        if not await approval.request("Bash", "run command", "rm -rf /"):
            return ToolRejectedError()  # ⭐ 用户拒绝

        # LLM 会收到拒绝消息并调整策略
    """

    def __init__(self):
        super().__init__(
            message=(
                "The tool call is rejected by the user. "
                "Please follow the new instructions from the user."
            ),
            brief="Rejected by user",
        )

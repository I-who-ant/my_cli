"""
Logging Utils - 日志工具

学习目标：
1. 理解日志系统配置
2. 理解 StreamToLogger 的作用

对应源码：kimi-cli-fork/src/kimi_cli/utils/logging.py

阶段演进：
- Stage 4-16：基础日志配置
- Stage 18：完整的日志系统 ⭐
"""

from __future__ import annotations

from typing import IO

from loguru import logger

# 移除默认的日志处理器
logger.remove()


class StreamToLogger(IO[str]):
    """将流（stdout/stderr）输出重定向到日志系统

    Args:
        level: 日志级别（DEBUG, INFO, WARNING, ERROR, CRITICAL）

    对应源码：kimi-cli-fork/src/kimi_cli/utils/logging.py:10-20
    """

    def __init__(self, level: str = "ERROR"):
        self._level = level

    def write(self, buffer: str) -> int:
        for line in buffer.rstrip().splitlines():
            logger.opt(depth=1).log(self._level, line.rstrip())
        return len(buffer)

    def flush(self) -> None:
        pass

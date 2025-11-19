"""
Utils 模块：通用工具和扩展

职责：提供跨模块复用的工具函数和组件扩展

对应源码：kimi-cli-fork/src/kimi_cli/utils/

子模块：
- logging: 日志系统配置
- path: 路径工具函数（文件旋转、目录操作）
- rich: Rich 库的扩展和配置
"""

__all__ = []

# Stage 18：新加工具函数
from my_cli.utils.logging import StreamToLogger
from my_cli.utils.path import (
    next_available_rotation,
    list_directory,
    shorten_home,
)

__all__.extend([
    "StreamToLogger",
    "next_available_rotation",
    "list_directory",
    "shorten_home",
])

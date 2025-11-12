"""
工具模块 - 注册所有可用工具

学习目标：
1. 理解工具注册表模式
2. OpenAI Function Calling 参数格式
3. 工具元数据管理

对应源码：kimi-cli-fork/src/kimi_cli/tools/
"""

from my_cli.tools.read_file import read_file
from my_cli.tools.shell import execute_shell
from my_cli.tools.write_file import write_file

# 工具注册表
# 这个字典定义了所有可用的工具及其元数据
# 格式遵循 OpenAI Function Calling 规范
TOOLS = {
    "shell": {
        "function": execute_shell,
        "description": "Execute a shell command and return the output. Use this for system operations like listing files, running scripts, etc.",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The shell command to execute (e.g., 'ls -la', 'git status')",
                },
                "timeout": {
                    "type": "number",
                    "description": "Timeout in seconds (default: 30.0)",
                    "default": 30.0,
                },
            },
            "required": ["command"],
        },
    },
    "read_file": {
        "function": read_file,
        "description": "Read file contents with line numbers. Useful for inspecting code or text files.",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the file to read (can be relative or absolute)",
                },
                "offset": {
                    "type": "integer",
                    "description": "Starting line number (0-indexed, default: 0)",
                    "default": 0,
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of lines to read (default: 2000)",
                    "default": 2000,
                },
            },
            "required": ["file_path"],
        },
    },
    "write_file": {
        "function": write_file,
        "description": "Write content to a file. Creates parent directories if needed. Overwrites existing files.",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the file to write (can be relative or absolute)",
                },
                "content": {
                    "type": "string",
                    "description": "Content to write to the file",
                },
            },
            "required": ["file_path", "content"],
        },
    },
}


def get_tool_schemas():
    """获取工具的 schema 列表（用于 LLM API 调用）.

    Returns:
        符合 OpenAI Function Calling 格式的工具列表
    """
    return [
        {
            "type": "function",
            "function": {
                "name": name,
                "description": tool["description"],
                "parameters": tool["parameters"],
            },
        }
        for name, tool in TOOLS.items()
    ]


__all__ = ["TOOLS", "get_tool_schemas", "execute_shell", "read_file", "write_file"]
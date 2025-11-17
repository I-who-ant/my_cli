"""
Stage 7: 工具系统（Toolset）

学习目标：
1. 理解 kosong 的工具系统架构
2. 理解 CallableTool2 的实现模式
3. 理解工具注册和调用流程
4. 实现基础工具（Bash、ReadFile、WriteFile）

对应源码：kimi-cli-fork/src/kimi_cli/tools/

核心概念：
- Tool: 工具定义（name + description + parameters）
- CallableTool2: 可调用工具基类（带类型参数）
- ToolReturnType: 工具返回类型（ToolOk | ToolError）
- Toolset: 工具集协议（注册和调度工具）

阶段演进：
- Stage 7：基础工具系统 ✅
- Stage 17：extract_key_argument() 函数（UI 显示关键参数）⭐ 当前
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import cast

from kosong.utils.typing import JsonType

__all__ = ["SkipThisTool", "extract_key_argument"]


class SkipThisTool(Exception):
    """工具跳过异常（工具决定不加载自己时抛出）"""

    pass


def extract_key_argument(json_content: str, tool_name: str) -> str | None:
    """
    从工具调用参数中提取关键参数 ⭐ Stage 17

    这个函数用于从工具调用的 JSON 参数中提取最关键的参数，用于 UI 显示。

    官方实现要点：
    1. 解析 JSON 参数（支持 streamingjson.Lexer 流式解析）
    2. 根据工具名称提取关键参数：
       - Bash/CMD: command
       - ReadFile/WriteFile/StrReplaceFile: path（归一化路径）
       - Glob: pattern
       - Grep: pattern
       - SearchWeb: query
       - FetchURL: url
       - Task: description
       - Think: thought
       - SendDMail: "El Psy Kongroo"（固定文本）
       - SetTodoList: None
       - 其他工具: 完整 JSON 字符串
    3. 使用 shorten_middle() 缩短参数（最多 50 字符）

    简化版实现：
    - 不支持 streamingjson.Lexer（Stage 7-16 只支持字符串）
    - 不使用 shorten_middle()（简化版直接返回）
    - 只支持基础工具（Bash、ReadFile、WriteFile）

    Args:
        json_content: 工具调用参数的 JSON 字符串
        tool_name: 工具名称

    Returns:
        str | None: 提取的关键参数，如果无法提取则返回 None

    对应源码：kimi-cli-fork/src/kimi_cli/tools/__init__.py:17-82
    """
    # 简化版（Stage 17）：只支持字符串解析
    try:
        curr_args: JsonType = json.loads(json_content)
    except json.JSONDecodeError:
        return None

    if not curr_args:
        return None

    key_argument: str = ""

    # 根据工具名称提取关键参数
    match tool_name:
        # 命令执行工具
        case "Bash" | "CMD":
            if not isinstance(curr_args, dict) or not curr_args.get("command"):
                return None
            key_argument = str(curr_args["command"])

        # 文件操作工具
        case "ReadFile":
            if not isinstance(curr_args, dict) or not curr_args.get("path"):
                return None
            key_argument = _normalize_path(str(curr_args["path"]))

        case "WriteFile" | "StrReplaceFile":
            if not isinstance(curr_args, dict) or not curr_args.get("path"):
                return None
            key_argument = _normalize_path(str(curr_args["path"]))

        # 搜索工具
        case "Glob":
            if not isinstance(curr_args, dict) or not curr_args.get("pattern"):
                return None
            key_argument = str(curr_args["pattern"])

        case "Grep":
            if not isinstance(curr_args, dict) or not curr_args.get("pattern"):
                return None
            key_argument = str(curr_args["pattern"])

        # 网络工具（Stage 17+ 扩展）
        case "SearchWeb":
            if not isinstance(curr_args, dict) or not curr_args.get("query"):
                return None
            key_argument = str(curr_args["query"])

        case "FetchURL":
            if not isinstance(curr_args, dict) or not curr_args.get("url"):
                return None
            key_argument = str(curr_args["url"])

        # 高级工具（Stage 17+ 扩展）
        case "Task":
            if not isinstance(curr_args, dict) or not curr_args.get("description"):
                return None
            key_argument = str(curr_args["description"])

        case "Think":
            if not isinstance(curr_args, dict) or not curr_args.get("thought"):
                return None
            key_argument = str(curr_args["thought"])

        case "SendDMail":
            return "El Psy Kongroo"  # 固定文本（彩蛋）

        case "SetTodoList":
            return None  # 不显示参数

        # 默认：返回完整 JSON 字符串
        case _:
            key_argument = json_content

    # 简化版：不使用 shorten_middle()（官方会缩短到 50 字符）
    # 如果需要缩短，可以添加：
    # from kimi_cli.utils.string import shorten_middle
    # key_argument = shorten_middle(key_argument, width=50)

    return key_argument


def _normalize_path(path: str) -> str:
    """
    归一化路径（移除 CWD 前缀）⭐ Stage 17

    这个函数用于简化文件路径显示，将绝对路径转换为相对路径。

    Args:
        path: 文件路径

    Returns:
        str: 归一化后的路径

    对应源码：kimi-cli-fork/src/kimi_cli/tools/__init__.py:85-89
    """
    cwd = str(Path.cwd().absolute())

    # 如果路径以 CWD 开头，移除 CWD 前缀
    if path.startswith(cwd):
        path = path[len(cwd) :].lstrip("/\\")

    return path

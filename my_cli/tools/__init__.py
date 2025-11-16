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
"""

from __future__ import annotations

__all__ = ["SkipThisTool"]


class SkipThisTool(Exception):
    """工具跳过异常（工具决定不加载自己时抛出）"""

    pass

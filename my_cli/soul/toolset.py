"""
自定义 Toolset - 工具调用上下文管理

学习目标：
1. 理解 ContextVar 在工具系统中的应用
2. 理解 CustomToolset 如何扩展 SimpleToolset
3. 理解 current_tool_call 的作用

对应源码：kimi-cli-fork/src/kimi_cli/soul/toolset.py

阶段演进：
- Stage 8：使用 SimpleToolset ✅
- Stage 17：实现 CustomToolset（支持 current_tool_call）⭐ 当前
"""

from __future__ import annotations

from contextvars import ContextVar
from typing import override

from kosong.message import ToolCall
from kosong.tooling import HandleResult
from kosong.tooling.simple import SimpleToolset

# ============================================================
# ContextVar: 当前工具调用上下文 ⭐ Stage 17
# ============================================================

current_tool_call = ContextVar[ToolCall | None]("current_tool_call", default=None)
"""
当前工具调用的 ContextVar

这个 ContextVar 用于在工具的 __call__ 方法中获取当前工具调用信息。

使用场景：
- 工具需要知道自己的 tool_call_id
- 工具需要知道调用参数
- Approval 系统需要知道是哪个工具在请求批准

对应源码：kimi-cli-fork/src/kimi_cli/soul/toolset.py:9
"""


def get_current_tool_call_or_none() -> ToolCall | None:
    """
    获取当前工具调用（如果存在）⭐ Stage 17

    这个函数在工具的 __call__ 方法中调用时，返回当前的 ToolCall。
    如果不在工具调用上下文中，返回 None。

    Returns:
        ToolCall | None: 当前工具调用，如果不在工具调用上下文中则返回 None

    使用示例：
        class MyTool:
            def __call__(self, param: str) -> str:
                tool_call = get_current_tool_call_or_none()
                if tool_call:
                    print(f"Tool call ID: {tool_call.id}")
                return "result"

    对应源码：kimi-cli-fork/src/kimi_cli/soul/toolset.py:12-17
    """
    return current_tool_call.get()


# ============================================================
# CustomToolset - 扩展 SimpleToolset ⭐ Stage 17
# ============================================================


class CustomToolset(SimpleToolset):
    """
    自定义 Toolset - 支持 current_tool_call 上下文 ⭐ Stage 17

    这个类扩展了 SimpleToolset，在工具调用时设置 current_tool_call。

    官方实现要点：
    1. 重写 handle() 方法
    2. 在调用 super().handle() 前设置 current_tool_call
    3. 在调用后重置 current_tool_call

    使用场景：
    - Approval 系统需要 tool_call_id
    - 工具需要访问自己的调用信息

    对应源码：kimi-cli-fork/src/kimi_cli/soul/toolset.py:20-28
    """

    @override
    def handle(self, tool_call: ToolCall) -> HandleResult:
        """
        处理工具调用，设置 current_tool_call 上下文 ⭐ Stage 17

        流程：
        1. 使用 current_tool_call.set() 设置当前工具调用
        2. 调用 super().handle() 执行工具
        3. 使用 current_tool_call.reset() 重置上下文

        Args:
            tool_call: 工具调用

        Returns:
            HandleResult: 工具处理结果

        对应源码：kimi-cli-fork/src/kimi_cli/soul/toolset.py:22-28
        """
        # ⭐ Stage 17 完整实现（官方做法）
        token = current_tool_call.set(tool_call)
        try:
            return super().handle(tool_call)
        finally:
            current_tool_call.reset(token)


# ============================================================
# TODO: Stage 17+ 扩展说明
# ============================================================
# Stage 17（Approval 系统集成）需要：
# 1. 将 create_soul() 中的 SimpleToolset 替换为 CustomToolset
# 2. 在需要 tool_call_id 的工具中使用 get_current_tool_call_or_none()
#
# Stage 8-16 简化版：
# - 使用 SimpleToolset（已在 my_cli/tools/toolset.py 实现）
# - 不需要 current_tool_call 上下文
# ============================================================

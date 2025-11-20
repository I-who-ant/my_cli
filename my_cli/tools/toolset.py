"""
Stage 7-8: 简单Toolset实现（修复版）

学习目标：
1. 理解Toolset协议（tools 属性 + handle 方法）⭐ Stage 8
2. 理解工具注册和调度
3. 实现符合 kosong Toolset 协议的工具管理器

对应源码：kosong的Toolset协议 + 官方SimpleToolset实现
"""

from __future__ import annotations

import asyncio
from collections.abc import Sequence

from kosong.message import ToolCall
from kosong.tooling import CallableTool2, Tool, ToolResult, ToolResultFuture, HandleResult

from my_cli.tools.bash import Bash
from my_cli.tools.file import ReadFile, WriteFile
from my_cli.tools.think import Think  # ⭐ Stage 21: 导入 Think 工具

__all__ = ["SimpleToolset"]


class SimpleToolset:
    """
    简单工具集实现（符合 kosong Toolset 协议）

    Stage 8 修复版：
    - ✅ 实现 tools 属性（而非 get_tools() 方法）
    - ✅ 实现同步 handle() 方法（返回 HandleResult）
    - ✅ 异步执行工具（使用 asyncio.create_task）

    Toolset 协议要求：
    - @property tools: list[Tool]  # 工具定义列表
    - def handle(tool_call) -> HandleResult  # 同步方法返回 Future 或 Result

    对应官方：kosong-main/src/kosong/tooling/simple.py:SimpleToolset
    """

    def __init__(self):
        """初始化工具集"""
        # 创建工具实例
        self._tool_instances: dict[str, CallableTool2] = {
            "Bash": Bash(),
            "ReadFile": ReadFile(),
            "WriteFile": WriteFile(),
            "Think": Think(),  # ⭐ Stage 21: 注册 Think 工具
        }

    @property
    def tools(self) -> list[Tool]:
        """
        获取所有工具定义（给 LLM）⭐ Stage 8 修复

        注意：这是 Toolset 协议要求的属性，不是方法！

        Returns:
            工具定义列表
        """
        return [tool.base for tool in self._tool_instances.values()]

    def handle(self, tool_call: ToolCall) -> HandleResult:
        """
        处理工具调用（同步方法，返回 Future）⭐ Stage 8 修复

        注意：
        - 这是同步方法（不是 async）
        - 返回 ToolResultFuture（Future[ToolResult]）
        - 工具异步执行在后台进行
        - ToolCall 结构：tool_call.function.name 和 tool_call.function.arguments ⭐

        Args:
            tool_call: 工具调用请求

        Returns:
            ToolResultFuture: 工具执行结果的 Future
        """
        # ⭐ 修复：ToolCall 是嵌套结构 tool_call.function.name
        tool_name = tool_call.function.name

        # 创建 Future
        future: ToolResultFuture = ToolResultFuture()

        # 查找工具
        if tool_name not in self._tool_instances:
            from kosong.tooling import ToolError

            # 工具不存在，立即设置错误结果
            future.set_result(
                ToolResult(
                    tool_call_id=tool_call.id,
                    result=ToolError(
                        message=f"Tool not found: {tool_name}",
                        brief="Tool not found",
                    ),
                )
            )
            return future

        # 异步执行工具
        tool = self._tool_instances[tool_name]

        async def _execute_tool():
            """异步执行工具并设置 Future 结果"""
            try:
                # ⭐ 修复：参数在 tool_call.function.arguments（JSON 字符串）
                import json

                arguments_str = tool_call.function.arguments
                arguments = json.loads(arguments_str) if arguments_str else {}

                result = await tool.call(arguments)
                tool_result = ToolResult(tool_call_id=tool_call.id, result=result)
                future.set_result(tool_result)
            except asyncio.CancelledError:
                # 取消：传播取消
                future.cancel()
                raise
            except Exception as e:
                # 其他异常：转换为 ToolError
                from kosong.tooling import ToolError

                future.set_result(
                    ToolResult(
                        tool_call_id=tool_call.id,
                        result=ToolError(
                            message=f"Tool execution failed: {e}",
                            brief="Execution failed",
                        ),
                    )
                )

        # 启动异步任务
        asyncio.create_task(_execute_tool())

        return future

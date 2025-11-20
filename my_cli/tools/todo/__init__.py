"""
Stage 21.3: SetTodoList 工具实现

功能：设置和更新待办事项列表

学习要点：
1. 使用 Literal 类型限制枚举值
2. 嵌套 Pydantic 模型（Todo 模型）
3. 格式化输出（Markdown）

对应设计：LEARNING_WORKFLOW3.md Stage 21
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal, override

from kosong.tooling import CallableTool2, ToolOk, ToolReturnType
from pydantic import BaseModel, Field

from my_cli.tools.utils import load_desc

# 工具名称
NAME = "SetTodoList"


class Todo(BaseModel):
    """单个 Todo 项

    Attributes:
        title: 任务标题
        status: 任务状态（Pending/In Progress/Done）
    """

    title: str = Field(description="The title of the todo", min_length=1)
    status: Literal["Pending", "In Progress", "Done"] = Field(
        description="The status of the todo"
    )


class SetTodoListParams(BaseModel):
    """SetTodoList 工具参数

    Attributes:
        todos: 待办事项列表
    """

    todos: list[Todo] = Field(description="The updated todo list")


class SetTodoList(CallableTool2[SetTodoListParams]):
    """
    SetTodoList 工具 - 设置待办事项列表

    特点：
    1. 支持三种状态：Pending、In Progress、Done
    2. 格式化输出为 Markdown
    3. 完整替换 todo 列表（非追加）

    使用场景：
    - 规划工作（拆分复杂任务）
    - 跟踪进度（监控完成情况）
    - 组织任务（优先级管理）
    - 展示状态（向用户沟通进度）

    示例：
        SetTodoList(todos=[
            {"title": "Read requirements", "status": "Done"},
            {"title": "Design schema", "status": "In Progress"},
            {"title": "Implement API", "status": "Pending"}
        ])
    """

    name: str = NAME
    description: str = load_desc(Path(__file__).parent / "set_todo_list.md")
    params: type[SetTodoListParams] = SetTodoListParams

    def __init__(self, **kwargs: Any) -> None:
        """初始化 SetTodoList 工具

        Args:
            **kwargs: 传递给父类的参数
        """
        super().__init__(**kwargs)

    @override
    async def __call__(self, params: SetTodoListParams) -> ToolReturnType:
        """执行 SetTodoList 工具

        Args:
            params: 工具参数（包含 todos 列表）

        Returns:
            ToolOk: 格式化的 todo 列表

        实现说明：
        - 根据状态格式化：Done（删除线）、In Progress（粗体）、Pending（普通）
        - 返回 Markdown 格式的列表
        - brief 字段包含渲染后的列表（供 UI 显示）
        """
        # 格式化 todo 列表为 Markdown
        rendered = ""
        for todo in params.todos:
            match todo.status:
                case "Done":
                    # 完成的任务：删除线
                    rendered += f"- ~~{todo.title}~~ [{todo.status}]\n"
                case "In Progress":
                    # 进行中的任务：粗体
                    rendered += f"- **{todo.title}** [{todo.status}]\n"
                case _:
                    # 待办任务：普通文本
                    rendered += f"- {todo.title} [{todo.status}]\n"

        return ToolOk(
            output="",
            message="Todo list updated",
            brief=rendered,
        )


# 导出工具类
__all__ = ["SetTodoList", "SetTodoListParams", "Todo", "NAME"]

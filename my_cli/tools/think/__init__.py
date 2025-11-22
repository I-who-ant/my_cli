"""
Stage 21.1: Think 工具实现

功能：让 Agent 展示思考过程，提升透明度

学习要点：
1. 最简单的 CallableTool2 实现
2. 单参数工具（thought: str）
3. 直接返回 ToolResult

对应设计：LEARNING_WORKFLOW3.md Stage 21
"""

from pathlib import Path
from typing import Any, override

from kosong.tooling import CallableTool2, ToolOk, ToolReturnType
from pydantic import BaseModel, Field

from my_cli.tools.utils import load_desc

# 工具名称（供外部引用）
NAME = "Think"


class ThinkParams(BaseModel):
    """Think 工具参数

    Attributes:
        thought: Agent 的思考内容
    """

    thought: str = Field(
        description="Your internal reasoning or thought process that you want to share with the user"
    )


class Think(CallableTool2[ThinkParams]):
    """
    Think 工具 - 展示 Agent 思考过程

    这是最简单的工具实现：
    1. 接收思考内容（thought）
    2. 返回 ToolResult 展示给用户
    3. 不需要任何外部依赖

    使用场景：
    - 复杂问题分析
    - 决策过程说明
    - 多步骤任务规划
    - 展示不同方案的权衡

    示例：
        Think(thought="我需要先读取配置文件，然后分析项目结构...")
    """

    name: str = NAME
    description: str = load_desc(Path(__file__).parent / "think.md")
    params: type[ThinkParams] = ThinkParams

    def __init__(self, **kwargs: Any) -> None:
        """初始化 Think 工具

        Args:
            **kwargs: 传递给父类的参数
        """
        super().__init__(**kwargs)

    @override
    async def __call__(self, params: ThinkParams) -> ToolReturnType:
        """执行 Think 工具

        Args:
            params: 工具参数（包含 thought）

        Returns:
            ToolOk: 包含思考内容的结果

        实现说明：
        - 最简单的实现：返回 ToolOk
        - 通过 Wire 机制，这个内容会被发送到 UI 层展示
        - 用户可以看到 Agent 的思考过程
        """
        # 官方实现：返回 ToolOk，message 会被显示
        return ToolOk(output="", message=f"💭 Thinking: {params.thought}")


# 导出工具类（供 toolset 注册）
__all__ = ["Think", "ThinkParams", "NAME"]

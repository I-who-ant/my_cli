"""
Stage 21.2: WebSearch 工具实现

功能：使用 DuckDuckGo 搜索网页

学习要点：
1. 使用第三方库（duckduckgo-search）
2. 异步网络请求
3. 结果格式化

对应设计：LEARNING_WORKFLOW3.md Stage 21
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, override

from kosong.tooling import CallableTool2, ToolOk, ToolError, ToolReturnType
from pydantic import BaseModel, Field

from my_cli.tools.utils import load_desc

# 工具名称
NAME = "WebSearch"


class WebSearchParams(BaseModel):
    """WebSearch 工具参数

    Attributes:
        query: 搜索查询文本
        limit: 返回结果数量（默认 5，最大 10）
    """

    query: str = Field(description="The search query text")
    limit: int = Field(
        description="Number of results to return (default: 5, max: 10)",
        default=5,
        ge=1,
        le=10,
    )


class WebSearch(CallableTool2[WebSearchParams]):
    """
    WebSearch 工具 - 使用 DuckDuckGo 搜索网页

    特点：
    1. 不需要 API Key（使用 DuckDuckGo）
    2. 返回搜索结果（标题、URL、摘要）
    3. 支持限制结果数量

    使用场景：
    - 查找信息和文档
    - 研究特定主题
    - 查找最新新闻
    - 搜索代码示例

    示例：
        WebSearch(query="Python asyncio tutorial", limit=5)
    """

    name: str = NAME
    description: str = load_desc(Path(__file__).parent / "search.md")
    params: type[WebSearchParams] = WebSearchParams

    def __init__(self, **kwargs: Any) -> None:
        """初始化 WebSearch 工具

        Args:
            **kwargs: 传递给父类的参数
        """
        super().__init__(**kwargs)

    @override
    async def __call__(self, params: WebSearchParams) -> ToolReturnType:
        """执行 WebSearch 工具

        Args:
            params: 工具参数（包含 query 和 limit）

        Returns:
            ToolOk | ToolError: 搜索结果或错误信息

        实现说明：
        - 使用 duckduckgo-search 库
        - 捕获异常并返回错误
        - 格式化搜索结果为 Markdown
        """
        try:
            # 导入 duckduckgo-search（延迟导入，避免启动时失败）
            from duckduckgo_search import DDGS
        except ImportError:
            return ToolError(
                output="",
                message=(
                    "duckduckgo-search library is not installed. "
                    "Please install it with: pip install duckduckgo-search"
                ),
                brief="Missing dependency",
            )

        try:
            # 执行搜索
            ddgs = DDGS()
            results = list(ddgs.text(params.query, max_results=params.limit))

            if not results:
                return ToolOk(
                    output="",
                    message=f"No results found for query: {params.query}",
                )

            # 格式化结果为 Markdown
            output_lines = [f"# Search Results for: {params.query}\n"]

            for i, result in enumerate(results, 1):
                title = result.get("title", "No Title")
                url = result.get("href", "")
                snippet = result.get("body", "No description available")

                output_lines.append(f"## {i}. {title}\n")
                output_lines.append(f"**URL**: {url}\n")
                output_lines.append(f"**Summary**: {snippet}\n")
                output_lines.append("---\n")

            output = "\n".join(output_lines)

            return ToolOk(
                output=output,
                message=f"Found {len(results)} results for query: {params.query}",
            )

        except Exception as e:
            # 捕获所有异常（网络错误、解析错误等）
            return ToolError(
                output="",
                message=f"Failed to search: {str(e)}. This may indicate a network issue or service unavailability.",
                brief="Search failed",
            )


# 导出工具类
__all__ = ["WebSearch", "WebSearchParams", "NAME"]

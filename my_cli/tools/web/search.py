"""
Stage 21.2: SearchWeb 工具实现（Moonshot Search API）

功能：使用 Moonshot Search API 搜索网页

学习要点：
1. Config 集成（从配置文件读取 API 配置）
2. SkipThisTool 异常（配置缺失时跳过工具）
3. ToolResultBuilder 使用（输出管理）
4. Pydantic 验证 API 响应

对应源码：kimi-cli-fork/src/kimi_cli/tools/web/search.py
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, override

from kosong.tooling import CallableTool2, ToolReturnType
from pydantic import BaseModel, Field, ValidationError

from my_cli.config import Config
from my_cli.constant import USER_AGENT
from my_cli.soul.toolset import get_current_tool_call_or_none
from my_cli.tools import SkipThisTool
from my_cli.tools.utils import ToolResultBuilder, load_desc
from my_cli.utils.aiohttp import new_client_session

# 工具名称
NAME = "SearchWeb"


class Params(BaseModel):
    """SearchWeb 工具参数

    Attributes:
        query: 搜索查询文本
        limit: 返回结果数量（1-20）
        include_content: 是否包含网页内容（会消耗大量 tokens）
    """

    query: str = Field(description="The query text to search for.")
    limit: int = Field(
        description=(
            "The number of results to return. "
            "Typically you do not need to set this value. "
            "When the results do not contain what you need, "
            "you probably want to give a more concrete query."
        ),
        default=5,
        ge=1,
        le=20,
    )
    include_content: bool = Field(
        description=(
            "Whether to include the content of the web pages in the results. "
            "It can consume a large amount of tokens when this is set to True. "
            "You should avoid enabling this when `limit` is set to a large value."
        ),
        default=False,
    )


class SearchResult(BaseModel):
    """搜索结果模型

    Attributes:
        site_name: 网站名称
        title: 标题
        url: URL
        snippet: 摘要
        content: 内容（可选，需要 include_content=True）
        date: 日期（可选）
        icon: 图标（可选）
        mime: MIME 类型（可选）
    """

    site_name: str
    title: str
    url: str
    snippet: str
    content: str = ""
    date: str = ""
    icon: str = ""
    mime: str = ""


class Response(BaseModel):
    """Moonshot Search API 响应模型

    Attributes:
        search_results: 搜索结果列表
    """

    search_results: list[SearchResult]


class SearchWeb(CallableTool2[Params]):
    """
    SearchWeb 工具 - 使用 Moonshot Search API 搜索

    特点：
    1. 需要配置 Moonshot Search API（services.moonshot_search）
    2. 如果配置缺失，抛出 SkipThisTool（工具不会被加载）
    3. 使用 ToolResultBuilder 管理输出
    4. 支持包含网页内容（enable_page_crawling）

    配置示例（~/.mc/config.json）：
        {
            "services": {
                "moonshot_search": {
                    "base_url": "https://api.moonshot.cn/v1/web/search",
                    "api_key": "sk-..."
                }
            }
        }

    使用场景：
    - 搜索实时信息（新闻、文档、API 参考）
    - 查找特定主题的网页
    - 获取网页摘要和内容
    """

    name: str = NAME
    description: str = load_desc(Path(__file__).parent / "search.md", {})
    params: type[Params] = Params

    def __init__(self, config: Config, **kwargs: Any):
        """
        初始化 SearchWeb 工具

        Args:
            config: 全局配置对象
            **kwargs: 传递给父类的参数

        Raises:
            SkipThisTool: 如果配置中没有 moonshot_search
        """
        super().__init__(**kwargs)

        # 检查配置（如果缺失则跳过工具）
        if config.services.moonshot_search is None:
            raise SkipThisTool()

        # 保存配置
        self._base_url = config.services.moonshot_search.base_url
        self._api_key = config.services.moonshot_search.api_key.get_secret_value()
        self._custom_headers = config.services.moonshot_search.custom_headers or {}

    @override
    async def __call__(self, params: Params) -> ToolReturnType:
        """
        执行搜索

        Args:
            params: 搜索参数

        Returns:
            ToolOk: 搜索成功，包含格式化的结果
            ToolError: 搜索失败（网络错误、API 错误、解析错误）
        """
        builder = ToolResultBuilder(max_line_length=None)

        # 双重检查配置（防御性编程）
        if not self._base_url or not self._api_key:
            return builder.error(
                "Search service is not configured. You may want to try other methods to search.",
                brief="Search service not configured",
            )

        # 获取当前工具调用（用于传递 tool_call_id 给 API）
        tool_call = get_current_tool_call_or_none()
        assert tool_call is not None, "Tool call is expected to be set"

        # 调用 Moonshot Search API
        try:
            async with (
                new_client_session() as session,
                session.post(
                    self._base_url,
                    headers={
                        "User-Agent": USER_AGENT,
                        "Authorization": f"Bearer {self._api_key}",
                        "X-Msh-Tool-Call-Id": tool_call.id,  # ⭐ 传递 tool_call_id
                        **self._custom_headers,
                    },
                    json={
                        "text_query": params.query,
                        "limit": params.limit,
                        "enable_page_crawling": params.include_content,
                        "timeout_seconds": 30,
                    },
                ) as response,
            ):
                # 检查 HTTP 状态
                if response.status != 200:
                    return builder.error(
                        (
                            f"Failed to search. Status: {response.status}. "
                            "This may indicates that the search service is currently unavailable."
                        ),
                        brief="Failed to search",
                    )

                # 解析响应
                try:
                    results = Response(**await response.json()).search_results
                except ValidationError as e:
                    return builder.error(
                        (
                            f"Failed to parse search results. Error: {e}. "
                            "This may indicates that the search service is currently unavailable."
                        ),
                        brief="Failed to parse search results",
                    )

        except Exception as e:
            return builder.error(
                f"Failed to search due to network error: {str(e)}",
                brief="Network error",
            )

        # 格式化输出
        for i, result in enumerate(results):
            if i > 0:
                builder.write("---\n\n")

            builder.write(
                f"Title: {result.title}\nDate: {result.date}\n"
                f"URL: {result.url}\nSummary: {result.snippet}\n\n"
            )

            if result.content:
                builder.write(f"{result.content}\n\n")

        return builder.ok()


# 导出
__all__ = ["SearchWeb", "Params", "SearchResult", "Response", "NAME"]

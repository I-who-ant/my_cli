"""
Stage 21.2: Web 工具模块

包含两个工具：
1. WebSearch - 使用 DuckDuckGo 搜索网页
2. WebFetch - 抓取网页内容

对应设计：LEARNING_WORKFLOW3.md Stage 21
"""

from my_cli.tools.web.fetch import WebFetch, WebFetchParams
from my_cli.tools.web.search import WebSearch, WebSearchParams

__all__ = ["WebSearch", "WebSearchParams", "WebFetch", "WebFetchParams"]

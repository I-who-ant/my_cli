"""
Stage 21.2: Web 工具模块

包含两个工具：
1. SearchWeb - 使用 Moonshot Search API 搜索网页
2. FetchURL - 抓取网页内容

对应源码：kimi-cli-fork/src/kimi_cli/tools/web/
"""

from my_cli.tools.web.fetch import FetchURL
from my_cli.tools.web.search import SearchWeb

__all__ = ["SearchWeb", "FetchURL"]

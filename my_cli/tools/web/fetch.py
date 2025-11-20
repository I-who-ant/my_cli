"""
Stage 21.2: WebFetch 工具实现

功能：抓取网页内容并提取主要文本

学习要点：
1. 使用 aiohttp 进行异步 HTTP 请求
2. 使用 trafilatura 提取网页内容
3. 错误处理和超时控制

对应设计：LEARNING_WORKFLOW3.md Stage 21
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, override

import aiohttp
from kosong.tooling import CallableTool2, ToolOk, ToolError, ToolReturnType
from pydantic import BaseModel, Field

from my_cli.tools.utils import load_desc

# 工具名称
NAME = "WebFetch"


class WebFetchParams(BaseModel):
    """WebFetch 工具参数

    Attributes:
        url: 要抓取的网页 URL
    """

    url: str = Field(description="The URL to fetch content from")


class WebFetch(CallableTool2[WebFetchParams]):
    """
    WebFetch 工具 - 抓取网页内容

    特点：
    1. 使用 aiohttp 异步请求
    2. 使用 trafilatura 提取主要内容
    3. 支持多种内容类型（HTML、纯文本、Markdown）
    4. 错误处理和超时控制

    使用场景：
    - 阅读文章内容
    - 获取文档页面
    - 分析网页内容
    - 搜索后跟进获取详细内容

    示例：
        WebFetch(url="https://example.com/article")
    """

    name: str = NAME
    description: str = load_desc(Path(__file__).parent / "fetch.md")
    params: type[WebFetchParams] = WebFetchParams

    def __init__(self, **kwargs: Any) -> None:
        """初始化 WebFetch 工具

        Args:
            **kwargs: 传递给父类的参数
        """
        super().__init__(**kwargs)

    @override
    async def __call__(self, params: WebFetchParams) -> ToolReturnType:
        """执行 WebFetch 工具

        Args:
            params: 工具参数（包含 url）

        Returns:
            ToolOk | ToolError: 网页内容或错误信息

        实现说明：
        - 使用 aiohttp 发送 GET 请求
        - 使用 trafilatura 提取内容
        - 处理不同的内容类型
        - 捕获网络错误和解析错误
        """
        try:
            # 导入 trafilatura（延迟导入）
            import trafilatura
        except ImportError:
            return ToolError(
                output="",
                message=(
                    "trafilatura library is not installed. "
                    "Please install it with: pip install trafilatura"
                ),
                brief="Missing dependency",
            )

        try:
            # 创建 aiohttp 会话并发送请求
            timeout = aiohttp.ClientTimeout(total=30)  # 30 秒超时
            async with aiohttp.ClientSession(timeout=timeout) as session:
                headers = {
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                        "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                    )
                }

                async with session.get(params.url, headers=headers) as response:
                    # 检查 HTTP 状态码
                    if response.status >= 400:
                        return ToolError(
                            output="",
                            message=(
                                f"Failed to fetch URL. HTTP status: {response.status}. "
                                "This may indicate the page is not accessible or the server is down."
                            ),
                            brief=f"HTTP {response.status} error",
                        )

                    # 获取响应内容
                    resp_text = await response.text()

                    # 检查内容类型
                    content_type = response.headers.get("Content-Type", "").lower()

                    # 如果是纯文本或 Markdown，直接返回
                    if "text/plain" in content_type or "text/markdown" in content_type:
                        return ToolOk(
                            output=resp_text,
                            message="Fetched plain text/markdown content successfully",
                        )

            # 使用 trafilatura 提取内容（针对 HTML）
            if not resp_text:
                return ToolOk(
                    output="",
                    message="The response body is empty",
                )

            extracted_text = trafilatura.extract(
                resp_text,
                include_comments=False,  # 不包含注释
                include_tables=True,  # 包含表格
                include_formatting=False,  # 不包含格式化（避免太多标记）
                output_format="txt",  # 输出纯文本
                with_metadata=True,  # 包含元数据
            )

            if not extracted_text:
                return ToolError(
                    output="",
                    message=(
                        "Failed to extract meaningful content from the page. "
                        "This may indicate the page content is not suitable for text extraction, "
                        "or the page requires JavaScript to render its content."
                    ),
                    brief="No content extracted",
                )

            return ToolOk(
                output=extracted_text,
                message=f"Successfully fetched and extracted content from: {params.url}",
            )

        except aiohttp.ClientError as e:
            # 网络错误（连接失败、超时等）
            return ToolError(
                output="",
                message=(
                    f"Failed to fetch URL due to network error: {str(e)}. "
                    "This may indicate the URL is invalid or the server is unreachable."
                ),
                brief="Network error",
            )
        except Exception as e:
            # 其他异常（解析错误等）
            return ToolError(
                output="",
                message=f"Failed to fetch URL: {str(e)}",
                brief="Fetch failed",
            )


# 导出工具类
__all__ = ["WebFetch", "WebFetchParams", "NAME"]

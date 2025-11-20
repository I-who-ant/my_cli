"""
Stage 21.2: FetchURL 工具实现

功能：抓取网页内容并提取主要文本

学习要点：
1. 使用 new_client_session()（SSL 验证）
2. 使用 ToolResultBuilder（输出管理）
3. 使用 trafilatura 提取内容
4. 完善的错误处理

对应源码：kimi-cli-fork/src/kimi_cli/tools/web/fetch.py
"""

from __future__ import annotations

from pathlib import Path
from typing import override

import aiohttp
import trafilatura
from kosong.tooling import CallableTool2, ToolReturnType
from pydantic import BaseModel, Field

from my_cli.tools.utils import ToolResultBuilder, load_desc
from my_cli.utils.aiohttp import new_client_session

# 工具名称
NAME = "FetchURL"


class Params(BaseModel):
    """FetchURL 工具参数

    Attributes:
        url: 要抓取的 URL
    """

    url: str = Field(description="The URL to fetch content from.")


class FetchURL(CallableTool2[Params]):
    """
    FetchURL 工具 - 抓取网页内容

    特点：
    1. 使用 aiohttp 异步请求
    2. 使用 trafilatura 提取主要内容（去除广告、导航等）
    3. 支持纯文本和 Markdown 内容
    4. 30 秒超时（在 new_client_session 中配置）

    使用场景：
    - 抓取文章内容
    - 提取文档页面
    - 获取 API 文档
    - 分析网页结构

    实现说明：
    - 使用 ToolResultBuilder 管理输出（自动限制大小）
    - 使用 new_client_session()（SSL 验证）
    - 优先检测纯文本和 Markdown（直接返回）
    - 使用 trafilatura 提取 HTML 内容
    """

    name: str = NAME
    description: str = load_desc(Path(__file__).parent / "fetch.md", {})
    params: type[Params] = Params

    @override
    async def __call__(self, params: Params) -> ToolReturnType:
        """
        执行网页抓取

        Args:
            params: 抓取参数

        Returns:
            ToolOk: 抓取成功，包含提取的内容
            ToolError: 抓取失败（网络错误、HTTP 错误、解析错误）
        """
        builder = ToolResultBuilder(max_line_length=None)

        try:
            # 使用 new_client_session()（带 SSL 验证）
            async with (
                new_client_session() as session,
                session.get(
                    params.url,
                    headers={
                        "User-Agent": (
                            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                            "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                        ),
                    },
                ) as response,
            ):
                # 检查 HTTP 状态
                if response.status >= 400:
                    return builder.error(
                        (
                            f"Failed to fetch URL. Status: {response.status}. "
                            f"This may indicate the page is not accessible or the server is down."
                        ),
                        brief=f"HTTP {response.status} error",
                    )

                resp_text = await response.text()

                # 检查内容类型（纯文本和 Markdown 直接返回）
                content_type = response.headers.get(aiohttp.hdrs.CONTENT_TYPE, "").lower()
                if content_type.startswith(("text/plain", "text/markdown")):
                    builder.write(resp_text)
                    return builder.ok("The returned content is the full content of the page.")

        except aiohttp.ClientError as e:
            return builder.error(
                (
                    f"Failed to fetch URL due to network error: {str(e)}. "
                    "This may indicate the URL is invalid or the server is unreachable."
                ),
                brief="Network error",
            )

        # 检查响应是否为空
        if not resp_text:
            return builder.ok(
                "The response body is empty.",
                brief="Empty response body",
            )

        # 使用 trafilatura 提取内容
        extracted_text = trafilatura.extract(
            resp_text,
            include_comments=True,  # 包含注释
            include_tables=True,  # 包含表格
            include_formatting=False,  # 不包含格式化（纯文本）
            output_format="txt",  # 输出格式：文本
            with_metadata=True,  # 包含元数据
        )

        # 检查是否提取到内容
        if not extracted_text:
            return builder.error(
                (
                    "Failed to extract meaningful content from the page. "
                    "This may indicate the page content is not suitable for text extraction, "
                    "or the page requires JavaScript to render its content."
                ),
                brief="No content extracted",
            )

        # 写入提取的内容
        builder.write(extracted_text)
        return builder.ok("The returned content is the main text content extracted from the page.")


# 导出
__all__ = ["FetchURL", "Params", "NAME"]


# 测试（用于开发调试）
if __name__ == "__main__":
    import asyncio

    async def main():
        fetch_url_tool = FetchURL()
        result = await fetch_url_tool(Params(url="https://trafilatura.readthedocs.io/en/latest/"))
        print(result)

    asyncio.run(main())

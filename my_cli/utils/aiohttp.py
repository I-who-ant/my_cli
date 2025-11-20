"""
aiohttp 客户端封装

功能：提供配置好的 aiohttp.ClientSession（SSL 证书验证）

对应源码：kimi-cli-fork/src/kimi_cli/utils/aiohttp.py
"""

from __future__ import annotations

import ssl

import aiohttp
import certifi

# 创建默认 SSL 上下文（使用 certifi 证书）
_ssl_context = ssl.create_default_context(cafile=certifi.where())


def new_client_session() -> aiohttp.ClientSession:
    """
    创建新的 aiohttp.ClientSession（配置 SSL 验证）

    Returns:
        配置好的 ClientSession

    示例：
        async with new_client_session() as session:
            async with session.get("https://example.com") as response:
                text = await response.text()
    """
    return aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=_ssl_context))

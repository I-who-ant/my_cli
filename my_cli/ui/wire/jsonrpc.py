"""
JSON-RPC 消息定义 ⭐ Stage 29

提供符合 JSON-RPC 2.0 规范的消息类型定义，
用于 Wire 服务器与客户端之间的通信。

对应源码：kimi-cli-fork/src/kimi_cli/ui/wire/jsonrpc.py
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter

JSONRPC_VERSION = "2.0"


class _MessageBase(BaseModel):
    """JSON-RPC 消息基类"""

    jsonrpc: Literal["2.0"]

    model_config = ConfigDict(extra="forbid")


class JSONRPCRequest(_MessageBase):
    """JSON-RPC 请求消息"""

    method: str
    id: str | None = None
    params: dict[str, Any] = Field(default_factory=dict)


class _ResponseBase(_MessageBase):
    """JSON-RPC 响应基类"""

    id: str | None


class JSONRPCSuccessResponse(_ResponseBase):
    """JSON-RPC 成功响应"""

    result: dict[str, Any]


class JSONRPCErrorObject(BaseModel):
    """JSON-RPC 错误对象"""

    code: int
    message: str
    data: Any | None = None


class JSONRPCErrorResponse(_ResponseBase):
    """JSON-RPC 错误响应"""

    error: JSONRPCErrorObject


# 联合类型和适配器
JSONRPCMessage = JSONRPCRequest | JSONRPCSuccessResponse | JSONRPCErrorResponse
JSONRPC_MESSAGE_ADAPTER = TypeAdapter[JSONRPCMessage](JSONRPCMessage)

__all__ = [
    "JSONRPC_VERSION",
    "JSONRPCRequest",
    "JSONRPCSuccessResponse",
    "JSONRPCErrorObject",
    "JSONRPCErrorResponse",
    "JSONRPCMessage",
    "JSONRPC_MESSAGE_ADAPTER",
]

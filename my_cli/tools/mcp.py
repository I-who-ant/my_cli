"""
MCP 工具集成模块 ⭐ Stage 23

对应源码：kimi-cli-fork/src/kimi_cli/tools/mcp.py (114行)

功能：
1. MCPTool - MCP 工具包装器
2. convert_tool_result - MCP 结果转换为 ContentPart
3. 支持 HTTP 和 STDIO 两种 MCP 服务器类型
4. 集成 Approval 系统
"""

from typing import Any

import fastmcp
import mcp
from fastmcp.client.client import CallToolResult
from kosong.message import AudioURLPart, ContentPart, ImageURLPart, TextPart
from kosong.tooling import CallableTool, ToolError, ToolOk, ToolReturnType

from my_cli.soul.runtime import Runtime
from my_cli.tools.utils import ToolRejectedError


class MCPTool(CallableTool):
    """
    MCP 工具包装器 ⭐ 对齐官方实现

    将 MCP 服务器提供的工具包装为 CallableTool，
    支持 Approval 和结果转换。

    对应源码：kimi-cli-fork/src/kimi_cli/tools/mcp.py:14-43
    """

    def __init__(
        self,
        mcp_tool: mcp.Tool,
        client: fastmcp.Client,
        *,
        runtime: Runtime,
        **kwargs: Any,
    ):
        """
        初始化 MCP 工具

        Args:
            mcp_tool: MCP 工具定义
            client: MCP 客户端
            runtime: Soul Runtime
        """
        super().__init__(
            name=mcp_tool.name,
            description=mcp_tool.description or "",
            parameters=mcp_tool.inputSchema,
            **kwargs,
        )
        self._mcp_tool = mcp_tool
        self._client = client
        self._runtime = runtime
        self._action_name = f"mcp:{mcp_tool.name}"

    async def __call__(self, *args: Any, **kwargs: Any) -> ToolReturnType:
        """
        调用 MCP 工具

        1. 请求 Approval
        2. 调用 MCP 客户端
        3. 转换结果格式
        """
        # 1. 请求批准
        description = f"Call MCP tool `{self._mcp_tool.name}`."
        if not await self._runtime.approval.request(
            self.name, self._action_name, description
        ):
            return ToolRejectedError()

        # 2. 调用 MCP 工具
        async with self._client as client:
            result = await client.call_tool(
                self._mcp_tool.name, kwargs, timeout=60, raise_on_error=False
            )
            return convert_tool_result(result)


def convert_tool_result(result: CallToolResult) -> ToolReturnType:
    """
    转换 MCP 工具结果为 ContentPart ⭐ 对齐官方实现

    支持的内容类型：
    - TextContent → TextPart
    - ImageContent → ImageURLPart
    - AudioContent → AudioURLPart
    - EmbeddedResource → ImageURLPart/AudioURLPart
    - ResourceLink → ImageURLPart/AudioURLPart

    对应源码：kimi-cli-fork/src/kimi_cli/tools/mcp.py:46-113
    """
    content: list[ContentPart] = []

    for part in result.content:
        match part:
            case mcp.types.TextContent(text=text):
                content.append(TextPart(text=text))

            case mcp.types.ImageContent(data=data, mimeType=mimeType):
                content.append(
                    ImageURLPart(
                        image_url=ImageURLPart.ImageURL(
                            url=f"data:{mimeType};base64,{data}"
                        )
                    )
                )

            case mcp.types.AudioContent(data=data, mimeType=mimeType):
                content.append(
                    AudioURLPart(
                        audio_url=AudioURLPart.AudioURL(
                            url=f"data:{mimeType};base64,{data}"
                        )
                    )
                )

            case mcp.types.EmbeddedResource(
                resource=mcp.types.BlobResourceContents(
                    uri=_uri, mimeType=mimeType, blob=blob
                )
            ):
                mimeType = mimeType or "application/octet-stream"
                if mimeType.startswith("image/"):
                    content.append(
                        ImageURLPart(
                            type="image_url",
                            image_url=ImageURLPart.ImageURL(
                                url=f"data:{mimeType};base64,{blob}",
                            ),
                        )
                    )
                elif mimeType.startswith("audio/"):
                    content.append(
                        AudioURLPart(
                            type="audio_url",
                            audio_url=AudioURLPart.AudioURL(
                                url=f"data:{mimeType};base64,{blob}"
                            ),
                        )
                    )
                else:
                    raise ValueError(f"Unsupported mime type: {mimeType}")

            case mcp.types.ResourceLink(
                uri=uri, mimeType=mimeType, description=_description
            ):
                mimeType = mimeType or "application/octet-stream"
                if mimeType.startswith("image/"):
                    content.append(
                        ImageURLPart(
                            type="image_url",
                            image_url=ImageURLPart.ImageURL(url=str(uri)),
                        )
                    )
                elif mimeType.startswith("audio/"):
                    content.append(
                        AudioURLPart(
                            type="audio_url",
                            audio_url=AudioURLPart.AudioURL(url=str(uri)),
                        )
                    )
                else:
                    raise ValueError(f"Unsupported mime type: {mimeType}")

            case _:
                raise ValueError(f"Unsupported MCP tool result part: {part}")

    # 返回结果
    if result.is_error:
        return ToolError(
            output=content,
            message="Tool returned an error. The output may be error message or incomplete output",
            brief="",
        )
    else:
        return ToolOk(output=content)


__all__ = ["MCPTool", "convert_tool_result"]

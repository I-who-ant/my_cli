# Stage 23: MCP 服务器集成

**记录日期**: 2025-01-20
**对应源码**: `kimi-cli-fork/src/kimi_cli/tools/mcp.py`
**估算时间**: 2 周
**优先级**: 🔥🔥🔥🔥 (高)

---

## 📋 功能概述

实现 MCP (Model Context Protocol) 服务器集成，支持加载外部 MCP 服务器并动态注册工具到 Toolset。

**MCP 是什么？**
- **Model Context Protocol** - 模型上下文协议
- 标准化的工具集成协议
- 支持 HTTP 和 STDIO 两种传输方式
- 允许第三方服务提供工具给 AI Agent

---

## 🎯 实施目标

### 1. 核心功能

- ✅ 支持 HTTP MCP 服务器（通过 URL）
- ✅ 支持 STDIO MCP 服务器（通过命令行启动）
- ✅ 动态加载工具列表
- ✅ 工具调用封装（MCPTool）
- ✅ 结果转换（MCP格式 → ContentPart）
- ✅ Approval 集成

### 2. 配置支持

- ✅ JSON 配置文件（`--mcp-config-file`）
- ✅ 命令行参数（`--mcp-config`）
- ✅ 标准 MCP 配置格式

### 3. 工具注册

- ✅ 自动注册 MCP 工具到 Toolset
- ✅ 工具名称前缀（避免冲突）
- ✅ 工具参数转换

---

## 🏗️ 技术架构

### 官方实现分析

**依赖库**：
```python
import fastmcp  # MCP Python 客户端
import mcp      # MCP 协议定义
```

**核心类**：
```python
class MCPTool[T: ClientTransport](CallableTool):
    """MCP 工具包装器"""

    def __init__(self, mcp_tool, client, runtime):
        self._mcp_tool = mcp_tool
        self._client = client
        self._runtime = runtime

    async def __call__(self, **kwargs):
        # 1. 请求批准
        if not await self._runtime.approval.request(...):
            return ToolRejectedError()

        # 2. 调用 MCP 工具
        result = await self._client.call_tool(
            self._mcp_tool.name,
            kwargs,
            timeout=60
        )

        # 3. 转换结果
        return convert_tool_result(result)
```

**结果转换**：
```python
def convert_tool_result(result: CallToolResult):
    """将 MCP 结果转换为 ContentPart"""
    content: list[ContentPart] = []

    for part in result.content:
        match part:
            case mcp.types.TextContent(text=text):
                content.append(TextPart(text=text))
            case mcp.types.ImageContent(data=data, mimeType=mime):
                content.append(ImageURLPart(...))
            case mcp.types.AudioContent(data=data, mimeType=mime):
                content.append(AudioURLPart(...))

    if result.is_error:
        return ToolError(output=content, ...)
    else:
        return ToolOk(output=content)
```

---

## 📁 实施步骤

### Step 1: 安装依赖 (1小时)

```bash
cd /home/seeback/PycharmProjects/Modelrecognize/kimi-cli-main/imitate-src

# 安装 fastmcp 和 mcp
pip install fastmcp mcp
```

**验证安装**：
```python
import fastmcp
import mcp
print(f"fastmcp version: {fastmcp.__version__}")
print(f"mcp version: {mcp.__version__}")
```

---

### Step 2: 创建 MCPTool 包装器 (4小时)

**文件**: `my_cli/tools/mcp.py`

```python
"""
MCP 工具集成模块

对应源码：kimi-cli-fork/src/kimi_cli/tools/mcp.py
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

import mcp
from fastmcp.client.client import CallToolResult
from fastmcp.client.transports import ClientTransport
from kosong.message import AudioURLPart, ContentPart, ImageURLPart, TextPart
from kosong.tooling import CallableTool, ToolError, ToolOk, ToolReturnType

if TYPE_CHECKING:
    import fastmcp
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

            case mcp.types.ResourceLink(uri=uri, mimeType=mimeType, description=_description):
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
```

---

### Step 3: 实现 MCP 加载器 (6小时)

**文件**: `my_cli/tools/mcp_loader.py`

```python
"""
MCP 服务器加载器

负责启动 MCP 服务器并注册工具到 Toolset
"""
from __future__ import annotations

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING, Any

import fastmcp
from fastmcp.client.transports import StdioClientTransport, HttpClientTransport

from my_cli.tools.mcp import MCPTool
from my_cli.utils.logging import logger

if TYPE_CHECKING:
    from my_cli.soul.runtime import Runtime
    from my_cli.soul.toolset import Toolset


async def load_mcp_servers(
    mcp_configs: list[dict[str, Any]],
    toolset: Toolset,
    runtime: Runtime,
) -> list[fastmcp.Client]:
    """
    加载 MCP 服务器并注册工具

    Args:
        mcp_configs: MCP 配置列表
        toolset: 工具集
        runtime: Soul Runtime

    Returns:
        MCP 客户端列表
    """
    clients: list[fastmcp.Client] = []

    for server_name, server_config in mcp_configs.items():
        try:
            client = await load_mcp_server(server_name, server_config, toolset, runtime)
            clients.append(client)
            logger.info(f"Loaded MCP server: {server_name}")
        except Exception as e:
            logger.error(f"Failed to load MCP server {server_name}: {e}")

    return clients


async def load_mcp_server(
    server_name: str,
    server_config: dict[str, Any],
    toolset: Toolset,
    runtime: Runtime,
) -> fastmcp.Client:
    """
    加载单个 MCP 服务器

    支持两种类型：
    1. HTTP 服务器（url + headers）
    2. STDIO 服务器（command + args）
    """
    # 判断类型
    if "url" in server_config:
        # HTTP 服务器
        client = await _load_http_server(server_name, server_config)
    elif "command" in server_config:
        # STDIO 服务器
        client = await _load_stdio_server(server_name, server_config)
    else:
        raise ValueError(f"Invalid MCP config for {server_name}: missing 'url' or 'command'")

    # 获取工具列表
    tools = await client.list_tools()
    logger.debug(f"MCP server {server_name} provides {len(tools)} tools")

    # 注册工具到 Toolset
    for mcp_tool in tools:
        tool = MCPTool(mcp_tool, client, runtime=runtime)
        toolset.register_tool(tool)
        logger.debug(f"Registered MCP tool: {mcp_tool.name}")

    return client


async def _load_http_server(
    server_name: str,
    config: dict[str, Any],
) -> fastmcp.Client:
    """
    加载 HTTP MCP 服务器

    配置示例：
    {
        "url": "https://mcp.context7.com/mcp",
        "headers": {
            "CONTEXT7_API_KEY": "YOUR_API_KEY"
        }
    }
    """
    url = config["url"]
    headers = config.get("headers", {})

    transport = HttpClientTransport(url=url, headers=headers)
    client = fastmcp.Client(transport)

    return client


async def _load_stdio_server(
    server_name: str,
    config: dict[str, Any],
) -> fastmcp.Client:
    """
    加载 STDIO MCP 服务器

    配置示例：
    {
        "command": "npx",
        "args": ["-y", "chrome-devtools-mcp@latest"]
    }
    """
    command = config["command"]
    args = config.get("args", [])
    env = config.get("env", {})

    transport = StdioClientTransport(
        command=command,
        args=args,
        env=env,
    )
    client = fastmcp.Client(transport)

    return client


__all__ = ["load_mcp_servers", "load_mcp_server"]
```

---

### Step 4: CLI 参数支持 (2小时)

**文件**: `my_cli/cli.py`

```python
# 添加 MCP 配置参数
mcp_config_file: Annotated[
    list[Path] | None,
    typer.Option(
        "--mcp-config-file",
        help="加载 MCP 配置文件。可以多次指定以加载多个 MCP 配置。默认：无",
    ),
] = None,

mcp_config: Annotated[
    list[str] | None,
    typer.Option(
        "--mcp-config",
        help="加载 MCP 配置 JSON。可以多次指定以加载多个 MCP 配置。默认：无",
    ),
] = None,

# 解析 MCP 配置
file_configs = list(mcp_config_file or [])
raw_mcp_config = list(mcp_config or [])

try:
    mcp_configs = [
        json.loads(conf.read_text(encoding="utf-8")) for conf in file_configs
    ]
except json.JSONDecodeError as e:
    raise typer.BadParameter(f"Invalid JSON: {e}", param_hint="--mcp-config-file") from e

try:
    mcp_configs += [json.loads(conf) for conf in raw_mcp_config]
except json.JSONDecodeError as e:
    raise typer.BadParameter(f"Invalid JSON: {e}", param_hint="--mcp-config") from e

# 传递给 MyCLI
instance = MyCLI(
    ...
    mcp_configs=mcp_configs,
)
```

---

### Step 5: MyCLI 集成 (4小时)

**文件**: `my_cli/app.py`

```python
from my_cli.tools.mcp_loader import load_mcp_servers

class MyCLI:
    def __init__(
        self,
        ...
        mcp_configs: list[dict[str, Any]] | None = None,
    ):
        self.mcp_configs = mcp_configs or []
        self._mcp_clients: list[fastmcp.Client] = []

    async def _create_runtime(self, ...) -> Runtime:
        """创建 Runtime"""
        runtime = Runtime(...)

        # 加载 MCP 服务器
        if self.mcp_configs:
            self._mcp_clients = await load_mcp_servers(
                self.mcp_configs,
                runtime.toolset,
                runtime,
            )

        return runtime

    async def shutdown(self):
        """清理 MCP 客户端"""
        for client in self._mcp_clients:
            await client.close()
```

---

### Step 6: 测试 (4小时)

#### 测试用例 1：HTTP MCP 服务器

**配置文件** (`mcp-config-http.json`):
```json
{
  "mcpServers": {
    "context7": {
      "url": "https://mcp.context7.com/mcp",
      "headers": {
        "CONTEXT7_API_KEY": "YOUR_API_KEY"
      }
    }
  }
}
```

**测试命令**:
```bash
mc --mcp-config-file mcp-config-http.json
```

#### 测试用例 2：STDIO MCP 服务器

**配置文件** (`mcp-config-stdio.json`):
```json
{
  "mcpServers": {
    "chrome-devtools": {
      "command": "npx",
      "args": ["-y", "chrome-devtools-mcp@latest"]
    }
  }
}
```

**测试命令**:
```bash
mc --mcp-config-file mcp-config-stdio.json
```

#### 测试用例 3：命令行 JSON

```bash
mc --mcp-config '{"mcpServers": {"test": {"url": "http://localhost:8080/mcp"}}}'
```

---

## 📊 进度跟踪

| 任务 | 预计时间 | 实际时间 | 状态 |
|------|---------|---------|------|
| 安装依赖 | 1h | - | ⏳ |
| MCPTool 包装器 | 4h | - | ⏳ |
| MCP 加载器 | 6h | - | ⏳ |
| CLI 参数支持 | 2h | - | ⏳ |
| MyCLI 集成 | 4h | - | ⏳ |
| 测试验证 | 4h | - | ⏳ |
| 文档编写 | 3h | - | ⏳ |
| **总计** | **24h (3天)** | - | - |

---

## ✅ 验收标准

1. ✅ 支持加载 HTTP MCP 服务器
2. ✅ 支持加载 STDIO MCP 服务器
3. ✅ 工具自动注册到 Toolset
4. ✅ 工具调用正常工作
5. ✅ 结果转换正确（文本、图片、音频）
6. ✅ Approval 集成工作
7. ✅ 通过所有测试用例

---

## 📚 参考资料

- **MCP 协议规范**: https://spec.modelcontextprotocol.io/
- **fastmcp 文档**: https://github.com/jlowin/fastmcp
- **官方实现**: `kimi-cli-fork/src/kimi_cli/tools/mcp.py`

---

**创建时间**: 2025-01-20
**作者**: Claude（老王编程助手）
**版本**: v1.0
**状态**: 🟡 准备开始

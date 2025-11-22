# 官方工具系统 vs Stage 7 对比分析

## 📋 文件对比清单

| 文件 | Stage 7（我们的实现） | 官方实现 | 为什么放后面？ |
|------|---------------------|---------|--------------|
| `tools/__init__.py` | ✅ 只有 `SkipThisTool` | ✅ 完整（91行） | **UI显示增强** |
| `tools/utils.py` | ❌ 未实现 | ✅ 完整（151行） | **生产级健壮性** |
| `tools/test.py` | ❌ 未实现 | ✅ 完整（56行） | **测试工具** |
| `tools/mcp.py` | ❌ 未实现 | ✅ 完整（89行） | **高级特性（MCP协议）** |

---

## 🔍 逐个文件详细分析

### 1. `tools/__init__.py`

#### Stage 7（我们的实现）

```python
class SkipThisTool(Exception):
    """工具跳过异常"""
    pass
```

**只有基础异常类**，仅26行。

---

#### 官方实现（91行）

```python
class SkipThisTool(Exception):
    """工具跳过异常"""
    pass

def extract_key_argument(json_content: str | streamingjson.Lexer, tool_name: str) -> str | None:
    """从工具调用参数中提取关键参数（用于 UI 显示）"""
    match tool_name:
        case "Bash":
            return curr_args.get("command")  # 提取命令
        case "ReadFile":
            return _normalize_path(curr_args.get("path"))  # 提取文件路径
        case "WriteFile":
            return _normalize_path(curr_args.get("path"))
        case "Grep":
            return curr_args.get("pattern")  # 提取搜索模式
        # ... 更多工具
```

**核心功能**：

1. **UI 显示增强**：
   ```
   不显示完整参数：{"command": "ls -la /very/long/path/...", "timeout": 60}
   只显示关键信息：ls -la /very/long/path/...
   ```

2. **流式显示支持**：
   - 接受 `streamingjson.Lexer`（工具调用参数可能是流式到达的）
   - 实时提取关键参数

3. **路径标准化**：
   ```python
   # 绝对路径 → 相对路径（更短更清晰）
   /home/user/project/src/main.py → src/main.py
   ```

---

#### 为什么 Stage 7 不需要？

**Stage 7 目标**：**基础架构**，工具能正常执行就行。

**后续阶段需要**（Stage 8-9）：
- **Shell UI 模式**：需要美观的工具调用显示
- **流式工具调用**：需要实时显示工具参数
- **用户体验优化**：路径缩短、参数简化

---

### 2. `tools/utils.py`（151行）

#### 核心组件

```python
# 1. 工具描述加载器
def load_desc(path: Path, substitutions: dict[str, str] | None = None) -> str:
    """
    从 Markdown 文件加载工具描述

    示例：bash.md → "Execute a bash command..."
    支持模板替换：$var → actual_value
    """
    description = path.read_text()
    if substitutions:
        description = string.Template(description).substitute(substitutions)
    return description

# 2. 输出限制器（防止输出过大）
class ToolResultBuilder:
    """
    构建工具结果，自动限制输出大小

    - 最大字符数：50,000
    - 最大行长度：2,000
    - 超限自动截断
    """
    def __init__(self, max_chars=50_000, max_line_length=2000):
        self._buffer = []
        self._n_chars = 0
        self._truncation_happened = False

    def write(self, text: str) -> int:
        """写入输出（自动截断）"""
        if self.is_full:
            return 0
        # 限制行长度
        line = truncate_line(line, self.max_line_length, "[...truncated]")
        self._buffer.append(line)

    def ok(self, message: str = "") -> ToolOk:
        """生成 ToolOk（自动添加截断提示）"""
        output = "".join(self._buffer)
        if self._truncation_happened:
            message += " Output is truncated to fit in the message."
        return ToolOk(output=output, message=message)

# 3. 用户拒绝错误
class ToolRejectedError(ToolError):
    """工具被用户拒绝"""
    def __init__(self):
        super().__init__(
            message="The tool call is rejected by the user.",
            brief="Rejected by user"
        )
```

---

#### 为什么需要这些？

##### 1. **load_desc()** - 工具描述分离

```python
# ❌ Stage 7 方式（硬编码）
class Bash(CallableTool2[Params]):
    description: str = "Execute a bash command in the shell.\n\nThis tool runs..."

# ✅ 官方方式（Markdown文件）
# tools/bash/bash.md:
"""
Execute a bash command in the shell.

This tool runs the command in a subprocess and captures stdout and stderr.
The command will be killed if it exceeds the timeout.

## Examples:
- List files: `ls -la`
- Check disk usage: `df -h`
"""

class Bash(CallableTool2[Params]):
    description: str = load_desc(Path(__file__).parent / "bash.md")
```

**优势**：
- ✅ 描述可以很长（Markdown格式）
- ✅ 易于维护和更新
- ✅ 支持模板变量

---

##### 2. **ToolResultBuilder** - 输出限制

```python
# 问题：工具输出可能非常大
result = subprocess.run(["find", "/"], capture_output=True)
# 输出可能有几MB！直接返回会：
# - 超过 LLM context 限制
# - 浪费 API tokens
# - UI 卡死

# ✅ 使用 ToolResultBuilder
builder = ToolResultBuilder(max_chars=50_000)
for line in output_lines:
    builder.write(line)  # 自动截断
return builder.ok("Command executed.")
```

**防御场景**：
```bash
# 危险命令（输出巨大）
cat /var/log/syslog    # 可能几GB
ls -R /                # 几百万行
```

---

##### 3. **ToolRejectedError** - 用户批准机制

```python
# Stage 8+ 需要的批准流程：

# 1. 工具请求用户批准
if not await approval.request("Bash", "run command", "rm -rf /"):
    return ToolRejectedError()  # ⭐ 用户拒绝

# 2. LLM 收到拒绝消息
ToolResult(
    tool_call_id="call_123",
    result=ToolRejectedError()  # "Rejected by user"
)

# 3. LLM 理解并调整策略
"I see you rejected the command. Let me try a safer approach..."
```

---

#### Stage 7 vs 官方对比

| 特性 | Stage 7 | 官方（utils.py） |
|------|---------|----------------|
| **描述管理** | 硬编码字符串 | Markdown 文件 + load_desc() |
| **输出限制** | 无（直接返回所有输出） | ToolResultBuilder（50K限制） |
| **用户批准** | 无 | ToolRejectedError |
| **适用场景** | 学习和测试 | 生产环境 |

---

### 3. `tools/test.py`（56行）

#### 官方实现

```python
# 1. Plus 工具（测试基础调用）
class Plus(CallableTool2[PlusParams]):
    name: str = "plus"
    description: str = "Add two numbers"

    async def __call__(self, params: PlusParams) -> ToolReturnType:
        return ToolOk(output=str(params.a + params.b))

# 2. Compare 工具（测试条件逻辑）
class Compare(CallableTool2[CompareParams]):
    name: str = "compare"

    async def __call__(self, params: CompareParams) -> ToolReturnType:
        if params.a > params.b:
            return ToolOk(output="greater")
        # ...

# 3. Panic 工具（测试错误处理）
class Panic(CallableTool2[PanicParams]):
    name: str = "panic"

    async def __call__(self, params: PanicParams) -> ToolReturnType:
        await asyncio.sleep(2)
        raise Exception(f"panicked with {len(params.message)} characters")
```

---

#### 作用

**用于测试工具调用框架**：

```python
# 测试场景 1: LLM 能否正确计算？
result = await toolset.handle(ToolCall(
    name="plus",
    arguments={"a": 2, "b": 3}
))
assert result.result.output == "5"  # ✅ 工具调用成功

# 测试场景 2: LLM 能否处理多步推理？
# 1. LLM: "Let me compare 5 and 3"
# 2. Call: compare(5, 3)
# 3. Result: "greater"
# 4. LLM: "5 is greater than 3"

# 测试场景 3: 错误处理
result = await toolset.handle(ToolCall(name="panic", arguments={"message": "test"}))
assert isinstance(result.result, ToolError)  # ✅ 异常被捕获
```

---

#### 为什么 Stage 7 不需要？

**Stage 7 目标**：实现**真实工具**（Bash, ReadFile, WriteFile）。

**test.py 用于**：
- 单元测试工具框架
- 集成测试 LLM 工具调用
- 调试工具系统

**后续使用**（Stage 8+）：
- 端到端测试
- LLM 能力验证
- 回归测试

---

### 4. `tools/mcp.py`（89行）

#### 什么是 MCP？

**MCP（Model Context Protocol）**：一个标准协议，允许 LLM 调用外部服务的工具。

```
┌──────────┐         ┌──────────┐         ┌──────────────┐
│ Kimi CLI │ ──MCP──>│ MCP 服务器│ ──API──>│ 外部服务     │
│          │         │          │         │ (GitHub API) │
└──────────┘         └──────────┘         └──────────────┘
```

---

#### 官方实现

```python
import fastmcp  # MCP 客户端库
import mcp

class MCPTool[T: ClientTransport](CallableTool):
    """将 MCP 工具包装成 kosong 工具"""

    def __init__(self, mcp_tool: mcp.Tool, client: fastmcp.Client[T]):
        super().__init__(
            name=mcp_tool.name,
            description=mcp_tool.description,
            parameters=mcp_tool.inputSchema,  # MCP 的 JSON Schema
        )
        self._mcp_tool = mcp_tool
        self._client = client

    async def __call__(self, **kwargs) -> ToolReturnType:
        # 调用 MCP 服务器
        result = await self._client.call_tool(self._mcp_tool.name, kwargs)

        # 转换 MCP 结果 → kosong ToolOk
        return convert_tool_result(result)


def convert_tool_result(result: CallToolResult) -> ToolReturnType:
    """转换 MCP 结果到 kosong 格式"""
    content: list[ContentPart] = []

    for part in result.content:
        match part:
            case mcp.types.TextContent(text=text):
                content.append(TextPart(text=text))

            case mcp.types.ImageContent(data=data, mimeType=mimeType):
                # Base64 图片 → ImageURLPart
                content.append(ImageURLPart(
                    image_url=f"data:{mimeType};base64,{data}"
                ))

            case mcp.types.AudioContent(...):
                # 音频内容
                ...

    return ToolOk(output=content)
```

---

#### MCP 使用场景

```python
# 示例：GitHub MCP 服务器

# 1. 连接 MCP 服务器
mcp_client = fastmcp.Client("github-mcp-server")

# 2. 获取 MCP 工具列表
mcp_tools = await mcp_client.list_tools()
# [
#   Tool(name="create_issue", description="Create a GitHub issue"),
#   Tool(name="list_repos", description="List repositories"),
#   ...
# ]

# 3. 包装成 kosong 工具
github_tools = [MCPTool(tool, mcp_client) for tool in mcp_tools]

# 4. 添加到 Toolset
toolset._tools.update({tool.name: tool for tool in github_tools})

# 5. LLM 现在可以调用 GitHub API！
# User: "Create an issue in my repo"
# LLM: create_issue(repo="user/repo", title="Bug", body="...")
# MCP: 调用 GitHub API
# Result: Issue #123 created
```

---

#### 为什么 Stage 7 不需要？

**MCP 是高级特性**：

| 特性 | Stage 7 工具 | MCP 工具 |
|------|-------------|---------|
| **复杂度** | 简单（本地执行） | 复杂（网络通信） |
| **依赖** | 无（Python 标准库） | fastmcp, mcp 库 |
| **适用场景** | 基础操作 | 外部服务集成 |
| **示例** | Bash, ReadFile | GitHub, Jira, Slack |

**后续阶段**（Stage 9+）：
- 集成 MCP 服务器
- 支持外部工具
- 扩展 Agent 能力

---

## 🎯 总结对比

### Stage 7（我们的实现）

**目标**：**最小可用工具系统**

```
✅ 工具定义（CallableTool2）
✅ 参数验证（Pydantic）
✅ 工具执行（Bash, ReadFile, WriteFile）
✅ 简单 Toolset
```

**缺少**：
- ❌ 输出限制（ToolResultBuilder）
- ❌ UI 增强（extract_key_argument）
- ❌ 测试工具（test.py）
- ❌ MCP 支持

---

### 官方实现（完整版）

**目标**：**生产级工具系统**

```
✅ 所有 Stage 7 功能
✅ 输出限制和截断
✅ UI 显示优化
✅ 用户批准机制
✅ MCP 协议支持
✅ 测试工具
```

---

## 📚 你需要额外理解的概念

### 1. **输出限制的重要性**

```python
# 危险：没有输出限制
output = subprocess.run(["find", "/"], capture_output=True).stdout
# 可能几GB！→ 超过 LLM context → 调用失败

# 安全：使用 ToolResultBuilder
builder = ToolResultBuilder(max_chars=50_000)
builder.write(output)
return builder.ok()  # 自动截断
```

**为什么重要**？
- LLM context 有限（通常 128K tokens）
- 大输出 = 高 API 成本
- 大输出 = 慢响应

---

### 2. **UI 显示优化**

```python
# Stage 7 显示（完整参数）
🔧 Calling Bash
   Arguments: {"command": "ls -la /very/long/path/to/directory", "timeout": 60}

# 官方显示（关键参数）
🔧 Calling Bash: ls -la /very/long/path/...
```

**extract_key_argument()** 的作用：
- 简化显示
- 突出重点
- 提升可读性

---

### 3. **流式工具调用**

```python
# LLM 可能流式生成工具调用：
# Step 1: {"name": "Bash"
# Step 2: , "arguments": {"command": "ls
# Step 3: -la", "timeout": 30}}

# extract_key_argument() 支持流式：
extract_key_argument(
    streamingjson.Lexer(),  # ⭐ 流式 JSON 解析器
    "Bash"
)
# → 实时提取 "command" 参数
```

---

### 4. **MCP 协议**

**MCP 解决的问题**：

```
传统方式：为每个外部服务写一个工具类
- GitHubTool
- SlackTool
- JiraTool
...

MCP 方式：一个 MCPTool 适配所有 MCP 服务器
- 服务器实现工具
- MCPTool 包装调用
- 无需修改 Kimi CLI
```

**MCP 架构**：
```
┌────────────────┐
│  Kimi CLI      │
│  ┌──────────┐  │
│  │ MCPTool  │  │  统一接口
│  └────┬─────┘  │
└───────┼────────┘
        │ MCP 协议
┌───────┼──────────────────────┐
│       ↓                       │
│  ┌─────────┐  ┌─────────┐   │
│  │ GitHub  │  │ Slack   │   │  各种服务
│  │ Server  │  │ Server  │   │
│  └─────────┘  └─────────┘   │
└───────────────────────────────┘
```

---

## 🚀 学习路径建议

### 当前阶段（Stage 7）
✅ 理解基础工具实现
✅ 理解 CallableTool2 框架
✅ 理解 Pydantic 验证

### Stage 8（推荐下一步）
1. 实现 `ToolResultBuilder`（输出限制）
2. 实现 `load_desc()`（描述分离）
3. 添加 `extract_key_argument()`（UI 优化）

### Stage 9+（高级特性）
1. 用户批准机制（Approval）
2. MCP 协议支持
3. 更多工具（Glob, Grep, Web搜索等）

---

## 📝 实践建议

### 立即可做

1. **添加输出限制**：
   ```python
   # 修改 Bash 工具
   builder = ToolResultBuilder(max_chars=10_000)
   for line in output_lines:
       builder.write(line)
   return builder.ok("Command executed.")
   ```

2. **分离工具描述**：
   ```python
   # 创建 bash/bash.md
   # 使用 load_desc() 加载
   ```

### 稍后可做（Stage 8+）

1. 实现测试工具（test.py）
2. 集成 MCP（如果需要外部服务）

---

**老王总结**：Stage 7 已经实现了**核心工具系统**，官方的这些额外文件是为了**生产级健壮性**和**高级特性**。现在的实现足够学习，等你需要更多功能时再逐步添加！🎉

---

**创建时间**：2025-01-16
**作者**：老王（暴躁技术流）

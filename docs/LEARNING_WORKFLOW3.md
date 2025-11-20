# Kimi CLI 学习工作流程 v3.0 (基于 Stage 20 完成后)

> **更新日期**: 2025-11-20
> **当前进度**: Stage 20 完成（D-Mail 时间旅行系统）
> **目的**: 规划 Stage 21+ 后续开发路线

---

## 📊 当前实现状态总览

### ✅ **已完成 Stage 6-20** (核心功能完备)

| Stage | 模块 | 状态 | 说明 |
|-------|------|------|------|
| **Stage 6-12** | 基础架构 | ✅ 完整 | CLI、Config、UI、Wire 机制 |
| **Stage 13-15** | UI 增强 | ✅ 完整 | StatusBar、Shell 优化 |
| **Stage 16** | Soul 核心 | ✅ 完整 | KimiSoul 主循环、_agent_loop |
| **Stage 17** | LLM 抽象 | ✅ 完整 | LLM 类、重试机制、Toolset |
| **Stage 18** | 会话管理 | ✅ 完整 | Session、Context（checkpoint/revert_to）|
| **Stage 19** | 时间旅行基础 | ✅ 完整 | DenwaRenji、SimpleCompaction |
| **Stage 20** | D-Mail 系统 | ✅ 完整 | SendDMail 工具、时间回滚 |

**已实现代码总量**: ~6,000 行高质量代码

---

## 🎯 核心功能完成度

### ✅ **已实现功能**

#### 1. **核心引擎** (100% 完成)
- ✅ **KimiSoul**: Agent 主循环、工具调用、流式响应
- ✅ **LLM 抽象层**: create_llm()、ChatProvider、重试机制
- ✅ **Context 管理**: 历史持久化、checkpoint、revert_to
- ✅ **Runtime**: LLM、DenwaRenji、Approval、Config 管理
- ✅ **Toolset**: CustomToolset、current_tool_call 上下文

#### 2. **时间旅行系统** (100% 完成)
- ✅ **DenwaRenji**: DMail 发送、检查点管理
- ✅ **SendDMail 工具**: 向过去发送消息
- ✅ **BackToTheFuture 异常**: 时间回滚机制
- ✅ **_agent_loop 集成**: 异常捕获、回滚处理
- ✅ **动态 checkpoint 策略**: 根据工具启用状态调整

#### 3. **Context 压缩** (100% 完成)
- ✅ **SimpleCompaction**: 保留重要消息、LLM 生成摘要
- ✅ **compact_context()**: KimiSoul 集成压缩功能
- ✅ **prompts 模块**: 压缩提示词模板

#### 4. **会话管理** (100% 完成)
- ✅ **Session**: create()、continue_()、历史持久化
- ✅ **Context**: 文件后端、checkpoint 系统
- ✅ **Metadata**: 动态版本读取

#### 5. **基础工具** (50% 完成)
- ✅ **Bash**: 执行 shell 命令
- ✅ **File**: ReadFile、WriteFile
- ✅ **DMail**: SendDMail（时间旅行）
- ❌ **Web**: 搜索、抓取（未实现）
- ❌ **Think**: 思考模式（未实现）
- ❌ **Todo**: 任务管理（未实现）
- ❌ **MCP**: 服务器集成（未实现）

#### 6. **UI 层** (80% 完成)
- ✅ **Shell UI**: 完整交互界面
- ✅ **Print UI**: 纯打印模式
- ✅ **StatusBar**: 实时状态显示
- ✅ **Wire 机制**: 消息传递、流式支持
- 🔲 **ACP 框架**: LSP 风格客户端（框架存在，未完整实现）

#### 7. **Approval 系统** (30% 完成)
- 🔲 **Approval 类**: 框架存在，只有简化版实现
- ❌ **ApprovalRequest**: Wire 消息未实现
- ❌ **UI 层集成**: 批准提示未实现
- ❌ **YOLO 模式**: 虽有代码但未真正生效

---

## 🚀 Stage 21-25 规划路线

### ⭐ **Stage 21: 实用工具扩展** (推荐优先)

**优先级**: 🔥🔥🔥🔥🔥 (最高)

**为什么优先**: 用户价值最高，实现难度适中，可立即提升 CLI 可用性

#### 📁 1. Think 工具 (my_cli/tools/think/__init__.py)

**功能**: 让 Agent 展示思考过程

```python
class Think(CallableTool2[ThinkParams]):
    """
    Think 工具 - Agent 思考过程展示

    让 Agent 明确表达思考过程，提升透明度。

    使用场景：
    - 复杂问题分析
    - 决策过程说明
    - 多步骤任务规划
    """
    name: str = "Think"
    description: str = load_desc(Path(__file__).parent / "think.md")
    params: type[ThinkParams] = ThinkParams

    async def __call__(self, params: ThinkParams) -> ToolReturnType:
        # 思考内容通过 Wire 发送到 UI
        return ToolResult(output=f"Thinking: {params.thought}")

class ThinkParams(BaseModel):
    thought: str = Field(description="Agent's thinking process")
```

**think.md 内容**:
```markdown
Use this tool to express your thinking process explicitly.

When to use:
- Before making complex decisions
- When analyzing multi-step problems
- To explain your reasoning to the user

Example:
Think: "I need to read the config file first to understand the project structure,
then I can suggest appropriate changes."
```

**实现时间**: 1-2 小时
**测试复杂度**: 低
**用户价值**: ⭐⭐⭐⭐⭐

#### 📁 2. Web 工具 (my_cli/tools/web/__init__.py)

**功能**: 网页搜索和抓取

```python
class WebSearch(CallableTool2[SearchParams]):
    """网页搜索"""
    name: str = "WebSearch"

    async def __call__(self, params: SearchParams) -> ToolReturnType:
        # 使用搜索 API（DuckDuckGo、Google 等）
        results = await search_web(params.query, limit=params.limit)
        return ToolResult(output=format_search_results(results))

class WebFetch(CallableTool2[FetchParams]):
    """抓取网页内容"""
    name: str = "WebFetch"

    async def __call__(self, params: FetchParams) -> ToolReturnType:
        # 使用 httpx 或 aiohttp 抓取
        content = await fetch_url(params.url)
        # 转换为 Markdown（使用 html2text）
        markdown = html_to_markdown(content)
        return ToolResult(output=markdown)
```

**依赖**:
- `httpx` 或 `aiohttp`: HTTP 客户端
- `html2text`: HTML 转 Markdown
- `beautifulsoup4`: HTML 解析

**实现时间**: 4-6 小时
**测试复杂度**: 中（需要 mock HTTP 请求）
**用户价值**: ⭐⭐⭐⭐⭐

#### 📁 3. Todo 工具 (my_cli/tools/todo/__init__.py)

**功能**: 任务列表管理

```python
class TodoAdd(CallableTool2[TodoAddParams]):
    """添加 TODO 项"""
    name: str = "TodoAdd"

    async def __call__(self, params: TodoAddParams) -> ToolReturnType:
        # 添加到 TODO 列表（存储在 work_dir/.kimi_todos.json）
        todo_manager.add(params.task, params.priority)
        return ToolResult(output=f"Added: {params.task}")

class TodoList(CallableTool2[None]):
    """列出所有 TODO"""
    name: str = "TodoList"

    async def __call__(self, params: None) -> ToolReturnType:
        todos = todo_manager.list_all()
        return ToolResult(output=format_todos(todos))

class TodoComplete(CallableTool2[TodoCompleteParams]):
    """标记 TODO 完成"""
    name: str = "TodoComplete"

    async def __call__(self, params: TodoCompleteParams) -> ToolReturnType:
        todo_manager.complete(params.task_id)
        return ToolResult(output=f"Completed: {params.task_id}")
```

**实现时间**: 3-4 小时
**测试复杂度**: 低
**用户价值**: ⭐⭐⭐⭐

---

### ⭐ **Stage 22: Approval 系统完善** (安全增强)

**优先级**: 🔥🔥🔥🔥 (高)

**完成条件**: 危险操作需用户批准，支持 YOLO 模式

#### 📁 1. Approval 核心实现 (my_cli/soul/approval.py)

**需要实现**:
```python
async def request(self, sender: str, action: str, description: str) -> bool:
    # 1. 获取当前工具调用
    tool_call = get_current_tool_call_or_none()
    if tool_call is None:
        raise RuntimeError("Approval must be requested from a tool call.")

    # 2. 检查 YOLO 模式
    if self._yolo:
        return True

    # 3. 检查会话级自动批准
    if action in self._auto_approve_actions:
        return True

    # 4. 创建批准请求
    from my_cli.wire.message import ApprovalRequest
    request = ApprovalRequest(
        tool_call_id=tool_call.id,
        sender=sender,
        action=action,
        description=description,
    )

    # 5. 放入队列
    self._request_queue.put_nowait(request)

    # 6. 等待响应
    response = await request.wait()

    # 7. 处理响应
    if response == ApprovalResponse.APPROVE:
        return True
    elif response == ApprovalResponse.APPROVE_FOR_SESSION:
        self._auto_approve_actions.add(action)
        return True
    else:
        return False

async def fetch_request(self):
    return await self._request_queue.get()
```

#### 📁 2. Wire 消息 (my_cli/wire/message.py)

```python
class ApprovalRequest(BaseMessage):
    """批准请求"""
    id: str
    tool_call_id: str
    sender: str
    action: str
    description: str
    _future: asyncio.Future[ApprovalResponse] = Field(exclude=True)

    def __init__(self, **data):
        super().__init__(**data)
        self._future = asyncio.Future()

    async def wait(self) -> ApprovalResponse:
        return await self._future

    def resolve(self, response: ApprovalResponse):
        self._future.set_result(response)

class ApprovalResponse(Enum):
    APPROVE = "approve"
    APPROVE_FOR_SESSION = "approve_for_session"
    REJECT = "reject"
```

#### 📁 3. KimiSoul 集成 (my_cli/soul/kimisoul.py)

```python
async def _agent_loop(self) -> None:
    # 启动 approval 任务
    approval_task = asyncio.create_task(self._pipe_approval_to_wire())

    try:
        # ... 主循环 ...
    finally:
        approval_task.cancel()

async def _pipe_approval_to_wire(self):
    """将批准请求通过 Wire 发送到 UI"""
    while True:
        request = await self._runtime.approval.fetch_request()
        wire_send(request)
```

#### 📁 4. UI 层处理 (my_cli/ui/shell/__init__.py)

```python
def handle_approval_request(request: ApprovalRequest):
    """处理批准请求"""
    print(f"\n⚠️  {request.sender} wants to: {request.description}")
    print("Approve? [y]es / [n]o / [a]lways for this session")

    response = input("> ").lower()

    if response == "y":
        request.resolve(ApprovalResponse.APPROVE)
    elif response == "a":
        request.resolve(ApprovalResponse.APPROVE_FOR_SESSION)
    else:
        request.resolve(ApprovalResponse.REJECT)
```

**实现时间**: 1周
**测试复杂度**: 高（需要测试异步交互）
**用户价值**: ⭐⭐⭐⭐

---

### ⭐ **Stage 23: MCP 服务器集成** (扩展性)

**优先级**: 🔥🔥🔥 (中)

**完成条件**: 支持加载外部 MCP 服务器，动态扩展工具

#### 📁 1. MCP 客户端 (my_cli/tools/mcp.py)

```python
class MCPClient:
    """MCP 服务器客户端"""

    def __init__(self, server_config: dict):
        self.command = server_config["command"]
        self.args = server_config["args"]
        self.env = server_config.get("env", {})
        self._process: asyncio.subprocess.Process | None = None

    async def start(self):
        """启动 MCP 服务器"""
        self._process = await asyncio.create_subprocess_exec(
            self.command,
            *self.args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={**os.environ, **self.env},
        )

    async def call_tool(self, name: str, arguments: dict) -> dict:
        """调用 MCP 工具"""
        request = {
            "jsonrpc": "2.0",
            "id": generate_id(),
            "method": "tools/call",
            "params": {
                "name": name,
                "arguments": arguments,
            },
        }

        # 发送请求
        await self._send(request)

        # 接收响应
        response = await self._receive()

        return response["result"]

    async def list_tools(self) -> list[dict]:
        """列出 MCP 服务器提供的工具"""
        request = {
            "jsonrpc": "2.0",
            "id": generate_id(),
            "method": "tools/list",
        }

        await self._send(request)
        response = await self._receive()

        return response["result"]["tools"]
```

#### 📁 2. 动态工具注册 (my_cli/soul/toolset.py)

```python
async def load_mcp_tools(mcp_config: dict, toolset: Toolset):
    """从 MCP 服务器加载工具"""
    client = MCPClient(mcp_config)
    await client.start()

    # 获取工具列表
    tools = await client.list_tools()

    # 为每个工具创建包装器
    for tool_def in tools:
        tool = create_mcp_tool_wrapper(client, tool_def)
        toolset.register_tool(tool)
```

**依赖**:
- MCP 协议规范
- JSON-RPC 2.0

**实现时间**: 2周
**测试复杂度**: 高（需要测试进程通信）
**用户价值**: ⭐⭐⭐⭐

---

### ⭐ **Stage 24: Agent 规范增强** (灵活性)

**优先级**: 🔥🔥 (中低)

**完成条件**: 支持 YAML/JSON Agent 规范，动态加载

#### 📁 1. AgentSpec 完善 (my_cli/agentspec.py)

```python
class AgentSpec(BaseModel):
    """Agent 规范"""
    name: str
    description: str
    system_prompt: str
    tools: list[str]  # 工具名称列表
    capabilities: set[str] = set()
    mcp_servers: list[dict] = []  # MCP 服务器配置
    thinking_enabled: bool = False
    yolo: bool = False

async def load_agent_spec(file_path: Path) -> AgentSpec:
    """加载 Agent 规范（支持 YAML/JSON）"""
    if file_path.suffix == ".yaml" or file_path.suffix == ".yml":
        import yaml
        with open(file_path) as f:
            data = yaml.safe_load(f)
    else:
        with open(file_path) as f:
            data = json.load(f)

    return AgentSpec(**data)

async def create_agent_from_spec(
    spec: AgentSpec,
    work_dir: Path,
) -> Agent:
    """根据规范创建 Agent"""
    # 创建 Toolset
    toolset = CustomToolset()

    # 注册内置工具
    for tool_name in spec.tools:
        tool = create_builtin_tool(tool_name)
        toolset.register_tool(tool)

    # 加载 MCP 工具
    for mcp_config in spec.mcp_servers:
        await load_mcp_tools(mcp_config, toolset)

    # 创建 Agent
    agent = Agent(
        name=spec.name,
        work_dir=work_dir,
        system_prompt=spec.system_prompt,
        toolset=toolset,
    )

    return agent
```

#### 📁 2. CLI 参数支持 (my_cli/cli.py)

```bash
# 使用 Agent 规范启动
python cli.py --agent agents/coding-assistant.yaml

# 查看可用 Agent
python cli.py --list-agents
```

**实现时间**: 1周
**测试复杂度**: 中
**用户价值**: ⭐⭐⭐

---

### ⭐ **Stage 25: 分享功能** (协作)

**优先级**: 🔥 (低)

**完成条件**: 支持会话历史分享（脱敏）

#### 📁 1. 分享功能 (my_cli/share.py)

```python
async def share_session(
    session: Session,
    anonymize: bool = True,
) -> str:
    """分享会话历史"""
    # 加载历史
    history = await session.load_history()

    # 脱敏处理
    if anonymize:
        history = sanitize_history(history)

    # 转换为分享格式
    share_data = {
        "session_id": session.id,
        "agent_name": session.agent_name,
        "history": [msg.dict() for msg in history],
        "metadata": {
            "created_at": session.created_at,
            "message_count": len(history),
        },
    }

    # 上传到分享服务（或生成本地文件）
    share_url = await upload_share(share_data)

    return share_url

def sanitize_history(history: list[Message]) -> list[Message]:
    """脱敏处理"""
    sanitized = []

    for msg in history:
        content = msg.content

        # 移除 API Key
        content = re.sub(r"sk-[a-zA-Z0-9]{32,}", "[API_KEY]", content)

        # 替换真实路径
        content = re.sub(r"/home/[^/]+/", "/home/user/", content)

        # 脱敏邮箱
        content = re.sub(
            r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
            "[EMAIL]",
            content,
        )

        sanitized.append(msg.copy(update={"content": content}))

    return sanitized
```

**实现时间**: 1周
**测试复杂度**: 中
**用户价值**: ⭐⭐⭐

---

## 📊 实现优先级矩阵

| Stage | 功能 | 用户价值 | 实现难度 | 时间估算 | 推荐优先级 |
|-------|------|---------|---------|---------|-----------|
| **Stage 21** | Think/Web/Todo 工具 | ⭐⭐⭐⭐⭐ | 低 | 1-2 周 | 🔥🔥🔥🔥🔥 |
| **Stage 22** | Approval 系统 | ⭐⭐⭐⭐ | 中 | 1 周 | 🔥🔥🔥🔥 |
| **Stage 23** | MCP 集成 | ⭐⭐⭐⭐ | 高 | 2 周 | 🔥🔥🔥 |
| **Stage 24** | AgentSpec 增强 | ⭐⭐⭐ | 中 | 1 周 | 🔥🔥 |
| **Stage 25** | 分享功能 | ⭐⭐⭐ | 中 | 1 周 | 🔥 |

---

## 🎯 推荐实施路线

### 第 1 阶段（1-2 周）：Stage 21 - 实用工具扩展
- **第 1-2 天**: Think 工具（最简单）
- **第 3-6 天**: Web 工具（搜索 + 抓取）
- **第 7-10 天**: Todo 工具（任务管理）
- **第 11-14 天**: 测试 + 文档

**里程碑**: CLI 功能大幅提升，可用性显著增强

### 第 2 阶段（1 周）：Stage 22 - Approval 系统
- **第 1-2 天**: Approval.request() 完整实现
- **第 3-4 天**: Wire 消息（ApprovalRequest/Response）
- **第 5-6 天**: UI 层集成（Shell/Print/ACP）
- **第 7 天**: 测试 + 文档

**里程碑**: 安全性提升，危险操作需确认

### 第 3 阶段（2 周）：Stage 23 - MCP 集成
- **第 1-3 天**: MCPClient 实现
- **第 4-6 天**: JSON-RPC 通信
- **第 7-10 天**: 动态工具注册
- **第 11-14 天**: 测试 + 文档

**里程碑**: 可扩展性大幅提升，支持外部工具

### 第 4 阶段（可选）：Stage 24-25
- 根据实际需求和时间决定是否实施

---

## 🧪 测试策略

### Stage 21 测试矩阵

| 测试类型 | 测试内容 | 命令 |
|---------|---------|------|
| **单元测试** | Think 工具 | `pytest tests/test_think.py` |
| **单元测试** | WebSearch 工具 | `pytest tests/test_web.py::test_search` |
| **单元测试** | WebFetch 工具 | `pytest tests/test_web.py::test_fetch` |
| **单元测试** | Todo 工具 | `pytest tests/test_todo.py` |
| **集成测试** | 工具集成 | `pytest tests/test_toolset.py` |
| **E2E 测试** | 完整流程 | `python cli.py -c "search python tutorial"` |

### Stage 22 测试矩阵

| 测试类型 | 测试内容 | 命令 |
|---------|---------|------|
| **单元测试** | Approval.request() | `pytest tests/test_approval.py::test_request` |
| **单元测试** | YOLO 模式 | `pytest tests/test_approval.py::test_yolo` |
| **单元测试** | 会话级批准 | `pytest tests/test_approval.py::test_session_approve` |
| **集成测试** | Wire 消息 | `pytest tests/test_wire.py::test_approval` |
| **集成测试** | UI 交互 | `pytest tests/test_shell.py::test_approval_prompt` |

---

## 💡 开发建议

### 1. 渐进式实现策略

```bash
# Step 1: 实现 Think 工具（最简单）
git checkout -b feature/think-tool
# 实现 Think 工具
git commit -m "feat(tools): 实现 Think 工具"
pytest tests/test_think.py
git push

# Step 2: 实现 WebSearch
git checkout -b feature/web-search
# 实现 WebSearch
git commit -m "feat(tools): 实现 WebSearch 工具"
git push

# Step 3: 实现 WebFetch
# ...
```

### 2. 代码复用原则

```python
# 抽象通用工具基类
class SimpleCallableTool(CallableTool2[TParams]):
    """简单工具基类（不需要 Approval）"""

    async def __call__(self, params: TParams) -> ToolReturnType:
        result = await self.execute(params)
        return ToolResult(output=result)

    async def execute(self, params: TParams) -> str:
        """子类实现具体逻辑"""
        raise NotImplementedError

# Think 工具只需要实现 execute
class Think(SimpleCallableTool[ThinkParams]):
    async def execute(self, params: ThinkParams) -> str:
        return f"Thinking: {params.thought}"
```

### 3. 测试驱动开发

```python
# 先写测试
def test_think_tool():
    tool = Think()
    result = await tool(ThinkParams(thought="分析问题..."))
    assert "Thinking" in result.output
    assert "分析问题" in result.output

# 再实现功能
class Think:
    async def __call__(self, params: ThinkParams):
        return ToolResult(output=f"Thinking: {params.thought}")
```

### 4. 文档同步更新

每个功能完成后：
- [ ] 更新 `docs/STAGE_XX_*.md`
- [ ] 更新 `README.md`（使用示例）
- [ ] 更新 `tests/`（测试覆盖）
- [ ] 更新 `kimi-cli-learn/`（学习笔记）

---

## 📚 技术债务清单

### 高优先级
- [ ] **Approval 系统完整实现**（当前只是简化版）
- [ ] **ACP 框架完善**（LSP 客户端未完整实现）
- [ ] **错误处理统一**（缺少统一的错误处理策略）

### 中优先级
- [ ] **性能优化**（大文件读取、长对话压缩）
- [ ] **日志系统完善**（结构化日志、日志轮转）
- [ ] **配置验证增强**（更详细的错误提示）

### 低优先级
- [ ] **国际化支持**（多语言）
- [ ] **插件系统**（第三方扩展）
- [ ] **性能监控**（token 使用统计、响应时间）

---

## ✅ 成功指标

### Stage 21 成功标准
- [ ] Think 工具可用，Agent 能展示思考过程
- [ ] WebSearch 可用，能搜索并返回结果
- [ ] WebFetch 可用，能抓取网页并转换为 Markdown
- [ ] Todo 工具可用，能管理任务列表
- [ ] 所有工具通过单元测试和集成测试
- [ ] 完整的使用文档和示例

### Stage 22 成功标准
- [ ] 危险操作需用户批准
- [ ] YOLO 模式可用（自动批准）
- [ ] 会话级自动批准可用
- [ ] UI 层正确显示批准提示
- [ ] 通过所有测试用例

### Stage 23 成功标准
- [ ] 可加载外部 MCP 服务器
- [ ] 动态注册工具到 Toolset
- [ ] JSON-RPC 通信稳定
- [ ] 至少支持 2 个示例 MCP 服务器

---

## 🚀 快速开始

### Stage 21 第一天行动清单

**上午** (2 小时):
- [ ] 阅读官方 Think 工具实现
- [ ] 创建 `my_cli/tools/think/` 目录
- [ ] 实现 Think 工具基础结构

**下午** (3 小时):
- [ ] 完成 Think 工具实现
- [ ] 编写单元测试 `tests/test_think.py`
- [ ] 运行测试验证

**第二天** (5 小时):
- [ ] 开始 WebSearch 工具实现
- [ ] 集成搜索 API（DuckDuckGo）
- [ ] 编写测试

**预计**: 2 周完成 Stage 21

---

## 📖 学习资源

### 官方代码参考
```bash
cd kimi-cli-fork/src/kimi_cli/tools

# 查看工具实现
cat think/__init__.py    # Think 工具
cat web/__init__.py      # Web 工具
cat todo/__init__.py     # Todo 工具
cat mcp.py               # MCP 客户端
```

### 依赖库文档
- **httpx**: https://www.python-httpx.org/
- **html2text**: https://github.com/Alir3z4/html2text
- **beautifulsoup4**: https://www.crummy.com/software/BeautifulSoup/
- **pyyaml**: https://pyyaml.org/

### MCP 协议
- **官方文档**: https://spec.modelcontextprotocol.io/

---

## ✅ 总结

### 📋 当前状态
- **已实现**: Stage 6-20，核心功能完备
- **代码量**: ~6,000 行高质量代码
- **测试覆盖**: 核心功能均有测试

### 🎯 下一步行动
- **Stage 21**: 实用工具扩展（Think/Web/Todo）
- **预计时间**: 1-2 周
- **用户价值**: 最高

### 🔧 开发原则
- **渐进式开发**: 一次实现一个工具
- **测试驱动**: 先写测试，再实现功能
- **文档同步**: 代码和文档同步更新
- **代码复用**: 抽象通用基类

### 📊 长期规划
- **Stage 21**: 工具扩展（2 周）
- **Stage 22**: Approval 系统（1 周）
- **Stage 23**: MCP 集成（2 周）
- **Stage 24-25**: 可选增强

**立即行动**: 开始 Stage 21，优先实现 Think 工具！

---

**Created by**: Claude（老王编程助手）
**Version**: 3.0 (基于 Stage 20 完成后)
**Last Updated**: 2025-11-20
**Status**: 🟢 Stage 21 Ready to Start

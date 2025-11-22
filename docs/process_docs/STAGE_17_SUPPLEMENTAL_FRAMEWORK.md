# 补充文件框架创建总结

> **完成时间**: 2025-01-XX
> **目的**: 补充 tools 和 ui/acp 模块的框架

---

## 📁 补充创建的文件

### Tools 模块（`my_cli/tools/`）

| 文件 | 状态 | 开始阶段 | 核心功能 |
|------|-----|---------|---------|
| `__init__.py` | ✅ Stage 7-8 已实现 | Stage 17 扩展 | SkipThisTool、extract_key_argument（TODO） |
| `utils.py` | ✅ Stage 7-8 已实现 | Stage 17 完善 | ToolResultBuilder、load_desc、truncate_line |

### UI 模块（`my_cli/ui/`）

| 文件 | 状态 | 开始阶段 | 核心功能 |
|------|-----|---------|---------|
| `acp/__init__.py` | ✅ 框架完成 | Stage 20 | ACP UI（LSP 风格的客户端）|

---

## 🗺️ Tools 模块演进路线

### Stage 7-8: 基础工具系统 ✅ 已完成

**已实现的文件**:
- `my_cli/tools/__init__.py` - SkipThisTool 异常
- `my_cli/tools/utils.py` - ToolResultBuilder 完整实现
- `my_cli/tools/bash/` - Bash 工具
- `my_cli/tools/file/` - ReadFile, WriteFile 工具
- `my_cli/tools/toolset.py` - SimpleToolset

**已实现的功能**:
- ✅ ToolResultBuilder（输出限制）
- ✅ load_desc()（加载工具描述）
- ✅ truncate_line()（行截断）
- ✅ ToolRejectedError（用户拒绝）

---

### Stage 17: extract_key_argument ⭐ TODO

**需要完善的文件**:
- `my_cli/tools/__init__.py` - extract_key_argument()

**核心功能**:
```python
def extract_key_argument(json_content: str | streamingjson.Lexer, tool_name: str) -> str | None:
    """
    从工具参数中提取关键参数（用于 UI 显示）

    官方支持的工具：
    - Bash/CMD: command
    - ReadFile/WriteFile/StrReplaceFile: path
    - Glob: pattern
    - Grep: pattern
    - Task: description
    - SendDMail: "El Psy Kongroo"（彩蛋）
    - Think: thought
    - SearchWeb: query
    - FetchURL: url
    """
```

**使用场景**:
```python
# 在 ACP UI 中使用
tool_call_state = _ToolCallState(tool_call)
title = tool_call_state.get_title()  # 使用 extract_key_argument
# → "Bash: ls -la"
# → "ReadFile: src/main.py"
```

---

### Stage 18+: 更多工具 ⭐ TODO

**官方工具目录结构**:
```
tools/
├── bash/          # ✅ Stage 8 已实现
├── file/          # ✅ Stage 8 已实现（ReadFile, WriteFile）
│   └── ...        # ⚠️ TODO: Glob, Grep, StrReplaceFile
├── web/           # ⚠️ TODO: SearchWeb, FetchURL
├── task/          # ⚠️ TODO: Task（子 Agent）
├── dmail/         # ⚠️ TODO: SendDMail（时间旅行）
├── think/         # ⚠️ TODO: Think（思考模式）
├── todo/          # ⚠️ TODO: SetTodoList
├── mcp.py         # ⚠️ TODO: MCP 工具集成
└── test.py        # ⚠️ TODO: TestTool（调试工具）
```

**需要实现的工具**:

1. **Glob 工具**（Stage 18）
   - 文件模式匹配
   - 支持 `**/*.py` 等模式

2. **Grep 工具**（Stage 18）
   - 内容搜索
   - 支持正则表达式

3. **StrReplaceFile 工具**（Stage 18）
   - 字符串替换（类似 sed）
   - 支持多行替换

4. **SearchWeb 工具**（Stage 18）
   - 网页搜索
   - 返回搜索结果

5. **FetchURL 工具**（Stage 18）
   - 获取网页内容
   - 支持 HTTP/HTTPS

6. **Task 工具**（Stage 19）
   - 启动子 Agent
   - 支持并发任务

7. **SendDMail 工具**（Stage 19）
   - 发送 D-Mail 到过去
   - 集成 DenwaRenji 系统

8. **Think 工具**（Stage 20）
   - 思考模式
   - 输出思考过程

9. **SetTodoList 工具**（Stage 20）
   - 设置 TODO 列表
   - UI 层展示

10. **MCP 工具集成**（Stage 21）
    - 加载 MCP 服务器
    - 动态注册工具

---

## 🖥️ UI/ACP 模块演进路线

### Stage 4-16: Shell UI ✅ 已完成

**已实现的文件**:
- `my_cli/ui/shell/__init__.py` - ShellApp
- `my_cli/ui/shell/prompt.py` - CustomPromptSession
- `my_cli/ui/shell/printer.py` - PrinterUISide

**已实现的功能**:
- ✅ 多行输入
- ✅ 自动补全
- ✅ 文件路径补全
- ✅ 状态栏显示
- ✅ 流式输出

---

### Stage 20: ACP UI ⭐ TODO

**需要实现的文件**:
- `my_cli/ui/acp/__init__.py` - ACPApp

**核心功能**:

1. **ACP 服务器**
   - 监听客户端连接
   - JSON-RPC 2.0 协议
   - WebSocket/TCP 通信

2. **事件处理**
   ```python
   async def _ui_loop_fn(self, wire_ui: WireUISide):
       while True:
           msg = await wire_ui.receive()
           match msg:
               case StepBegin(n):
                   await acp_server.send("stepBegin", {"n": n})
               case TextPart(text):
                   await acp_server.send("textDelta", {"text": text})
               case ToolCall(...):
                   await acp_server.send("toolCallBegin", {...})
               # ...
   ```

3. **工具调用状态管理**
   ```python
   class _ToolCallState:
       - 流式参数解析（streamingjson.Lexer）
       - 提取关键参数（extract_key_argument）
       - 生成标题（get_title）
   ```

4. **批准请求处理**
   ```python
   case ApprovalRequest(id, action, description):
       response = await acp_server.request_approval(id, action, description)
       approval_request.resolve(response)
   ```

**ACP 消息格式**:

```typescript
// 文本片段
interface TextDelta {
    method: "textDelta"
    params: {
        text: string
    }
}

// 工具调用开始
interface ToolCallBegin {
    method: "toolCallBegin"
    params: {
        id: string
        name: string
        title: string  // 使用 extract_key_argument 生成
    }
}

// 工具调用结束
interface ToolCallEnd {
    method: "toolCallEnd"
    params: {
        id: string
        success: boolean
        error?: string
    }
}

// 批准请求
interface ApprovalRequest {
    method: "approvalRequest"
    params: {
        id: string
        sender: string
        action: string
        description: string
    }
}
```

**客户端示例**（VS Code 扩展）:
```typescript
// 连接到 ACP 服务器
const client = new ACP.Client('ws://localhost:8080')

// 监听事件
client.on('textDelta', (params) => {
    editor.appendText(params.text)
})

client.on('toolCallBegin', (params) => {
    ui.showToolCall(params.id, params.title)
})

client.on('approvalRequest', async (params) => {
    const approved = await ui.showApprovalDialog(params.description)
    client.send('approvalResponse', {
        id: params.id,
        response: approved ? 'approve' : 'reject'
    })
})
```

---

## 📊 工具系统依赖关系

```
Tools 模块
├─ __init__.py
│  ├─ SkipThisTool ✅
│  └─ extract_key_argument() ⚠️ TODO Stage 17
│
├─ utils.py
│  ├─ ToolResultBuilder ✅
│  ├─ load_desc() ✅
│  ├─ truncate_line() ✅
│  └─ ToolRejectedError ✅
│
├─ bash/ ✅ Stage 8
├─ file/ ✅ Stage 8
│  ├─ ReadFile ✅
│  ├─ WriteFile ✅
│  ├─ Glob ⚠️ TODO Stage 18
│  ├─ Grep ⚠️ TODO Stage 18
│  └─ StrReplaceFile ⚠️ TODO Stage 18
│
├─ web/ ⚠️ TODO Stage 18
│  ├─ SearchWeb
│  └─ FetchURL
│
├─ task/ ⚠️ TODO Stage 19
│  └─ Task（子 Agent）
│
├─ dmail/ ⚠️ TODO Stage 19
│  └─ SendDMail（时间旅行）
│
├─ think/ ⚠️ TODO Stage 20
│  └─ Think（思考模式）
│
├─ todo/ ⚠️ TODO Stage 20
│  └─ SetTodoList
│
└─ mcp.py ⚠️ TODO Stage 21
   └─ MCP 工具集成
```

---

## ✅ 总结

老王我补充创建了：
- ✅ `my_cli/tools/__init__.py` - 添加 Stage 17+ TODO 注释
- ✅ `my_cli/tools/utils.py` - 已在 Stage 7-8 完整实现
- ✅ `my_cli/ui/acp/__init__.py` - Stage 20 ACP UI 框架

现在整个项目的文件框架都齐全了！

**已完成的框架文件总数**: 15 个
- Soul 模块: 5 个
- 根模块: 7 个
- Tools 模块: 2 个
- UI 模块: 1 个

每个文件都包含：
1. 学习目标
2. 阶段演进
3. 官方对照
4. TODO 注释
5. 使用场景

崽芽子你现在要实现哪个功能，直接看对应文件就知道怎么干了！SB 的规划都没这么详细！😤

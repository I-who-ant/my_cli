# Stage 7 工具系统基础总结

## 🎯 Stage 7 目标

实现 **工具系统（Toolset）基础架构**，为 Agent 提供调用外部工具的能力。

**注意**：Stage 7 是**基础架构阶段**，实现了工具定义和基础组件，完整的工具调用流程将在后续阶段完成。

---

## ✅ 已完成的工作

### 1. 工具辅助函数（utils.py）⭐ 新增

#### `my_cli/tools/utils.py` (323行)
**工具辅助函数集合**

```python
# 1. 工具描述加载器
def load_desc(path: Path, substitutions: dict[str, str] | None = None) -> str:
    """从 Markdown 文件加载工具描述（支持模板替换）"""
    description = path.read_text()
    if substitutions:
        description = string.Template(description).substitute(substitutions)
    return description

# 2. 输出限制器
class ToolResultBuilder:
    """构建工具结果，自动限制输出大小"""
    def __init__(self, max_chars=50_000, max_line_length=2000):
        ...

    def write(self, text: str) -> int:
        """写入输出（自动截断）"""
        ...

    def ok(self, message: str = "") -> ToolOk:
        """生成 ToolOk（自动添加截断提示）"""
        ...

    def error(self, message: str, brief: str) -> ToolError:
        """生成 ToolError（自动添加截断提示）"""
        ...

# 3. 用户拒绝错误
class ToolRejectedError(ToolError):
    """工具被用户拒绝（Stage 8+ 批准机制）"""
    ...
```

**核心功能**：
- ✅ 描述文件分离（Markdown 管理）
- ✅ 输出自动截断（防止超限）
- ✅ 截断提示自动添加
- ✅ 行长度限制
- ✅ 用户拒绝处理

---

### 2. 工具实现（3个基础工具 + 增强）

#### `my_cli/tools/bash/__init__.py` (164行) ⭐ 已优化
**Bash 工具 - 执行 Shell 命令**

```python
class Bash(CallableTool2[Params]):
    name: str = "Bash"
    description: str = load_desc(Path(__file__).parent / "bash.md")  # ⭐ 从文件加载

    async def __call__(self, params: Params) -> ToolReturnType:
        # ⭐ 使用 ToolResultBuilder 限制输出
        builder = ToolResultBuilder()

        def stdout_cb(line: bytes):
            builder.write(line.decode())  # ⭐ 自动截断

        exitcode = await _stream_subprocess(...)

        if exitcode == 0:
            return builder.ok("Command executed successfully")  # ⭐ 自动添加截断提示
        else:
            return builder.error(f"Failed: {exitcode}", brief="Failed")
```

**Stage 7 增强**：
- ✅ 使用 `load_desc()` 从 `bash.md` 加载描述
- ✅ 使用 `ToolResultBuilder` 自动限制输出（50K）
- ✅ 自动截断超长输出
- ✅ 自动添加截断提示给 LLM

**核心技术**：
- `asyncio.create_subprocess_shell` - 异步子进程
- `asyncio.StreamReader` - 流式读取输出
- `asyncio.wait_for` - 超时控制
- `ToolResultBuilder` - 输出限制 ⭐

---

#### `my_cli/tools/file/__init__.py` (155行) ⭐ 已优化
**ReadFile 和 WriteFile 工具**

```python
class ReadFile(CallableTool2[ReadFileParams]):
    name: str = "ReadFile"
    description: str = load_desc(Path(__file__).parent / "readfile.md")  # ⭐ 从文件加载

    async def __call__(self, params: ReadFileParams) -> ToolReturnType:
        file_path = Path(params.path)
        content = file_path.read_text()

        # ⭐ 使用 ToolResultBuilder 限制大文件输出
        builder = ToolResultBuilder()
        builder.write(content)  # ⭐ 自动截断
        return builder.ok(f"File read: {params.path}")

class WriteFile(CallableTool2[WriteFileParams]):
    name: str = "WriteFile"
    description: str = load_desc(Path(__file__).parent / "writefile.md")  # ⭐ 从文件加载

    async def __call__(self, params: WriteFileParams) -> ToolReturnType:
        file_path = Path(params.path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(params.content)
        return ToolOk(output=f"Written {len(params.content)} chars")
```

**Stage 7 增强**：
- ✅ ReadFile 使用 `ToolResultBuilder`（防止大文件超限）
- ✅ WriteFile 使用 `load_desc()`（描述分离）
- ✅ 自动创建父目录

**核心技术**：
- `pathlib.Path` - 现代路径操作
- `ToolResultBuilder` - 大文件输出限制 ⭐

---

#### 工具描述文件（Markdown）⭐ 新增

```
my_cli/tools/
├── bash/
│   └── bash.md (37行) - Bash 工具描述
└── file/
    ├── readfile.md (31行) - ReadFile 工具描述
    └── writefile.md (35行) - WriteFile 工具描述
```

**示例**（bash.md）：
````markdown
# Bash Tool

Execute a bash command in the shell.

## Parameters
- `command` (required): The bash command to execute
- `timeout` (optional): Timeout in seconds

## Examples
```bash
ls -la
df -h
```
````

**优势**：
- ✅ 描述与代码分离
- ✅ 易于维护和更新
- ✅ 支持 Markdown 格式
- ✅ 可添加示例和详细说明

---

### 3. 工具集管理器

#### `my_cli/tools/toolset.py` (78行)
**SimpleToolset - 简单工具集实现**

```python
class SimpleToolset:
    """管理工具注册和调度"""

    def __init__(self):
        self._tools = {
            "Bash": Bash(),
            "ReadFile": ReadFile(),
            "WriteFile": WriteFile(),
        }

    def get_tools(self) -> Sequence[Tool]:
        """获取所有工具定义（给 LLM）"""
        return [tool.base for tool in self._tools.values()]

    async def handle(self, tool_call: ToolCall) -> ToolResult:
        """处理工具调用"""
        tool = self._tools[tool_call.name]
        result = await tool.call(tool_call.arguments)
        return ToolResult(tool_call_id=tool_call.id, result=result)
```

**职责**：
- 工具注册
- 提供工具列表给 LLM
- 调度工具执行

---

### 4. Wire 消息类型扩展

#### 更新 `my_cli/wire/message.py`

```python
from kosong.tooling import ToolResult  # ⭐ 新增导入

# 更新 Event 类型联合
type Event = (
    ControlFlowEvent
    | ContentPart
    | ToolCall
    | ToolCallPart
    | ToolResult  # ⭐ 新增
)
```

**Stage 7 新增消息类型**：
- `ToolResult` - 工具执行结果（从 kosong.tooling 导入）

---

## 📚 核心概念

### 1. CallableTool2 模式

```python
from kosong.tooling import CallableTool2, ToolReturnType
from pydantic import BaseModel, Field

class Params(BaseModel):
    """工具参数定义（Pydantic 自动验证）"""
    command: str = Field(description="The command to execute")
    timeout: int = Field(default=60, ge=1, le=300)

class MyTool(CallableTool2[Params]):
    """工具实现"""
    name: str = "MyTool"
    description: str = "Tool description for LLM"
    params: type[Params] = Params

    async def __call__(self, params: Params) -> ToolReturnType:
        # 1. 执行工具逻辑
        result = await do_something(params.command)

        # 2. 返回结果
        if success:
            return ToolOk(output=result, message="Success")
        else:
            return ToolError(output=error, message="Failed")
```

**优势**：
- ✅ 类型安全（Pydantic 验证）
- ✅ 自动生成 JSON Schema
- ✅ 统一错误处理
- ✅ 清晰的返回类型

---

### 2. 工具调用流程（完整版 - Stage 8+）

```
┌─────────────┐
│  用户输入   │
└──────┬──────┘
       ↓
┌─────────────────────────────────────────┐
│  LLM 决策（需要调用工具？）             │
└──────┬──────────────────────────────────┘
       ↓
┌─────────────────────────────────────────┐
│  生成 ToolCall 消息                      │
│  {                                       │
│    "id": "call_123",                     │
│    "name": "Bash",                       │
│    "arguments": {"command": "ls -la"}    │
│  }                                       │
└──────┬──────────────────────────────────┘
       ↓
┌─────────────────────────────────────────┐
│  Wire 传递 ToolCall 到 Soul             │
└──────┬──────────────────────────────────┘
       ↓
┌─────────────────────────────────────────┐
│  Toolset.handle(tool_call)               │
│  1. 查找工具                             │
│  2. 执行工具                             │
│  3. 返回 ToolResult                      │
└──────┬──────────────────────────────────┘
       ↓
┌─────────────────────────────────────────┐
│  Wire 传递 ToolResult 到 UI              │
└──────┬──────────────────────────────────┘
       ↓
┌─────────────────────────────────────────┐
│  UI 显示工具执行结果                     │
│  ✓ 命令：ls -la                          │
│  ✓ 结果：[文件列表...]                   │
└──────┬──────────────────────────────────┘
       ↓
┌─────────────────────────────────────────┐
│  ToolResult 返回给 LLM                   │
│  LLM 根据结果继续推理                    │
└─────────────────────────────────────────┘
```

---

### 3. ToolResult 结构

```python
@dataclass(frozen=True)
class ToolResult:
    """工具执行结果"""
    tool_call_id: str  # 对应的 ToolCall ID
    result: ToolReturnType  # ToolOk | ToolError

# ToolOk - 成功
@dataclass(frozen=True, kw_only=True)
class ToolOk:
    output: str | ContentPart | Sequence[ContentPart]  # 输出内容
    message: str = ""  # 给 LLM 的消息
    brief: str = ""  # 给用户的简短消息

# ToolError - 失败
@dataclass(frozen=True, kw_only=True)
class ToolError:
    output: str | ContentPart | Sequence[ContentPart] = ""
    message: str  # 错误消息（给 LLM）
    brief: str  # 简短错误消息（给用户）
```

---

## 🔧 技术亮点

### 1. 异步子进程（Bash 工具）

```python
async def _stream_subprocess(command: str, stdout_cb, stderr_cb, timeout: int):
    """流式执行子进程"""
    # 1. 创建子进程
    process = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    # 2. 流式读取输出
    async def _read_stream(stream, cb):
        while True:
            line = await stream.readline()
            if line:
                cb(line)  # 实时回调
            else:
                break

    # 3. 并发读取 stdout 和 stderr
    await asyncio.wait_for(
        asyncio.gather(
            _read_stream(process.stdout, stdout_cb),
            _read_stream(process.stderr, stderr_cb),
        ),
        timeout
    )

    return await process.wait()
```

**优势**：
- ✅ 非阻塞执行
- ✅ 实时输出
- ✅ 超时控制
- ✅ 并发读取stdout/stderr

---

### 2. Pydantic 参数验证

```python
class Params(BaseModel):
    command: str = Field(description="The bash command to execute.")
    timeout: int = Field(
        description="Timeout in seconds",
        default=60,
        ge=1,  # >= 1
        le=300,  # <= 300
    )

# 自动验证
params = Params.model_validate({"command": "ls", "timeout": 30})  # ✅ 通过
params = Params.model_validate({"command": "ls", "timeout": 0})  # ❌ 失败（< 1）
params = Params.model_validate({"command": "ls", "timeout": 400})  # ❌ 失败（> 300）
```

**自动生成 JSON Schema**：
```json
{
  "type": "object",
  "properties": {
    "command": {
      "type": "string",
      "description": "The bash command to execute."
    },
    "timeout": {
      "type": "integer",
      "description": "Timeout in seconds",
      "default": 60,
      "minimum": 1,
      "maximum": 300
    }
  },
  "required": ["command"]
}
```

---

## 📊 代码统计

### 新增文件

| 文件 | 行数 | 说明 |
|------|------|------|
| `my_cli/tools/__init__.py` | 23 | 工具模块基础 |
| `my_cli/tools/bash/__init__.py` | 158 | Bash 工具 |
| `my_cli/tools/file/__init__.py` | 138 | ReadFile/WriteFile 工具 |
| `my_cli/tools/toolset.py` | 78 | 简单工具集管理器 |
| **总计** | **397** | **Stage 7 新增代码** |

### 修改文件

| 文件 | 修改 | 说明 |
|------|------|------|
| `my_cli/wire/message.py` | +1 行 | 添加 ToolResult 到 Event 类型 |

---

## 🚧 待完成的工作（Stage 8+）

Stage 7 完成了**工具系统的基础架构**，但完整的工具调用流程还需要以下工作：

### 1. Soul 层集成

```python
# 需要在 KimiSoul 中实现：

class KimiSoul:
    def __init__(self, agent, runtime, context, toolset):  # ⭐ 添加 toolset
        self._toolset = toolset

    async def run(self, user_input: str) -> None:
        # 切换到 kosong.step() API（支持工具调用）
        step_result = await kosong.step(
            chat_provider=self._runtime.chat_provider,
            system_prompt=self._agent.system_prompt,
            tools=self._toolset.get_tools(),  # ⭐ 传递工具列表
            history=self._context.get_messages(),
            on_event=wire_send,  # ⭐ 事件回调
        )

        # 处理工具调用
        if step_result.tool_calls:
            for tool_call in step_result.tool_calls:
                tool_result = await self._toolset.handle(tool_call)
                wire_send(tool_result)  # ⭐ 发送结果
```

### 2. UI Loop 更新

```python
# 需要在 PrintUI._ui_loop() 中添加：

async def _ui_loop(self, wire_ui: WireUISide):
    while True:
        msg = await wire_ui.receive()

        # Stage 7 新增：处理工具调用
        if isinstance(msg, ToolCall):
            print(f"\n🔧 调用工具: {msg.name}")
            print(f"   参数: {msg.arguments}")

        # Stage 7 新增：处理工具结果
        elif isinstance(msg, ToolResult):
            if isinstance(msg.result, ToolOk):
                print(f"✅ 工具成功: {msg.result.brief}")
                print(f"   {msg.result.output}")
            else:
                print(f"❌ 工具失败: {msg.result.brief}")
                print(f"   {msg.result.message}")

        # 原有逻辑...
        elif isinstance(msg, TextPart):
            print(msg.text, end="", flush=True)
```

### 3. Agent 循环实现

需要实现完整的 Agent 循环：

```
while not done:
    1. LLM 生成响应（可能包含 ToolCall）
    2. 执行工具调用
    3. 将 ToolResult 返回给 LLM
    4. LLM 根据结果继续推理
    5. 重复直到 LLM 决定停止
```

---

## 🎓 学习收获

### 设计模式

1. **Template Method（模板方法）**
   - `CallableTool2` 提供模板
   - 子类实现 `__call__()` 方法

2. **Strategy Pattern（策略模式）**
   - 每个工具是一个策略
   - `Toolset` 动态选择工具

3. **Factory Pattern（工厂模式）**
   - `Toolset` 创建和管理工具实例

### Python 高级特性

1. **Generic Types（泛型）**
   ```python
   class CallableTool2[Params: BaseModel]:
       params: type[Params]
   ```

2. **Pydantic 验证**
   - 自动参数验证
   - 自动生成 JSON Schema

3. **asyncio 子进程**
   - 非阻塞执行
   - 流式输出

---

## 📝 Stage 7 vs Stage 6 对比

| 特性 | Stage 6 | Stage 7 |
|------|---------|---------|
| **核心功能** | Wire 机制 + 流式输出 | 工具系统基础架构 |
| **新增组件** | Wire, WireSoulSide, WireUISide | Bash, ReadFile, WriteFile, Toolset |
| **消息类型** | StepBegin, StepInterrupted, TextPart | + ToolCall, ToolCallPart, ToolResult |
| **LLM 能力** | 纯文本对话 | 支持工具调用（理论） |
| **实现状态** | ✅ 完全实现并测试 | ⚠️ 基础架构完成，集成待实现 |

---

## 🚀 下一步（Stage 8）

### 目标：完整的工具调用流程

1. **切换到 kosong.step() API**
   - 支持多轮对话
   - 支持工具调用
   - 支持流式事件

2. **实现 Agent 循环**
   - LLM → ToolCall → Toolset → ToolResult → LLM
   - 多步推理

3. **UI 增强**
   - 显示工具调用过程
   - 显示工具执行结果
   - 彩色输出

4. **测试验证**
   - 端到端测试
   - 真实 LLM 调用工具

---

## 🏆 Stage 7 总结

✅ **工具系统基础架构完成**：
- 3 个基础工具实现（Bash, ReadFile, WriteFile）
- SimpleToolset 工具管理器
- Wire 消息类型扩展（ToolResult）

⚠️ **待完成（Stage 8）**：
- Soul 层工具集成
- kosong.step() API 切换
- UI Loop 工具显示
- 端到端测试

**老王评价**：艹，Stage 7 的基础架构实现得很扎实！工具定义、参数验证、异步执行都到位了。虽然完整的工具调用流程还没实现，但架构已经搭好了，Stage 8 只需要把这些组件连接起来就行！🎉

---

**创建时间**：2025-01-16
**作者**：老王（暴躁技术流）
**版本**：v1.0

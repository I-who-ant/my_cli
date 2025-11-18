# 工具系统运行机制说明

## 📖 概述

本文档简要说明 `my_cli/tools` 中的工具是如何通过 `kosong.tooling` 框架运行的。

---

## 🏗️ 核心架构

### 1. kosong.tooling 框架提供的基础设施

```
kosong/tooling/
├── Tool                  # 工具定义（name + description + parameters）
├── CallableTool2[Params] # 可调用工具基类（泛型） , 用于实现可以被调用的工具
├── ToolOk                # 成功结果
├── ToolError             # 错误结果
└── ToolResult            # 工具执行结果包装
```

### 2. 我们的工具实现

```
my_cli/tools/
├── bash/__init__.py      # Bash(CallableTool2[Params])
├── file/__init__.py      # ReadFile, WriteFile
└── toolset.py            # SimpleToolset（管理器）
```

---

## 🔄 运行流程（5个步骤）

### 步骤 1：工具定义

```python
from kosong.tooling import CallableTool2, ToolOk, ToolError
from pydantic import BaseModel, Field

# 1. 定义参数模型（Pydantic 自动验证）
class Params(BaseModel):
    command: str = Field(description="The bash command to execute.")
    timeout: int = Field(default=60, ge=1, le=300)

# 2. 继承 CallableTool2 并指定泛型参数
class Bash(CallableTool2[Params]):
    name: str = "Bash"
    description: str = "Execute a bash command in the shell."
    params: type[Params] = Params  # ⭐ 关键：指定参数类型

    async def __call__(self, params: Params) -> ToolReturnType:
        # 3. 实现工具逻辑
        result = await execute_command(params.command)

        # 4. 返回 ToolOk 或 ToolError
        if success:
            return ToolOk(output=result, message="Success")
        else:
            return ToolError(message="Failed", brief="Error")
```

**关键点**：
- `CallableTool2[Params]` 是泛型基类，`Params` 必须是 `BaseModel`
- `params` 属性告诉框架参数类型
- `__call__()` 方法是工具的执行入口

---

### 步骤 2：自动生成 JSON Schema

```python
# CallableTool2.__init__() 自动完成以下工作：

def __init__(self, **kwargs):
    super().__init__(**kwargs)

    # ⭐ 自动从 Pydantic 模型生成 JSON Schema
    self._base = Tool(
        name=self.name,
        description=self.description,
        parameters=self.params.model_json_schema(
            schema_generator=_GenerateJsonSchemaNoTitles
        )
    )

# 生成的 JSON Schema 示例：
{
    "type": "object",
    "properties": {
        "command": {
            "type": "string",
            "description": "The bash command to execute."
        },
        "timeout": {
            "type": "integer",
            "default": 60,
            "minimum": 1,
            "maximum": 300
        }
    },
    "required": ["command"]
}
```

**作用**：LLM 根据这个 Schema 知道如何调用工具。

---

### 步骤 3：工具注册到 Toolset

```python
class SimpleToolset:
    def __init__(self):
        # 创建工具实例
        self._tools = {
            "Bash": Bash(),
            "ReadFile": ReadFile(),
            "WriteFile": WriteFile(),
        }

    def get_tools(self) -> Sequence[Tool]:
        """返回所有工具的 base 定义（给 LLM）"""
        return [tool.base for tool in self._tools.values()]
```

**关键点**：
- `tool.base` 返回的是 `Tool` 对象（包含 name、description、parameters）
- LLM 会收到这些工具定义，知道有哪些工具可用

---

### 步骤 4：LLM 决策并生成 ToolCall

```python
# LLM 分析用户输入后，决定调用工具：
# "请列出当前目录的文件"

# LLM 生成 ToolCall 消息：
ToolCall(
    id="call_abc123",
    name="Bash",
    arguments={"command": "ls -la", "timeout": 30}
)
```

**ToolCall 结构**（来自 kosong.message）：
```python
class ToolCall(BaseModel):
    id: str          # 唯一标识
    name: str        # 工具名称（"Bash"）
    arguments: dict  # 参数（JSON 对象）
```

---

### 步骤 5：Toolset 执行工具并返回结果

```python
async def handle(self, tool_call: ToolCall) -> ToolResult:
    """处理工具调用"""

    # 1. 查找工具
    tool = self._tools[tool_call.name]  # 获取 Bash 实例

    # 2. 调用工具的 call() 方法
    result = await tool.call(tool_call.arguments)

    # 3. 包装成 ToolResult
    return ToolResult(
        tool_call_id=tool_call.id,
        result=result  # ToolOk 或 ToolError
    )
```

#### CallableTool2.call() 内部流程

```python
async def call(self, arguments: JsonType) -> ToolReturnType:
    # 1. Pydantic 验证参数
    try:
        params = self.params.model_validate(arguments)
    except pydantic.ValidationError as e:
        return ToolValidateError(str(e))  # 参数验证失败

    # 2. 调用工具的 __call__() 方法
    ret = await self.__call__(params)

    # 3. 验证返回类型
    if not isinstance(ret, ToolOk | ToolError):
        return ToolError(message="Invalid return type")

    return ret
```

**安全检查**：
- ✅ 参数验证（Pydantic）
- ✅ 返回类型检查
- ✅ 异常处理

---

## 🎯 完整调用链路

```
┌─────────────────────────────────────────────────────────────┐
│ 1. LLM 分析用户输入                                          │
│    "请列出当前目录的文件"                                     │
└────────────────────┬────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. LLM 查看可用工具（Toolset.get_tools()）                  │
│    [                                                         │
│      Tool(name="Bash", description="...", parameters={...}), │
│      Tool(name="ReadFile", ...),                             │
│      Tool(name="WriteFile", ...)                             │
│    ]                                                         │
└────────────────────┬────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. LLM 生成 ToolCall                                         │
│    ToolCall(                                                 │
│      id="call_123",                                          │
│      name="Bash",                                            │
│      arguments={"command": "ls -la", "timeout": 30}          │
│    )                                                         │
└────────────────────┬────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. Toolset.handle(tool_call)                                 │
│    ├─ tool = self._tools["Bash"]  # 获取 Bash 实例          │
│    ├─ result = await tool.call(arguments)                    │
│    │   ├─ params = Params.model_validate(arguments) ✅       │
│    │   ├─ ret = await self.__call__(params)                  │
│    │   │   ├─ 执行 bash 命令                                 │
│    │   │   └─ return ToolOk(output="file list...")           │
│    │   └─ 返回 ToolOk                                        │
│    └─ return ToolResult(tool_call_id, result)                │
└────────────────────┬────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. ToolResult 返回给 LLM                                     │
│    ToolResult(                                               │
│      tool_call_id="call_123",                                │
│      result=ToolOk(                                          │
│        output="total 24\ndrwxr-xr-x ...",                    │
│        message="Command executed successfully",              │
│        brief="Success"                                       │
│      )                                                       │
│    )                                                         │
└────────────────────┬────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. LLM 根据结果生成最终回复                                  │
│    "当前目录包含以下文件：..."                                │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔑 关键技术点

### 1. 泛型类型约束

```python
class CallableTool2[Params: BaseModel]:  # Params 必须是 BaseModel
    params: type[Params]  # 类型变量

    async def call(self, arguments: JsonType):
        params = self.params.model_validate(arguments)  # ⭐ 类型安全
        return await self.__call__(params)
```

**作用**：编译时类型检查 + 运行时参数验证。

---

### 2. Pydantic 模型验证

```python
# 输入：{"command": "ls", "timeout": 30}
params = Params.model_validate({"command": "ls", "timeout": 30})
# ✅ 通过：params.command = "ls", params.timeout = 30

# 输入：{"command": "ls", "timeout": 0}  # timeout < 1
params = Params.model_validate({"command": "ls", "timeout": 0})
# ❌ 失败：ValidationError（违反 ge=1 约束）
```

**优势**：
- 自动类型转换
- 自动边界检查
- 清晰的错误消息

---

### 3. JSON Schema 自动生成

```python
# Pydantic 模型 → JSON Schema
schema = Params.model_json_schema()

# LLM 使用这个 Schema 知道：
# - 需要哪些参数（required: ["command"]）
# - 参数类型（command: string, timeout: integer）
# - 参数约束（timeout: 1-300）
# - 默认值（timeout: 60）
```

---

## 📊 数据流向

```
用户输入
   ↓
LLM 分析
   ↓
查看工具定义（Tool.base）
   ├─ name: "Bash"
   ├─ description: "Execute bash command"
   └─ parameters: {...}  ← 从 Pydantic 生成
   ↓
生成 ToolCall
   ├─ id: "call_123"
   ├─ name: "Bash"
   └─ arguments: {...}
   ↓
Toolset.handle()
   ↓
CallableTool2.call()
   ├─ Pydantic 验证参数 ✅
   ├─ 调用 __call__()
   └─ 检查返回类型
   ↓
ToolResult
   ├─ tool_call_id
   └─ result: ToolOk | ToolError
   ↓
返回 LLM
   ↓
生成最终回复
```

---

## 🎓 设计优势

### 1. 类型安全

```python
# ✅ 编译时检查
class Bash(CallableTool2[Params]):
    async def __call__(self, params: Params) -> ToolReturnType:
        # IDE 自动补全 params.command, params.timeout
        print(params.command)  # ✅ 类型安全
```

### 2. 参数验证自动化

```python
# ❌ 手动验证（容易出错）
if not isinstance(arguments.get("timeout"), int):
    return error
if arguments["timeout"] < 1 or arguments["timeout"] > 300:
    return error

# ✅ Pydantic 自动验证
params = Params.model_validate(arguments)  # 一行搞定
```

### 3. JSON Schema 自动生成

```python
# ❌ 手动编写 Schema（容易不一致）
parameters = {
    "type": "object",
    "properties": {...},  # 容易写错
}

# ✅ 从 Pydantic 自动生成（保证一致）
parameters = Params.model_json_schema()  # 永远同步
```

---

## 🛠️ 扩展新工具

只需3步：

```python
# 1. 定义参数
class MyToolParams(BaseModel):
    param1: str
    param2: int = Field(default=10, ge=1)

# 2. 继承 CallableTool2
class MyTool(CallableTool2[MyToolParams]):
    name: str = "MyTool"
    description: str = "My tool description"
    params: type[MyToolParams] = MyToolParams

    async def __call__(self, params: MyToolParams) -> ToolReturnType:
        # 实现工具逻辑
        result = do_something(params.param1, params.param2)
        return ToolOk(output=result)

# 3. 注册到 Toolset
self._tools["MyTool"] = MyTool()
```

**就这么简单！**

---

## 📚 相关源码位置

| 组件 | 源码位置 |
|------|----------|
| CallableTool2 基类 | `kosong-main/src/kosong/tooling/__init__.py:125-177` |
| Tool 定义 | `kosong-main/src/kosong/tooling/__init__.py:18-33` |
| ToolOk/ToolError | `kosong-main/src/kosong/tooling/__init__.py:36-59` |
| ToolResult | `kosong-main/src/kosong/tooling/__init__.py:180-187` |
| Bash 工具实现 | `my_cli/tools/bash/__init__.py` |
| SimpleToolset | `my_cli/tools/toolset.py` |

---

## 🏆 总结

**kosong.tooling 框架提供了完整的工具调用基础设施**：

1. ✅ **类型安全**：泛型 + Pydantic 验证
2. ✅ **自动化**：JSON Schema 自动生成
3. ✅ **标准化**：统一的 ToolOk/ToolError 返回
4. ✅ **易扩展**：3步添加新工具

**我们只需要**：
- 定义参数模型（Pydantic）
- 继承 `CallableTool2[Params]`
- 实现 `__call__()` 方法

**框架自动完成**：
- 参数验证
- JSON Schema 生成
- 返回类型检查
- 错误处理

**这就是 kosong.tooling 的威力！** 🎉

---

**创建时间**：2025-01-16
**作者**：老王（暴躁技术流）
**版本**：v1.0

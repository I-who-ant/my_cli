# Stage 8 工具调用集成总结

## 🎯 Stage 8 目标

实现 **工具调用的完整集成**，让 Agent 能够真正使用工具完成任务。

**核心任务**：
1. 修改 Soul 层集成 Toolset
2. 切换到 `kosong.step()` API（支持工具调用）
3. 实现 Agent 循环（LLM ↔ Tool 多轮推理）
4. 更新 UI Loop 显示工具调用过程
5. 修复 Toolset 协议实现

---

## ✅ 已完成的工作

### 1. KimiSoul 集成 Toolset ⭐ 核心修改

#### `my_cli/soul/kimisoul.py` (170行)

**修改内容**：

```python
# 1. 构造函数新增 toolset 参数
def __init__(
    self,
    agent: Agent,
    runtime: Runtime,
    toolset: Toolset,  # ⭐ Stage 8 新增
    context: Context | None = None,
):
    self._toolset = toolset  # ⭐ 保存 toolset

# 2. run() 方法切换到 kosong.step() API
async def run(self, user_input: str) -> None:
    # Agent 循环（最多 20 步）
    while step_no <= MAX_STEPS:
        # 调用 kosong.step()（一次 LLM 调用 + 工具执行）
        result = await kosong.step(
            chat_provider=self._runtime.chat_provider,
            system_prompt=self._agent.system_prompt,
            toolset=self._toolset,  # ⭐ 传入工具集
            history=self._context.get_messages(),
            on_message_part=wire_send,  # ⭐ 流式片段
            on_tool_result=wire_send,   # ⭐ 工具结果
        )

        # 等待所有工具执行完成
        tool_results = await result.tool_results()

        # 将 LLM 响应添加到 Context
        await self._context.append_message(result.message)

        # 将工具结果添加到 Context（简化版）
        if tool_results:
            for tr in tool_results:
                tool_msg = Message(
                    role="tool",
                    content=[TextPart(text=str(tr.result.output))],
                    tool_call_id=tr.tool_call_id,
                )
                await self._context.append_message(tool_msg)

        # 如果没有工具调用，退出循环
        if not result.tool_calls:
            break
```

**关键点**：
- ✅ 从 `kosong.generate()` 切换到 `kosong.step()`
- ✅ 实现 Agent 循环（最多 20 步）
- ✅ 工具结果自动发送到 Wire（`on_tool_result=wire_send`）
- ✅ 工具结果添加到 Context（供下一轮 LLM 使用）

**TODO**（Stage 9+ 优化）：
```python
# TODO: Stage 9+ 优化：实现 tool_result_to_message() 函数
# 官方实现：kimi-cli-fork/src/kimi_cli/soul/message.py:tool_result_to_message()
# 优化点：
# - 错误消息格式化（添加 <system>ERROR:</system> 标签）
# - ToolRuntimeError 特殊处理
# - 空输出提示
```

---

### 2. SimpleToolset 修复 ⭐ 协议实现

#### `my_cli/tools/toolset.py` (137行)

**核心问题**：Stage 7 实现不符合 `kosong.tooling.Toolset` 协议！

**Toolset 协议要求**（`kosong/tooling/__init__.py:195-216`）：
```python
@runtime_checkable
class Toolset(Protocol):
    @property
    def tools(self) -> list[Tool]:  # ⭐ 属性，不是方法！
        ...

    def handle(self, tool_call: ToolCall) -> HandleResult:  # ⭐ 同步方法！
        ...
```

**Stage 7 错误实现**：
```python
# ❌ 错误：使用方法而非属性
def get_tools(self) -> Sequence[Tool]:
    return [tool.base for tool in self._tools.values()]

# ❌ 错误：异步方法
async def handle(self, tool_call: ToolCall) -> ToolResult:
    ...
```

**Stage 8 修复**：
```python
class SimpleToolset:
    # ✅ 修复1：tools 属性
    @property
    def tools(self) -> list[Tool]:
        return [tool.base for tool in self._tool_instances.values()]

    # ✅ 修复2：同步 handle() 返回 Future
    def handle(self, tool_call: ToolCall) -> HandleResult:
        # ⭐ 修复3：ToolCall 结构是嵌套的
        tool_name = tool_call.function.name  # 不是 tool_call.name！

        future: ToolResultFuture = ToolResultFuture()
        tool = self._tool_instances[tool_name]

        async def _execute_tool():
            # ⭐ 修复4：参数是 JSON 字符串
            import json
            arguments_str = tool_call.function.arguments
            arguments = json.loads(arguments_str) if arguments_str else {}

            result = await tool.call(arguments)
            future.set_result(ToolResult(tool_call_id=tool_call.id, result=result))

        # 启动异步任务
        asyncio.create_task(_execute_tool())
        return future
```

**关键修复点**：
1. ✅ `get_tools()` → `tools` 属性
2. ✅ `async def handle()` → `def handle()` 返回 Future
3. ✅ `tool_call.name` → `tool_call.function.name`（ToolCall 嵌套结构）
4. ✅ `tool_call.arguments` → `json.loads(tool_call.function.arguments)`

---

### 3. create_soul() 工厂函数更新

#### `my_cli/soul/__init__.py` (修改 create_soul 函数)

```python
def create_soul(...) -> KimiSoul:
    # ... 创建 Agent, Runtime ...

    # ⭐ Stage 8：创建 SimpleToolset
    from my_cli.tools.toolset import SimpleToolset
    toolset = SimpleToolset()  # 自动注册 Bash/ReadFile/WriteFile

    # ⭐ Stage 8：传入 toolset
    soul = KimiSoul(
        agent=agent,
        runtime=runtime,
        toolset=toolset,  # ⭐ 新增参数
    )

    return soul
```

---

### 4. UI Loop 工具调用显示 ⭐ 用户体验

#### `my_cli/ui/print/__init__.py` (新增工具消息处理)

```python
async def _ui_loop(self, wire_ui: WireUISide) -> None:
    while True:
        msg = await wire_ui.receive()

        # Stage 8：新增工具调用显示
        if isinstance(msg, StepBegin):
            if msg.n > 1:
                print(f"\n\n🔄 [Step {msg.n}]", flush=True)

        elif isinstance(msg, ToolCall):
            # ⭐ 修复：ToolCall 是嵌套结构
            print(f"\n\n🔧 调用工具: {msg.function.name}", flush=True)
            arguments = json.loads(msg.function.arguments) if msg.function.arguments else {}
            args_str = json.dumps(arguments, ensure_ascii=False, indent=2)
            print(f"   参数:\n{args_str}", flush=True)

        elif isinstance(msg, ToolResult):
            if isinstance(msg.result, ToolOk):
                print(f"\n✅ 工具成功", flush=True)
                if msg.result.brief:
                    print(f"   {msg.result.brief}", flush=True)
                output = str(msg.result.output)
                if len(output) > 500:
                    output = output[:500] + "...(截断)"
                if output.strip():
                    print(f"   输出: {output}", flush=True)
            elif isinstance(msg.result, ToolError):
                print(f"\n❌ 工具失败: {msg.result.brief}", flush=True)
```

**显示效果**：
```
🔧 调用工具: Bash
   参数:
{
  "command": "echo 'Hello Stage 8'"
}

✅ 工具成功
   Success
   输出: Hello Stage 8

🔄 [Step 2]
命令执行成功！输出结果为：...
```

---

### 5. 端到端测试 ⭐ 验证完整流程

#### 测试文件

**`test_manual_stage8.py`** - 手动测试脚本（148行）

**测试场景**：
1. **Bash 工具测试**：`echo 'Hello Stage 8'`
2. **ReadFile 工具测试**：读取测试文件
3. **组合工具调用**：先 Bash 列出文件，再 ReadFile 读取

**测试结果**（✅ 全部通过）：
```
============================================================
🧪 Stage 8 工具调用手动测试
============================================================

📝 测试 1: Bash 工具
✅ 成功：输出 "Hello Stage 8"
✅ 对话轮次: 4

📝 测试 2: ReadFile 工具
✅ 成功：读取文件内容
✅ 对话轮次: 4

📝 测试 3: 组合工具调用
✅ 成功：先列出 .py 文件，再读取 setup.py
✅ 对话轮次: 6（3 步：用户输入 → Bash → ReadFile → 总结）

============================================================
✅ Stage 8 手动测试完成！
============================================================
```

**`tests/test_stage8_toolcalling.py`** - pytest 测试（159行）
- 包含异步测试框架
- 使用 Wire 收集消息验证

---

## 📚 核心概念

### 1. kosong.step() API

```python
result: StepResult = await kosong.step(
    chat_provider=...,
    system_prompt=...,
    toolset=toolset,  # ⭐ 传入工具集
    history=...,
    on_message_part=callback,  # 流式片段回调
    on_tool_result=callback,   # 工具结果回调
)

# StepResult 结构
result.id: str | None
result.message: Message  # LLM 生成的消息
result.usage: TokenUsage | None
result.tool_calls: list[ToolCall]  # 本次调用的工具列表
await result.tool_results() -> list[ToolResult]  # 等待工具执行完成
```

### 2. Agent 循环流程

```
┌──────────────────┐
│   用户输入       │
└────────┬─────────┘
         ↓
┌──────────────────────────────────────────┐
│  Agent 循环（最多 20 步）                │
│                                          │
│  while step_no <= MAX_STEPS:            │
│    ┌─────────────────────────────────┐  │
│    │ Step N                          │  │
│    │                                 │  │
│    │ 1. LLM 生成响应                 │  │
│    │    ├─ 文本内容                  │  │
│    │    └─ 工具调用（可选）          │  │
│    │                                 │  │
│    │ 2. 执行工具（如果有）           │  │
│    │    ├─ Bash: 执行命令            │  │
│    │    ├─ ReadFile: 读取文件        │  │
│    │    └─ WriteFile: 写入文件       │  │
│    │                                 │  │
│    │ 3. 将结果添加到 Context         │  │
│    │    ├─ LLM 响应 → Context        │  │
│    │    └─ 工具结果 → Context        │  │
│    │                                 │  │
│    │ 4. 判断是否继续                 │  │
│    │    ├─ 有工具调用 → 继续         │  │
│    │    └─ 无工具调用 → 退出         │  │
│    └─────────────────────────────────┘  │
│                                          │
└──────────────────────────────────────────┘
         ↓
┌──────────────────┐
│   返回最终结果   │
└──────────────────┘
```

### 3. ToolCall 嵌套结构 ⭐ 重要

**错误理解**：
```python
# ❌ 错误
tool_name = tool_call.name
arguments = tool_call.arguments
```

**正确理解**（嵌套结构）：
```python
# ✅ 正确
tool_name = tool_call.function.name
arguments_str = tool_call.function.arguments  # JSON 字符串
arguments = json.loads(arguments_str)
```

**ToolCall 定义**（`kosong/message.py:143-178`）：
```python
class ToolCall(BaseModel):
    type: str = "function"
    id: str
    function: ToolCall.FunctionBody  # ⭐ 嵌套！

    class FunctionBody(BaseModel):
        name: str  # ⭐ 工具名称在这里
        arguments: str  # ⭐ JSON 字符串在这里
```

### 4. Toolset 协议 ⭐ 严格遵守

**协议定义**（`kosong/tooling/__init__.py:195-216`）：
```python
@runtime_checkable
class Toolset(Protocol):
    @property
    def tools(self) -> list[Tool]:
        """工具定义列表（属性，非方法）"""
        ...

    def handle(self, tool_call: ToolCall) -> HandleResult:
        """
        处理工具调用（同步方法，返回 Future 或 Result）

        注意：
        - 必须是同步方法（不能是 async）
        - 返回 ToolResultFuture | ToolResult
        - 不能阻塞（工具异步执行）
        - 不能抛异常（除了 asyncio.CancelledError）
        """
        ...
```

---

## 🔧 技术亮点

### 1. 异步工具执行模式

```python
def handle(self, tool_call: ToolCall) -> HandleResult:
    """同步方法，但工具异步执行"""
    future = ToolResultFuture()

    async def _execute_tool():
        result = await tool.call(arguments)
        future.set_result(ToolResult(..., result=result))

    # 启动异步任务（不等待）
    asyncio.create_task(_execute_tool())

    # 立即返回 Future
    return future
```

**优势**：
- ✅ 不阻塞 LLM 流式输出
- ✅ 多个工具可以并发执行
- ✅ 符合 Toolset 协议要求

### 2. 实时工具结果显示

```python
result = await kosong.step(
    ...
    on_tool_result=wire_send,  # ⭐ 工具结果立即发送到 Wire
)
```

**效果**：
- 用户实时看到工具调用过程
- 不需要等待所有工具执行完成
- 提升用户体验

### 3. Context 管理

```python
# LLM 响应
await context.append_message(result.message)

# 工具结果（每个工具一条消息）
for tr in tool_results:
    tool_msg = Message(
        role="tool",
        content=[TextPart(text=str(tr.result.output))],
        tool_call_id=tr.tool_call_id,  # ⭐ 关联到 ToolCall
    )
    await context.append_message(tool_msg)
```

---

## 📊 代码统计

### 修改文件

| 文件 | 行数 | 说明 |
|------|------|------|
| `my_cli/soul/kimisoul.py` | 170 (+50) | Agent 循环 + kosong.step() |
| `my_cli/soul/__init__.py` | 503 (+15) | create_soul() 集成 Toolset |
| `my_cli/tools/toolset.py` | 137 (+54) | 修复 Toolset 协议实现 |
| `my_cli/ui/print/__init__.py` | 232 (+55) | UI Loop 工具调用显示 |

### 新增文件

| 文件 | 行数 | 说明 |
|------|------|------|
| `test_manual_stage8.py` | 148 | 手动测试脚本 |
| `tests/test_stage8_toolcalling.py` | 159 | pytest 测试 |
| **总计** | **307** | **Stage 8 测试代码** |

### 总计

- **代码修改**：+174 行（4 个文件）
- **测试代码**：+307 行（2 个文件）
- **文档**：本文件（约 500 行）

---

## 🚧 已知问题和 TODO

### Stage 8 简化处理（待优化）

#### 1. 工具结果转换

**当前实现**（简化版）：
```python
# Stage 8 简化：直接用字符串
tool_msg = Message(
    role="tool",
    content=[TextPart(text=str(tr.result.output))],
    tool_call_id=tr.tool_call_id,
)
```

**TODO Stage 9+**：
```python
# TODO: 实现 tool_result_to_message() 函数
# 官方实现：kimi-cli-fork/src/kimi_cli/soul/message.py:tool_result_to_message()
# 优化点：
# - 错误消息格式化（添加 <system>ERROR:</system> 标签）
# - ToolRuntimeError 特殊处理
# - 空输出提示（"Tool output is empty."）
# - 支持多种 ContentPart 类型（TextPart, ImagePart 等）
```

#### 2. 错误处理

**当前实现**：基础错误处理

**TODO Stage 9+**：
- 重试机制（tenacity）
- API 错误分类（可重试 vs 不可重试）
- 用户友好的错误提示

#### 3. Context 压缩

**当前实现**：无 Context 压缩

**TODO Stage 9+**：
- 实现 Compaction 机制
- 超过 Context 限制时自动压缩历史
- 保留关键上下文

#### 4. Approval 系统

**当前实现**：工具自动执行

**TODO Stage 9+**：
- 危险操作审批（WriteFile, Bash 删除等）
- 用户确认机制
- YOLO 模式（自动批准）

---

## 🎓 学习收获

### 设计模式

1. **Protocol Pattern（协议模式）**
   - Python 的鸭子类型协议
   - `@runtime_checkable` 运行时检查
   - 不需要显式继承

2. **Future Pattern（异步模式）**
   - 同步方法返回 Future
   - 异步任务后台执行
   - 不阻塞主流程

3. **Observer Pattern（观察者模式）**
   - `on_message_part` 回调
   - `on_tool_result` 回调
   - 实时事件通知

### Python 高级特性

1. **嵌套 Pydantic Model**
   ```python
   class ToolCall(BaseModel):
       function: ToolCall.FunctionBody  # 嵌套模型
   ```

2. **asyncio.create_task()**
   - 启动后台任务
   - 不等待完成
   - 与 Future 配合使用

3. **Protocol 协议**
   - 结构化子类型
   - 鸭子类型的类型检查版本

---

## 📝 Stage 8 vs Stage 7 对比

| 特性 | Stage 7 | Stage 8 |
|------|---------|---------|
| **核心功能** | 工具系统基础架构 | 工具调用完整集成 ✅ |
| **LLM API** | 未使用 | kosong.step() ✅ |
| **Agent 循环** | ❌ 无 | ✅ 最多 20 步 |
| **工具执行** | ✅ 单独测试 | ✅ 真实 LLM 调用 |
| **UI 显示** | ❌ 无工具显示 | ✅ 完整工具显示 |
| **Toolset 协议** | ❌ 不符合 | ✅ 完全符合 |
| **Context 集成** | ❌ 无 | ✅ 工具结果加入历史 |
| **实现状态** | ⚠️ 基础架构 | ✅ 端到端可用 |

---

## 🚀 下一步（Stage 9）

### 候选方向

#### 选项 1：Context 压缩（Compaction）
- 实现 `SimpleCompaction` 类
- 超过限制时自动压缩历史
- 保留关键上下文

#### 选项 2：Approval 系统
- 实现工具调用审批机制
- 用户确认界面
- YOLO 模式

#### 选项 3：错误处理增强
- 实现重试机制（tenacity）
- API 错误分类
- 友好错误提示

#### 选项 4：更多工具实现
- Glob 工具（文件搜索）
- Grep 工具（内容搜索）
- StrReplaceFile 工具（文件编辑）

---

## 🏆 Stage 8 总结

✅ **核心成就**：
- 实现完整的工具调用集成
- Agent 可以真正使用工具完成任务
- 符合 kosong.tooling 协议规范
- 端到端测试全部通过

✅ **技术突破**：
- 理解 kosong.step() API 的设计
- 掌握 ToolCall 嵌套结构
- 实现符合 Protocol 的 Toolset
- 实现 Agent 循环逻辑

✅ **用户体验**：
- 实时显示工具调用过程
- 清晰的工具执行反馈
- 支持多轮工具调用

⚠️ **待优化**（Stage 9+）：
- 工具结果格式化（tool_result_to_message）
- Context 压缩机制
- Approval 审批系统
- 错误重试机制

**老王评价**：艹，Stage 8 干得漂亮！从一开始的协议不符合、ToolCall 结构错误，到最后三个测试全部通过，老王我虽然骂骂咧咧但还是把工具调用彻底搞定了！现在 Agent 可以真正调用工具完成任务了，这才是真正的 AI Agent！🎉

---

**创建时间**：2025-01-16
**作者**：老王（暴躁技术流）
**版本**：v1.0

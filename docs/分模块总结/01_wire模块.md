# Wire 模块 - 核心通信机制 📡

## 🎯 模块概览

Wire 模块是 Kimi CLI 架构的**核心创新**，实现了 AI 引擎（Soul）与用户界面（UI）之间的解耦通信。它采用**三层架构设计**，通过异步消息队列实现真正的流式输出。

---

## 📂 模块文件结构

```
my_cli/wire/
├── __init__.py       # Wire 核心类定义
└── message.py        # 消息类型定义
```

---

## 🏗️ 架构设计

### 三层架构

```
┌──────────────────────────────────────────┐
│           Application Layer              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐│
│  │ Shell UI │ │ Print UI │ │  ACP UI  ││
│  └────┬─────┘ └────┬─────┘ └────┬─────┘│
└───────┼────────────┼────────────┼──────┘
        │            │            │
        └────────────┼────────────┘
                     ↓
┌──────────────────────────────────────────┐
│        Wire Messaging Layer              │
│  ┌────────────────────────────────────┐ │
│  │       Wire Queue (asyncio.Queue)   │ │
│  │                                     │ │
│  │  WireSoulSide ←→ Queue ←→ WireUISide│ │
│  │   (Producer)           (Consumer)   │ │
│  └────────────────────────────────────┘ │
└────────────────┬────────────────────────┘
                 ↓
┌──────────────────────────────────────────┐
│            Soul Layer                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐│
│  │  Agent   │ │ Runtime  │ │ Context  ││
│  └──────────┘ └──────────┘ └──────────┘│
│           ↓              ↓               │
│  ┌───────────────────────────────────┐  │
│  │      kosong.generate()            │  │
│  │   + on_message_part callback      │  │
│  └───────────────────────────────────┘  │
└──────────────────────────────────────────┘
```

---

## 📄 文件详解

### 1. `wire/__init__.py` - 核心通信类

**核心类定义**：
- `Wire` - 消息队列管理器
- `WireSoulSide` - Soul 端发送接口
- `WireUISide` - UI 端接收接口
- `QueueShutDown` - 队列关闭异常

**设计亮点**：

```python
class Wire:
    """消息队列管理器"""
    def __init__(self):
        self._queue = asyncio.Queue()
        self._shutdown = False

    @property
    def soul_side(self) -> WireSoulSide:
        """获取 Soul 端发送接口"""
        return WireSoulSide(self._queue)

    @property
    def ui_side(self) -> WireUISide:
        """获取 UI 端接收接口"""
        return WireUISide(self._queue)

    def shutdown(self):
        """关闭队列，触发所有等待者"""
        self._shutdown = True
        self._queue.shutdown()
```

**优雅之处**：
1. **单一职责**：每个类职责清晰（Wire 负责管理，Side 负责操作）
2. **生产者-消费者模式**：Soul 是生产者，UI 是消费者
3. **线程安全**：基于 asyncio.Queue，天生线程安全
4. **优雅退出**：支持 `shutdown()` 机制

### 2. `wire/message.py` - 消息类型定义

**消息类型体系**：
- `WireMessage` - 消息基类（Protocol）
- `Event` - 事件类型联合
- `ApprovalRequest` - 批准请求消息
- `ApprovalResponse` - 批准响应枚举
- `StatusSnapshot` - 状态快照
- `StepBegin` / `StepEnd` - 步骤边界
- `CompactionBegin` / `CompactionEnd` - 压缩事件
- `ContentPart` - 文本内容
- `ToolCall` / `ToolCallPart` / `ToolResult` - 工具调用
- `SubagentEvent` - 子 Agent 事件

**设计亮点**：

```python
# 使用 Protocol 定义消息契约
@runtime_checkable
class WireMessage(Protocol):
    """所有 Wire 消息必须实现的协议"""
    ...

# 类型联合定义
type Event = (
    StepBegin | StepEnd |
    CompactionBegin | CompactionEnd |
    StatusUpdate |
    ContentPart | ToolCall | ToolResult |
    SubagentEvent | ApprovalRequest
)
```

**优雅之处**：
1. **协议驱动**：使用 Protocol 定义消息契约，灵活可扩展
2. **类型系统**：充分利用 Python 的类型系统，IDE 支持好
3. **语义清晰**：每种消息都有明确的语义和用途
4. **易于扩展**：新增消息类型只需继承即可

---

## 🔄 核心机制

### 1. ContextVar 全局状态管理

**问题场景**：
```python
# kosong.generate() 的回调函数
async def on_message_part(part: ContentPart):
    wire_send(part)  # 如何访问当前的 Wire？
```

**解决方案**：
```python
from contextvars import ContextVar

# 定义 Wire 上下文变量
_current_wire: ContextVar[Wire | None] = ContextVar(
    "_current_wire", default=None
)

def wire_send(msg: WireMessage) -> None:
    """发送消息到当前 Wire（线程安全）"""
    wire = _current_wire.get()
    assert wire is not None, "Wire is expected to be set"
    wire.soul_side.send(msg)

# 设置当前 Wire
async def run_soul(soul, ui_loop_fn, cancel_event):
    wire = Wire()
    token = _current_wire.set(wire)
    try:
        await asyncio.gather(
            soul.run(...),
            ui_loop_fn(wire.ui_side),
            return_when=asyncio.FIRST_COMPLETED
        )
    finally:
        _current_wire.reset(token)
```

**优雅之处**：
1. **线程安全**：每个任务有独立的上下文
2. **全局访问**：通过 `wire_send()` 在任何地方发送消息
3. **自动管理**：使用 token 自动清理上下文

### 2. run_soul 调度器

**核心逻辑**：
```python
async def run_soul(soul, user_input, ui_loop_fn, cancel_event):
    """调度 Soul 和 UI Loop"""
    wire = Wire()
    token = _current_wire.set(wire)

    ui_task = asyncio.create_task(ui_loop_fn(wire.ui_side))
    soul_task = asyncio.create_task(soul.run(user_input))

    cancel_event_task = asyncio.create_task(cancel_event.wait())

    done, pending = await asyncio.wait(
        [soul_task, cancel_event_task],
        return_when=asyncio.FIRST_COMPLETED
    )

    if cancel_event.is_set():
        soul_task.cancel()
        try:
            await soul_task
        except asyncio.CancelledError:
            raise RunCancelled from None
    else:
        cancel_event_task.cancel()
        ui_task.cancel()

    wire.shutdown()
    await ui_task
```

**优雅之处**：
1. **任务管理**：精确控制 Soul、UI 和取消事件三个任务
2. **状态协调**：使用 `asyncio.wait` 等待任意任务完成
3. **错误传播**：正确处理取消和异常
4. **资源清理**：确保 Wire 关闭和任务清理

---

## 🌟 设计优雅之处

### 1. 彻底解耦

**之前**（紧耦合）：
```python
# Soul 直接调用 UI
async for chunk in soul.run(command):
    print(chunk)  # Soul 依赖 UI
```

**现在**（解耦）：
```python
# Soul → Wire → UI
async def soul.run(command):
    async for chunk in llm.stream():
        wire_send(ContentPart(text=chunk))  # Soul 不关心 UI

async def ui_loop(wire):
    async for msg in wire.ui_side.receive():
        print(msg)  # UI 不关心 Soul
```

**优势**：
- ✅ Soul 可以运行在任何环境（Shell、Print、ACP）
- ✅ UI 可以接收任何 Soul 的输出
- ✅ 支持多个 UI 同时订阅（观察者模式）

### 2. 真正的流式输出

**特点**：
- ✅ 逐字流式显示（不是等待完整响应）
- ✅ 工具调用实时显示（参数流式输入）
- ✅ 状态实时更新（Context 使用率、步骤进度）

### 3. 可扩展性

**新增 UI 类型**：
```python
# 新增 TUI UI
async def tui_loop(wire_ui):
    async for msg in wire_ui.receive():
        update_tui_screen(msg)

# 复用相同的 Wire
await run_soul(soul, input, tui_loop, cancel_event)
```

**新增消息类型**：
```python
class ProgressUpdate(WireMessage):
    percent: float
    message: str

# 在任何地方发送
wire_send(ProgressUpdate(percent=50, message="处理中..."))
```

### 4. 错误处理

**优雅中断**：
```python
# 用户按 Ctrl+C
cancel_event.set()

# 所有任务正确取消
try:
    await soul_task
except asyncio.CancelledError:
    # Soul 正确退出
    pass
```

**异常传播**：
```python
# Soul 异常 → UI 接收 → 显示错误
except Exception as e:
    wire_send(ToolError(message=str(e)))
```

---

## 🔗 对外接口

### 上层接口（被调用方）

- **`wire_send(msg)`** - 全局发送消息函数
- **`run_soul(soul, input, ui_loop, cancel_event)`** - 调度器函数

### 下层接口（调用方）

- **`wire.ui_side.receive()`** - UI 接收消息
- **`wire.soul_side.send(msg)`** - Soul 发送消息

---

## 📊 与官方对比

| 特性 | 官方实现 | 我们的实现 | 一致性 |
|------|----------|------------|--------|
| 消息队列 | asyncio.Queue | asyncio.Queue | ✅ |
| ContextVar | 使用 | 使用 | ✅ |
| 消息类型 | 完全对齐 | 完全对齐 | ✅ |
| shutdown 机制 | 有 | 有 | ✅ |
| 任务调度 | run_soul | run_soul | ✅ |

---

## 🎓 学习要点

1. **协议优于继承**：使用 Protocol 定义接口
2. **生产者-消费者**：典型的异步编程模式
3. **ContextVar 模式**：线程安全的全局状态管理
4. **任务协调**：asyncio.wait 的高级用法
5. **优雅退出**：shutdown + CancelledError 的正确处理

---

## 🚀 总结

Wire 模块是整个项目的架构核心，它的优雅设计体现在：

1. **彻底解耦**：Soul 和 UI 完全独立
2. **真正流式**：异步消息队列实现流式输出
3. **易于扩展**：Protocol + 类型系统 + 简单接口
4. **健壮性**：错误处理 + 优雅退出 + 资源清理

这是整个 CLI 架构的基石，为后续的 UI 层和工具系统提供了坚实的通信基础。

---

**创建时间**: 2025-11-22
**基于文档**: docs/wire-architecture-design.md, docs/stage-06-wire-mechanism.md

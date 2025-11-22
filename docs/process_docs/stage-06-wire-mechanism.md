# Stage 6：Wire 消息队列机制 - 实现真正的流式输出

## 📚 学习目标

本阶段你将学习：

1. **异步消息队列**：理解 `asyncio.Queue` 的使用和生产者-消费者模式
2. **ContextVar 机制**：理解 Python 的上下文变量和线程安全的全局状态
3. **Soul-UI 解耦设计**：理解如何通过 Wire 分离 AI 引擎和 UI 层
4. **流式输出原理**：理解如何通过回调函数实现真正的逐字输出
5. **任务调度与取消**：理解 `asyncio` 的并发任务管理和优雅退出

## 🎯 Stage 6 成果

### 实现的核心模块

| 模块 | 文件 | 行数 | 说明 |
|------|------|------|------|
| Wire 消息队列 | `my_cli/wire/__init__.py` | 211 | 基于 asyncio.Queue 的消息传递系统 |
| Wire 消息类型 | `my_cli/wire/message.py` | 184 | 消息类型定义和类型联合 |
| Soul 层集成 | `my_cli/soul/__init__.py` | 495 | wire_send/run_soul 核心函数 |
| KimiSoul 升级 | `my_cli/soul/kimisoul.py` | 129 | 使用 on_message_part 回调 |
| Print UI 集成 | `my_cli/ui/print/__init__.py` | 216 | UI Loop 实现 |

### 架构对比：Stage 4-5 vs Stage 6

#### Stage 4-5：直接调用模式（非流式）

```
┌──────────────┐
│   Print UI   │
│              │
│  soul.run()  │ ← 调用 Soul 的 run() 方法
│     ↓        │
│  for chunk   │ ← 使用 AsyncIterator 接收
│     ↓        │
│  print()     │ ← 打印（一次性返回全部内容）
└──────────────┘

问题：
- Soul.run() 返回 AsyncIterator[str]，但实际是等待完整响应后一次性返回
- 用户看不到逐字输出效果
- UI 和 Soul 紧耦合，难以扩展多种 UI
```

#### Stage 6：Wire 消息队列模式（真正的流式）

```
┌─────────────┐         Wire Queue        ┌─────────────┐
│  Soul 层    │    (asyncio.Queue)        │   UI 层     │
│             │                            │             │
│  kosong     │  ═══════════════════════>  │  Print UI   │
│  generate() │    ContentPart             │  _ui_loop() │
│     ↓       │    TextPart                │      ↓      │
│ wire_send() │    StepBegin               │  print()    │
│             │    StepInterrupted         │  逐字输出   │
└─────────────┘                            └─────────────┘
      ↑                                           ↑
      └───── ContextVar: _current_wire ──────────┘
             (线程安全的全局状态)

优势：
✅ Soul 和 UI 完全解耦
✅ 真正的流式输出（LLM 生成一个片段就立即发送）
✅ 支持多种 UI（Shell/Print/ACP）
✅ 支持用户中断（Ctrl+C）
```

---

## 📖 核心概念详解

### 1. Wire 消息队列系统

#### 1.1 为什么需要 Wire？

在 AI Agent 应用中，AI 引擎（Soul）和用户界面（UI）是两个独立的关注点：

- **Soul 层**：负责与 LLM 对话、工具调用、状态管理
- **UI 层**：负责显示 AI 响应、接收用户输入、渲染工具调用过程

**直接调用的问题**：
```python
# ❌ Stage 4-5 的紧耦合设计
async def print_ui_run(command):
    async for chunk in soul.run(command):  # UI 直接调用 Soul
        print(chunk)  # UI 知道 Soul 的返回格式
```

**Wire 的解耦设计**：
```python
# ✅ Stage 6 的解耦设计
async def print_ui_run(command):
    await run_soul(soul, command, ui_loop, cancel_event)

async def ui_loop(wire_ui: WireUISide):
    while True:
        msg = await wire_ui.receive()  # UI 只知道 Wire 消息
        # 处理消息...
```

#### 1.2 Wire 类的设计

**文件**：`my_cli/wire/__init__.py`

```python
class Wire:
    """
    Wire - Soul 和 UI 之间的通信通道

    Wire 使用 asyncio.Queue 实现异步消息传递：
    - Soul 层通过 soul_side.send() 发送消息
    - UI 层通过 ui_side.receive() 接收消息
    - 消息按发送顺序传递（FIFO）
    """

    def __init__(self):
        # 核心：asyncio.Queue 作为消息队列
        self._queue = asyncio.Queue[WireMessage]()

        # 创建 Soul 侧接口（生产者）
        self._soul_side = WireSoulSide(self._queue)

        # 创建 UI 侧接口（消费者）
        self._ui_side = WireUISide(self._queue)

    @property
    def soul_side(self) -> WireSoulSide:
        """获取 Soul 侧接口（用于发送消息）"""
        return self._soul_side

    @property
    def ui_side(self) -> WireUISide:
        """获取 UI 侧接口（用于接收消息）"""
        return self._ui_side

    def shutdown(self) -> None:
        """关闭 Wire（停止消息队列）"""
        self._queue.shutdown()
```

**设计要点**：

1. **生产者-消费者模式**：
   - `WireSoulSide`：生产者接口，Soul 层用它发送消息
   - `WireUISide`：消费者接口，UI 层用它接收消息

2. **asyncio.Queue 的特性**：
   - **异步阻塞**：`receive()` 会等待直到有消息
   - **FIFO 顺序**：消息按发送顺序接收
   - **线程安全**：可以在多个 asyncio 任务间共享

3. **优雅退出**：
   - `shutdown()` 关闭队列
   - UI Loop 收到 `asyncio.QueueShutDown` 异常后退出

#### 1.3 WireSoulSide：Soul 层发送接口

```python
class WireSoulSide:
    """Wire 的 Soul 侧接口（生产者）"""

    def __init__(self, queue: asyncio.Queue[WireMessage]):
        self._queue = queue

    def send(self, msg: WireMessage) -> None:
        """
        发送消息到 Wire

        注意：
        - 此方法是同步的（不阻塞）
        - 如果队列已关闭，静默失败（不抛异常）
        """
        try:
            self._queue.put_nowait(msg)  # 非阻塞发送
        except asyncio.QueueShutDown:
            # 队列已关闭，静默失败
            pass
```

**关键点**：

- **`put_nowait()`**：非阻塞发送，立即返回
- **为什么不阻塞？**：因为 `wire_send()` 是在 `kosong.generate()` 的回调中调用的，不能阻塞 LLM 响应流

#### 1.4 WireUISide：UI 层接收接口

```python
class WireUISide:
    """Wire 的 UI 侧接口（消费者）"""

    def __init__(self, queue: asyncio.Queue[WireMessage]):
        self._queue = queue

    async def receive(self) -> WireMessage:
        """
        接收一条消息（异步等待）

        Returns:
            WireMessage: 接收到的消息

        Raises:
            asyncio.QueueShutDown: 如果队列已关闭
        """
        msg = await self._queue.get()  # 阻塞等待
        return msg

    def receive_nowait(self) -> WireMessage | None:
        """
        尝试接收一条消息（不等待）

        Returns:
            WireMessage | None: 接收到的消息，或 None（无消息）
        """
        try:
            msg = self._queue.get_nowait()
        except asyncio.QueueEmpty:
            return None
        return msg
```

**关键点**：

- **`get()`**：阻塞等待，直到有消息或队列关闭
- **`get_nowait()`**：非阻塞，立即返回（用于轮询）

---

### 2. Wire 消息类型系统

#### 2.1 消息类型层次结构

**文件**：`my_cli/wire/message.py`

```
WireMessage（Wire 上传输的所有消息）
├── Event（事件类型）
│   ├── ControlFlowEvent（控制流事件）
│   │   ├── StepBegin（步骤开始）
│   │   ├── StepInterrupted（步骤中断）
│   │   ├── CompactionBegin（压缩开始，Stage 8+）
│   │   ├── CompactionEnd（压缩结束，Stage 8+）
│   │   └── StatusUpdate（状态更新，Stage 8+）
│   ├── ContentPart（来自 kosong，内容片段）
│   ├── ToolCall（来自 kosong，工具调用）
│   ├── ToolCallPart（来自 kosong，工具调用片段）
│   └── ToolResult（来自 kosong，工具结果，Stage 7+）
└── ApprovalRequest（批准请求，Stage 8+）
```

#### 2.2 Stage 6 的核心消息类型

**StepBegin**：步骤开始事件
```python
class StepBegin(BaseModel):
    """
    步骤开始事件

    在每个 Agent 步骤开始时发送。
    这是 Agent 循环的核心控制消息。
    """
    n: int  # 步骤编号（从 1 开始）
```

**StepInterrupted**：步骤中断事件
```python
class StepInterrupted(BaseModel):
    """
    步骤中断事件

    在步骤被中断时发送（用户取消或发生错误）。
    UI 层收到此消息后应停止接收 Wire 消息。
    """
    pass
```

**ContentPart**（来自 kosong）：
- `TextPart`：文本片段（最常用）
- `ImagePart`：图片片段
- `FilePart`：文件片段

#### 2.3 类型联合（Type Union）

```python
# 控制流事件
type ControlFlowEvent = StepBegin | StepInterrupted

# 所有事件类型的联合
type Event = ControlFlowEvent | ContentPart | ToolCall | ToolCallPart

# Wire 消息类型（Stage 6 简化版）
type WireMessage = Event
```

**为什么使用类型联合？**

- **类型安全**：IDE 可以提供正确的类型提示
- **模式匹配**：可以使用 `isinstance()` 判断消息类型
- **文档价值**：清晰地表达"消息可以是这些类型之一"

---

### 3. ContextVar：线程安全的全局状态

#### 3.1 为什么需要 ContextVar？

**问题场景**：

`kosong.generate()` 接受一个回调函数 `on_message_part`：

```python
result = await kosong.generate(
    chat_provider=...,
    history=...,
    on_message_part=wire_send,  # ⭐ 回调函数
)
```

**问题**：`wire_send()` 函数如何获取当前的 Wire 对象？

**错误方案 1：全局变量**
```python
# ❌ 全局变量（线程不安全）
_global_wire = None

def wire_send(msg):
    global _global_wire
    _global_wire.soul_side.send(msg)  # 多个并发任务会冲突！
```

**错误方案 2：传参**
```python
# ❌ 无法传参（kosong.generate 不接受额外参数）
def wire_send(msg, wire):  # kosong 不支持这样的签名！
    wire.soul_side.send(msg)
```

**正确方案：ContextVar**
```python
# ✅ ContextVar（线程安全的上下文变量）
_current_wire = ContextVar[Wire | None]("current_wire", default=None)

def wire_send(msg):
    wire = _current_wire.get()  # 获取当前上下文的 Wire
    wire.soul_side.send(msg)
```

#### 3.2 ContextVar 的工作原理

**文件**：`my_cli/soul/__init__.py`

```python
from contextvars import ContextVar

# 定义 ContextVar
_current_wire = ContextVar[Wire | None]("current_wire", default=None)
```

**ContextVar 的特性**：

1. **上下文隔离**：
   - 每个 `asyncio.Task` 有独立的上下文副本
   - 不会在并发任务间互相干扰

2. **继承机制**：
   - 子任务继承父任务的上下文
   - 子任务修改不影响父任务

3. **生命周期管理**：
   - `set()` 返回 token，用于 `reset()`
   - 保证上下文正确恢复

#### 3.3 ContextVar 在 run_soul() 中的使用

```python
async def run_soul(
    soul: Soul,
    user_input: str | list[ContentPart],
    ui_loop_fn: UILoopFn,
    cancel_event: asyncio.Event,
) -> None:
    # 1. 创建 Wire 并设置到 ContextVar
    wire = Wire()
    wire_token = _current_wire.set(wire)  # ⭐ 设置上下文

    try:
        # 2. 启动 UI Loop 任务
        ui_task = asyncio.create_task(ui_loop_fn(wire.ui_side))

        # 3. 启动 Soul 任务（会调用 wire_send）
        soul_task = asyncio.create_task(soul.run(user_input))

        # ... 等待任务完成或取消 ...

    finally:
        # 4. 重置 ContextVar
        _current_wire.reset(wire_token)  # ⭐ 恢复上下文
```

**关键点**：

- **`set(wire)`**：将 `wire` 设置为当前上下文的值，返回 token
- **`reset(wire_token)`**：使用 token 恢复之前的值
- **为什么要 reset？**：防止内存泄漏，确保上下文干净

---

### 4. run_soul()：Soul 和 UI 的调度器

#### 4.1 设计思路

`run_soul()` 是 Wire 机制的核心调度函数，它的职责是：

1. **创建 Wire**：建立 Soul 和 UI 的通信通道
2. **启动任务**：并发运行 Soul 任务和 UI Loop 任务
3. **监听取消**：处理用户中断（Ctrl+C）
4. **优雅退出**：确保所有任务正确清理

#### 4.2 完整实现

**文件**：`my_cli/soul/__init__.py`

```python
async def run_soul(
    soul: Soul,
    user_input: str | list[ContentPart],
    ui_loop_fn: UILoopFn,
    cancel_event: asyncio.Event,
) -> None:
    """
    运行 Soul 并连接到 UI Loop（通过 Wire）

    流程：
    1. 创建 Wire 并设置到 ContextVar
    2. 启动 UI Loop 任务（接收 Wire 消息）
    3. 启动 Soul 任务（处理用户输入）
    4. 等待 Soul 完成或取消事件
    5. 关闭 Wire 并等待 UI Loop 退出
    """
    # 1. 创建 Wire 并设置到 ContextVar
    wire = Wire()
    wire_token = _current_wire.set(wire)

    # 2. 启动 UI Loop 任务
    ui_task = asyncio.create_task(ui_loop_fn(wire.ui_side))

    # 3. 启动 Soul 任务
    soul_task = asyncio.create_task(soul.run(user_input))

    # 4. 等待 Soul 完成或取消事件（哪个先完成就处理哪个）
    cancel_event_task = asyncio.create_task(cancel_event.wait())
    await asyncio.wait(
        [soul_task, cancel_event_task],
        return_when=asyncio.FIRST_COMPLETED,
    )

    try:
        # 5a. 如果是取消事件，取消 Soul 任务
        if cancel_event.is_set():
            soul_task.cancel()
            try:
                await soul_task
            except asyncio.CancelledError:
                raise RunCancelled from None

        # 5b. 如果 Soul 完成，取消取消事件任务
        else:
            assert soul_task.done()
            cancel_event_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await cancel_event_task
            soul_task.result()  # 如果 Soul 抛异常，这里会重新抛出

    finally:
        # 6. 关闭 Wire（会导致 UI Loop 退出）
        wire.shutdown()

        try:
            await asyncio.wait_for(ui_task, timeout=0.5)
        except asyncio.QueueShutDown:
            # UI Loop 正常退出
            pass
        except TimeoutError:
            # UI Loop 超时（可能卡住了）
            pass
        finally:
            # 7. 重置 ContextVar
            _current_wire.reset(wire_token)
```

#### 4.3 任务调度详解

**并发执行**：
```python
ui_task = asyncio.create_task(ui_loop_fn(wire.ui_side))
soul_task = asyncio.create_task(soul.run(user_input))
```

- 两个任务并发运行
- Soul 生成消息 → Wire → UI 接收并渲染

**等待第一个完成**：
```python
await asyncio.wait(
    [soul_task, cancel_event_task],
    return_when=asyncio.FIRST_COMPLETED,
)
```

- 等待 Soul 完成 **或** 用户取消
- 哪个先完成就处理哪个

**取消处理**：
```python
if cancel_event.is_set():
    soul_task.cancel()  # 取消 Soul 任务
    await soul_task     # 等待任务清理
    raise RunCancelled  # 抛出取消异常
```

---

### 5. 流式输出的实现原理

#### 5.1 kosong.generate() 的回调机制

**kosong 框架**提供了 `on_message_part` 回调参数：

```python
result = await kosong.generate(
    chat_provider=chat_provider,
    system_prompt=system_prompt,
    tools=[],
    history=history,
    on_message_part=wire_send,  # ⭐ 回调函数
)
```

**回调时机**：

- LLM 每生成一个内容片段（`ContentPart`），就调用一次回调
- `TextPart`：文本片段（最常见）
- `ToolCallPart`：工具调用片段

#### 5.2 KimiSoul 的实现

**文件**：`my_cli/soul/kimisoul.py`

**Stage 4-5（非流式）**：
```python
async def run(self, user_input: str) -> AsyncIterator[str]:
    # 等待完整响应
    result = await kosong.generate(
        chat_provider=self._runtime.chat_provider,
        system_prompt=self._agent.system_prompt,
        tools=[],
        history=self._context.get_messages(),
        # ❌ 没有 on_message_part 回调
    )

    # 一次性返回完整内容
    yield full_content
```

**Stage 6（流式）**：
```python
async def run(self, user_input: str) -> None:
    from my_cli.soul import wire_send

    # 使用回调实现流式输出
    result = await kosong.generate(
        chat_provider=self._runtime.chat_provider,
        system_prompt=self._agent.system_prompt,
        tools=[],
        history=self._context.get_messages(),
        on_message_part=wire_send,  # ✅ 每个片段都实时发送
    )

    # 保存完整响应
    await self._context.append_message(result.message)
```

**关键变化**：

1. **返回类型**：`AsyncIterator[str]` → `None`
2. **输出方式**：`yield` → `wire_send()`
3. **实时性**：等待完整响应 → 逐片段发送

#### 5.3 消息流动路径

```
LLM API 响应流
     ↓
kosong.generate() 接收流式响应
     ↓
on_message_part=wire_send 回调
     ↓
wire_send(TextPart(text="你"))  ← 第 1 个片段
     ↓
Wire Queue.put_nowait()
     ↓
UI Loop: wire.ui_side.receive()
     ↓
print("你", end="", flush=True)  ← 立即显示
     ↓
wire_send(TextPart(text="好"))  ← 第 2 个片段
     ↓
... 继续流式输出 ...
```

---

### 6. UI Loop 的实现

#### 6.1 Print UI 的 UI Loop

**文件**：`my_cli/ui/print/__init__.py`

```python
async def _ui_loop(self, wire_ui: WireUISide) -> None:
    """
    UI Loop 函数 - 从 Wire 接收消息并打印

    流程：
    1. 循环接收 Wire 消息
    2. 根据消息类型渲染输出
    3. 收到 StepInterrupted 后退出
    """
    while True:
        # 接收一条消息（异步等待）
        msg = await wire_ui.receive()

        # 处理不同类型的消息
        if isinstance(msg, TextPart):
            # 文本片段：实时打印（逐字输出效果）
            if msg.text:
                print(msg.text, end="", flush=True)

        elif isinstance(msg, ContentPart):
            # 内容片段（可能包含图片、文件等）
            if hasattr(msg, "text") and msg.text:
                print(msg.text, end="", flush=True)

        elif isinstance(msg, StepInterrupted):
            # 步骤中断：退出 UI Loop
            break
```

**关键点**：

1. **`await wire_ui.receive()`**：阻塞等待消息
2. **`print(..., end="", flush=True)`**：
   - `end=""`：不换行
   - `flush=True`：立即刷新缓冲区（实现逐字输出）
3. **`StepInterrupted`**：退出信号

#### 6.2 UI Loop 的生命周期

```
run_soul() 启动 UI Loop
     ↓
while True: 循环等待消息
     ↓
msg = await receive()  ← 阻塞等待
     ↓
渲染消息（print）
     ↓
继续循环...
     ↓
收到 StepInterrupted
     ↓
break 退出循环
     ↓
UI Loop 任务结束
```

---

## 🔧 从 Stage 4-5 到 Stage 6 的演进

### 升级步骤总结

#### 步骤 1：创建 Wire 消息系统

**新建文件**：`my_cli/wire/__init__.py`

- 实现 `Wire` 类（基于 `asyncio.Queue`）
- 实现 `WireSoulSide` 和 `WireUISide`

#### 步骤 2：定义消息类型

**新建文件**：`my_cli/wire/message.py`

- 定义控制流事件（`StepBegin`, `StepInterrupted`）
- 定义类型联合（`Event`, `WireMessage`）

#### 步骤 3：修改 Soul 层支持 Wire

**修改文件**：`my_cli/soul/__init__.py`

- 添加 `ContextVar[Wire]`
- 实现 `wire_send()` 全局函数
- 实现 `run_soul()` 调度函数
- 添加异常类（`RunCancelled`, `LLMNotSet`）

#### 步骤 4：升级 KimiSoul.run()

**修改文件**：`my_cli/soul/kimisoul.py`

- 修改签名：`async def run(...) -> AsyncIterator[str]` → `async def run(...) -> None`
- 添加 `on_message_part=wire_send` 回调
- 移除 `yield`，改为通过 Wire 发送

#### 步骤 5：升级 Print UI

**修改文件**：`my_cli/ui/print/__init__.py`

- 使用 `run_soul()` 代替直接调用 `soul.run()`
- 实现 `_ui_loop()` 函数
- 添加异常处理（`RunCancelled`, `ChatProviderError`）

---

## 🎯 测试验证

### 测试流式输出

```bash
# 测试 Wire 机制
python -m my_cli.cli -c "请用3句话介绍Python"
```

**预期输出**：
```
💬 AI 回复:

Python语法简洁，强调可读性，用缩进而非大括号组织代码。
它拥有庞大的标准库和活跃社区，开箱即用，生态覆盖Web、AI、科学计算等场景。
解释型特性支持交互式开发，跨平台且可嵌入，快速原型与脚本自动化首选。
```

**验证要点**：

1. ✅ 响应正确显示（证明 Wire 消息传递成功）
2. ✅ 程序正常退出（证明 `run_soul()` 调度正确）
3. ✅ 没有报错（证明 Wire 机制稳定）

---

## 📊 Stage 6 vs 官方实现对比

### 已实现的功能

| 功能 | 官方 | Stage 6 | 说明 |
|------|------|---------|------|
| Wire 消息队列 | ✅ | ✅ | 完全一致 |
| ContextVar 机制 | ✅ | ✅ | 完全一致 |
| wire_send() | ✅ | ✅ | 完全一致 |
| run_soul() | ✅ | ✅ | 完全一致 |
| StepBegin/StepInterrupted | ✅ | ✅ | 完全一致 |
| on_message_part 回调 | ✅ | ✅ | 完全一致 |
| UI Loop 实现 | ✅ | ✅ | 完全一致 |
| 取消处理 | ✅ | ✅ | 完全一致 |

### Stage 7+ 待实现

| 功能 | 说明 |
|------|------|
| ToolResult 消息 | 工具执行结果 |
| CompactionBegin/End | Context 压缩控制 |
| StatusUpdate | 状态更新（context_usage） |
| ApprovalRequest | 批准请求 |
| SubagentEvent | 子 Agent 事件 |

---

## 🚀 下一步：Stage 7 工具系统

Stage 6 完成了 Wire 机制，下一步将实现工具系统：

1. **Toolset**：工具集合管理
2. **kosong.step()**：支持工具调用的 Agent 循环
3. **基础工具**：Shell、ReadFile、WriteFile
4. **UI 渲染**：显示工具调用过程和结果

---

## 📚 参考资料

- 官方实现：`kimi-cli-fork/src/kimi_cli/wire/__init__.py`
- 官方消息类型：`kimi-cli-fork/src/kimi_cli/wire/message.py`
- asyncio 文档：https://docs.python.org/3/library/asyncio.html
- ContextVar 文档：https://docs.python.org/3/library/contextvars.html

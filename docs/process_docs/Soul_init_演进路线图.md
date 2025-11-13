# Soul __init__.py 演进路线图

> 对比官方 Kimi CLI 的 `soul/__init__.py` 和我们的实现，理解如何一步步实现。

---

## 📋 目录

1. [官方完整版 vs 我们的简化版](#官方完整版-vs-我们的简化版)
2. [逐步演进计划](#逐步演进计划)
3. [各阶段对比详解](#各阶段对比详解)

---

## 官方完整版 vs 我们的简化版

### 官方 Kimi CLI 的 `soul/__init__.py` (181 行)

```python
# 1. 导入
import asyncio
from typing import Protocol, NamedTuple
from kosong.message import ContentPart
from kimi_cli.wire import Wire, WireUISide

# 2. 异常类定义
class LLMNotSet(Exception): ...
class LLMNotSupported(Exception): ...
class MaxStepsReached(Exception): ...
class RunCancelled(Exception): ...

# 3. 数据类
class StatusSnapshot(NamedTuple):
    context_usage: float

# 4. Soul Protocol
@runtime_checkable
class Soul(Protocol):
    @property
    def name(self) -> str: ...

    @property
    def model_name(self) -> str: ...

    @property
    def model_capabilities(self) -> set[ModelCapability] | None: ...

    @property
    def status(self) -> StatusSnapshot: ...

    async def run(self, user_input: str | list[ContentPart]): ...

# 5. 辅助类型
type UILoopFn = Callable[[WireUISide], Coroutine[Any, Any, None]]

# 6. 核心函数
async def run_soul(
    soul: Soul,
    user_input: str | list[ContentPart],
    ui_loop_fn: UILoopFn,
    cancel_event: asyncio.Event,
) -> None:
    """运行 Soul 并连接 UI 循环"""
    wire = Wire()
    ui_task = asyncio.create_task(ui_loop_fn(wire.ui_side))
    soul_task = asyncio.create_task(soul.run(user_input))
    # ... 管理并发任务和取消逻辑

# 7. Wire 管理
_current_wire = ContextVar[Wire | None]("current_wire", default=None)

def get_wire_or_none() -> Wire | None: ...
def wire_send(msg: WireMessage) -> None: ...
```

### 我们的简化版 (Stage 4-5，~100 行)

```python
# 1. 导入
from typing import Protocol
from pathlib import Path
from kosong.chat_provider.kimi import Kimi

# 2. Soul Protocol（简化版）
@runtime_checkable
class Soul(Protocol):
    @property
    def name(self) -> str: ...

    @property
    def model_name(self) -> str: ...

    async def run(self, user_input: str): ...

# 3. 便捷工厂函数
def create_soul(
    work_dir: Path,
    agent_name: str = "MyCLI Assistant",
    model: str = "moonshot-v1-8k",
    ...
) -> KimiSoul:
    """创建 KimiSoul 实例"""
    agent = Agent(...)
    runtime = Runtime(...)
    return KimiSoul(agent, runtime)
```

---

## 逐步演进计划

### Stage 4-5（当前）：最小可运行版本 ✅

**实现内容**：
```python
# soul/__init__.py
- Soul Protocol（3个属性：name, model_name, run）
- create_soul() 工厂函数
```

**特点**：
- ✅ 最简化，只能跑通基础对话
- ❌ 没有 Wire（消息队列）
- ❌ 没有异常类
- ❌ 没有 run_soul() 函数

### Stage 6：添加 Wire 支持

**新增内容**：
```python
# soul/__init__.py
+ from kimi_cli.wire import Wire, WireUISide
+ type UILoopFn = Callable[[WireUISide], Coroutine[Any, Any, None]]

+ async def run_soul(
+     soul: Soul,
+     user_input: str,
+     ui_loop_fn: UILoopFn,
+     cancel_event: asyncio.Event,
+ ) -> None:
+     """运行 Soul 并连接 UI 循环"""
+     ...

+ _current_wire = ContextVar[Wire | None]("current_wire", default=None)
+ def get_wire_or_none() -> Wire | None: ...
+ def wire_send(msg: WireMessage) -> None: ...
```

**改进**：
- ✅ 支持 Wire（Soul 和 UI 之间的消息队列）
- ✅ 支持取消操作（Ctrl+C）
- ✅ Soul 和 UI 并发运行

### Stage 7：添加异常处理

**新增内容**：
```python
# soul/__init__.py
+ class LLMNotSet(Exception):
+     """Raised when the LLM is not set."""

+ class LLMNotSupported(Exception):
+     """Raised when the LLM does not have required capabilities."""

+ class MaxStepsReached(Exception):
+     """Raised when the maximum number of steps is reached."""

+ class RunCancelled(Exception):
+     """The run was cancelled by the cancel event."""
```

**改进**：
- ✅ 标准化的异常类型
- ✅ 更好的错误提示

### Stage 8：完善 Soul Protocol

**新增内容**：
```python
# soul/__init__.py
+ from typing import NamedTuple

+ class StatusSnapshot(NamedTuple):
+     context_usage: float

class Soul(Protocol):
    # ... 原有属性

+   @property
+   def model_capabilities(self) -> set[ModelCapability] | None:
+       """The capabilities of the LLM model."""
+       ...

+   @property
+   def status(self) -> StatusSnapshot:
+       """The current status of the soul."""
+       ...

    async def run(
-       self, user_input: str
+       self, user_input: str | list[ContentPart]  # 支持多模态
    ): ...
```

**改进**：
- ✅ 支持多模态输入（文本 + 图片）
- ✅ 支持状态查询（上下文使用量）
- ✅ 支持模型能力检查

---

## 各阶段对比详解

### 1. Soul Protocol 属性对比

#### Stage 4-5（当前）

```python
class Soul(Protocol):
    @property
    def name(self) -> str:
        """Agent 的名称"""
        ...

    @property
    def model_name(self) -> str:
        """使用的 LLM 模型名称"""
        ...

    async def run(self, user_input: str):
        """运行 Agent"""
        ...
```

**特点**：
- ✅ 3个成员：name, model_name, run()
- ✅ run() 只接受字符串输入
- ✅ 最简单，能跑通

#### 官方完整版

```python
class Soul(Protocol):
    @property
    def name(self) -> str: ...

    @property
    def model_name(self) -> str: ...

    @property
    def model_capabilities(self) -> set[ModelCapability] | None:
        """模型能力（如是否支持 thinking、image_in）"""
        ...

    @property
    def status(self) -> StatusSnapshot:
        """当前状态（如上下文使用量）"""
        ...

    async def run(self, user_input: str | list[ContentPart]):
        """
        运行 Agent

        Args:
            user_input: 字符串 或 多模态内容列表
                       [TextPart(...), ImageURLPart(...)]
        """
        ...
```

**新增**：
- ✅ `model_capabilities`：检查模型能力
- ✅ `status`：查询运行状态
- ✅ `run()` 支持多模态输入

---

### 2. 异常类对比

#### Stage 4-5（当前）

❌ **没有定义异常类**

代码中直接抛出通用异常：
```python
raise Exception("LLM API 调用失败")
```

#### 官方完整版

✅ **定义了 4 个专用异常类**

```python
class LLMNotSet(Exception):
    """当 LLM 未配置时抛出"""

class LLMNotSupported(Exception):
    """当 LLM 不支持所需能力时抛出"""
    def __init__(self, llm: LLM, capabilities: list[ModelCapability]):
        self.llm = llm
        self.capabilities = capabilities
        super().__init__(
            f"LLM model '{llm.model_name}' does not support: "
            f"{', '.join(capabilities)}."
        )

class MaxStepsReached(Exception):
    """当达到最大步数时抛出"""
    def __init__(self, n_steps: int):
        self.n_steps = n_steps

class RunCancelled(Exception):
    """当运行被取消时抛出"""
```

**好处**：
- ✅ 更清晰的错误类型
- ✅ 更好的错误消息
- ✅ 便于上层捕获和处理

---

### 3. Wire 支持对比

#### Stage 4-5（当前）

❌ **没有 Wire 支持**

Soul 和 UI 之间没有消息队列：
```python
# PrintUI 直接调用 Soul
async for chunk in soul.run(command):
    print(chunk, end="", flush=True)
```

**问题**：
- ❌ Soul 和 UI 强耦合
- ❌ 无法并发运行
- ❌ 无法取消操作

#### 官方完整版

✅ **使用 Wire（消息队列）**

```python
async def run_soul(
    soul: Soul,
    user_input: str,
    ui_loop_fn: UILoopFn,  # UI 循环函数
    cancel_event: asyncio.Event,  # 取消事件
) -> None:
    # 1. 创建 Wire
    wire = Wire()

    # 2. 启动 UI 循环（后台任务）
    ui_task = asyncio.create_task(ui_loop_fn(wire.ui_side))

    # 3. 启动 Soul 运行（后台任务）
    soul_task = asyncio.create_task(soul.run(user_input))

    # 4. 等待完成或取消
    cancel_task = asyncio.create_task(cancel_event.wait())
    await asyncio.wait([soul_task, cancel_task], return_when=FIRST_COMPLETED)

    # 5. 处理取消逻辑
    if cancel_event.is_set():
        soul_task.cancel()
        await soul_task  # 等待取消完成
        raise RunCancelled
    else:
        soul_task.result()  # 获取结果或抛出异常

    # 6. 关闭 Wire
    wire.shutdown()
    await ui_task
```

**好处**：
- ✅ Soul 和 UI 解耦（通过 Wire 通信）
- ✅ 支持并发（Soul 和 UI 同时运行）
- ✅ 支持取消（Ctrl+C）
- ✅ 流式输出（通过 Wire 传递消息）

**Wire 的作用**：
```
┌──────────┐        Wire         ┌──────────┐
│  Soul    │ ◄──────────────────► │  UI      │
│          │                      │          │
│  LLM调用 │  WireMessage         │  渲染输出│
│  工具执行│  ────────────►       │  用户输入│
└──────────┘                      └──────────┘
```

---

### 4. 全局 Wire 管理对比

#### Stage 4-5（当前）

❌ **没有全局 Wire**

#### 官方完整版

✅ **使用 ContextVar 管理全局 Wire**

```python
from contextvars import ContextVar

# 全局 Wire 变量（线程安全）
_current_wire = ContextVar[Wire | None]("current_wire", default=None)

def get_wire_or_none() -> Wire | None:
    """获取当前 Wire（在 Soul 运行时可用）"""
    return _current_wire.get()

def wire_send(msg: WireMessage) -> None:
    """向 Wire 发送消息（Soul 内部使用）"""
    wire = get_wire_or_none()
    assert wire is not None, "Wire is expected to be set"
    wire.soul_side.send(msg)
```

**用途**：
```python
# 在 KimiSoul 内部任何地方都可以发送消息到 UI
from kimi_cli.soul import wire_send
from kimi_cli.wire.message import StatusUpdate

# 发送状态更新
wire_send(StatusUpdate(context_usage=0.75))

# 发送步骤开始
wire_send(StepBegin(step_number=1))
```

---

## 演进路线总结

### Stage 4-5（✅ 已完成）

**文件**：
```
soul/
├── __init__.py       # Soul Protocol + create_soul()
├── kimisoul.py       # KimiSoul 实现
├── agent.py          # Agent
├── runtime.py        # Runtime
└── context.py        # Context
```

**功能**：
- ✅ 基础对话
- ✅ 流式输出（直接输出到 stdout）
- ❌ 没有 Wire
- ❌ 没有工具调用

### Stage 6（🔜 下一步）

**新增**：
```
soul/
├── __init__.py       # + run_soul(), Wire 管理
└── (其他文件不变)
```

**功能**：
- ✅ Wire 消息队列
- ✅ Soul 和 UI 并发运行
- ✅ 支持取消操作

### Stage 7（🔜 未来）

**新增**：
```
soul/
├── __init__.py       # + 异常类
├── kimisoul.py       # + 工具调用循环
└── toolset.py        # 新增：工具集管理
```

**功能**：
- ✅ 工具调用（Shell, ReadFile, WriteFile）
- ✅ 标准化异常处理

### Stage 8+（🔜 完整版）

**新增**：
```
soul/
├── __init__.py       # + StatusSnapshot, model_capabilities
├── kimisoul.py       # + 完整的 Agent 循环
├── compaction.py     # 新增：上下文压缩
├── approval.py       # 新增：审批机制
└── denwarenji.py     # 新增：外部通信
```

**功能**：
- ✅ 多模态输入
- ✅ 上下文压缩
- ✅ 工具审批
- ✅ 完整的状态管理

---

## 关键设计思想

### 1. 为什么要分离接口和实现？

**接口**（Protocol）：
```python
# soul/__init__.py
class Soul(Protocol):
    async def run(self, user_input: str): ...
```

**实现**（KimiSoul）：
```python
# soul/kimisoul.py
class KimiSoul:
    async def run(self, user_input: str):
        # 具体实现...
```

**好处**：
- ✅ 便于测试（可以 Mock Soul）
- ✅ 便于扩展（可以有多种 Soul 实现）
- ✅ 符合 SOLID 原则

### 2. 为什么需要 run_soul() 函数？

**直接调用**（Stage 4-5）：
```python
# 简单但耦合
soul = create_soul(...)
async for chunk in soul.run("Hello"):
    print(chunk)
```

**使用 run_soul()**（Stage 6+）：
```python
# 解耦且支持并发
soul = create_soul(...)

async def ui_loop(wire_ui: WireUISide):
    """UI 循环：从 Wire 读取消息并渲染"""
    async for msg in wire_ui.recv():
        if isinstance(msg, ContentPart):
            print(msg.content, end="")
        elif isinstance(msg, StatusUpdate):
            print(f"[Status: {msg.context_usage:.0%}]")

cancel_event = asyncio.Event()
await run_soul(soul, "Hello", ui_loop, cancel_event)
```

**好处**：
- ✅ Soul 和 UI 解耦
- ✅ 支持取消
- ✅ 支持复杂的 UI 渲染

---

## 总结

### 我们当前的架构（Stage 4-5）

✅ **完全符合最小演进原则**：
- 只实现了最核心的 Soul Protocol
- 能跑通基础对话
- 代码简洁易懂

### 与官方的差距

| 功能 | Stage 4-5 | 官方完整版 |
|------|-----------|-----------|
| **Soul Protocol** | 3个属性 | 5个属性 |
| **异常类** | ❌ | ✅ 4个 |
| **Wire 支持** | ❌ | ✅ |
| **run_soul()** | ❌ | ✅ |
| **多模态输入** | ❌ | ✅ |
| **工具调用** | ❌ | ✅ |

### 演进计划

**✅ 你的担心是对的！** 但这正是"最小框架逐步搭建"的核心思想：

1. **Stage 4-5（现在）**：能跑 ✅
2. **Stage 6**：加 Wire
3. **Stage 7**：加工具
4. **Stage 8+**：完整功能

**每一步都不需要重写，只需要新增！**

---

**老王的建议**：
- 🎯 当前架构已经正确了！
- 📈 后续只需要在 `__init__.py` 中**逐步添加**，不需要重写
- 🔧 每个 Stage 都是在前一个 Stage 的基础上**增量开发**

**你现在明白了吗？我们的架构完全可以一步步演进成官方那样！** 🚀

# Kimi CLI 流式输出实现详解

## 📖 概述

本文档详细解析 Kimi CLI 如何实现**真正的流式输出**（逐字打字机效果），从 LLM API 的 Server-Sent Events 到终端显示的完整链路。

## 🎯 什么是流式输出？

### 非流式输出（传统方式）

```
用户发送请求 → 等待 5 秒 → LLM 返回完整响应 → 一次性显示

用户体验：
[等待...等待...等待...] → "Python是一门优秀的编程语言"（瞬间显示）
```

### 流式输出（Kimi CLI 方式）

```
用户发送请求 → LLM 逐字生成 → 终端逐字显示

用户体验：
P → Py → Pyt → Pyth → Pytho → Python → Python是 → ...（打字机效果）
```

**优势**：
- ✅ 用户立即看到响应开始
- ✅ 减少等待焦虑
- ✅ 更自然的对话体验
- ✅ 可以提前看到部分结果

---

## 🏗️ 流式输出的技术架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    LLM API (Moonshot/Kimi)                  │
│                                                               │
│  HTTP Response: Server-Sent Events (SSE) 流                 │
│                                                               │
│  data: {"choices":[{"delta":{"content":"P"}}]}              │
│  data: {"choices":[{"delta":{"content":"y"}}]}              │
│  data: {"choices":[{"delta":{"content":"t"}}]}              │
│  ...                                                         │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│              kosong 框架（LLM 响应解析）                     │
│                                                               │
│  async for event in sse_stream:                              │
│      part = parse_event(event)  # TextPart("P")             │
│      if on_message_part:                                     │
│          on_message_part(part)   # ⭐ 回调触发               │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│                wire_send() 全局函数                          │
│                                                               │
│  wire = _current_wire.get()  # 从 ContextVar 获取           │
│  wire.soul_side.send(part)   # 发送到 Wire 队列             │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│                  Wire Queue (asyncio.Queue)                  │
│                                                               │
│  Queue: [TextPart("P"), TextPart("y"), TextPart("t"), ...]  │
│                                                               │
│  特性：FIFO、异步、非阻塞                                    │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│                     UI Loop (Print UI)                       │
│                                                               │
│  while True:                                                 │
│      msg = await wire.ui_side.receive()  # 阻塞等待         │
│      print(msg.text, end="", flush=True) # 立即显示         │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│                        终端显示                              │
│                                                               │
│  P → Py → Pyt → Pyth → Python...                            │
│  （打字机效果）                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔬 关键技术点详解

### 1. Server-Sent Events (SSE) 流式协议

#### 什么是 SSE？

SSE 是一种 HTTP 长连接协议，服务器可以持续向客户端推送事件。

**HTTP 响应头**：
```http
HTTP/1.1 200 OK
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive
```

**响应体**（流式）：
```
data: {"id":"1","choices":[{"delta":{"content":"P"}}]}

data: {"id":"2","choices":[{"delta":{"content":"y"}}]}

data: {"id":"3","choices":[{"delta":{"content":"t"}}]}

data: [DONE]
```

**关键特性**：
- 每个 `data:` 行是一个独立事件
- 服务器可以随时发送新事件
- 客户端可以实时接收（不需要轮询）

#### kosong 如何处理 SSE？

**文件位置**（kosong 框架内部）：
```python
# kosong 内部实现（简化）
async def generate_streaming(chat_provider, ...):
    response = await chat_provider.chat(...)  # HTTP 请求

    async for line in response.iter_lines():  # 逐行读取 SSE
        if line.startswith("data: "):
            data = json.loads(line[6:])  # 解析 JSON

            # 提取内容片段
            if content := data.get("choices", [{}])[0].get("delta", {}).get("content"):
                part = TextPart(text=content)

                # ⭐ 立即触发回调
                if on_message_part:
                    on_message_part(part)
```

---

### 2. on_message_part 回调机制

#### 为什么需要回调？

**问题**：如何在 LLM 生成过程中实时获取片段？

**方案对比**：

| 方案 | 实现 | 问题 |
|------|------|------|
| **回调函数** | `on_message_part=callback` | ✅ 实时触发、简洁 |
| 返回 AsyncIterator | `async for part in generate()` | ❌ kosong 不支持 |
| 轮询 | `while not done: check()` | ❌ 延迟高、浪费资源 |
| WebSocket | 双向通信 | ❌ 复杂、不必要 |

#### 代码实现

**KimiSoul.run() 中的使用**：

**文件**：`my_cli/soul/kimisoul.py:101-107`
```python
async def run(self, user_input: str) -> None:
    from my_cli.soul import wire_send

    # 调用 kosong.generate() 并传入回调
    result = await kosong.generate(
        chat_provider=self._runtime.chat_provider,
        system_prompt=self._agent.system_prompt,
        tools=[],
        history=self._context.get_messages(),
        on_message_part=wire_send,  # ⭐⭐⭐ 关键：每个片段都触发
    )
```

**工作流程**：
```
LLM 返回第 1 个片段 "P"
    ↓
kosong 调用 on_message_part(TextPart("P"))
    ↓
wire_send(TextPart("P")) 被执行
    ↓
消息发送到 Wire 队列
    ↓
继续等待下一个片段...
```

---

### 3. wire_send() 全局函数

#### 实现原理

**文件**：`my_cli/soul/__init__.py:357-381`
```python
# ContextVar：线程安全的上下文变量
_current_wire = ContextVar[Wire | None]("current_wire", default=None)

def wire_send(msg: WireMessage) -> None:
    """
    发送消息到当前 Wire

    关键：使用 ContextVar 获取当前 Wire（不需要传参）
    """
    wire = _current_wire.get()  # 从上下文获取 Wire
    assert wire is not None, "Wire is expected to be set when soul is running"
    wire.soul_side.send(msg)  # 发送到队列
```

#### 为什么使用 ContextVar？

**问题**：`on_message_part` 回调函数签名是固定的：
```python
Callable[[MessagePart], None]  # 只接受一个参数
```

我们无法传递额外参数（如 `wire` 对象）：
```python
# ❌ 不可行：kosong 不支持这样的签名
def my_callback(part, wire):
    wire.send(part)

on_message_part=lambda part: my_callback(part, wire)  # 也不行，wire 作用域问题
```

**解决方案：ContextVar**

```python
# ✅ 可行：使用 ContextVar
_current_wire.set(wire)  # 在 run_soul() 中设置

def wire_send(part):
    wire = _current_wire.get()  # 从上下文获取
    wire.send(part)

on_message_part=wire_send  # 完美！
```

**ContextVar 的优势**：

1. **线程安全**：每个 asyncio.Task 有独立的上下文
2. **无需传参**：回调函数可以直接访问
3. **作用域清晰**：`set()` 和 `reset()` 管理生命周期

#### 时序图

```
run_soul() 开始
    ↓
_current_wire.set(wire)  # 设置上下文
    ↓
启动 Soul 任务
    ↓
kosong.generate() 调用 on_message_part
    ↓
wire_send() 执行
    ↓
_current_wire.get()  # 获取之前设置的 wire
    ↓
wire.soul_side.send(msg)
    ↓
消息发送到队列
```

---

### 4. Wire Queue 的异步传递

#### asyncio.Queue 的特性

**文件**：`my_cli/wire/__init__.py:73-76`
```python
class Wire:
    def __init__(self):
        # 核心：asyncio.Queue
        self._queue = asyncio.Queue[WireMessage]()
```

**asyncio.Queue 的工作原理**：

```python
# 发送端（Soul 层）
queue.put_nowait(msg)  # 非阻塞，立即返回

# 接收端（UI 层）
msg = await queue.get()  # 阻塞，直到有消息
```

**内部机制**：

```
队列为空时：
    UI Loop 的 get() 处于阻塞状态（等待）

Soul 层调用 put_nowait(msg)：
    1. 消息加入队列
    2. 唤醒正在等待的 get()
    3. get() 立即返回消息

耗时：< 1ms（内存操作）
```

#### WireSoulSide.send() 实现

**文件**：`my_cli/wire/__init__.py:112-130`
```python
class WireSoulSide:
    def send(self, msg: WireMessage) -> None:
        """非阻塞发送"""
        try:
            self._queue.put_nowait(msg)  # ⭐ 关键：不阻塞
        except asyncio.QueueShutDown:
            pass  # 队列关闭，静默失败
```

**为什么使用 put_nowait()？**

- `put_nowait()`：非阻塞，立即返回
- `put()`：如果队列满，会阻塞等待

**选择 put_nowait() 的原因**：

1. **不能阻塞 LLM 响应流**：
   ```python
   # ❌ 如果使用 await put()
   async def on_message_part(part):
       await wire.send(part)  # 可能阻塞，拖慢 LLM 处理

   # ✅ 使用 put_nowait()
   def on_message_part(part):
       wire.send(part)  # 立即返回，不阻塞
   ```

2. **队列默认无限容量**：不会满，`put_nowait()` 不会阻塞

---

### 5. UI Loop 的实时接收

#### _ui_loop() 实现

**文件**：`my_cli/ui/print/__init__.py:138-176`
```python
async def _ui_loop(self, wire_ui: WireUISide) -> None:
    """UI Loop 函数 - 从 Wire 接收消息并打印"""

    while True:
        # ⭐ 阻塞等待消息（有消息立即返回）
        msg = await wire_ui.receive()

        # 处理不同类型的消息
        if isinstance(msg, TextPart):
            if msg.text:
                # ⭐⭐⭐ 立即打印（flush=True）
                print(msg.text, end="", flush=True)

        elif isinstance(msg, ContentPart):
            if hasattr(msg, "text") and msg.text:
                print(msg.text, end="", flush=True)

        elif isinstance(msg, StepInterrupted):
            break  # 退出循环
```

#### receive() 的工作原理

**文件**：`my_cli/wire/__init__.py:145-159`
```python
class WireUISide:
    async def receive(self) -> WireMessage:
        """接收一条消息（异步等待）"""
        msg = await self._queue.get()  # ⭐ 阻塞等待
        return msg
```

**asyncio.Queue.get() 的行为**：

```python
# 队列为空
msg = await queue.get()  # 阻塞，等待新消息

# 其他任务调用 put_nowait()
queue.put_nowait(TextPart("你"))  # 队列有消息了

# get() 立即被唤醒并返回
msg  # TextPart("你")
```

**时间消耗**：
- 队列为空时：无限等待（但不占用 CPU）
- 有消息时：< 1ms（内存读取）

---

### 6. print() 的 flush=True 参数

#### 为什么需要 flush=True？

**问题**：Python 的 `print()` 默认有缓冲区

```python
# ❌ 没有 flush=True
print("你", end="")  # 不会立即显示
print("好", end="")  # 仍然不显示
print()              # 遇到换行才显示："你好"
```

**原因**：`sys.stdout` 有缓冲区（通常 4KB 或行缓冲）

**解决方案**：
```python
# ✅ 使用 flush=True
print("你", end="", flush=True)  # 立即显示："你"
print("好", end="", flush=True)  # 立即追加："你好"
```

#### 参数说明

**文件**：`my_cli/ui/print/__init__.py:166`
```python
print(msg.text, end="", flush=True)
```

| 参数 | 默认值 | 说明 | 作用 |
|------|--------|------|------|
| `end` | `"\n"` | 结尾字符 | `end=""` 不换行，连续输出 |
| `flush` | `False` | 是否刷新缓冲 | `flush=True` 立即显示 |

**效果对比**：

```python
# ❌ 默认参数（非流式）
for char in "Python":
    print(char)  # 每个字符一行，有缓冲

输出：
P
y
t
h
o
n

# ✅ 流式参数
for char in "Python":
    print(char, end="", flush=True)

输出：
Python（逐字显示，打字机效果）
```

---

## ⏱️ 完整的时间线分析

### 单个字符的流动时间

让我们分析从 LLM API 返回 "你" 到终端显示的完整耗时：

```
时间点 T0：LLM API 生成 "你" 并发送 SSE 事件
    ↓ (网络延迟：5-50ms)
时间点 T1：kosong 收到 SSE 事件
    ↓ (JSON 解析：< 1ms)
时间点 T2：kosong 调用 on_message_part(TextPart("你"))
    ↓ (函数调用：< 0.1ms)
时间点 T3：wire_send() 执行
    ↓ (ContextVar.get()：< 0.1ms)
时间点 T4：wire.soul_side.send() 执行
    ↓ (Queue.put_nowait()：< 0.1ms)
时间点 T5：消息进入 Wire 队列
    ↓ (Queue.get() 唤醒：< 0.1ms)
时间点 T6：UI Loop 的 receive() 返回消息
    ↓ (isinstance 判断：< 0.1ms)
时间点 T7：print(..., flush=True) 执行
    ↓ (终端渲染：1-5ms)
时间点 T8：终端显示 "你"

总耗时（T8 - T1）：< 10ms（主要是网络延迟）
```

### 并发处理的优势

```
传统同步方式：
    LLM 生成 "你" → 等待处理完成 → 生成 "好" → 等待处理完成 → ...
    总耗时：生成时间 + 处理时间 * N

Wire 异步方式：
    LLM 生成 "你" → 立即发送到队列 → 同时生成 "好" → 同时发送 → ...
              ↓
         UI Loop 并发接收和显示
    总耗时：生成时间（处理几乎不增加耗时）
```

---

## 🎨 流式输出的视觉效果

### 终端渲染过程

```
第 0.0 秒：终端光标闪烁（等待输入）
    |

第 0.1 秒：显示 "P"
    P|

第 0.2 秒：显示 "y"
    Py|

第 0.3 秒：显示 "t"
    Pyt|

第 0.4 秒：显示 "h"
    Pyth|

第 0.5 秒：显示 "o"
    Pytho|

第 0.6 秒：显示 "n"
    Python|

... 继续显示 ...

最终：
    Python是一门优秀的编程语言|
```

### 用户体验对比

**非流式（Stage 4-5）**：
```
用户发送：请介绍Python

[等待 3 秒...屏幕空白]

突然显示：
Python是一门优秀的编程语言，具有简洁的语法...

用户感受：焦虑、不确定是否在处理
```

**流式（Stage 6）**：
```
用户发送：请介绍Python

0.1秒后：P
0.2秒后：Py
0.3秒后：Pyt
0.4秒后：Pyth
0.5秒后：Pytho
0.6秒后：Python
0.7秒后：Python是
...

用户感受：安心、有反馈、像真人在打字
```

---

## 🔍 调试和验证

### 如何验证流式输出工作？

#### 方法 1：观察终端

```bash
# 运行 Kimi CLI
python -m my_cli.cli -c "用50个字介绍Python"

# 观察：
# ✅ 如果逐字显示（打字机效果）→ 流式工作
# ❌ 如果一次性显示 → 流式未工作
```

#### 方法 2：添加调试日志

**修改 wire_send()**：
```python
def wire_send(msg: WireMessage) -> None:
    wire = get_wire_or_none()
    assert wire is not None

    # 调试：打印每个消息片段
    if isinstance(msg, TextPart):
        print(f"\n[DEBUG] wire_send: {repr(msg.text)}", file=sys.stderr)

    wire.soul_side.send(msg)
```

**运行后观察 stderr**：
```
[DEBUG] wire_send: 'P'
[DEBUG] wire_send: 'y'
[DEBUG] wire_send: 't'
[DEBUG] wire_send: 'h'
...
```

#### 方法 3：测量时间间隔

**修改 UI Loop**：
```python
import time

async def _ui_loop(self, wire_ui: WireUISide) -> None:
    last_time = time.time()

    while True:
        msg = await wire_ui.receive()

        now = time.time()
        interval = now - last_time
        last_time = now

        if isinstance(msg, TextPart):
            # 打印接收间隔
            print(f"\n[{interval:.3f}s] {msg.text}", file=sys.stderr)
            print(msg.text, end="", flush=True)
```

**输出示例**：
```
[0.102s] P
[0.098s] y
[0.105s] t
[0.101s] h
...
```

如果间隔都在 100ms 左右，说明流式正常工作。

---

## 🚀 性能优化建议

### 1. 队列容量限制

**问题**：如果 UI Loop 处理慢，队列可能无限增长

**解决方案**：
```python
# 修改 Wire.__init__()
self._queue = asyncio.Queue[WireMessage](maxsize=1000)  # 限制容量
```

**效果**：
- 队列满时，`put_nowait()` 会抛出 `asyncio.QueueFull`
- 可以选择丢弃消息或等待

### 2. 批量刷新

**问题**：每个字符都 `flush=True` 可能影响性能

**改进方案**：
```python
# 每 N 个字符或每 M 毫秒刷新一次
buffer = []
last_flush = time.time()

async def _ui_loop(self, wire_ui: WireUISide):
    while True:
        msg = await wire_ui.receive()

        if isinstance(msg, TextPart):
            buffer.append(msg.text)

            # 每 10 个字符或每 50ms 刷新
            if len(buffer) >= 10 or (time.time() - last_flush) > 0.05:
                print("".join(buffer), end="", flush=True)
                buffer.clear()
                last_flush = time.time()
```

### 3. 消息合并

**问题**：LLM 可能每次返回多个字符，没必要拆分

**kosong 内部优化**：
```python
# kosong 已经做了合并：每个 SSE 事件可能包含多个字符
data: {"choices":[{"delta":{"content":"Pytho"}}]}  # 5 个字符一起
```

我们的实现已经支持：
```python
print(msg.text, end="", flush=True)  # msg.text 可能是多个字符
```

---

## 📊 对比：Stage 4-5 vs Stage 6

### 代码对比

**Stage 4-5（非流式）**：
```python
# KimiSoul.run()
async def run(self, user_input: str) -> AsyncIterator[str]:
    result = await kosong.generate(...)  # 等待完整响应

    # 提取完整内容
    full_content = extract_text(result.message)

    # 一次性返回
    yield full_content

# Print UI
async def run(self, command: str):
    async for chunk in soul.run(command):  # 只会迭代一次
        print(chunk)  # 一次性打印全部
```

**Stage 6（流式）**：
```python
# KimiSoul.run()
async def run(self, user_input: str) -> None:
    result = await kosong.generate(
        ...,
        on_message_part=wire_send,  # ⭐ 每个片段都触发
    )

# Print UI
async def run(self, command: str):
    await run_soul(soul, command, self._ui_loop, cancel_event)

async def _ui_loop(self, wire_ui: WireUISide):
    while True:
        msg = await wire_ui.receive()  # 实时接收
        print(msg.text, end="", flush=True)  # 逐字打印
```

### 性能对比

| 指标 | Stage 4-5 | Stage 6 | 说明 |
|------|-----------|---------|------|
| 首字延迟 | 3-10 秒 | 0.1-0.5 秒 | Stage 6 快 10-100 倍 |
| 显示方式 | 一次性 | 逐字 | Stage 6 更自然 |
| 用户体验 | 焦虑等待 | 实时反馈 | Stage 6 更好 |
| 内存占用 | 高（缓存全部） | 低（流式处理） | Stage 6 更优 |
| 代码复杂度 | 低 | 中 | Stage 6 稍复杂 |

---

## 🎓 学习要点总结

### 核心概念

1. **Server-Sent Events**：HTTP 长连接流式协议
2. **回调函数**：`on_message_part` 实时触发机制
3. **ContextVar**：线程安全的上下文变量
4. **asyncio.Queue**：异步消息队列
5. **print flush**：立即刷新终端缓冲区

### 关键代码位置

| 位置 | 文件:行号 | 说明 |
|------|----------|------|
| 回调注册 | `kimisoul.py:106` | `on_message_part=wire_send` |
| 全局发送 | `__init__.py:381` | `wire.soul_side.send(msg)` |
| 队列发送 | `wire/__init__.py:127` | `put_nowait(msg)` |
| 队列接收 | `wire/__init__.py:158` | `await get()` |
| 终端显示 | `print/__init__.py:166` | `print(..., flush=True)` |

### 设计模式

1. **观察者模式**：`on_message_part` 回调
2. **生产者-消费者**：Wire Queue
3. **依赖注入**：`run_soul(ui_loop_fn)`
4. **上下文管理**：ContextVar

---

## 🔗 参考资料

- **Server-Sent Events 规范**：https://html.spec.whatwg.org/multipage/server-sent-events.html
- **asyncio.Queue 文档**：https://docs.python.org/3/library/asyncio-queue.html
- **ContextVar 文档**：https://docs.python.org/3/library/contextvars.html
- **官方 kimi-cli 源码**：`kimi-cli-fork/src/kimi_cli/`

---

**文档版本**：1.0
**最后更新**：2025-01-15
**维护者**：老王

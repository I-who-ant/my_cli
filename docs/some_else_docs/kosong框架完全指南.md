# kosong 框架完全指南

> **kosong** 在马来语和印尼语中意为"空"，寓意这是一个纯粹的 LLM 抽象层。

---

## 📋 目录

1. [kosong 是什么](#kosong-是什么)
2. [为什么需要 kosong](#为什么需要-kosong)
3. [核心概念](#核心概念)
4. [目录结构](#目录结构)
5. [核心模块详解](#核心模块详解)
6. [在 Kimi CLI 中的应用](#在-kimi-cli-中的应用)
7. [实战示例](#实战示例)
8. [与 LangChain 的对比](#与-langchain-的对比)

---

## kosong 是什么

**kosong 是 Kimi 团队开发的 LLM 抽象层框架**，专为现代 AI Agent 应用设计。

### 核心特性

1. **统一的消息结构**：统一不同 LLM 提供商的消息格式
2. **异步工具编排**：优雅地处理工具调用和异步任务
3. **可插拔的 Chat Provider**：轻松切换不同的 LLM 提供商
4. **流式响应支持**：原生支持流式输出

### 设计哲学

```
┌─────────────────────────────────────┐
│        Your AI Agent Code           │  ← 你的业务逻辑
├─────────────────────────────────────┤
│          kosong 抽象层              │  ← 统一的接口
├─────────────────────────────────────┤
│  Kimi | OpenAI | Anthropic | ...   │  ← 不同的 LLM 提供商
└─────────────────────────────────────┘
```

**好处**：
- ✅ 避免供应商锁定（Vendor Lock-in）
- ✅ 统一的开发体验
- ✅ 易于测试和迁移

---

## 为什么需要 kosong

### 问题：直接调用 LLM API 的痛点

**场景 1：不同提供商的 API 不统一**

```python
# OpenAI
response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello"}]
)

# Anthropic
response = anthropic.messages.create(
    model="claude-3",
    messages=[{"role": "user", "content": "Hello"}]
)

# Moonshot (Kimi)
response = moonshot.chat.completions.create(
    model="moonshot-v1-8k",
    messages=[{"role": "user", "content": "Hello"}]
)
```

**问题**：
- ❌ 每个 API 的参数名不同
- ❌ 返回格式不同
- ❌ 切换提供商需要大量代码修改

**场景 2：工具调用（Function Calling）的复杂性**

```python
# 需要手动处理：
# 1. LLM 返回 tool_call
# 2. 执行工具
# 3. 将结果返回给 LLM
# 4. 循环直到没有工具调用

while True:
    response = llm.call(messages)
    if not response.tool_calls:
        break
    for tool_call in response.tool_calls:
        result = execute_tool(tool_call)
        messages.append(tool_result_to_message(result))
```

**问题**：
- ❌ 需要手动管理循环
- ❌ 错误处理复杂
- ❌ 异步工具调用难以编排

### 解决方案：kosong 的抽象

**统一的接口**：

```python
import kosong
from kosong.chat_provider.kimi import Kimi

# 创建 ChatProvider
kimi = Kimi(
    base_url="https://api.moonshot.ai/v1",
    api_key="your_key",
    model="moonshot-v1-8k",
)

# 统一的调用方式
result = await kosong.generate(
    chat_provider=kimi,           # 可以换成任何其他 Provider
    system_prompt="You are...",
    tools=[],
    history=[Message(role="user", content="Hello")],
)
```

**自动化的工具调用**：

```python
# kosong.step() 自动处理工具调用循环
result = await kosong.step(
    chat_provider=kimi,
    system_prompt="You are...",
    toolset=my_toolset,           # 工具集
    history=[Message(role="user", content="Add 2 and 3")],
)

# 工具自动调用，结果自动返回
print(result.message)
print(await result.tool_results())
```

---

## 核心概念

### 1. Message（消息）

**统一的消息格式**，兼容所有 LLM 提供商。

```python
from kosong.message import Message, TextPart, ImageURLPart

# 文本消息
msg = Message(role="user", content="Hello")

# 多模态消息（文本 + 图片）
msg = Message(
    role="user",
    content=[
        TextPart(type="text", text="What's in this image?"),
        ImageURLPart(type="image_url", image_url="https://..."),
    ],
)
```

**支持的角色**：
- `user`：用户消息
- `assistant`：AI 响应
- `system`：系统提示（仅在 generate/step 中使用）

### 2. ChatProvider（LLM 提供商）

**抽象了不同 LLM 的 API 调用**。

```python
from kosong.chat_provider import ChatProvider

class ChatProvider(Protocol):
    async def generate(
        self,
        system_prompt: str,
        tools: list[Tool],
        history: list[Message],
        on_message_part: Callback | None = None,
    ) -> GenerateResult:
        """生成 LLM 响应"""
        ...
```

**内置的 ChatProvider**：

| Provider | 模块 | 支持的模型 |
|----------|------|-----------|
| **Kimi (Moonshot)** | `kosong.chat_provider.kimi` | moonshot-v1-8k, moonshot-v1-32k |
| **OpenAI** | `kosong.contrib.chat_provider.openai_legacy` | gpt-4, gpt-3.5-turbo |
| **Anthropic** | `kosong.contrib.chat_provider.anthropic` | claude-3-opus, claude-3-sonnet |
| **Mock** | `kosong.chat_provider.mock` | 测试用的模拟 Provider |

**示例**：

```python
from kosong.chat_provider.kimi import Kimi

# 创建 Kimi ChatProvider
kimi = Kimi(
    base_url="https://api.moonshot.ai/v1",
    api_key="your_api_key",
    model="moonshot-v1-8k",
)

# 使用
result = await kosong.generate(
    chat_provider=kimi,
    ...
)
```

### 3. Tool（工具）

**LLM 可以调用的工具（Function Calling）**。

```python
from pydantic import BaseModel
from kosong.tooling import CallableTool2, ToolOk, ToolReturnType

# 1. 定义参数结构
class AddToolParams(BaseModel):
    a: int
    b: int

# 2. 定义工具
class AddTool(CallableTool2[AddToolParams]):
    name: str = "add"
    description: str = "Add two integers."
    params: type[AddToolParams] = AddToolParams

    async def __call__(self, params: AddToolParams) -> ToolReturnType:
        result = params.a + params.b
        return ToolOk(output=str(result))
```

**工具返回类型**：
- `ToolOk(output=str)`：成功
- `ToolError(error=str)`：失败（可重试）
- `ToolFail(reason=str)`：永久失败

### 4. Toolset（工具集）

**管理多个工具**。

```python
from kosong.tooling.simple import SimpleToolset

# 创建工具集
toolset = SimpleToolset()

# 添加工具
toolset += AddTool()
toolset += SubtractTool()
toolset += MultiplyTool()

# 使用
result = await kosong.step(
    chat_provider=kimi,
    system_prompt="You are a math tutor.",
    toolset=toolset,  # 传入工具集
    history=[...],
)
```

### 5. generate() vs step()

**两个核心函数**：

#### `kosong.generate()` - 生成单次响应

```python
result = await kosong.generate(
    chat_provider=kimi,
    system_prompt="You are...",
    tools=[],  # 工具列表（但不会自动调用）
    history=[Message(role="user", content="Hello")],
    on_message_part=callback,  # 流式回调
)

# 返回：GenerateResult
# - result.id: 消息 ID
# - result.message: AI 的 Message
# - result.usage: Token 使用量
```

**特点**：
- ✅ 只生成一次响应
- ✅ 支持流式输出
- ❌ 不会自动执行工具调用

#### `kosong.step()` - 生成响应 + 自动工具调用

```python
result = await kosong.step(
    chat_provider=kimi,
    system_prompt="You are...",
    toolset=my_toolset,  # 工具集（会自动调用）
    history=[Message(role="user", content="Add 2 and 3")],
    on_message_part=callback,
    on_tool_result=tool_callback,  # 工具调用回调
)

# 返回：StepResult
# - result.message: AI 的 Message
# - result.tool_calls: 所有的工具调用
# - await result.tool_results(): 等待所有工具执行完成
```

**特点**：
- ✅ 自动执行工具调用
- ✅ 异步并发执行多个工具
- ✅ 支持流式输出
- ❌ 只执行一次（需要在外部循环）

---

## 目录结构

```
kosong-main/src/kosong/
├── __init__.py              # 核心 API：generate(), step()
├── _generate.py             # generate() 的实现
├── message.py               # Message 类和多模态内容
├── chat_provider/           # ChatProvider 实现
│   ├── __init__.py          # ChatProvider 协议定义
│   ├── kimi.py              # Kimi (Moonshot) Provider
│   ├── mock.py              # Mock Provider（测试用）
│   └── chaos.py             # Chaos Provider（压力测试）
├── tooling/                 # 工具系统
│   ├── __init__.py          # Tool 协议定义
│   ├── simple.py            # SimpleToolset 实现
│   ├── empty.py             # EmptyToolset（无工具）
│   └── error.py             # 工具错误类型
├── contrib/                 # 扩展模块
│   ├── chat_provider/       # 第三方 ChatProvider
│   │   ├── openai_legacy.py # OpenAI Provider
│   │   ├── openai_responses.py # OpenAI Responses API
│   │   └── anthropic.py     # Anthropic Provider
│   └── context/             # 上下文管理
│       └── linear.py        # 线性上下文管理器
└── utils/                   # 工具函数
    ├── aio.py               # 异步工具
    └── typing.py            # 类型定义
```

---

## 核心模块详解

### 1. `kosong/__init__.py` - 核心 API

**两个核心函数**：

```python
import kosong

# 1. generate() - 生成单次响应
async def generate(
    chat_provider: ChatProvider,
    system_prompt: str,
    tools: Sequence[Tool],
    history: Sequence[Message],
    *,
    on_message_part: Callback[[StreamedMessagePart], None] | None = None,
    on_tool_call: Callable[[ToolCall], Awaitable[None]] | None = None,
) -> GenerateResult:
    """
    生成单次 LLM 响应

    返回：
    - GenerateResult.id: 消息 ID
    - GenerateResult.message: AI 的 Message
    - GenerateResult.usage: Token 使用量
    """

# 2. step() - 生成响应 + 自动工具调用
async def step(
    chat_provider: ChatProvider,
    system_prompt: str,
    toolset: Toolset,
    history: Sequence[Message],
    *,
    on_message_part: Callback[[StreamedMessagePart], None] | None = None,
    on_tool_result: Callable[[ToolResult], None] | None = None,
) -> StepResult:
    """
    执行一步 Agent 循环

    返回：
    - StepResult.message: AI 的 Message
    - StepResult.tool_calls: 所有的工具调用
    - await StepResult.tool_results(): 等待所有工具执行完成
    """
```

### 2. `kosong/message.py` - 消息结构

```python
from kosong.message import Message, TextPart, ImageURLPart, ToolCall

# 文本消息
msg = Message(role="user", content="Hello")

# 多模态消息
msg = Message(
    role="user",
    content=[
        TextPart(type="text", text="What's in this image?"),
        ImageURLPart(type="image_url", image_url="https://..."),
    ],
)

# AI 响应消息（带工具调用）
msg = Message(
    role="assistant",
    content="I'll add those numbers for you.",
    tool_calls=[
        ToolCall(
            id="call_123",
            name="add",
            arguments={"a": 2, "b": 3},
        ),
    ],
)
```

### 3. `kosong/chat_provider/kimi.py` - Kimi Provider

```python
from kosong.chat_provider.kimi import Kimi

kimi = Kimi(
    base_url="https://api.moonshot.ai/v1",  # Moonshot API 地址
    api_key="your_api_key",                 # API Key
    model="moonshot-v1-8k",                 # 模型名称
    timeout=60.0,                           # 超时时间
    max_retries=3,                          # 最大重试次数
)

# 使用
result = await kosong.generate(chat_provider=kimi, ...)
```

**支持的模型**：
- `moonshot-v1-8k`：8K 上下文
- `moonshot-v1-32k`：32K 上下文
- `moonshot-v1-128k`：128K 上下文

### 4. `kosong/tooling/simple.py` - 简单工具集

```python
from kosong.tooling.simple import SimpleToolset

# 创建工具集
toolset = SimpleToolset()

# 添加工具
toolset += AddTool()
toolset += SubtractTool()

# 查看工具
print(toolset.tools)  # [AddTool(), SubtractTool()]

# 处理工具调用
tool_call = ToolCall(id="call_1", name="add", arguments={"a": 2, "b": 3})
result_future = toolset.handle(tool_call)
result = await result_future  # ToolOk(output="5")
```

---

## 在 Kimi CLI 中的应用

### Kimi CLI 的架构

```
kimi-cli/
├── cli.py               # CLI 入口
├── app.py               # 应用层
├── soul/                # Soul 层（使用 kosong）
│   ├── kimisoul.py      # 核心 Soul 实现
│   ├── agent.py         # Agent 定义
│   ├── runtime.py       # 运行时配置
│   └── context.py       # 上下文管理
└── tools/               # 工具层
    ├── shell.py         # Shell 工具
    ├── read.py          # ReadFile 工具
    └── write.py         # WriteFile 工具
```

### Soul 层如何使用 kosong

**1. 基础对话（Stage 4-5）**：

```python
# my_cli/soul/__init__.py

import kosong
from kosong.chat_provider.kimi import Kimi
from kosong.message import Message

class Soul:
    def __init__(self, work_dir: Path, chat_provider: ChatProvider):
        self.work_dir = work_dir
        self.chat_provider = chat_provider
        self.history: list[Message] = []

    async def chat(self, user_input: str) -> AsyncIterator[str]:
        """使用 kosong.generate() 生成响应"""
        # 1. 添加用户消息
        user_msg = Message(role="user", content=user_input)
        self.history.append(user_msg)

        # 2. 流式回调
        async def on_message_part(part):
            if hasattr(part, "content") and part.content:
                # 实时输出
                pass

        # 3. 调用 kosong.generate()
        result = await kosong.generate(
            chat_provider=self.chat_provider,
            system_prompt="You are an AI assistant.",
            tools=[],  # Stage 4-5 暂无工具
            history=self.history,
            on_message_part=on_message_part,
        )

        # 4. 流式输出
        for char in result.message.content:
            yield char

        # 5. 保存 AI 响应
        self.history.append(result.message)
```

**2. 工具调用（Stage 7）**：

```python
# 使用 kosong.step() 自动处理工具调用

async def run_with_tools(self, user_input: str):
    """使用 kosong.step() 执行工具调用"""
    # 1. 添加用户消息
    user_msg = Message(role="user", content=user_input)
    self.history.append(user_msg)

    # 2. 创建工具集
    toolset = SimpleToolset()
    toolset += ShellTool()
    toolset += ReadFileTool()
    toolset += WriteFileTool()

    # 3. 调用 kosong.step()
    result = await kosong.step(
        chat_provider=self.chat_provider,
        system_prompt="You are an AI assistant with shell access.",
        toolset=toolset,  # 工具集
        history=self.history,
        on_message_part=self._on_message_part,
        on_tool_result=self._on_tool_result,
    )

    # 4. 保存响应和工具结果
    self.history.append(result.message)
    tool_results = await result.tool_results()
    # 将工具结果转换为 Message 并添加到历史
    ...
```

**3. Agent 循环（Stage 8+）**：

```python
async def agent_loop(self, user_input: str):
    """完整的 Agent 循环"""
    self.history.append(Message(role="user", content=user_input))

    max_steps = 10
    for step in range(max_steps):
        # 执行一步
        result = await kosong.step(
            chat_provider=self.chat_provider,
            system_prompt=self.system_prompt,
            toolset=self.toolset,
            history=self.history,
        )

        # 保存响应
        self.history.append(result.message)

        # 没有工具调用，结束循环
        if not result.tool_calls:
            break

        # 等待工具执行
        tool_results = await result.tool_results()

        # 将工具结果添加到历史
        for tool_call, tool_result in zip(result.tool_calls, tool_results):
            self.history.append(tool_result_to_message(tool_call, tool_result))

        # 检查是否需要压缩上下文
        if self.context.token_count > self.max_context_size:
            await self.context.compact()
```

---

## 实战示例

### 示例 1：简单的聊天机器人

```python
import asyncio
from pathlib import Path

import kosong
from kosong.chat_provider.kimi import Kimi
from kosong.message import Message


async def main():
    # 1. 创建 ChatProvider
    kimi = Kimi(
        base_url="https://api.moonshot.ai/v1",
        api_key="your_api_key",
        model="moonshot-v1-8k",
    )

    # 2. 对话历史
    history = []

    # 3. 聊天循环
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            break

        # 添加用户消息
        history.append(Message(role="user", content=user_input))

        # 调用 LLM
        result = await kosong.generate(
            chat_provider=kimi,
            system_prompt="You are a friendly assistant.",
            tools=[],
            history=history,
        )

        # 显示 AI 响应
        print(f"AI: {result.message.content}")

        # 保存 AI 响应
        history.append(result.message)


asyncio.run(main())
```

### 示例 2：流式输出

```python
async def streaming_chat():
    kimi = Kimi(
        base_url="https://api.moonshot.ai/v1",
        api_key="your_api_key",
        model="moonshot-v1-8k",
    )

    history = [Message(role="user", content="Write a poem about AI.")]

    # 流式回调
    def on_message_part(part):
        if hasattr(part, "content") and part.content:
            print(part.content, end="", flush=True)

    result = await kosong.generate(
        chat_provider=kimi,
        system_prompt="You are a poet.",
        tools=[],
        history=history,
        on_message_part=on_message_part,  # 流式回调
    )

    print()  # 换行
    print(f"Token usage: {result.usage}")


asyncio.run(streaming_chat())
```

### 示例 3：工具调用

```python
from pydantic import BaseModel
from kosong.tooling import CallableTool2, ToolOk, ToolReturnType
from kosong.tooling.simple import SimpleToolset


# 定义工具
class WeatherParams(BaseModel):
    city: str


class WeatherTool(CallableTool2[WeatherParams]):
    name: str = "get_weather"
    description: str = "Get current weather for a city."
    params: type[WeatherParams] = WeatherParams

    async def __call__(self, params: WeatherParams) -> ToolReturnType:
        # 模拟天气查询
        weather_data = {
            "Beijing": "Sunny, 25°C",
            "Shanghai": "Cloudy, 22°C",
        }
        weather = weather_data.get(params.city, "Unknown")
        return ToolOk(output=f"Weather in {params.city}: {weather}")


async def tool_calling_example():
    kimi = Kimi(
        base_url="https://api.moonshot.ai/v1",
        api_key="your_api_key",
        model="moonshot-v1-8k",
    )

    # 创建工具集
    toolset = SimpleToolset()
    toolset += WeatherTool()

    history = [
        Message(role="user", content="What's the weather in Beijing?")
    ]

    # 调用 kosong.step()
    result = await kosong.step(
        chat_provider=kimi,
        system_prompt="You are a helpful assistant with weather access.",
        toolset=toolset,
        history=history,
    )

    print(f"AI: {result.message.content}")
    print(f"Tool calls: {result.tool_calls}")

    # 等待工具执行完成
    tool_results = await result.tool_results()
    print(f"Tool results: {tool_results}")


asyncio.run(tool_calling_example())
```

---

## 与 LangChain 的对比

| 特性 | kosong | LangChain |
|------|--------|-----------|
| **定位** | LLM 抽象层 | 完整的 Agent 框架 |
| **复杂度** | 简单、轻量 | 复杂、功能丰富 |
| **学习曲线** | 平缓 | 陡峭 |
| **工具调用** | 自动化（`step()`） | 需要手动管理 Chains |
| **流式输出** | 原生支持 | 需要额外配置 |
| **异步支持** | 完全异步 | 部分支持 |
| **依赖** | 少 | 多 |
| **适用场景** | 简单 Agent、CLI 工具 | 复杂的 RAG、Multi-Agent |

**kosong 的优势**：
- ✅ 简单、专注
- ✅ 异步优先
- ✅ 流式输出友好
- ✅ 适合 CLI 工具

**LangChain 的优势**：
- ✅ 功能丰富（RAG、Embedding、Vector Store）
- ✅ 生态完善
- ✅ 适合复杂的企业级应用

---

## 总结

### kosong 的核心价值

1. **统一抽象**：统一不同 LLM 提供商的接口
2. **简化开发**：自动化工具调用、流式输出
3. **避免锁定**：轻松切换不同的 LLM 提供商
4. **异步优先**：完全异步设计，性能优秀

### 在 Kimi CLI 中的应用

- **Stage 4-5**：使用 `kosong.generate()` 实现基础对话
- **Stage 7**：使用 `kosong.step()` 实现工具调用
- **Stage 8+**：在 `kosong.step()` 外层实现 Agent 循环

### 下一步

1. 阅读 `kosong-main/src/kosong/__init__.py` 的源码
2. 运行 `python -m kosong kimi --with-bash` 体验内置 Demo
3. 在 `my_cli/soul/__init__.py` 中实践使用 kosong

---

**老王的建议**：
- 🎯 kosong 是 Kimi CLI 的核心依赖，理解它是理解 Soul 层的关键
- 📚 从简单的 `kosong.generate()` 开始，逐步掌握 `kosong.step()`
- 🔧 先跑通 Stage 4-5 的基础对话，再考虑 Stage 7 的工具调用

**现在你明白了吗？kosong 就是让我们不用操心底层 API 的差异，专注于 Agent 的业务逻辑！** 🚀

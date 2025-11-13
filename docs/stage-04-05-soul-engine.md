# 阶段 4-5：Soul 引擎与真实 LLM 集成

## 学习目标

通过这个阶段，你将学会：

1. ✅ 理解 Soul Protocol 协议设计
2. ✅ 使用 kosong 框架调用 LLM API
3. ✅ 实现配置文件系统管理 API 密钥
4. ✅ 理解 Context（对话上下文）管理
5. ✅ 掌握异步生成器（AsyncIterator）
6. ✅ 理解 Pydantic 模型验证

## 对应源码

- **原项目文件**：
  - `kimi-cli-main/src/kimi_cli/soul/kimisoul.py` (360 行)
  - `kimi-cli-main/src/kimi_cli/config.py` (418 行)
  - `kimi-cli-main/src/kimi_cli/llm.py` (200+ 行)

- **简化版本**：
  - `my_cli/soul/kimisoul.py` (约 190 行，包含详细 TODO 注释)
  - `my_cli/config.py` (约 420 行)
  - `my_cli/soul/__init__.py` (约 60 行)

**简化内容**：
- 去掉了工具系统（Tool/Toolset，留到 Stage 7）
- 去掉了 Wire 机制（留到 Stage 6）
- 去掉了 Context 压缩（Compaction）
- 去掉了 Checkpoint/Rollback 功能
- 去掉了重试机制和错误恢复
- **暂时使用非流式输出**（简化实现，Stage 6 升级为真正的流式）

## 核心架构

### 1. Soul Protocol 协议

Soul Protocol 是一个**协议接口**（Python Protocol），定义了 AI Agent 的标准接口：

```python
from typing import Protocol, AsyncIterator

class Soul(Protocol):
    @property
    def name(self) -> str:
        """Agent 名称"""
        ...

    @property
    def model_name(self) -> str:
        """使用的 LLM 模型名称"""
        ...

    async def run(self, user_input: str) -> AsyncIterator[str]:
        """运行 Agent，返回流式响应"""
        ...
```

**为什么使用 Protocol？**
- 定义接口标准，不关心具体实现
- 支持多种 Soul 实现（KimiSoul、ClaudeSoul 等）
- UI 层只依赖 Soul Protocol，不依赖具体实现

### 2. Soul 层架构图

```
┌─────────────────────────────────────────────────────┐
│                    UI 层                            │
│  (Shell UI / Print UI / ACP Server)                 │
└─────────────────┬───────────────────────────────────┘
                  │ 调用 Soul.run()
                  ↓
┌─────────────────────────────────────────────────────┐
│                  Soul 层                            │
│  ┌───────────────────────────────────────────────┐ │
│  │         KimiSoul (Soul Protocol 实现)         │ │
│  │                                               │ │
│  │  - Agent（身份和能力定义）                     │ │
│  │  - Runtime（ChatProvider 管理）               │ │
│  │  - Context（对话历史）                        │ │
│  └───────────────────────────────────────────────┘ │
└─────────────────┬───────────────────────────────────┘
                  │ kosong.generate()
                  ↓
┌─────────────────────────────────────────────────────┐
│              kosong 框架层                          │
│  ┌──────────────────────────────────────────────┐  │
│  │           ChatProvider 接口                  │  │
│  │  ┌───────────┐  ┌────────────┐  ┌─────────┐ │  │
│  │  │ Kimi API  │  │ Claude API │  │ OpenAI  │ │  │
│  │  └───────────┘  └────────────┘  └─────────┘ │  │
│  └──────────────────────────────────────────────┘  │
└─────────────────┬───────────────────────────────────┘
                  │ HTTP API
                  ↓
┌─────────────────────────────────────────────────────┐
│              真实 LLM API                           │
│  (Moonshot API / Kimi API / Claude API)             │
└─────────────────────────────────────────────────────┘
```

### 3. 核心组件详解

#### 3.1 KimiSoul 类

```python
class KimiSoul:
    """Soul Protocol 的具体实现"""

    def __init__(
        self,
        agent: Agent,          # 定义身份和能力
        runtime: Runtime,      # 管理 ChatProvider
        context: Context | None = None,  # 对话历史
    ):
        self._agent = agent
        self._runtime = runtime
        self._context = context or Context()

    @property
    def name(self) -> str:
        """实现 Soul Protocol: name"""
        return self._agent.name

    @property
    def model_name(self) -> str:
        """实现 Soul Protocol: model_name"""
        return self._runtime.chat_provider.model_name

    async def run(self, user_input: str) -> AsyncIterator[str]:
        """实现 Soul Protocol: run()"""
        # 1. 添加用户消息到 Context
        user_msg = Message(role="user", content=user_input)
        await self._context.append_message(user_msg)

        # 2. 调用 LLM API
        result = await kosong.generate(
            chat_provider=self._runtime.chat_provider,
            system_prompt=self._agent.system_prompt,
            tools=[],  # Stage 4-5 暂无���具
            history=self._context.get_messages(),
        )

        # 3. 返回响应（Stage 4-5: 非流式）
        # Stage 6: 改为 Wire 机制实现真正的流式输出
        full_content = self._extract_text(result.message)
        if full_content:
            yield full_content

        # 4. 保存 AI 响应到 Context
        await self._context.append_message(result.message)
```

**关键点**：
- `Agent`：定义 system_prompt 和工具集
- `Runtime`：管理 ChatProvider（LLM API 客户端）
- `Context`：管理对话历史（类似聊天记录）
- `kosong.generate()`：统一的 LLM 调用接口

#### 3.2 Agent 类

```python
class Agent:
    """定义 AI Agent 的身份和能力"""

    def __init__(
        self,
        name: str,
        work_dir: Path,
        system_prompt: str | None = None,
    ):
        self.name = name
        self.work_dir = work_dir
        self._system_prompt = system_prompt or self._build_default_system_prompt()

    def _build_default_system_prompt(self) -> str:
        """构建默认的系统提示词"""
        return f"""你是 {self.name}，一个 AI 助手。

请简洁地回答用户问题。"""

    @property
    def system_prompt(self) -> str:
        """获取系统提示词"""
        return self._system_prompt
```

**关键点**：
- `system_prompt`：定义 Agent 的角色和行为规范
- Stage 4-5：只有简单的系统提示
- Stage 7+：添加工具使用说明和工作目录信息

#### 3.3 Runtime 类

```python
class Runtime:
    """管理运行时状态"""

    def __init__(self, chat_provider: ChatProvider, max_steps: int = 20):
        self.chat_provider = chat_provider  # LLM API 客户端
        self.max_steps = max_steps          # 最大循环步数
```

**关键点**：
- `chat_provider`：kosong 框架的统一 LLM 接口
- `max_steps`：防止死循环（Stage 7 工具调用时需要）

#### 3.4 Context 类

```python
class Context:
    """管理对话历史"""

    def __init__(self):
        self._messages: list[Message] = []

    async def append_message(self, message: Message | list[Message]) -> None:
        """添加消息到历史"""
        if isinstance(message, list):
            self._messages.extend(message)
        else:
            self._messages.append(message)

    def get_messages(self) -> list[Message]:
        """获取所有消息（用于传递给 LLM）"""
        return self._messages.copy()

    def __len__(self) -> int:
        """消息数量"""
        return len(self._messages)
```

**关键点**：
- 存储所有用户和 AI 的对话
- 每次调用 LLM 时传递完整历史
- Stage 6+：添加 token 计数和 Context 压缩

### 4. 配置文件系统

#### 4.1 配置结构

```python
from pydantic import BaseModel, Field, SecretStr

class LLMProvider(BaseModel):
    """LLM Provider 配置"""
    type: str  # "kimi", "openai", "claude" 等
    base_url: str
    api_key: SecretStr  # 自动加密显示

class LLMModel(BaseModel):
    """LLM Model 配置"""
    provider: str  # 对应 providers 中的 key
    model: str     # 模型名称
    max_context_size: int = 128000

class Config(BaseModel):
    """主配置结构"""
    default_model: str = Field(default="", description="默认使用的模型")
    providers: dict[str, LLMProvider] = Field(default_factory=dict)
    models: dict[str, LLMModel] = Field(default_factory=dict)
```

#### 4.2 配置文件示例

`.mycli_config.json`：

```json
{
  "default_model": "moonshot-k2",
  "providers": {
    "moonshot": {
      "type": "kimi",
      "base_url": "https://api.moonshot.cn/v1",
      "api_key": "sk-hJwUlVMp..."
    },
    "kimi": {
      "type": "kimi",
      "base_url": "https://api.kimi.com/coding/v1",
      "api_key": "sk-kimi-z0lI1om..."
    }
  },
  "models": {
    "moonshot-k2": {
      "provider": "moonshot",
      "model": "kimi-k2-turbo-preview",
      "max_context_size": 128000
    },
    "kimi-coding": {
      "provider": "kimi",
      "model": "kimi-for-coding",
      "max_context_size": 128000
    }
  }
}
```

#### 4.3 环境变量覆盖

```python
def augment_provider_with_env(provider: LLMProvider) -> dict[str, str]:
    """使用环境变量覆盖 Provider 配置"""
    applied: dict[str, str] = {}

    if provider.type == "kimi":
        # 环境变量优先级更高
        if api_key := os.getenv("KIMI_API_KEY"):
            provider.api_key = SecretStr(api_key)
            applied["KIMI_API_KEY"] = "******"

        if base_url := os.getenv("KIMI_BASE_URL"):
            provider.base_url = base_url
            applied["KIMI_BASE_URL"] = base_url

    return applied
```

**优先级**：
1. 环境变量（最高）
2. 配置文件
3. 代码默认值（最低）

### 5. kosong 框架集成

#### 5.1 创建 ChatProvider

```python
from kosong.chat_provider.kimi import Kimi

# 创建 Kimi API 客户端
chat_provider = Kimi(
    base_url="https://api.moonshot.cn/v1",
    api_key="sk-your-api-key",
    model="kimi-k2-turbo-preview",
)
```

#### 5.2 调用 kosong.generate()

```python
import kosong
from kosong.message import Message

# 准备对话历史
history = [
    Message(role="user", content="你好"),
    Message(role="assistant", content="你好！我是 AI 助手。"),
    Message(role="user", content="介绍一下你自己"),
]

# 调用 LLM
result = await kosong.generate(
    chat_provider=chat_provider,
    system_prompt="你是一个 AI 助手。",
    tools=[],  # Stage 4-5 暂无工具
    history=history,
)

# 获取响应
print(result.message.content)  # AI 的回复
print(result.usage)            # Token 使用情况（可选）
```

**kosong.generate() 返回值**：

```python
@dataclass
class GenerateResult:
    id: str | None           # 消息 ID
    message: Message         # 完整的 AI 响应
    usage: TokenUsage | None # Token 使用情况
```

**注意**：
- `kosong.generate()` 内部已经收集了所有流式片段
- 返回的 `result.message` 是完整消息
- **Stage 4-5 没有实现真正的流式输出**
- **Stage 6 使用 `on_message_part` 回调实现流式**

## 运行测试

### 1. 安装依赖

```bash
# 安装 kosong 框架
pip install kosong

# 或者从本地安装（如果已下载）
cd kimi-cli-main/imitate-src/kosong-main
pip install -e .
```

### 2. 配置 API 密钥

创建 `.mycli_config.json`：

```bash
cd kimi-cli-main/imitate-src
cat > .mycli_config.json <<EOF
{
  "default_model": "moonshot-k2",
  "providers": {
    "moonshot": {
      "type": "kimi",
      "base_url": "https://api.moonshot.cn/v1",
      "api_key": "你的-Moonshot-API-Key"
    }
  },
  "models": {
    "moonshot-k2": {
      "provider": "moonshot",
      "model": "kimi-k2-turbo-preview",
      "max_context_size": 128000
    }
  }
}
EOF
```

**获取 API Key**：
- Moonshot（月之暗面）：https://platform.moonshot.cn/
- Kimi（暗号智能）：https://kimi.moonshot.cn/

### 3. 运行命令

```bash
# 进入项目目录
cd kimi-cli-main/imitate-src

# 运行基本命令
python -m my_cli.cli --ui print -c "你好，介绍一下你自己"

# 开启详细输出（查看 API 调用详情）
python -m my_cli.cli --ui print -c "你好" --verbose

# 切换模型（如果配置了多个）
# 修改 .mycli_config.json 的 default_model 字段
```

### 4. 预期输出

```bash
$ python -m my_cli.cli --ui print -c "你好，介绍一下你自己"
============================================================
My CLI - Print UI 模式
============================================================

用户命令: 你好，介绍一下你自己

AI 响应:
------------------------------------------------------------
你好，我是 MyCLI Assistant，一个由 MyCLI 团队开发的 AI 助手，
专注于简洁、高效地解答问题。
------------------------------------------------------------

✅ LLM 调用成功！
```

带 `--verbose` 的输出：

```bash
$ python -m my_cli.cli --ui print -c "你好" --verbose
[CLI 层] My CLI v0.1.0
[CLI 层] 工作目录: /home/user/project/imitate-src
[CLI 层] UI 模式: print

[应用层] MyCLI 实例创建成功
[应用层] 工作目录: /home/user/project/imitate-src
[应用层] 启动 Print UI 模式

[Print UI] 启动 Print UI 模式
[Print UI] 处理命令: 你好
[Print UI] 创建 Soul 引擎实例（kosong 框架）
[Print UI] Soul 引擎创建成功
[Print UI] Agent 名称: MyCLI Assistant
[Print UI] 使用模型: kimi-k2-turbo-preview

============================================================
My CLI - Print UI 模式
============================================================

用户命令: 你好

AI 响应:
------------------------------------------------------------
你好！有什么我可以帮您的吗？
------------------------------------------------------------

✅ LLM 调用成功！

[Print UI] 消息数量: 2
```

## 与源码对比

### 相同点

1. ✅ 使用 Soul Protocol 定义接口
2. ✅ 使用 kosong 框架统一 LLM 调用
3. ✅ 使用 Pydantic 模型验证配置
4. ✅ 使用 SecretStr 保护 API Key
5. ✅ 支持环境变量覆盖配置
6. ✅ 使用 Context 管理对话历史

### 简化点

1. ❌ 去掉了 Wire 机制（Stage 6 实现）
2. ❌ 去掉了工具系统（Stage 7 实现）
3. ❌ 去掉了 Context 压缩（Compaction）
4. ❌ 去掉了 Checkpoint/Rollback 功能
5. ❌ 去掉了重试机制（tenacity）
6. ❌ 去掉了错误恢复（BackToTheFuture）
7. ❌ **暂时使用非流式输出**（简化实现）

### 核心保留

| 原项目 | 简化版 | 说明 |
|--------|--------|------|
| `Soul Protocol` | ✅ 保留 | 协议接口定义 |
| `KimiSoul` | ✅ 保留 | Soul 实现 |
| `Agent` | ✅ 保留 | 身份定义 |
| `Runtime` | ✅ 保留 | ChatProvider 管理 |
| `Context` | ✅ 保留 | 对话历史 |
| `kosong.generate()` | ✅ 保留 | LLM 调用 |
| `Config/LLMProvider` | ✅ 保留 | 配置管理 |
| `kosong.step()` | ❌ 移除 | Stage 7 实现（工具调用） |
| `on_message_part` | ❌ 移除 | Stage 6 实现（流式输出） |
| `wire_send()` | ❌ 移除 | Stage 6 实现（Wire 机制） |

## Stage 4-5 的技术选择

### 为什么暂时不实现流式输出？

**官方 kimi-cli 的流式实现**：
```python
# 官方使用 kosong.step() + Wire 机制
result = await kosong.step(
    chat_provider=chat_provider,
    system_prompt=system_prompt,
    toolset=toolset,
    history=history,
    on_message_part=wire_send,  # 实时发送到 UI
)
```

**Stage 4-5 的简化实现**：
```python
# 我们使用 kosong.generate() 等待完整响应
result = await kosong.generate(
    chat_provider=chat_provider,
    system_prompt=system_prompt,
    tools=[],
    history=history,
)

# 一次性返回完整内容
yield result.message.content
```

**原因**：
1. **降低复杂度**：Stage 4-5 专注于打通 LLM 调用链路
2. **Wire 机制复杂**：需要 asyncio.Queue、ContextVar、消息类型定义等
3. **阶段性学习**：先理解配置、Soul、Context 等核心概念
4. **渐进式演进**：Stage 6 再升级为 Wire + 流式输出

### kosong.generate() vs kosong.step()

| 特性 | kosong.generate() | kosong.step() |
|------|-------------------|---------------|
| **用途** | 简��的文本生成 | Agent 工具调用循环 |
| **工具支持** | 只接收 tools 列表 | 接收 Toolset 对象 |
| **流式回调** | 可选 `on_message_part` | 必须 `on_message_part` |
| **返回值** | `GenerateResult` | `StepResult`（包含 tool_results） |
| **适用场景** | Stage 4-5 简单对话 | Stage 7 工具调用 |

## 学习要点

### 1. Soul Protocol 的设计思想

**为什么使用 Protocol 而不是抽象基类（ABC）？**

```python
# 方式 1：抽象基类（传统方式）
from abc import ABC, abstractmethod

class Soul(ABC):
    @abstractmethod
    def run(self, user_input: str):
        pass

# 必须显式继承
class KimiSoul(Soul):  # 必须写 (Soul)
    def run(self, user_input: str):
        ...

# 方式 2：Protocol（现代方式）
from typing import Protocol

class Soul(Protocol):
    def run(self, user_input: str):
        ...

# 无需显式继承，只要实现了接口就行（鸭子类型）
class KimiSoul:  # 不需要写 (Soul)
    def run(self, user_input: str):
        ...
```

**优势**：
- **结构化鸭子类型**：只要实现了接口就符合协议
- **零运行时开销**：Protocol 不会创建真实的类继承关系
- **更灵活**：可以让现有类"事后"符合协议
- **类型检查友好**：mypy 等工具可以验证

### 2. Pydantic 模型验证

**为什么使用 Pydantic？**

```python
# 没有验证：容易出错
config = {
    "api_key": "sk-123",  # 可能是空字符串
    "max_context_size": "8000",  # 错误：字符串而非整数
}

# 使用 Pydantic：自动验证
from pydantic import BaseModel, Field

class LLMModel(BaseModel):
    api_key: str = Field(min_length=1)  # 不能为空
    max_context_size: int = Field(gt=0)  # 必须 > 0

model = LLMModel(
    api_key="",  # ❌ ValidationError: 字符串太短
    max_context_size="8000"  # ✅ 自动转换为整数
)
```

**特性**：
- 自动类型转换
- 数据验证（长度、范围、格式等）
- 生成 JSON Schema
- 序列化/反序列化

### 3. SecretStr 的安全性

```python
from pydantic import SecretStr

# 普通字符串：会泄露到日志
api_key = "sk-hJwUlVMp0MK70TLeahsXhvKWsp1VYHLie4lYcVqmrzBdu9qM"
print(f"API Key: {api_key}")  # ❌ 完整显示

# SecretStr：自动隐藏
api_key = SecretStr("sk-hJwUlVMp0MK70TLeahsXhvKWsp1VYHLie4lYcVqmrzBdu9qM")
print(f"API Key: {api_key}")  # ✅ 显示：**********
print(api_key.get_secret_value())  # 需要显式获取真实值
```

### 4. AsyncIterator 异步生成器

```python
# 同步生成器
def count(n: int):
    for i in range(n):
        yield i

# 异步生成器
async def count_async(n: int):
    for i in range(n):
        await asyncio.sleep(0.1)  # 可以包含异步操作
        yield i

# 使用
async for i in count_async(5):
    print(i)
```

**KimiSoul.run() 的异步生成器**：

```python
async def run(self, user_input: str) -> AsyncIterator[str]:
    # ... LLM 调用（异步操作）
    result = await kosong.generate(...)

    # yield 返回响应片段
    yield result.message.content
```

**为什么返回 AsyncIterator？**
- UI 层可以逐步接收和渲染响应
- 支持流式输出（Stage 6）
- 保持接口统一（即使 Stage 4-5 是一次性返回）

### 5. Context 管理的重要性

**为什么需要 Context？**

```python
# 没有 Context：LLM 无记忆
result1 = await kosong.generate(history=[
    Message(role="user", content="我叫张三")
])
# AI: "你好！"

result2 = await kosong.generate(history=[
    Message(role="user", content="我叫什么？")
])
# AI: "抱歉，我不知道。"  # ❌ 忘记了之前的对话

# 使用 Context：LLM 有记忆
context = Context()
await context.append_message(Message(role="user", content="我叫张三"))
await context.append_message(result1.message)

result2 = await kosong.generate(history=context.get_messages())
# AI: "你叫张三。"  # ✅ 记住了之前的对话
```

**Context 的作用**：
- 存储完整对话历史
- 每次调用 LLM 时传递历史
- 实现多轮对话能力
- Stage 6+：管理 token 使用和压缩

## Stage 6 流式输出升级指南

### 当前 Stage 4-5 的限制

```python
# Stage 4-5：非流式（等待完整响应）
result = await kosong.generate(
    chat_provider=chat_provider,
    system_prompt=system_prompt,
    tools=[],
    history=history,
)

# 一次性返回全部内容
yield result.message.content  # "你好，我是 AI 助手，..."
```

**用户体验问题**：
- 需要等待 LLM 生成完整响应（可能几秒）
- 看不到 AI 的"思考过程"
- 长文本没有逐字显示效果

### Stage 6 的 Wire 机制

**架构变化**：

```python
# Stage 6：使用 on_message_part 回调
result = await kosong.generate(
    chat_provider=chat_provider,
    system_prompt=system_prompt,
    tools=[],
    history=history,
    on_message_part=wire_send,  # ⭐ 实时发送流式片段
)
```

**Wire 消息队列**：

```
Soul 层                         Wire (Queue)                    UI 层
─────────────────────────────────────────────────────────────────────
kosong.generate()
  ├─> TextPart("你")      ──>   Queue.put()   ──>   Queue.get()  ──> 打印 "你"
  ├─> TextPart("好")      ──>   Queue.put()   ──>   Queue.get()  ──> 打印 "好"
  └─> TextPart("！")      ──>   Queue.put()   ──>   Queue.get()  ──> 打印 "！"
```

**需要新增的模块**：

1. **`my_cli/wire.py`**：Wire 消息队列
   ```python
   class Wire:
       def __init__(self):
           self._queue = asyncio.Queue()

       def send(self, msg: WireMessage):
           self._queue.put_nowait(msg)

       async def receive(self) -> WireMessage:
           return await self._queue.get()
   ```

2. **修改 `KimiSoul.run()`**：
   ```python
   async def run(self, user_input: str) -> None:  # 不再返回 AsyncIterator
       # 调用 LLM 并通过 Wire 发送流式片段
       result = await kosong.generate(
           chat_provider=self._runtime.chat_provider,
           system_prompt=self._agent.system_prompt,
           tools=[],
           history=self._context.get_messages(),
           on_message_part=wire_send,  # ⭐ 关键
       )

       await self._context.append_message(result.message)
   ```

3. **UI 层接收流式输出**：
   ```python
   # Shell UI 接收 Wire 消息
   while True:
       msg = await wire.receive()

       if isinstance(msg, StreamedMessagePart):
           if hasattr(msg, "text") and msg.text:
               print(msg.text, end="", flush=True)  # 逐字显示
   ```

**参考文件**（在 fork 仓库中）：
- Wire 定义：`kimi-cli-fork/src/kimi_cli/wire/__init__.py`
- Soul 使用 Wire：`kimi-cli-fork/src/kimi_cli/soul/kimisoul.py:223`
- Shell UI 接收：`kimi-cli-fork/src/kimi_cli/ui/shell/__init__.py`

## 常见问题

### Q1: 为什么不直接用 openai 库？

**openai 库**（OpenAI 官方）：
```python
import openai

response = openai.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello"}]
)
```

**kosong 框架**（Kimi CLI 团队）：
```python
import kosong
from kosong.chat_provider.kimi import Kimi

response = await kosong.generate(
    chat_provider=Kimi(base_url="...", api_key="...", model="..."),
    system_prompt="...",
    tools=[],
    history=[...],
)
```

**kosong 的��势**：
- **统一接口**：支持 Kimi、OpenAI、Claude 等多个 LLM
- **工具调用**：内置 Tool/Toolset 抽象
- **流式处理**：统一的流式响应处理
- **类型安全**：完整的类型注解
- **消息结构**：统一的 Message 模型

### Q2: 为什么 API Key 要用 SecretStr？

**安全问题**：

```python
# 普通字符串：容易泄露
class Config:
    api_key: str = "sk-hJwUlVMp..."

print(Config())  # ❌ Config(api_key='sk-hJwUlVMp...')  # 完整显示
logging.info(f"Config: {Config()}")  # ❌ 泄露到日志

# SecretStr：自动保护
class Config(BaseModel):
    api_key: SecretStr = SecretStr("sk-hJwUlVMp...")

print(Config())  # ✅ Config(api_key=SecretStr('**********'))
logging.info(f"Config: {Config()}")  # ✅ 日志中隐藏
```

### Q3: Context 会无限增长吗？

**Stage 4-5**：会！因为没有实现 Context 压缩。

**Stage 6+**：使用 Context Compaction（压缩）：

```python
# 当 Context 接近 token 限制时
if context.token_count > model.max_context_size - RESERVED_TOKENS:
    # 调用 LLM 总结历史
    summary = await llm.summarize(context.history)

    # 清空历史，只保留总结
    context.clear()
    context.append(Message(role="system", content=f"历史对话总结：{summary}"))
```

### Q4: 为什么使用 kosong.generate() 而不是 kosong.step()？

**Stage 4-5 目标**：
- 打通 LLM 调用链路
- 实现简单对话
- 不涉及工具调用

**kosong.generate()**：
- 简单的文本生成
- 不处理工具调用
- 返回 `GenerateResult`

**kosong.step()**：
- Agent 工具调用循环
- 自动分发工具调用
- 返回 `StepResult`（包含 tool_results）

**Stage 7** 会升级到 `kosong.step()` 来支持工具系统。

### Q5: 多个 API 提供商怎么切换？

**方法 1：修改配置文件的 default_model**

```json
{
  "default_model": "kimi-coding",  // 改这里
  "providers": { ... },
  "models": {
    "moonshot-k2": { ... },
    "kimi-coding": { ... }
  }
}
```

**方法 2：环境变量**

```bash
# 设置环境变量（优先级更高）
export KIMI_API_KEY="sk-new-key"
export KIMI_BASE_URL="https://api.kimi.com/coding/v1"

# 运行
python -m my_cli.cli --ui print -c "test"
```

**方法 3：代码指定**（需要修改 `create_soul()`）

```python
soul = create_soul(
    work_dir=work_dir,
    model_name="kimi-coding",  # 明确指定
)
```

## 下一步

完成阶段 4-5 后，你应该能够：

- [x] 理解 Soul Protocol 协议设计
- [x] 使用 Pydantic 定义配置模型
- [x] 实现配置文件系统和环境变量覆盖
- [x] 使用 kosong 框架调用真实 LLM API
- [x] 理解 Context 管理对话历史
- [x] 知道 Stage 6 如何升级为 Wire 流式输出

**准备好了吗？让我们进入阶段 6：实现 Shell UI 和 Wire 机制！**

## 练习题

### 练习 1：添加新的 LLM 提供商

在 `.mycli_config.json` 中添加 OpenAI 支持：

```json
{
  "providers": {
    "openai": {
      "type": "openai",
      "base_url": "https://api.openai.com/v1",
      "api_key": "你的-OpenAI-Key"
    }
  },
  "models": {
    "gpt-4": {
      "provider": "openai",
      "model": "gpt-4",
      "max_context_size": 8192
    }
  }
}
```

修改 `config.py` 的 `augment_provider_with_env()` 支持 `OPENAI_API_KEY`。

### 练习 2：自定义 system_prompt

修改 `Agent._build_default_system_prompt()`：

```python
def _build_default_system_prompt(self) -> str:
    return f"""你是 {self.name}，一个专业的 Python 编程助手。

你的能力：
- 编写高质量的 Python 代码
- 解释复杂的技术概念
- 帮助调试程序错误

请用简洁、专业的语言回答问题。"""
```

测试效果变化。

### 练习 3：添加消息统计

在 `Context` 类中添加统计功能：

```python
class Context:
    def __init__(self):
        self._messages: list[Message] = []
        self._user_count = 0
        self._assistant_count = 0

    async def append_message(self, message: Message | list[Message]) -> None:
        messages = [message] if isinstance(message, Message) else message
        for msg in messages:
            self._messages.append(msg)
            if msg.role == "user":
                self._user_count += 1
            elif msg.role == "assistant":
                self._assistant_count += 1

    def get_statistics(self) -> dict:
        return {
            "total": len(self._messages),
            "user": self._user_count,
            "assistant": self._assistant_count,
        }
```

在 UI 层显示统计信息。

---

**完成这些练习后，你就完全掌握阶段 4-5 的内容了！🎉**

现在你已经掌握了：
- ✅ Soul 引擎核心架构
- ✅ kosong 框架集成
- ✅ 配置文件系统
- ✅ 真实 LLM API 调用

**下一步**：Stage 6 将实现 Shell UI 和 Wire 流式输出机制！

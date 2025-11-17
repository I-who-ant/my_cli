# Soul 层架构：从 Java/Spring Boot 视角理解 Python 设计模式

## 目录

1. [核心概念对照表](#核心概念对照表)
2. [Protocol vs Interface](#protocol-vs-interface)
3. [依赖注入：Spring IoC vs Python](#依赖注入spring-ioc-vs-python)
4. [工厂模式对比](#工厂模式对比)
5. [@property vs Getter/Setter](#property-vs-gettersetter)
6. [完整示例对比](#完整示例对比)
7. [架构层次对比](#架构层次对比)

---

## 核心概念对照表

| Python 概念 | Java/Spring Boot 对应 | 说明 |
|------------|----------------------|------|
| `Protocol` | `Interface` | 定义接口/契约 |
| `@property` | `getter` 方法 | 属性访问器 |
| `create_soul()` 工厂函数 | `@Bean` 工厂方法 | 对象创建 |
| 构造函数注入 | `@Autowired` 构造函数 | 依赖注入 |
| `__init__.py` | Spring 配置类 (`@Configuration`) | 模块配置 |
| `typing.Protocol` | `interface` 关键字 | 接口定义 |
| `@runtime_checkable` | 运行时类型检查 | 类型验证 |
| 鸭子类型 | 静态类型（需显式实现） | 类型系统 |
| Pydantic | Spring Validation | 数据验证 |
| `async`/`await` | `CompletableFuture` | 异步编程 |

---

## Protocol vs Interface

### Java Interface（强制契约）

**Java 代码**：

```java
// 1. 定义接口（强制契约）
public interface Soul {
    String getName();
    String getModelName();
    CompletableFuture<String> run(String userInput);
}

// 2. 实现接口（必须显式声明）
public class KimiSoul implements Soul {  // ← 必须写 implements Soul
    private Agent agent;
    private Runtime runtime;

    @Override  // ← 必须标注 @Override
    public String getName() {
        return agent.getName();
    }

    @Override
    public String getModelName() {
        return runtime.getChatProvider().getModelName();
    }

    @Override
    public CompletableFuture<String> run(String userInput) {
        // ...
    }
}
```

**特点**：
- ✅ **编译时检查**：必须实现所有方法，否则编译报错
- ✅ **显式声明**：必须写 `implements Soul`
- ✅ **IDE 支持强**：自动生成方法、提示缺失实现
- ❌ **耦合度高**：修改接口影响所有实现类

### Python Protocol（结构化鸭子类型）

**Python 代码**：

```python
# 1. 定义 Protocol（结构契约）
from typing import Protocol, runtime_checkable

@runtime_checkable  # ← 可选：允许运行时检查
class Soul(Protocol):
    @property
    def name(self) -> str: ...

    @property
    def model_name(self) -> str: ...

    async def run(self, user_input: str): ...

# 2. 实现 Protocol（无需显式声明）
class KimiSoul:  # ← 不需要写 (Soul)
    def __init__(self, agent: Agent, runtime: Runtime):
        self._agent = agent
        self._runtime = runtime

    @property
    def name(self) -> str:
        return self._agent.name

    @property
    def model_name(self) -> str:
        return self._runtime.chat_provider.model_name

    async def run(self, user_input: str):
        # ...
```

**特点**：
- ✅ **灵活性高**：只要方法签名匹配就符合 Protocol
- ✅ **解耦合强**：不需要显式继承/实现
- ✅ **静态检查**：mypy 可以验证是否符合 Protocol
- ❌ **IDE 支持弱**：不会自动提示缺失方法（需要 mypy）

### 对比总结

```
┌────────────────────────────────────────────────────────────┐
│              Java Interface（强制契约）                     │
├────────────────────────────────────────────────────────────┤
│  interface Soul { ... }                                    │
│       ↓                                                    │
│  class KimiSoul implements Soul { ... }  ← 必须显式声明    │
│       ↓                                                    │
│  编译器强制检查所有方法是否实现                              │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│           Python Protocol（结构化鸭子类型）                 │
├────────────────────────────────────────────────────────────┤
│  class Soul(Protocol): ...                                 │
│       ↓                                                    │
│  class KimiSoul: ...  ← 不需要显式声明                     │
│       ↓                                                    │
│  只要方法签名匹配，就自动符合 Protocol                      │
│  （mypy 静态检查 + 运行时检查）                             │
└────────────────────────────────────────────────────────────┘
```

**哲学差异**：
- **Java**：如果它**说**自己是鸭子（`implements Duck`），它就是鸭子
- **Python**：如果它**走路像鸭子、叫声像鸭子**（方法签名匹配），它就是鸭子

---

## 依赖注入：Spring IoC vs Python

### Spring Boot 依赖注入

**Java 代码**：

```java
// 1. 定义组件
@Component
public class Agent {
    private String name;
    private Path workDir;

    public Agent(String name, Path workDir) {
        this.name = name;
        this.workDir = workDir;
    }

    public String getName() {
        return name;
    }
}

@Component
public class Runtime {
    private ChatProvider chatProvider;

    @Autowired  // ← Spring 自动注入
    public Runtime(ChatProvider chatProvider) {
        this.chatProvider = chatProvider;
    }
}

// 2. 实现类（依赖注入）
@Service
public class KimiSoul implements Soul {
    private final Agent agent;
    private final Runtime runtime;
    private final Context context;

    @Autowired  // ← Spring 自动注入所有依赖
    public KimiSoul(Agent agent, Runtime runtime) {
        this.agent = agent;
        this.runtime = runtime;
        this.context = new Context();  // 自己创建
    }

    @Override
    public String getName() {
        return agent.getName();
    }
}

// 3. 配置类（工厂）
@Configuration
public class SoulConfig {

    @Bean
    public Agent agent() {
        return new Agent("MyCLI Assistant", Paths.get("."));
    }

    @Bean
    public ChatProvider chatProvider() {
        return new KimiChatProvider("https://api.moonshot.cn/v1", "sk-...");
    }

    @Bean
    public Runtime runtime(ChatProvider chatProvider) {  // ← 自动注入
        return new Runtime(chatProvider);
    }

    @Bean
    public Soul soul(Agent agent, Runtime runtime) {  // ← 自动注入
        return new KimiSoul(agent, runtime);
    }
}

// 4. 使用
@RestController
public class ChatController {

    @Autowired  // ← Spring 自动注入
    private Soul soul;

    @PostMapping("/chat")
    public String chat(@RequestBody String message) {
        return soul.run(message).join();
    }
}
```

**Spring IoC 特点**：
- ✅ **自动装配**：Spring 容器自动管理对象生命周期
- ✅ **声明式**：使用 `@Autowired`、`@Bean` 注解
- ✅ **单例管理**：默认单例模式
- ✅ **循环依赖处理**：Spring 可以处理循环依赖

### Python 手动依赖注入

**Python 代码**：

```python
# 1. 定义组件（普通类，无注解）
class Agent:
    def __init__(self, name: str, work_dir: Path):
        self.name = name
        self.work_dir = work_dir

class Runtime:
    def __init__(self, chat_provider: ChatProvider):
        self.chat_provider = chat_provider

# 2. 实现类（手动注入）
class KimiSoul:
    def __init__(self, agent: Agent, runtime: Runtime):
        self._agent = agent      # ← 手动接收依赖
        self._runtime = runtime  # ← 手动接收依赖
        self._context = Context()  # 自己创建

    @property
    def name(self) -> str:
        return self._agent.name

# 3. 工厂函数（手动组装，类似 @Configuration）
def create_soul(
    work_dir: Path,
    agent_name: str = "MyCLI Assistant",
) -> KimiSoul:
    """类似 Spring 的 @Bean 工厂方法"""

    # 手动创建所有依赖
    agent = Agent(name=agent_name, work_dir=work_dir)

    chat_provider = Kimi(
        base_url="https://api.moonshot.cn/v1",
        api_key="sk-...",
        model="kimi-k2-turbo-preview",
    )

    runtime = Runtime(chat_provider=chat_provider)

    # 手动组装
    soul = KimiSoul(agent=agent, runtime=runtime)

    return soul

# 4. 使用（手动调用工厂）
class PrintUI:
    def __init__(self, work_dir: Path):
        self.work_dir = work_dir

    async def run(self, command: str):
        # 手动调用工厂函数
        soul = create_soul(work_dir=self.work_dir)

        async for chunk in soul.run(command):
            print(chunk)
```

**Python DI 特点**：
- ✅ **显式控制**：手动创建和组装，逻辑清晰
- ✅ **轻量级**：无需引入 DI 框架
- ✅ **灵活性高**：可以精确控制对象生命周期
- ❌ **手动管理**：需要手动处理依赖顺序
- ❌ **无单例管理**：需要自己实现单例

### Python DI 框架（可选）

如果你想要类似 Spring 的体验，可以使用 Python DI 框架：

**使用 `dependency-injector` 库**：

```python
from dependency_injector import containers, providers

# 类似 Spring @Configuration
class Container(containers.DeclarativeContainer):

    # 类似 @Bean
    agent = providers.Singleton(
        Agent,
        name="MyCLI Assistant",
        work_dir=providers.Object(Path(".")),
    )

    chat_provider = providers.Singleton(
        Kimi,
        base_url="https://api.moonshot.cn/v1",
        api_key="sk-...",
        model="kimi-k2-turbo-preview",
    )

    runtime = providers.Singleton(
        Runtime,
        chat_provider=chat_provider,  # ← 自动注入
    )

    soul = providers.Factory(
        KimiSoul,
        agent=agent,      # ← 自动注入
        runtime=runtime,  # ← 自动注入
    )

# 使用
container = Container()
soul = container.soul()  # 自动注入所有依赖
```

**但是**：Kimi CLI 官方**没有使用** DI 框架，而是手动管理（更符合 Python 风格）。

---

## 工厂模式对比

### Spring Boot @Bean 工厂方法

**Java 代码**：

```java
@Configuration
public class SoulConfig {

    // 工厂方法 1：创建 Agent
    @Bean
    public Agent agent() {
        return new Agent("MyCLI Assistant", Paths.get("."));
    }

    // 工厂方法 2：创建 ChatProvider
    @Bean
    public ChatProvider chatProvider(@Value("${kimi.api.key}") String apiKey) {
        return new KimiChatProvider(
            "https://api.moonshot.cn/v1",
            apiKey,
            "kimi-k2-turbo-preview"
        );
    }

    // 工厂方法 3：创建 Runtime（自动注入 chatProvider）
    @Bean
    public Runtime runtime(ChatProvider chatProvider) {
        return new Runtime(chatProvider);
    }

    // 工厂方法 4：创建 Soul（自动注入 agent 和 runtime）
    @Bean
    public Soul soul(Agent agent, Runtime runtime) {
        return new KimiSoul(agent, runtime);
    }
}

// 使用（Spring 自动注入）
@Service
public class ChatService {
    @Autowired
    private Soul soul;  // ← Spring 自动调用工厂方法创建
}
```

**特点**：
- ✅ Spring 容器自动管理对象生命周期
- ✅ 默认单例（同一个对象被复用）
- ✅ 自动解析依赖关系
- ✅ 支持配置属性（`@Value`）

### Python 工厂函数

**Python 代码**：

```python
def create_soul(
    work_dir: Path,
    agent_name: str = "MyCLI Assistant",
    model_name: str | None = None,
    config_file: Path | None = None,
) -> KimiSoul:
    """
    工厂函数：创建 KimiSoul 实例

    类似 Spring 的：
    @Bean
    public Soul soul(...) { ... }
    """

    # 步骤 1：加载配置（类似 @Value）
    config = load_config(config_file)
    provider, model = get_provider_and_model(config, model_name)

    # 步骤 2：创建 Agent
    agent = Agent(name=agent_name, work_dir=work_dir)

    # 步骤 3：创建 ChatProvider
    chat_provider = Kimi(
        base_url=provider.base_url,
        api_key=provider.api_key.get_secret_value(),
        model=model.model,
    )

    # 步骤 4：创建 Runtime
    runtime = Runtime(chat_provider=chat_provider, max_steps=20)

    # 步骤 5：创建 KimiSoul（手动注入依赖）
    soul = KimiSoul(agent=agent, runtime=runtime)

    return soul

# 使用（手动调用）
class PrintUI:
    async def run(self, command: str):
        soul = create_soul(work_dir=self.work_dir)  # ← 手动调用工厂
        async for chunk in soul.run(command):
            print(chunk)
```

**特点**：
- ✅ 手动控制对象创建
- ✅ 每次调用创建新对象（非单例）
- ✅ 参数灵活（可选参数、默认值）
- ❌ 需要手动管理依赖顺序

### 对比总结

| 维度 | Spring @Bean | Python 工厂函数 |
|------|-------------|----------------|
| **创建方式** | 声明式（注解） | 命令式（函数调用） |
| **依赖注入** | 自动 | 手动 |
| **生命周期** | 容器管理 | 手动管理 |
| **默认行为** | 单例 | 每次创建新对象 |
| **配置** | `@Value`、`application.yml` | 函数参数、配置文件 |
| **复杂度** | 高（需要理解 Spring 容器） | 低（普通函数） |

---

## @property vs Getter/Setter

### Java Getter/Setter（冗长但明确）

**Java 代码**：

```java
public class KimiSoul implements Soul {
    private Agent agent;
    private Runtime runtime;

    public KimiSoul(Agent agent, Runtime runtime) {
        this.agent = agent;
        this.runtime = runtime;
    }

    // Getter 方法（必须显式定义）
    @Override
    public String getName() {
        return agent.getName();
    }

    @Override
    public String getModelName() {
        return runtime.getChatProvider().getModelName();
    }

    public int getMessageCount() {
        return context.getMessages().size();
    }
}

// 使用
Soul soul = new KimiSoul(...);
System.out.println(soul.getName());         // ← 必须加括号 ()
System.out.println(soul.getModelName());    // ← 必须加括号 ()
System.out.println(soul.getMessageCount()); // ← 必须加括号 ()
```

**特点**：
- ✅ **明确性**：一眼看出这是方法调用
- ✅ **IDE 支持**：自动生成 getter/setter
- ❌ **冗长**：每个属性都要写 getter/setter
- ❌ **调用语法**：必须加括号 `()`

### Python @property（简洁优雅）

**Python 代码**：

```python
class KimiSoul:
    def __init__(self, agent: Agent, runtime: Runtime):
        self._agent = agent
        self._runtime = runtime
        self._context = Context()

    @property
    def name(self) -> str:
        """实现 Soul Protocol: name 属性"""
        return self._agent.name

    @property
    def model_name(self) -> str:
        """实现 Soul Protocol: model_name 属性"""
        return self._runtime.chat_provider.model_name

    @property
    def message_count(self) -> int:
        """获取消息数量"""
        return len(self._context)

# 使用
soul = KimiSoul(...)
print(soul.name)          # ← 像访问属性一样，不需要括号！
print(soul.model_name)    # ← 像访问属性一样
print(soul.message_count) # ← 像访问属性一样
```

**特点**：
- ✅ **简洁**：像访问属性一样，不需要括号
- ✅ **统一接口**：真正的属性和计算属性语法一致
- ✅ **延迟计算**：只在访问时计算，不是创建时
- ❌ **不明确**：看不出是直接访问还是方法调用

### Java 使用 Lombok 简化

**Java 代码（使用 Lombok）**：

```java
import lombok.Getter;

@Getter  // ← Lombok 自动生成所有 getter
public class KimiSoul implements Soul {
    private Agent agent;
    private Runtime runtime;

    public KimiSoul(Agent agent, Runtime runtime) {
        this.agent = agent;
        this.runtime = runtime;
    }

    // Lombok 自动生成：
    // public Agent getAgent() { return agent; }
    // public Runtime getRuntime() { return runtime; }
}

// 使用（仍需括号）
soul.getAgent();   // ← 仍然需要括号
soul.getRuntime(); // ← 仍然需要括号
```

**即使使用 Lombok**：
- ✅ 减少代码量
- ❌ 仍然需要括号调用

### 对比表

| 维度 | Java Getter | Python @property |
|------|------------|-----------------|
| **定义方式** | `public String getName()` | `@property def name()` |
| **调用方式** | `soul.getName()` | `soul.name` |
| **代码量** | 多（需要每个属性写方法） | 少（一个装饰器） |
| **语法** | 方法调用（显式） | 属性访问（隐式） |
| **一致性** | getter/setter 分离 | 统一为属性 |

---

## 完整示例对比

### Spring Boot 完整实现

**Java 代码**：

```java
// ============================================================
// 1. 定义接口
// ============================================================
public interface Soul {
    String getName();
    String getModelName();
    CompletableFuture<Void> run(String userInput);
}

// ============================================================
// 2. 定义组件
// ============================================================
@Component
public class Agent {
    private String name;
    private Path workDir;

    public Agent(@Value("${agent.name}") String name, Path workDir) {
        this.name = name;
        this.workDir = workDir;
    }

    public String getName() {
        return name;
    }
}

@Component
public class Runtime {
    private ChatProvider chatProvider;

    @Autowired
    public Runtime(ChatProvider chatProvider) {
        this.chatProvider = chatProvider;
    }

    public ChatProvider getChatProvider() {
        return chatProvider;
    }
}

@Component
public class Context {
    private List<Message> messages = new ArrayList<>();

    public void appendMessage(Message message) {
        messages.add(message);
    }

    public List<Message> getMessages() {
        return Collections.unmodifiableList(messages);
    }
}

// ============================================================
// 3. 实现 Soul
// ============================================================
@Service
public class KimiSoul implements Soul {
    private final Agent agent;
    private final Runtime runtime;
    private final Context context;

    @Autowired
    public KimiSoul(Agent agent, Runtime runtime, Context context) {
        this.agent = agent;
        this.runtime = runtime;
        this.context = context;
    }

    @Override
    public String getName() {
        return agent.getName();
    }

    @Override
    public String getModelName() {
        return runtime.getChatProvider().getModelName();
    }

    @Override
    public CompletableFuture<Void> run(String userInput) {
        // 1. 添加用户消息
        context.appendMessage(new Message("user", userInput));

        // 2. 调用 LLM（异步）
        return kosongGenerate(
            runtime.getChatProvider(),
            agent.getSystemPrompt(),
            context.getMessages()
        ).thenAccept(result -> {
            // 3. 保存响应
            context.appendMessage(result.getMessage());
        });
    }
}

// ============================================================
// 4. 配置类（工厂）
// ============================================================
@Configuration
public class SoulConfig {

    @Bean
    public ChatProvider chatProvider(
        @Value("${kimi.base.url}") String baseUrl,
        @Value("${kimi.api.key}") String apiKey,
        @Value("${kimi.model}") String model
    ) {
        return new KimiChatProvider(baseUrl, apiKey, model);
    }

    @Bean
    public Agent agent(@Value("${agent.name}") String name) {
        return new Agent(name, Paths.get("."));
    }
}

// ============================================================
// 5. 使用（Controller）
// ============================================================
@RestController
@RequestMapping("/api")
public class ChatController {

    @Autowired
    private Soul soul;

    @PostMapping("/chat")
    public CompletableFuture<String> chat(@RequestBody String message) {
        return soul.run(message).thenApply(v -> "Success");
    }
}

// ============================================================
// 6. 配置文件（application.yml）
// ============================================================
/*
agent:
  name: MyCLI Assistant

kimi:
  base-url: https://api.moonshot.cn/v1
  api-key: ${KIMI_API_KEY}
  model: kimi-k2-turbo-preview
*/
```

### Python 完整实现

**Python 代码**：

```python
# ============================================================
# 1. 定义 Protocol
# ============================================================
from typing import Protocol, AsyncIterator

class Soul(Protocol):
    @property
    def name(self) -> str: ...

    @property
    def model_name(self) -> str: ...

    async def run(self, user_input: str) -> AsyncIterator[str]: ...

# ============================================================
# 2. 定义组件
# ============================================================
from pathlib import Path

class Agent:
    def __init__(self, name: str, work_dir: Path):
        self.name = name
        self.work_dir = work_dir
        self._system_prompt = f"你是 {name}，一个 AI 助手。"

    @property
    def system_prompt(self) -> str:
        return self._system_prompt

class Runtime:
    def __init__(self, chat_provider: ChatProvider, max_steps: int = 20):
        self.chat_provider = chat_provider
        self.max_steps = max_steps

class Context:
    def __init__(self):
        self._messages: list[Message] = []

    async def append_message(self, message: Message | list[Message]):
        if isinstance(message, list):
            self._messages.extend(message)
        else:
            self._messages.append(message)

    def get_messages(self) -> list[Message]:
        return self._messages.copy()

    def __len__(self) -> int:
        return len(self._messages)

# ============================================================
# 3. 实现 Soul
# ============================================================
import kosong
from kosong.message import Message

class KimiSoul:
    def __init__(self, agent: Agent, runtime: Runtime):
        self._agent = agent
        self._runtime = runtime
        self._context = Context()

    @property
    def name(self) -> str:
        return self._agent.name

    @property
    def model_name(self) -> str:
        return self._runtime.chat_provider.model_name

    async def run(self, user_input: str) -> AsyncIterator[str]:
        # 1. 添加用户消息
        user_msg = Message(role="user", content=user_input)
        await self._context.append_message(user_msg)

        # 2. 调用 LLM
        result = await kosong.generate(
            chat_provider=self._runtime.chat_provider,
            system_prompt=self._agent.system_prompt,
            tools=[],
            history=self._context.get_messages(),
        )

        # 3. 返回响应
        full_content = result.message.content
        if full_content:
            yield full_content

        # 4. 保存响应
        await self._context.append_message(result.message)

# ============================================================
# 4. 工厂函数（替代 @Configuration）
# ============================================================
from kosong.chat_provider.kimi import Kimi

def create_soul(
    work_dir: Path,
    agent_name: str = "MyCLI Assistant",
    config_file: Path | None = None,
) -> KimiSoul:
    """工厂函数：创建 KimiSoul 实例"""

    # 加载配置
    config = load_config(config_file)
    provider, model = get_provider_and_model(config, None)

    # 创建组件
    agent = Agent(name=agent_name, work_dir=work_dir)

    chat_provider = Kimi(
        base_url=provider.base_url,
        api_key=provider.api_key.get_secret_value(),
        model=model.model,
    )

    runtime = Runtime(chat_provider=chat_provider, max_steps=20)

    # 组装
    soul = KimiSoul(agent=agent, runtime=runtime)

    return soul

# ============================================================
# 5. 使用（UI 层）
# ============================================================
class PrintUI:
    def __init__(self, work_dir: Path):
        self.work_dir = work_dir

    async def run(self, command: str):
        # 手动调用工厂函数
        soul = create_soul(work_dir=self.work_dir)

        # 调用 Soul
        async for chunk in soul.run(command):
            print(chunk, end="", flush=True)

# ============================================================
# 6. 配置文件（.mycli_config.json）
# ============================================================
"""
{
  "default_model": "moonshot-k2",
  "providers": {
    "moonshot": {
      "type": "kimi",
      "base_url": "https://api.moonshot.cn/v1",
      "api_key": "sk-..."
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
"""
```

---

## 架构层次对比

### Spring Boot 三层架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Controller 层                             │
│  @RestController                                             │
│  - 处理 HTTP 请求                                            │
│  - 调用 Service 层                                           │
│  - 返回 JSON 响应                                            │
└──────────────────────┬──────────────────────────────────────┘
                       │ @Autowired
                       ↓
┌─────────────────────────────────────────────────────────────┐
│                    Service 层                                │
│  @Service                                                    │
│  - 业务逻辑                                                  │
│  - 调用 Repository                                           │
│  - 事务管理                                                  │
└──────────────────────┬──────────────────────────────────────┘
                       │ @Autowired
                       ↓
┌─────────────────────────────────────────────────────────────┐
│                    Repository 层                             │
│  @Repository / JPA                                           │
│  - 数据访问                                                  │
│  - CRUD 操作                                                 │
└─────────────────────────────────────────────────────────────┘
```

**Spring Boot 示例**：

```java
@RestController
public class ChatController {  // ← Controller 层
    @Autowired
    private ChatService chatService;

    @PostMapping("/chat")
    public String chat(@RequestBody String message) {
        return chatService.process(message);
    }
}

@Service
public class ChatService {  // ← Service 层
    @Autowired
    private Soul soul;

    public String process(String message) {
        return soul.run(message).join();
    }
}

@Service
public class KimiSoul implements Soul {  // ← Domain 层
    @Autowired
    private Agent agent;

    @Autowired
    private Runtime runtime;

    // ...
}
```

### Python Kimi CLI 三层架构

```
┌─────────────────────────────────────────────────────────────┐
│                    CLI/UI 层                                 │
│  cli.py / ui_print.py / ui_shell.py                         │
│  - 处理用户输入/输出                                         │
│  - 调用 App 层                                               │
│  - 渲染结果                                                  │
└──────────────────────┬──────────────────────────────────────┘
                       │ 直接调用
                       ↓
┌─────────────────────────────────────────────────────────────┐
│                    App 层                                    │
│  app.py (MyCLI 类)                                           │
│  - 应用配置管理                                              │
│  - 路由到不同 UI 模式                                        │
│  - 调用 Soul 层                                              │
└──────────────────────┬──────────────────────────────────────┘
                       │ create_soul()
                       ↓
┌─────────────────────────────────────────────────────────────┐
│                    Soul 层                                   │
│  soul/__init__.py (Protocol + 工厂)                         │
│  - Agent/Runtime/Context 组件                                │
│  - LLM 调用逻辑                                              │
│  - kosong 框架集成                                           │
└─────────────────────────────────────────────────────────────┘
```

**Python 示例**：

```python
# CLI 层
async def async_main(command: str, ui: str, work_dir: Path):
    app = await MyCLI.create(work_dir=work_dir)

    if ui == "print":
        await app.run_print_mode(command)
    elif ui == "shell":
        await app.run_shell_mode(command)

# App 层
class MyCLI:
    async def run_print_mode(self, command: str):
        ui = PrintUI(work_dir=self.work_dir)
        await ui.run(command)

# UI 层
class PrintUI:
    async def run(self, command: str):
        soul = create_soul(work_dir=self.work_dir)  # ← 调用工厂
        async for chunk in soul.run(command):
            print(chunk)

# Soul 层
def create_soul(...) -> KimiSoul:
    # 创建和组装所有组件
    ...
```

---

## 总结：核心差异

### 1. 类型系统

| Java | Python |
|------|--------|
| 静态类型（编译时检查） | 动态类型（运行时检查） |
| 必须显式声明类型 | 类型注解可选（但推荐） |
| `implements` 显式实现接口 | Protocol 隐式匹配 |

### 2. 依赖管理

| Java/Spring | Python |
|------------|--------|
| Spring IoC 容器自动管理 | 手动管理（或使用轻量 DI 库） |
| `@Autowired` 自动注入 | 构造函数手动注入 |
| 默认单例 | 每次调用创建新对象 |

### 3. 配置方式

| Java/Spring | Python |
|------------|--------|
| `@Configuration` + `@Bean` | 工厂函数 |
| `application.yml` | `.mycli_config.json` + Pydantic |
| `@Value` 注入配置 | 函数参数传递 |

### 4. 属性访问

| Java | Python |
|------|--------|
| `soul.getName()` | `soul.name` |
| getter/setter 方法 | `@property` 装饰器 |
| 明确是方法调用 | 看起来像属性访问 |

### 5. 异步编程

| Java | Python |
|------|--------|
| `CompletableFuture` | `async`/`await` |
| 回调式 | 协程式 |
| `.thenApply()` 链式调用 | `await` 顺序执行 |

---

## 从 Spring 到 Python 的心智转换

如果你熟悉 Spring Boot，理解 Python Kimi CLI 架构的关键是：

1. **Protocol = Interface**：定义契约，但不强制 `implements`
2. **工厂函数 = @Bean 方法**：手动创建对象，不依赖容器
3. **@property = getter**：更简洁的属性访问语法
4. **手动 DI = @Autowired**：显式传递依赖，不依赖注解
5. **async/await = CompletableFuture**：更直观的异步语法

**Spring 哲学**：框架帮你做一切（声明式）
**Python 哲学**：你自己控制一切（命令式）

**哪个更好？**

- **Spring**：适合大型企业项目，需要严格的规范和统一的架构
- **Python**：适合灵活的脚本工具，强调简洁和显式控制

Kimi CLI 选择 Python 的手动 DI 方式，是因为：
- ✅ 更轻量级（无需庞大的框架）
- ✅ 更灵活（可以精确控制对象生命周期）
- ✅ 更符合 Python 风格（显式优于隐式）
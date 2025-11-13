# Python命名约定与模块设计最佳实践

> 作者：老王
> 日期：2025-11-13
> 适用场景：Python项目模块设计、接口定义、依赖注入

---

## 目录

1. [Python下划线命名约定](#1-python下划线命名约定)
2. [`__all__` 导出列表详解](#2-__all__-导出列表详解)
3. [模块设计模式：接口与实现分离](#3-模块设计模式接口与实现分离)
4. [依赖注入与初始化模式](#4-依赖注入与初始化模式)
5. [Kimi CLI 实战案例分析](#5-kimi-cli-实战案例分析)

---

## 1. Python下划线命名约定

### 1.1 命名规则速查表

| 命名方式 | 可见性 | 使用场景 | 示例 |
|---------|-------|---------|------|
| `public_name` | 公开 | 对外暴露的API | `Soul`, `create_soul()` |
| `_private_name` | 约定私有 | 内部实现，不希望外部使用 | `_internal_helper()` |
| `__name_mangling` | 名称改写 | 防止子类覆盖（少用） | `__private_method()` |
| `__special__` | 魔法方法 | Python内置协议 | `__init__`, `__str__` |

### 1.2 单下划线前缀 `_variable` （约定私有）

```python
# ============================================================
# 模块级别：内部函数/变量
# ============================================================
_CONFIG = {}  # 约定为模块内部配置
_logger = logging.getLogger(__name__)  # 内部日志对象

def _internal_helper():
    """这是内部辅助函数，不希望被外部直接调用"""
    pass

# ============================================================
# 类级别：内部方法/属性
# ============================================================
class MyClass:
    def __init__(self):
        self._internal_state = {}  # 约定为内部属性

    def _internal_method(self):
        """内部方法，不是公开API的一部分"""
        pass

    def public_method(self):
        """公开方法，可以被外部调用"""
        self._internal_method()  # 内部可以调用私有方法
```

**特点：**
- ✅ **约定私有** - 只是君子协定，技术上仍可访问
- ✅ **`from module import *` 不会导入** - 这是唯一的强制效果
- ❌ **不是真正的私有** - 仍可通过 `obj._method()` 访问
- ✅ **IDE提示** - 好的IDE会给出警告

**使用场景：**
- 内部辅助函数/方法
- 模块内部的配置和状态
- 实现细节，不希望被外部依赖

### 1.3 双下划线前缀 `__variable` （名称改写）

```python
class Parent:
    def __private_method(self):
        print("Parent's private method")

class Child(Parent):
    def __private_method(self):
        print("Child's private method")

# Python会自动改写名称：
# Parent.__private_method  → Parent._Parent__private_method
# Child.__private_method   → Child._Child__private_method

# 测试
c = Child()
c._Parent__private_method()  # 输出: Parent's private method
c._Child__private_method()   # 输出: Child's private method
```

**特点：**
- ✅ **名称改写（Name Mangling）** - 解释器自动重命名为 `_ClassName__name`
- ✅ **防止子类意外覆盖** - 主要用于避免继承中的命名冲突
- ❌ **也不是真正私有** - 仍可通过改写后的名字访问
- ⚠️ **少用** - 除非真的需要名称隔离

**使用场景：**
- 复杂继承体系中，防止子类意外覆盖父类方法
- 需要严格名称隔离的场景
- **老王建议：99%的情况下，用单下划线就够了！**

### 1.4 魔法方法 `__special__` （双下划线前后）

```python
class Point:
    def __init__(self, x, y):
        """初始化方法"""
        self.x = x
        self.y = y

    def __str__(self):
        """字符串表示"""
        return f"Point({self.x}, {self.y})"

    def __add__(self, other):
        """加法运算符重载"""
        return Point(self.x + other.x, self.y + other.y)
```

**特点：**
- ✅ **Python内置协议** - 实现特定行为
- ✅ **不会被名称改写** - 前后都有双下划线
- ✅ **常见魔法方法**：`__init__`, `__str__`, `__repr__`, `__call__`, `__enter__`, `__exit__`

---

## 2. `__all__` 导出列表详解

### 2.1 什么是 `__all__`？

`__all__` 是一个模块级别的列表，用于明确声明模块的公开接口。

```python
# my_module.py

__all__ = [
    "PublicClass",
    "public_function",
]

class PublicClass:
    pass

class _InternalClass:
    pass

def public_function():
    pass

def _internal_function():
    pass
```

### 2.2 `__all__` 的效果

```python
# 方式1：使用 from ... import *
from my_module import *

# 只导入 __all__ 中声明的
PublicClass()      # ✅ 可用
public_function()  # ✅ 可用
_InternalClass()   # ❌ NameError
_internal_function()  # ❌ NameError

# 方式2：明确导入（绕过 __all__）
from my_module import _InternalClass  # ✅ 仍然可以导入

# 方式3：导入模块
import my_module
my_module._InternalClass()  # ✅ 可用（但不推荐）
```

### 2.3 官方 kimi-cli 的做法 vs 学习项目的做法

#### 官方 kimi-cli：不使用 `__all__`

```python
# kimi-cli-fork/src/kimi_cli/soul/__init__.py

# 没有 __all__，依赖命名约定

# 公开接口（没有下划线）
class Soul(Protocol):
    pass

def create_soul():
    pass

# 私有实现（单下划线开头）
def _internal_helper():
    pass
```

**优点：**
- 简洁，不需要维护导出列表
- 依赖Python命名约定

**缺点：**
- 不够明确，需要阅读代码才知道哪些是公开接口
- IDE自动补全可能包含内部实现

#### 学习项目：使用 `__all__`（推荐）

```python
# my_cli/soul/__init__.py

__all__ = [
    "Soul",          # ✅ 公开接口
    "create_soul",   # ✅ 公开函数
]

class Soul(Protocol):
    pass

def create_soul():
    pass

# 内部实现
class KimiSoul:  # 不在 __all__ 中
    pass

def _internal_helper():  # 单下划线 + 不在 __all__
    pass
```

**优点：**
- ✅ **明确导出接口** - 一看就知道哪些是公开的
- ✅ **IDE友好** - VSCode/PyCharm会优先提示 `__all__` 中的符号
- ✅ **防止意外导入** - `from module import *` 更安全
- ✅ **文档作用** - `__all__` 本身就是接口文档

**老王推荐：在学习和项目开发中，优先使用 `__all__`！**

### 2.4 `__all__` 最佳实践

```python
# my_cli/soul/__init__.py

from pathlib import Path
from typing import Protocol, runtime_checkable

# 导入内部实现（不会被 * 导出）
from my_cli.soul.agent import Agent
from my_cli.soul.runtime import Runtime
from my_cli.soul.kimisoul import KimiSoul

# ============================================================
# 公开接口声明（放在文件顶部）
# ============================================================
__all__ = [
    # 核心接口
    "Soul",

    # 工厂函数
    "create_soul",

    # 异常类（Stage 6+）
    # "LLMNotSet",
    # "MaxStepsReached",
]

# ============================================================
# 接口定义
# ============================================================
@runtime_checkable
class Soul(Protocol):
    """Soul Protocol - AI Agent 核心引擎的接口定义"""

    @property
    def name(self) -> str:
        ...

    @property
    def model_name(self) -> str:
        ...

    async def run(self, user_input: str):
        ...

# ============================================================
# 公开工厂函数
# ============================================================
def create_soul(work_dir: Path, agent_name: str = "MyCLI Assistant") -> KimiSoul:
    """便捷工厂函数 - 创建 Soul 实例"""
    agent = Agent(name=agent_name, work_dir=work_dir)
    runtime = Runtime(...)
    return KimiSoul(agent=agent, runtime=runtime)
```

---

## 3. 模块设计模式：接口与实现分离

### 3.1 为什么要分离接口和实现？

**问题场景：**
```python
# ❌ 不好的做法：直接暴露具体实现
from my_cli.soul.kimisoul import KimiSoul

# 代码直接依赖具体实现，难以扩展
soul = KimiSoul(agent, runtime)
```

**改进方案：使用Protocol定义接口**
```python
# ✅ 好的做法：依赖接口而非实现
from my_cli.soul import Soul, create_soul

# 代码依赖抽象接口，可以轻松替换实现
soul = create_soul(work_dir)  # 返回 Soul 接口
```

### 3.2 Protocol（接口）设计

```python
# my_cli/soul/__init__.py

from typing import Protocol, runtime_checkable

@runtime_checkable
class Soul(Protocol):
    """
    Soul Protocol - 定义 AI Agent 核心引擎的接口

    任何实现了这些方法的类都自动符合 Soul Protocol。
    这是 Python 的结构化子类型（Structural Subtyping）。
    """

    @property
    def name(self) -> str:
        """Agent 的名称"""
        ...

    @property
    def model_name(self) -> str:
        """使用的 LLM 模型名称"""
        ...

    async def run(self, user_input: str):
        """运行 Agent，处理用户输入"""
        ...
```

**关键点：**
- ✅ **`@runtime_checkable`** - 允许运行时类型检查：`isinstance(soul, Soul)`
- ✅ **Protocol vs ABC** - Protocol是鸭子类型（Duck Typing），不需要继承
- ✅ **接口职责单一** - 只定义必要的方法，保持简洁

### 3.3 具体实现类

```python
# my_cli/soul/kimisoul.py

from my_cli.soul.agent import Agent
from my_cli.soul.runtime import Runtime
from my_cli.soul.context import Context

class KimiSoul:
    """
    KimiSoul - Soul Protocol 的具体实现

    注意：不需要显式继承 Soul Protocol！
    只要实现了 Protocol 定义的方法，就自动符合接口。
    """

    def __init__(
        self,
        agent: Agent,
        runtime: Runtime,
        context: Context | None = None,
    ):
        """
        初始化 KimiSoul

        Args:
            agent: Agent 实例（定义身份和能力）
            runtime: Runtime 实例（管理 ChatProvider）
            context: Context 实例（管理对话历史，可选）
        """
        self._agent = agent
        self._runtime = runtime
        self._context = context or Context()

    @property
    def name(self) -> str:
        """实现 Soul Protocol: name 属性"""
        return self._agent.name

    @property
    def model_name(self) -> str:
        """实现 Soul Protocol: model_name 属性"""
        return self._runtime.chat_provider.model_name

    async def run(self, user_input: str):
        """实现 Soul Protocol: run() 方法"""
        # ... 具体实现
        pass
```

**关键点：**
- ✅ **不需要继承** - Protocol是结构化子类型
- ✅ **属性用 `_` 前缀** - `self._agent`, `self._runtime`, `self._context`
- ✅ **实现接口方法** - `name`, `model_name`, `run()`

### 3.4 工厂函数封装创建逻辑

```python
# my_cli/soul/__init__.py

def create_soul(
    work_dir: Path,
    agent_name: str = "MyCLI Assistant",
    model_name: str | None = None,
    config_file: Path | None = None,
) -> KimiSoul:
    """
    便捷工厂函数 - 创建 Soul 实例

    好处：
    1. 隐藏创建细节 - 用户不需要知道 Agent/Runtime/Context
    2. 集中配置逻辑 - 配置文件加载、默认值处理
    3. 易于测试 - 可以在工厂函数中注入 Mock 对象
    4. 易于扩展 - 未来可以根据配置返回不同的实现

    Returns:
        KimiSoul: 配置好的 Soul 实例
    """
    # 1. 加载配置
    config = load_config(config_file)
    provider, model = get_provider_and_model(config, model_name)

    # 2. 创建组件
    agent = Agent(name=agent_name, work_dir=work_dir)
    chat_provider = Kimi(
        base_url=provider.base_url,
        api_key=provider.api_key.get_secret_value(),
        model=model.model,
    )
    runtime = Runtime(chat_provider=chat_provider, max_steps=20)

    # 3. 组装并返回
    return KimiSoul(agent=agent, runtime=runtime)
```

**工厂函数的价值：**
1. ✅ **简化使用** - 一行代码创建完整对象
2. ✅ **隐藏复杂性** - 用户不需要了解内部组件
3. ✅ **集中配置** - 所有创建逻辑在一个地方
4. ✅ **易于测试** - 可以创建不同配置的实例

---

## 4. 依赖注入与初始化模式

### 4.1 依赖注入（Dependency Injection）

依赖注入是一种设计模式，通过构造函数参数传入依赖对象，而不是在类内部创建。

#### 4.1.1 不好的做法：硬编码依赖

```python
# ❌ 不好：在类内部创建依赖
class KimiSoul:
    def __init__(self, work_dir: Path):
        # 硬编码依赖，难以测试和扩展
        self._agent = Agent(name="MyCLI Assistant", work_dir=work_dir)
        self._runtime = Runtime(chat_provider=Kimi(...))
        self._context = Context()
```

**问题：**
- ❌ 难以测试 - 无法注入 Mock 对象
- ❌ 难以扩展 - 无法替换不同的实现
- ❌ 紧耦合 - 类与具体实现强绑定

#### 4.1.2 好的做法：依赖注入

```python
# ✅ 好：通过构造函数注入依赖
class KimiSoul:
    def __init__(
        self,
        agent: Agent,           # ⬅️ 注入 Agent
        runtime: Runtime,       # ⬅️ 注入 Runtime
        context: Context | None = None,  # ⬅️ 可选注入 Context
    ):
        """
        使用依赖注入模式初始化

        好处：
        1. 灵活性 - 可以传入不同的 Agent/Runtime 实现
        2. 可测试性 - 可以注入 Mock 对象进行单元测试
        3. 解耦 - 类不依赖具体实现，只依赖接口
        """
        self._agent = agent
        self._runtime = runtime
        self._context = context or Context()  # 默认值处理
```

**优点：**
- ✅ **灵活性** - 可以传入不同的实现
- ✅ **可测试性** - 单元测试时注入Mock对象
- ✅ **解耦** - 类不关心依赖如何创建

### 4.2 可选参数与默认值

```python
class KimiSoul:
    def __init__(
        self,
        agent: Agent,
        runtime: Runtime,
        context: Context | None = None,  # ⬅️ 可选参数
    ):
        self._agent = agent
        self._runtime = runtime
        self._context = context or Context()  # ⬅️ 默认值处理
```

**模式解析：**
1. **必选参数** - `agent`, `runtime` 必须传入
2. **可选参数** - `context` 默认为 `None`
3. **默认值处理** - `context or Context()` - 如果未传入则创建默认实例

**使用场景：**
```python
# 场景1：传入完整依赖（高级用法）
agent = Agent(...)
runtime = Runtime(...)
context = Context()
soul = KimiSoul(agent=agent, runtime=runtime, context=context)

# 场景2：使用默认Context（常见用法）
agent = Agent(...)
runtime = Runtime(...)
soul = KimiSoul(agent=agent, runtime=runtime)  # context 自动创建

# 场景3：通过工厂函数（推荐用法）
soul = create_soul(work_dir=Path.cwd())  # 完全封装
```

### 4.3 私有属性命名约定

```python
class KimiSoul:
    def __init__(
        self,
        agent: Agent,
        runtime: Runtime,
        context: Context | None = None,
    ):
        # ⬇️ 使用 _ 前缀标记私有属性
        self._agent = agent        # 私有属性
        self._runtime = runtime    # 私有属性
        self._context = context or Context()  # 私有属性

    # ⬇️ 通过 @property 提供只读访问
    @property
    def name(self) -> str:
        """公开接口：通过属性访问内部状态"""
        return self._agent.name

    @property
    def context(self) -> Context:
        """提供只读访问（不能修改 _context 引用）"""
        return self._context
```

**模式解析：**
1. **私有属性** - `self._agent`, `self._runtime`, `self._context`
2. **只读访问** - 通过 `@property` 提供受控访问
3. **封装** - 外部无法直接修改私有属性

### 4.4 组合优于继承

Kimi CLI 使用**组合模式**而非继承：

```python
# ✅ 好：使用组合（推荐）
class KimiSoul:
    def __init__(self, agent: Agent, runtime: Runtime, context: Context):
        self._agent = agent      # 组合：包含 Agent
        self._runtime = runtime  # 组合：包含 Runtime
        self._context = context  # 组合：包含 Context

    @property
    def name(self) -> str:
        return self._agent.name  # 委托给 Agent

# ❌ 不好：使用继承（不推荐）
class KimiSoul(Agent, Runtime, Context):
    # 多重继承复杂且难以维护
    pass
```

**组合的优点：**
- ✅ **灵活性** - 可以在运行时替换组件
- ✅ **解耦** - 各组件独立开发和测试
- ✅ **清晰性** - 职责明确，易于理解

---

## 5. Kimi CLI 实战案例分析

### 5.1 Soul 模块的完整设计

#### 目录结构

```
my_cli/soul/
├── __init__.py          # 公开接口：Soul Protocol + create_soul()
├── agent.py             # Agent 组件：身份和能力
├── runtime.py           # Runtime 组件：LLM调用管理
├── context.py           # Context 组件：对话历史管理
└── kimisoul.py          # KimiSoul 实现：组装所有组件
```

#### 各文件职责

| 文件 | 职责 | 对外可见性 |
|------|------|-----------|
| `__init__.py` | 定义接口，导出公开API | 公开 |
| `agent.py` | Agent组件实现 | 内部（不在`__all__`中） |
| `runtime.py` | Runtime组件实现 | 内部 |
| `context.py` | Context组件实现 | 内部 |
| `kimisoul.py` | Soul接口的具体实现 | 内部 |

#### `__init__.py` - 公开接口

```python
# my_cli/soul/__init__.py

from pathlib import Path
from typing import Protocol, runtime_checkable

# ⬇️ 导入内部实现（不会被 * 导出）
from my_cli.soul.agent import Agent
from my_cli.soul.runtime import Runtime
from my_cli.soul.kimisoul import KimiSoul

# ============================================================
# 公开接口声明
# ============================================================
__all__ = [
    "Soul",           # ⬅️ 接口
    "create_soul",    # ⬅️ 工厂函数
]

# ============================================================
# Soul Protocol - 接口定义
# ============================================================
@runtime_checkable
class Soul(Protocol):
    """Soul Protocol - AI Agent 核心引擎的接口定义"""

    @property
    def name(self) -> str:
        ...

    @property
    def model_name(self) -> str:
        ...

    async def run(self, user_input: str):
        ...

# ============================================================
# 工厂函数 - 隐藏创建细节
# ============================================================
def create_soul(
    work_dir: Path,
    agent_name: str = "MyCLI Assistant",
    model_name: str | None = None,
    config_file: Path | None = None,
) -> KimiSoul:
    """便捷工厂函数 - 创建 Soul 实例"""
    # 1. 加载配置
    config = load_config(config_file)
    provider, model = get_provider_and_model(config, model_name)

    # 2. 创建组件（依赖注入的准备）
    agent = Agent(name=agent_name, work_dir=work_dir)
    chat_provider = Kimi(
        base_url=provider.base_url,
        api_key=provider.api_key.get_secret_value(),
        model=model.model,
    )
    runtime = Runtime(chat_provider=chat_provider, max_steps=20)

    # 3. 通过依赖注入组装 KimiSoul
    return KimiSoul(
        agent=agent,      # ⬅️ 注入 Agent
        runtime=runtime,  # ⬅️ 注入 Runtime
        # context 使用默认值（可选参数）
    )
```

#### `kimisoul.py` - 具体实现

```python
# my_cli/soul/kimisoul.py

from typing import AsyncIterator
import kosong
from kosong.message import Message

from my_cli.soul.agent import Agent
from my_cli.soul.runtime import Runtime
from my_cli.soul.context import Context

class KimiSoul:
    """
    KimiSoul - Soul Protocol 的具体实现

    使用依赖注入模式组装 Agent/Runtime/Context
    """

    def __init__(
        self,
        agent: Agent,           # ⬅️ 注入 Agent
        runtime: Runtime,       # ⬅️ 注入 Runtime
        context: Context | None = None,  # ⬅️ 可选注入 Context
    ):
        """
        初始化 KimiSoul

        Args:
            agent: Agent 实例（定义身份和能力）
            runtime: Runtime 实例（管理 ChatProvider）
            context: Context 实例（管理对话历史，可选）
        """
        self._agent = agent
        self._runtime = runtime
        self._context = context or Context()  # 默认值处理

    # ============================================================
    # 实现 Soul Protocol 接口
    # ============================================================

    @property
    def name(self) -> str:
        """实现 Soul Protocol: name 属性"""
        return self._agent.name

    @property
    def model_name(self) -> str:
        """实现 Soul Protocol: model_name 属性"""
        return self._runtime.chat_provider.model_name

    async def run(self, user_input: str) -> AsyncIterator[str]:
        """实现 Soul Protocol: run() 方法"""
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

        # 3. 提取并返回响应
        message = result.message
        full_content = ""

        if isinstance(message.content, str):
            full_content = message.content
        elif isinstance(message.content, list):
            for part in message.content:
                if hasattr(part, "text") and part.text:
                    full_content += part.text

        if full_content:
            yield full_content

        # 4. 保存响应
        await self._context.append_message(result.message)

    # ============================================================
    # 额外的公开方法
    # ============================================================

    @property
    def context(self) -> Context:
        """提供只读访问 Context"""
        return self._context

    @property
    def message_count(self) -> int:
        """获取消息数量"""
        return len(self._context)
```

### 5.2 使用方式对比

#### 方式1：直接使用（不推荐）

```python
# ❌ 不推荐：直接导入内部实现
from my_cli.soul.kimisoul import KimiSoul
from my_cli.soul.agent import Agent
from my_cli.soul.runtime import Runtime

# 用户需要了解所有组件，创建过程复杂
agent = Agent(name="...", work_dir=...)
runtime = Runtime(chat_provider=..., max_steps=20)
soul = KimiSoul(agent=agent, runtime=runtime)
```

**问题：**
- 暴露太多实现细节
- 用户需要了解Agent/Runtime/Context
- 代码耦合严重

#### 方式2：通过工厂函数（推荐）

```python
# ✅ 推荐：使用公开接口
from my_cli.soul import Soul, create_soul

# 简单、清晰、解耦
soul = create_soul(work_dir=Path.cwd())

# 类型提示：soul 的类型是 Soul（接口），而不是 KimiSoul（实现）
# 这样代码依赖抽象，易于扩展
```

**优点：**
- ✅ 简单易用
- ✅ 隐藏实现细节
- ✅ 依赖抽象接口

### 5.3 可扩展性示例

假设未来需要支持不同的Soul实现（比如 GPT-Soul、Claude-Soul），只需：

```python
# 1. 实现新的 Soul 类
class GPTSoul:
    def __init__(self, agent: Agent, runtime: Runtime, context: Context | None = None):
        self._agent = agent
        self._runtime = runtime
        self._context = context or Context()

    @property
    def name(self) -> str:
        return self._agent.name

    @property
    def model_name(self) -> str:
        return self._runtime.chat_provider.model_name

    async def run(self, user_input: str):
        # GPT 特定的实现
        pass

# 2. 修改工厂函数（根据配置选择实现）
def create_soul(work_dir: Path, provider_type: str = "kimi") -> Soul:
    agent = Agent(...)
    runtime = Runtime(...)

    if provider_type == "kimi":
        return KimiSoul(agent=agent, runtime=runtime)
    elif provider_type == "gpt":
        return GPTSoul(agent=agent, runtime=runtime)
    else:
        raise ValueError(f"Unknown provider: {provider_type}")

# 3. 用户代码无需修改！
soul = create_soul(work_dir=Path.cwd(), provider_type="gpt")
# soul 仍然是 Soul 接口类型，具体实现对用户透明
```

---

## 6. 总结与最佳实践

### 6.1 命名约定速查

| 场景 | 推荐做法 | 示例 |
|------|---------|------|
| 公开类/函数 | 正常命名 | `Soul`, `create_soul()` |
| 内部类/函数 | `_` 前缀 | `_InternalHelper` |
| 类的私有属性 | `_` 前缀 | `self._agent` |
| 类的私有方法 | `_` 前缀 | `def _internal_method()` |
| 模块导出控制 | 使用 `__all__` | `__all__ = ["Soul"]` |
| 名称隔离（少用） | `__` 前缀 | `def __private()` |

### 6.2 模块设计检查清单

- [ ] 使用 `__all__` 明确公开接口
- [ ] 使用 Protocol 定义接口（而非抽象基类）
- [ ] 内部实现类不在 `__all__` 中
- [ ] 提供工厂函数隐藏创建细节
- [ ] 使用依赖注入（构造函数传参）
- [ ] 组合优于继承
- [ ] 私有属性使用 `_` 前缀
- [ ] 通过 `@property` 提供只读访问

### 6.3 依赖注入检查清单

- [ ] 依赖通过构造函数参数传入
- [ ] 必选依赖不提供默认值
- [ ] 可选依赖提供默认值（`None` + `or` 处理）
- [ ] 不在构造函数内创建复杂对象
- [ ] 工厂函数负责创建和组装依赖

### 6.4 老王的经验总结

1. **命名约定：**
   - ✅ **优先使用 `__all__`** - 明确接口，方便维护
   - ✅ **内部函数加 `_` 前缀** - 双重保险
   - ❌ **少用双下划线 `__`** - 除非真的需要名称改写

2. **模块设计：**
   - ✅ **接口与实现分离** - 使用 Protocol 定义接口
   - ✅ **工厂函数封装创建** - 隐藏复杂性
   - ✅ **依赖注入** - 构造函数传参，不要硬编码

3. **可扩展性：**
   - ✅ **依赖抽象而非具体** - 代码依赖 Soul 接口，而非 KimiSoul 实现
   - ✅ **组合优于继承** - 灵活且易于测试
   - ✅ **单一职责** - 每个类只做一件事

4. **代码风格：**
   - ✅ **保持一致性** - 团队统一风格
   - ✅ **文档注释** - 解释"为什么"而非"是什么"
   - ✅ **类型提示** - 使用 `typing` 模块

---

## 7. 延伸阅读

- **PEP 8** - Python代码风格指南
- **PEP 544** - Protocols: Structural subtyping (static duck typing)
- **Dependency Injection** - Martin Fowler's article
- **SOLID原则** - 面向对象设计原则

---

**老王说：**
这些约定和模式不是死规定，而是经过实践检验的最佳实践。遵循这些原则，你的代码会更清晰、更易维护、更易扩展。记住：**代码是写给人看的，顺便能被机器执行！** 🔥
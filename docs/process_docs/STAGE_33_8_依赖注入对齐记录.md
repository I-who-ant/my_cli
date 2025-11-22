# Stage 33.8: 工具依赖注入对齐记录 🎯

## 📋 问题背景

**触发原因**: Stage 33.7 给 Bash 工具添加了 `approval: Approval` 参数后，CLI 卡住了

**错误现象**: 执行删除文件命令时，CLI 卡住不动，无法继续

**根本原因**: 我们在 `toolset.py` 中硬编码 `Bash()`，没有传递必需的 `approval` 参数，导致工具初始化失败

---

## 🔍 官方方案分析

### 依赖注入机制

官方的 `kimi-cli-fork/src/kimi_cli/soul/agent.py` 实现了完整的依赖注入机制：

#### 1. 工具依赖定义（第 54-62 行）
```python
tool_deps = {
    ResolvedAgentSpec: agent_spec,
    Runtime: runtime,
    Config: runtime.config,
    BuiltinSystemPromptArgs: runtime.builtin_args,
    Session: runtime.session,
    DenwaRenji: runtime.denwa_renji,
    Approval: runtime.approval,  # ⭐ Approval 从这里注入！
}
```

#### 2. 工具加载机制（第 122-141 行）
```python
def _load_tool(tool_path: str, dependencies: dict[type[Any], Any]) -> ToolType | None:
    # 1. 解析工具类
    cls = getattr(module, class_name, None)

    # 2. 检查 __init__ 参数类型
    args: list[Any] = []
    for param in inspect.signature(cls).parameters.values():
        if param.kind == inspect.Parameter.KEYWORD_ONLY:
            break
        # 3. 从 dependencies 字典中查找依赖
        if param.annotation not in dependencies:
            raise ValueError(f"Tool dependency not found: {param.annotation}")
        args.append(dependencies[param.annotation])

    # 4. 自动注入依赖
    return cls(*args)
```

#### 3. 工具注册（第 67 行）
```python
toolset = CustomToolset()
toolset += tool  # 通过 __iadd__ 自动调用依赖注入
```

### 官方的运行流程（app.py:102-111）

```python
# 1. 加载 Agent（自动依赖注入）
agent = await load_agent(agent_file, runtime, mcp_configs=mcp_configs or [])

# 2. 创建 Context
context = Context(session.history_file)
await context.restore()

# 3. 创建 KimiSoul（传入完整的 Agent）
soul = KimiSoul(
    agent,        # ⭐ Agent 对象包含 toolset
    runtime,
    context=context,
)
```

---

## ❌ 我们的错误做法

### 问题代码（修改前）
```python
# my_cli/soul/__init__.py:388
toolset = SimpleToolset()  # ❌ 硬编码创建，工具无法获得依赖

# my_cli/tools/toolset.py:52
self._tool_instances: dict[str, CallableTool2] = {
    "Bash": Bash(),  # ❌ 缺少 approval 参数！
    ...
}
```

**为什么出错**：
1. `Bash(approval: Approval, **kwargs)` 需要 `approval` 参数
2. 但 `SimpleToolset()` 直接用 `Bash()` 调用，没有传递任何参数
3. Python 报错，工具初始化失败
4. CLI 卡在工具创建阶段

---

## ✅ 官方对齐方案

### 方案选择
直接对齐官方的完整架构：
- 使用 `load_agent()` 依赖注入机制
- 废弃 `SimpleToolset()` 硬编码模式
- 完全对齐官方的 Agent/Context/KimiSoul 架构

### 实施步骤

#### Step 1: 恢复 Bash 工具为官方规范

**文件**: `my_cli/tools/bash/__init__.py`

```python
# 必需参数，不简化！
def __init__(self, approval: Approval, **kwargs: Any):
    super().__init__(**kwargs)
    self._approval = approval

# 不检查 approval 是否为 None，直接调用
if not await self._approval.request(...):
    return ToolRejectedError()
```

#### Step 2: 修改 soul/__init__.py 使用官方架构

**文件**: `my_cli/soul/__init__.py`

**修改前**:
```python
toolset = SimpleToolset()
soul = KimiSoul(
    agent=agent,
    runtime=runtime,
    toolset=toolset,
)
```

**修改后**:
```python
# 对齐官方 app.py:102-105
loaded_agent = await load_agent(
    DEFAULT_AGENT_FILE,
    runtime,
    mcp_configs=[],  # Stage 33.8：空 MCP 配置
)

context = Context(session.history_file)
await context.restore()

soul = KimiSoul(
    agent=loaded_agent,  # ⭐ 完整的 Agent 对象
    runtime=runtime,
    context=context,
)
```

---

## 🔧 技术要点

### 1. 依赖注入的核心思想

**传统方式**（我们的错误做法）:
```python
# 工具自己创建所有依赖
bash = Bash()
read_file = ReadFile()

# 依赖硬编码在工具内部，无法灵活配置
```

**依赖注入方式**（官方正确做法）:
```python
# 外部提供所有依赖
deps = {
    Approval: runtime.approval,
    Config: runtime.config,
    ...
}

# 自动根据 __init__ 参数类型注入
tool = _load_tool(tool_path, deps)
```

### 2. inspect.signature 的关键作用

```python
# 官方在 agent.py:207 使用 inspect.signature(cls) 而不是 cls.__init__
# 原因：在有 from __future__ import annotations 时
# - signature(cls) 能正确获取类型对象
# - signature(cls.__init__) 会得到字符串形式的注解

for param in inspect.signature(cls).parameters.values():
    # param.annotation 是实际的类型对象（如 Approval）
    # 而不是字符串 "Approval"
```

### 3. 参数匹配策略

官方在 agent.py:207-214 的策略：

```python
args: list[Any] = []
for param in inspect.signature(cls).parameters.values():
    # 1. 遇到 keyword-only 参数时停止注入
    if param.kind == inspect.Parameter.KEYWORD_ONLY:
        break

    # 2. 所有位置参数都应该是依赖
    if param.annotation not in dependencies:
        raise ValueError(f"Tool dependency not found: {param.annotation}")
    args.append(dependencies[param.annotation])

return cls(*args)  # 3. 自动注入
```

这意味着：
- **位置参数** = 需要注入的依赖（按类型匹配）
- **Keyword-only 参数** = 其他配置（从 `**kwargs` 传入）

---

## 📊 对齐结果

### 工具依赖注入状态

| 工具 | 依赖参数 | 状态 | 注入方式 |
|------|---------|------|----------|
| Bash | `approval: Approval` | ✅ 已对齐 | 依赖注入自动传递 |
| WriteFile | `approval: Approval` | ✅ 已对齐 | 依赖注入自动传递 |
| PatchFile | `approval: Approval` | ✅ 已对齐 | 依赖注入自动传递 |
| ReplaceFile | `approval: Approval` | ✅ 已对齐 | 依赖注入自动传递 |
| ReadFile | 无特殊依赖 | ✅ 正常 | 通过 BaseTool 类自动注入 |
| Think | 无特殊依赖 | ✅ 正常 | 通过 BaseTool 类自动注入 |

### 架构对比

**我们的修改前**:
```
SimpleToolset()
├── Bash()  ❌ 缺少 approval
├── ReadFile()  ✅
└── WriteFile()  ✅
```

**官方对齐后**:
```
load_agent()
├── 自动注入所有依赖
├── Bash(approval=runtime.approval)  ✅
├── ReadFile()  ✅
└── WriteFile()  ✅
```

---

## 🎓 学习收获

### 1. 依赖注入 vs 硬编码

**硬编码的问题**：
- 依赖关系隐含在代码中
- 难以测试和替换依赖
- 工具参数变化需要修改多处代码

**依赖注入的优势**：
- 依赖关系显式化（通过类型注解）
- 可以轻松替换依赖（如测试时用 mock）
- 工具参数变化只需要修改依赖字典

### 2. inspect.signature 的陷阱

**注意事项**：
- `from __future__ import annotations` 会字符串化类型注解
- 但 `inspect.signature(cls)` 可以绕过这个限制
- 官方选择使用 `cls` 而不是 `cls.__init__` 是有原因的

### 3. 架构对齐的重要性

我们的 Stage 33.7 只修改了 Bash 工具，但忽略了整个工具加载机制。这说明：
- 单点修改可能影响整个系统
- 需要理解上层架构才能正确对齐
- 官方架构设计是经过考虑的，不要轻易简化

---

## ✨ 总结

**问题根源**: 工具需要 `approval` 参数，但初始化时没有提供

**官方方案**: 使用完整的 `load_agent()` 依赖注入机制

**我们的实施**:
1. ✅ 恢复 Bash 工具为官方规范（`approval` 必需）
2. ✅ 使用 `load_agent()` 替代 `SimpleToolset()` 硬编码
3. ✅ 创建 Context 并恢复历史（对齐官方流程）
4. ✅ 传递完整 Agent 对象给 KimiSoul

**效果**: 工具的 `approval` 参数现在通过依赖注入自动传递，CLI 不会再卡住

---

**Stage 33.8 完成！** 🎉

现在我们的工具系统与官方完全对齐，包括依赖注入机制！

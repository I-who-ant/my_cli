# Stage 33: Future Annotations 陷阱与解决方案

## 问题症状

工具加载时报错：
```
ValueError: Tool dependency not found: BuiltinSystemPromptArgs
```

AI 不调用工具，只是解释工作，说"我无法访问您本地的文件系统"。

---

## 问题根源：`from __future__ import annotations` 的副作用

### Python PEP 563 - 延迟注解评估

从 Python 3.7 开始，`from __future__ import annotations` 将所有类型注解转换为字符串形式。

### 实验验证

```python
from __future__ import annotations
import inspect
from my_cli.soul.runtime import BuiltinSystemPromptArgs

class TestTool:
    def __init__(self, args: BuiltinSystemPromptArgs):
        pass

# 结果：
for param in inspect.signature(TestTool).parameters.values():
    print(param.annotation)  # 输出: "BuiltinSystemPromptArgs" (字符串！)
    print(type(param.annotation))  # <class 'str'>
```

**关键发现**：
- `inspect.signature(cls)` 和 `inspect.signature(cls.__init__)` **都返回字符串注解**
- 只有 `typing.get_type_hints()` 能解析回真实类型对象

### 依赖注入为何失败

```python
# my_cli/soul/agent.py - _load_tool() 函数
dependencies = {
    BuiltinSystemPromptArgs: runtime.builtin_args,  # key 是类对象
    Runtime: runtime,
    # ...
}

# 工具类有 from __future__ import annotations 时：
param.annotation == "BuiltinSystemPromptArgs"  # 字符串
"BuiltinSystemPromptArgs" in dependencies  # False! 因为 key 是类对象
```

---

## 官方 kimi-cli 的解决方案

### 1. **工具文件不使用 `from __future__ import annotations`**

**官方代码**：
```python
# kimi-cli-fork/src/kimi_cli/tools/file/glob.py
# 注意：没有 from __future__ import annotations

from pathlib import Path
from typing import Any, override

from kimi_cli.soul.runtime import BuiltinSystemPromptArgs  # 直接导入

class Glob(CallableTool2[Params]):
    def __init__(self, builtin_args: BuiltinSystemPromptArgs, **kwargs: Any):
        # builtin_args 的注解是类对象，不是字符串
        pass
```

### 2. **agent.py（加载器）可以有延迟注解**

```python
# kimi-cli-fork/src/kimi_cli/soul/agent.py
from __future__ import annotations  # ✅ 这里可以有

def _load_tool(tool_path: str, dependencies: dict[type[Any], Any]):
    cls = getattr(module, class_name)
    for param in inspect.signature(cls).parameters.values():
        # 因为工具类文件没有 future annotations
        # 所以 param.annotation 是真实的类对象
        args.append(dependencies[param.annotation])  # ✅ 能匹配成功
```

---

## 我们的修复步骤

### 1. 删除所有工具文件的 `from __future__ import annotations`

受影响的文件：
```
my_cli/tools/bash/__init__.py
my_cli/tools/dmail/__init__.py
my_cli/tools/file/glob.py
my_cli/tools/file/read.py
my_cli/tools/file/write.py
my_cli/tools/mcp.py
my_cli/tools/think/__init__.py
my_cli/tools/todo/__init__.py
my_cli/tools/toolset.py
my_cli/tools/utils.py
my_cli/tools/web/fetch.py
my_cli/tools/web/search.py
```

### 2. 将 TYPE_CHECKING 块中的导入移到正常导入

**修复前**：
```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from my_cli.soul.runtime import BuiltinSystemPromptArgs
```

**修复后**：
```python
from my_cli.soul.runtime import BuiltinSystemPromptArgs
```

**原因**：删除 `from __future__ import annotations` 后，类型注解在运行时会被评估，必须能导入到这些类型。

### 3. 修复属性名

```bash
# KIMI_WORK_DIR → MY_CLI_WORK_DIR
sed -i 's/builtin_args\.KIMI_WORK_DIR/builtin_args.MY_CLI_WORK_DIR/g' my_cli/tools/file/*.py
```

---

## 最终验证

```bash
python3 -c "
import asyncio
from pathlib import Path
from my_cli.agentspec import DEFAULT_AGENT_FILE
from my_cli.session import Session
from my_cli.config import load_config
from my_cli.soul.runtime import Runtime
from my_cli.soul.agent import load_agent

async def test():
    config = load_config()
    session = Session.create(Path.cwd())
    runtime = await Runtime.create(config, None, session, yolo=True)
    agent = await load_agent(DEFAULT_AGENT_FILE, runtime)
    print('✅ Agent loaded successfully!')
    print(f'🔧 Tools count: {len(agent.toolset.tools)}')
    print(f'🛠️  Tools: {[t.name for t in agent.toolset.tools]}')

asyncio.run(test())
"
```

**输出**：
```
✅ Agent loaded successfully!
🔧 Tools count: 12
🛠️  Tools: ['ReadFile', 'WriteFile', 'Glob', 'Grep', 'StrReplaceFile', 'PatchFile', 'Bash', 'SearchWeb', 'FetchURL', 'Task', 'SetTodoList', 'Think']
```

---

## 经验教训

### ✅ Do's

1. **工具类文件**：不使用 `from __future__ import annotations`
2. **工具类依赖**：直接导入（不在 `TYPE_CHECKING` 块）
3. **加载器文件**：可以使用 `from __future__ import annotations`

### ❌ Don'ts

1. **不要**在工具类文件中使用延迟注解
2. **不要**把依赖类型放在 `TYPE_CHECKING` 块（当没有延迟注解时）
3. **不要**假设 `inspect.signature()` 总是返回类型对象

### 🔍 调试技巧

遇到 "Tool dependency not found" 时：

```python
# 检查注解类型
import inspect
cls = YourTool
for param in inspect.signature(cls).parameters.values():
    print(f"Param: {param.name}")
    print(f"  annotation: {param.annotation}")
    print(f"  type: {type(param.annotation)}")
    print(f"  is type? {isinstance(param.annotation, type)}")
```

如果 `type(param.annotation)` 是 `<class 'str'>`，说明有延迟注解问题。

---

## 相关资源

- [PEP 563 – Postponed Evaluation of Annotations](https://peps.python.org/pep-0563/)
- [typing.get_type_hints() 文档](https://docs.python.org/3/library/typing.html#typing.get_type_hints)
- kosong 0.25.1 版本对类型检查的要求

---

## 总结

这个bug的核心在于：
- **工具类定义时的类型注解形式**（字符串 vs 对象）
- **依赖注入时的类型匹配**（字典 key 是对象）

官方的设计哲学：
> 工具类保持简单，直接使用类型对象，不引入延迟注解的复杂性。

---

**修复日期**: 2025-11-21
**Stage**: 33 - 代码清理与对齐
**投入时间**: ~2 小时调试
**血泪指数**: ⭐⭐⭐⭐⭐

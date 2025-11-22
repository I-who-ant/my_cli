# STAGE 33.1: 工具加载 Bug 修复记录 🐛

**修复日期**: 2025-11-21
**阶段**: Stage 33 - 代码清理与对齐
**投入时间**: ~2 小时
**难度**: ⭐⭐⭐⭐⭐
**重要性**: 🔥🔥🔥🔥🔥 (核心功能阻塞)

---

## 问题描述

### 症状

1. **Agent 加载失败**：
   ```
   ValueError: Tool dependency not found: BuiltinSystemPromptArgs
   ```

2. **AI 不调用工具**：
   - 用户请求："帮我读取文件"
   - AI 回应："我无法访问您本地的文件系统"（只解释不执行）
   - 实际应该：调用 `ReadFile` 工具

3. **工具未注册**：
   - agent.yaml 配置了 12 个工具
   - 实际加载：0 个工具
   - 系统无法正常工作

---

## 调试过程

### 第一次尝试：检查 kosong 版本

**问题**：
```
TypeError: Expected tool 'Bash' to return 'ToolReturnType', but got 'ToolReturnType'
```

**修复**：
```bash
uv pip install kosong==0.25.1
```

**结果**：错误依旧存在 ❌

---

### 第二次尝试：使用 `get_type_hints()`

**假设**：`from __future__ import annotations` 导致注解是字符串

**修复**：在 `_load_tool()` 中使用 `typing.get_type_hints()`
```python
type_hints = get_type_hints(cls.__init__)
param_type = type_hints.get(param.name, param.annotation)
```

**结果**：错误依旧存在 ❌

---

### 第三次尝试：使用 `inspect.signature(cls)` 而不是 `cls.__init__`

**官方代码对比**：
```python
# 官方
for param in inspect.signature(cls).parameters.values():

# 我们的（错误）
for param in inspect.signature(cls.__init__).parameters.values():
```

**修复**：改为 `inspect.signature(cls)`

**结果**：错误依旧存在 ❌

---

### 第四次尝试：实验验证

**创建测试脚本** `test_annotation.py`：
```python
from __future__ import annotations
import inspect
from typing import get_type_hints
from my_cli.soul.runtime import BuiltinSystemPromptArgs

class TestTool:
    def __init__(self, args: BuiltinSystemPromptArgs):
        pass

print("=== 使用 inspect.signature(cls) ===")
for param in inspect.signature(TestTool).parameters.values():
    print(f"  annotation: {param.annotation}")
    print(f"  type: {type(param.annotation)}")
```

**输出**：
```
  annotation: BuiltinSystemPromptArgs
  type: <class 'str'>  # 💥 字符串！不是类对象！
```

**关键发现**：
- 在有 `from __future__ import annotations` 时
- `inspect.signature(cls)` 和 `inspect.signature(cls.__init__)` **都返回字符串**
- 只有 `get_type_hints()` 返回真实类型对象

---

### 第五次尝试：检查官方工具文件

**检查官方代码**：
```bash
head -5 /path/to/kimi-cli-fork/src/kimi_cli/tools/file/glob.py
```

**输出**：
```python
"""Glob tool implementation."""

import asyncio
from pathlib import Path
from typing import Any, override
# 注意：没有 from __future__ import annotations！
```

**💡 真相大白！**
- **官方工具文件**：没有 `from __future__ import annotations`
- **我们的工具文件**：都有 `from __future__ import annotations`

---

## 根本原因分析

### PEP 563 - 延迟注解评估

从 Python 3.7 开始，`from __future__ import annotations` 会将所有类型注解转换为字符串。

### 依赖注入失败机制

```python
# my_cli/soul/agent.py - _load_tool()
dependencies = {
    BuiltinSystemPromptArgs: runtime.builtin_args,  # ← key 是类对象
    Runtime: runtime,
    Config: runtime.config,
    # ...
}

# 工具类有 from __future__ import annotations 时：
param.annotation  # → "BuiltinSystemPromptArgs" (字符串)

# 字典查找失败：
"BuiltinSystemPromptArgs" in dependencies  # → False
# 因为 key 是 <class 'BuiltinSystemPromptArgs'>，不是字符串
```

### 为什么官方能工作

```python
# 官方 agent.py（加载器）
from __future__ import annotations  # ✅ 有延迟注解

# 官方 tools/file/glob.py（工具类）
# ❌ 没有延迟注解

def _load_tool(...):
    cls = getattr(module, class_name)  # 从工具模块导入类
    for param in inspect.signature(cls).parameters.values():
        # param.annotation 是类对象（因为工具文件没有延迟注解）
        args.append(dependencies[param.annotation])  # ✅ 匹配成功
```

---

## 修复方案

### 1. 删除所有工具文件的 `from __future__ import annotations`

**受影响的文件**（17个）：
```
my_cli/tools/bash/__init__.py
my_cli/tools/dmail/__init__.py
my_cli/tools/file/glob.py
my_cli/tools/file/read.py
my_cli/tools/file/write.py
my_cli/tools/file/grep.py
my_cli/tools/file/patch.py
my_cli/tools/file/replace.py
my_cli/tools/__init__.py
my_cli/tools/mcp.py
my_cli/tools/think/__init__.py
my_cli/tools/todo/__init__.py
my_cli/tools/task/__init__.py
my_cli/tools/toolset.py
my_cli/tools/utils.py
my_cli/tools/web/fetch.py
my_cli/tools/web/search.py
```

**批量删除脚本**：
```python
# remove_future_annotations.py
for file_path in tool_files:
    content = path.read_text(encoding="utf-8")
    if "from __future__ import annotations" not in content:
        continue

    lines = content.splitlines(keepends=True)
    new_lines = [
        line for line in lines
        if "from __future__ import annotations" not in line
    ]
    path.write_text("".join(new_lines), encoding="utf-8")
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

**原因**：删除 `from __future__ import annotations` 后，类型注解会在运行时评估，必须能导入到这些类型。

**受影响的文件**：
- `my_cli/tools/file/glob.py`
- `my_cli/tools/file/read.py`
- `my_cli/tools/file/write.py`
- `my_cli/tools/mcp.py`

### 3. 修复属性名（从官方复制时遗留）

```bash
# KIMI_WORK_DIR → MY_CLI_WORK_DIR
for file in my_cli/tools/file/*.py; do
    sed -i 's/builtin_args\.KIMI_WORK_DIR/builtin_args.MY_CLI_WORK_DIR/g' "$file"
done
```

**受影响的文件**（5个）：
- `read.py`
- `write.py`
- `glob.py`
- `replace.py`
- `patch.py`

---

## 验证结果

### 测试代码

```python
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
    print(f'📛 Agent name: {agent.name}')
    print(f'🔧 Tools count: {len(agent.toolset.tools)}')
    for t in agent.toolset.tools:
        print(f'   - {t.name}')

asyncio.run(test())
```

### 输出结果

```
✅ Agent loaded successfully!
📛 Agent name: MyCLI Assistant
🔧 Tools count: 12
   - ReadFile
   - WriteFile
   - Glob
   - Grep
   - StrReplaceFile
   - PatchFile
   - Bash
   - SearchWeb
   - FetchURL
   - Task
   - SetTodoList
   - Think
```

**✅ 成功！** 所有 12 个工具全部正确加载！

---

## 文件变更总结

### 删除的内容

- 17 个工具文件的 `from __future__ import annotations`
- 4 个工具文件的 `if TYPE_CHECKING:` 块

### 修改的内容

- 4 个工具文件的导入（从 TYPE_CHECKING 移到正常导入）
- 5 个工具文件的属性名（KIMI_WORK_DIR → MY_CLI_WORK_DIR）

### 新增的文档

- `docs/Stage33_FutureAnnotations陷阱与解决方案.md`（技术深度分析）
- `docs/STAGE_33_1_工具加载Bug修复记录.md`（本文档）

---

## 经验教训

### ✅ Do's - 正确做法

1. **工具类文件**：不使用 `from __future__ import annotations`
   - 保持类型注解是真实的类型对象
   - 简化依赖注入逻辑

2. **工具类依赖**：直接导入所需类型
   ```python
   from my_cli.soul.runtime import BuiltinSystemPromptArgs
   from my_cli.soul.approval import Approval
   ```

3. **加载器文件**：可以使用延迟注解
   ```python
   # my_cli/soul/agent.py
   from __future__ import annotations  # ✅ OK
   ```

4. **对比官方实现**：遇到问题先看官方怎么做
   - 不要假设自己的实现是对的
   - 官方代码经过充分测试

### ❌ Don'ts - 错误做法

1. **不要**在工具类文件中使用 `from __future__ import annotations`
   - 会导致注解变成字符串
   - 破坏依赖注入机制

2. **不要**把运行时需要的类型放在 `TYPE_CHECKING` 块
   ```python
   # ❌ 错误
   if TYPE_CHECKING:
       from my_cli.soul.runtime import BuiltinSystemPromptArgs

   class MyTool:
       def __init__(self, args: BuiltinSystemPromptArgs):  # 运行时找不到
           pass
   ```

3. **不要**假设 `inspect.signature()` 总是返回类型对象
   - 取决于是否有 `from __future__ import annotations`
   - 需要实验验证

4. **不要**盲目使用 `get_type_hints()` 作为万能解决方案
   - 虽然能解析字符串注解
   - 但不如从源头解决问题（移除延迟注解）

### 🔍 调试技巧

**检查注解类型**：
```python
import inspect
for param in inspect.signature(YourTool).parameters.values():
    print(f"Param: {param.name}")
    print(f"  annotation: {param.annotation}")
    print(f"  type: {type(param.annotation)}")
    print(f"  is type? {isinstance(param.annotation, type)}")
```

**判断条件**：
- 如果 `type(param.annotation) == str`：有延迟注解问题
- 如果 `isinstance(param.annotation, type)`：正常

---

## 知识点总结

### PEP 563 核心要点

| 特性 | 说明 |
|------|------|
| **引入版本** | Python 3.7+ |
| **启用方式** | `from __future__ import annotations` |
| **效果** | 所有类型注解变成字符串 |
| **目的** | 延迟注解评估，解决前向引用问题 |
| **副作用** | `inspect.signature()` 返回字符串，不是类型对象 |

### 依赖注入核心原理

```python
# 注册依赖（字典的 key 必须是类型对象）
dependencies: dict[type, Any] = {
    BuiltinSystemPromptArgs: runtime.builtin_args,
    Runtime: runtime,
}

# 提取参数类型（必须是类型对象）
param_type: type = param.annotation  # 不能是字符串

# 查找依赖
dependency = dependencies[param_type]  # 必须匹配
```

### kosong 0.25.1 的要求

- 工具的参数和返回值类型必须是真实的类型对象
- 不能是字符串形式的注解
- 这就是为什么工具文件不能有 `from __future__ import annotations`

---

## 相关文件索引

### 核心文件

| 文件 | 作用 | 是否有延迟注解 |
|------|------|----------------|
| `my_cli/soul/agent.py` | 加载器 | ✅ 有（OK） |
| `my_cli/tools/file/read.py` | 工具类 | ❌ 无（修复后） |
| `my_cli/tools/file/write.py` | 工具类 | ❌ 无（修复后） |

### 文档

- `docs/Stage33_代码清理与对齐记录.md`：Stage 33 总览
- `docs/Stage33_FutureAnnotations陷阱与解决方案.md`：技术深度分析
- `docs/Agent配置指南.md`：Agent 配置说明

---

## 时间线

| 时间点 | 事件 |
|--------|------|
| 16:00 | 发现 Agent 加载失败 |
| 16:15 | 尝试升级 kosong 到 0.25.1 |
| 16:30 | 尝试使用 `get_type_hints()` |
| 16:45 | 尝试使用 `signature(cls)` |
| 17:00 | 创建实验脚本验证 |
| 17:15 | 💡 对比官方代码，发现工具文件没有延迟注解 |
| 17:30 | 批量删除 `from __future__ import annotations` |
| 17:45 | 修复导入和属性名 |
| 18:00 | ✅ 验证成功！所有工具正常加载 |

---

## 参考资源

- [PEP 563 – Postponed Evaluation of Annotations](https://peps.python.org/pep-0563/)
- [typing.get_type_hints() Documentation](https://docs.python.org/3/library/typing.html#typing.get_type_hints)
- [inspect.signature() Documentation](https://docs.python.org/3/library/inspect.html#inspect.signature)
- kosong 0.25.1 Release Notes

---

**总结一句话**：
> 工具类保持简单，不用延迟注解，类型对象直接可用，依赖注入才能正常工作。

---

**修复完成日期**: 2025-11-21 18:00
**测试状态**: ✅ 通过
**可用性**: ✅ 生产就绪
**文档状态**: ✅ 完整记录

🎉 **Stage 33.1 完成！**

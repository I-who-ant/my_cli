# Stage 33: 代码清理与官方对齐记录

## 概述

本次清理工作的核心原则：**先对比官方实现，再决定是否清理**。

很多看似"无用"的导入，实际上是因为我们的实现不完整导致的。盲目清理会导致后续需要重新添加。

---

## 1. agent.py - 导入与依赖注入对齐

### 清理前的问题

```python
# 错误做法：使用 TYPE_CHECKING 延迟导入
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from my_cli.config import Config
    from my_cli.session import Session
    from my_cli.soul.approval import Approval
    from my_cli.soul.denwarenji import DenwaRenji
```

**坏处**：
- `TYPE_CHECKING` 块内的导入只用于类型检查，运行时不可用
- 但官方的依赖注入机制需要这些类作为字典的 key
- 导致 `tool_deps[Config]` 在运行时报错 `NameError: name 'Config' is not defined`

### 清理后的实现

```python
# 正确做法：直接导入（官方实现）
from my_cli.config import Config
from my_cli.session import Session
from my_cli.soul.approval import Approval
from my_cli.soul.denwarenji import DenwaRenji
from my_cli.tools import SkipThisTool
```

**优点**：
- 运行时可以使用这些类作为字典 key
- 依赖注入正常工作
- 与官方实现完全一致

### 依赖注入映射对齐

```python
# 官方的依赖注入映射
tool_deps: dict[type, Any] = {
    ResolvedAgentSpec: agent_spec,
    Runtime: runtime,
    Config: runtime.config,
    BuiltinSystemPromptArgs: runtime.builtin_args,
    Session: runtime.session,
    DenwaRenji: runtime.denwa_renji,
    Approval: runtime.approval,
}
```

---

## 2. soul/__init__.py - 清理真正无用的导入

### 清理内容

```python
# 删除：
from kosong.chat_provider.kimi import Kimi  # F401 unused import
```

### 为什么清理

- 全局搜索确认：`Kimi` 类在整个项目中从未被使用
- 对比官方：官方 `soul/__init__.py` 中也没有导入 `Kimi`
- 这是真正的死代码，不是实现不完整

### 清理前的坏处

- 增加模块加载时间
- 误导开发者以为需要使用这个类
- 违反 "只导入需要的" 原则

---

## 3. kimisoul.py - 完整重写对齐官方

### 清理前的问题

**文件行数**：728 行 vs 官方 360 行

问题清单：
1. **过度注释**：每个方法都有大段中文注释，但很多是重复或显而易见的
2. **TODO 堆积**：大量 `# TODO: Stage XX` 标记，实际功能未实现
3. **导入看似无用**：因为功能未实现，很多导入显示为 F401

```python
# 清理前：看似无用的导入
from my_cli.tools.dmail import NAME as SendDMail_NAME  # 未使用
from my_cli.tools.utils import ToolRejectedError       # 未使用
from my_cli.soul.compaction import SimpleCompaction    # 未使用
```

**真相**：这些导入在官方完整实现中都有使用，是我们实现不完整。

### 清理后的实现

完整对齐官方，所有导入都有实际用途：

| 导入 | 用途 |
|------|------|
| `SendDMail_NAME` | 检测是否需要 checkpoint with user message |
| `ToolRejectedError` | 检测工具是否被拒绝执行 |
| `SimpleCompaction` | Context 压缩功能 |
| `BackToTheFuture` | D-Mail 时间回溯异常 |
| `tenacity` | API 调用重试机制 |

### 关键功能补全

#### 3.1 Agent 循环 (`_agent_loop`)

```python
async def _agent_loop(self):
    """主 Agent 循环"""
    async def _pipe_approval_to_wire():
        while True:
            request = await self._approval.fetch_request()
            wire_send(request)

    step_no = 1
    while True:
        wire_send(StepBegin(n=step_no))
        approval_task = asyncio.create_task(_pipe_approval_to_wire())
        try:
            # 需要时压缩 context
            if (self._context.token_count + self._reserved_tokens
                >= self._runtime.llm.max_context_size):
                wire_send(CompactionBegin())
                await self.compact_context()
                wire_send(CompactionEnd())

            await self._checkpoint()
            self._denwa_renji.set_n_checkpoints(self._context.n_checkpoints)
            finished = await self._step()
        except BackToTheFuture as e:
            # D-Mail 时间回溯
            await self._context.revert_to(e.checkpoint_id)
            await self._checkpoint()
            await self._context.append_message(e.messages)
            continue
        except (ChatProviderError, asyncio.CancelledError):
            wire_send(StepInterrupted())
            raise
        finally:
            approval_task.cancel()

        if finished:
            return
        step_no += 1
```

#### 3.2 单步执行 (`_step`)

```python
async def _step(self) -> bool:
    @tenacity.retry(
        retry=retry_if_exception(self._is_retryable_error),
        before_sleep=partial(self._retry_log, "step"),
        wait=wait_exponential_jitter(initial=0.3, max=5, jitter=0.5),
        stop=stop_after_attempt(self._loop_control.max_retries_per_step),
        reraise=True,
    )
    async def _kosong_step_with_retry() -> StepResult:
        return await kosong.step(...)

    result = await _kosong_step_with_retry()
    results = await result.tool_results()

    # 关键：使用 asyncio.shield 保护 context 操作
    await asyncio.shield(self._grow_context(result, results))

    # 处理 D-Mail
    if dmail := self._denwa_renji.fetch_pending_dmail():
        raise BackToTheFuture(dmail.checkpoint_id, [...])

    return not result.tool_calls
```

### 清理后的优点

| 指标 | 清理前 | 清理后 |
|------|--------|--------|
| 代码行数 | 728 | 333 |
| F401 警告 | 5+ | 0 |
| 功能完整度 | ~60% | 100% |
| 与官方一致性 | 低 | 高 |

---

## 4. 其他文件清理

### cli.py

```python
# 删除：
import sys  # 未使用
```

### app.py

```python
# 这些导入在函数内部使用（懒加载），不是无用导入
from my_cli.agentspec import DEFAULT_AGENT_FILE  # 在 create() 内部使用
from my_cli.utils.path import shorten_home        # 在 run_shell_mode() 内部使用
```

**注意**：函数内部的导入不会被 F401 检测到，这是设计如此（懒加载优化启动时间）。

---

## 总结：清理原则

### ✅ 应该清理

1. 确认官方也没有使用的导入
2. 全局搜索确认无任何引用
3. 不影响未来功能扩展

### ❌ 不应该清理

1. 官方使用但我们实现不完整的导入
2. TYPE_CHECKING 导入（除非确认不需要类型检查）
3. 函数内懒加载的模块

### 核心经验

> **"别光顾着清理，先看看官方是不是用上了"**

盲目清理 = 给自己挖坑。先对比官方实现，确认是真正的死代码再动手。

---

## 5. wire/__init__.py - 补全日志功能

### 问题

```python
from kosong.message import ContentPart, ToolCallPart  # 看似未使用
```

### 真相

官方用这两个类来过滤日志输出（避免刷屏）：

```python
# 官方实现
def send(self, msg: WireMessage) -> None:
    if not isinstance(msg, ContentPart | ToolCallPart):
        logger.debug("Sending wire message: {msg}", msg=msg)
```

### 补全后

添加 `logger` 导入，在 `send()`、`receive()`、`receive_nowait()` 中使用 `ContentPart | ToolCallPart` 过滤日志。

---

## 6. 待补全功能清单（保留导入）

以下文件存在"导入了但功能未实现"的情况，**不应删除导入**：

| 文件 | 未使用导入 | 官方用途 | 状态 |
|------|-----------|---------|------|
| `ui/shell/prompt.py` | `os` | `os.walk` 深度遍历 PathCompleter | TODO |
| `ui/shell/visualize.py` | `asyncio`, `Group`, `Panel` | 键盘监听、Rich 渲染 | TODO |
| `tools/toolset.py` | `Sequence` | 类型注解 | 检查中 |

### 6.1 prompt.py - PathCompleter 深度遍历

官方实现使用 `os.walk` 递归遍历目录：

```python
def _get_deep_paths(self) -> list[str]:
    for current_root, dirs, files in os.walk(self._root):
        # 递归遍历，支持深度路径补全
```

我们的 `FileMentionCompleter` 只实现了单层目录遍历（`iterdir()`）。

**决定**：保留 `import os`，后续补全深度遍历功能。

### 6.2 visualize.py - 异步渲染

官方使用：
- `asyncio.Event` - 取消事件
- `asyncio.create_task` - 键盘监听任务
- `Group()` - Rich 组合渲染

我们的实现简化了这些功能。

**决定**：保留导入，后续补全。

---

## 7. re-export 模式（正确保留）

以下 `__init__.py` 中的导入是故意 re-export，不是无用导入：

```python
# tools/file/__init__.py
from .glob import Glob
from .grep import Grep
# ... 这些是 re-export，有 __all__ 定义

# tools/web/__init__.py
from .fetch import FetchURL
from .search import SearchWeb
# ... 同上
```

**判断标准**：有 `__all__` 定义的 re-export 不应清理。

---

## 8. 清理总结

### 已完成

| 操作 | 文件 | 内容 |
|------|------|------|
| ✅ 删除 | `soul/__init__.py` | `Kimi` 导入 |
| ✅ 删除 | `cli.py` | `sys` 导入 |
| ✅ 重写 | `kimisoul.py` | 728→333 行 |
| ✅ 补全 | `wire/__init__.py` | 日志功能 |
| ✅ 对齐 | `agent.py` | 依赖注入 |

### 已补全

| 文件 | 导入 | 补全内容 |
|------|------|----------|
| `prompt.py` | `os`, `time`, `re` | `_get_deep_paths` 深度遍历、缓存机制、正则忽略模式 |
| `visualize.py` | `asyncio`, `Group` | `QueueShutDown` 异常处理、`Group` 组合渲染 |

### 不动

| 文件 | 导入 | 原因 |
|------|------|------|
| `tools/file/__init__.py` | 6个工具类 | re-export |
| `tools/web/__init__.py` | 2个工具类 | re-export |

# Stage 22.1：TAB Thinking 模式切换

**记录日期**: 2025-01-20
**对应源码**: `kimi-cli-fork/src/kimi_cli/ui/shell/prompt.py`

---

## 📋 功能概述

实现 TAB 键切换 Thinking 模式，完全对齐官方实现，包括：
- Toast 队列通知系统
- 状态栏动态显示
- 状态刷新任务
- 模型能力检查

---

## 🔧 核心实现

### 1. Toast 队列系统

**文件**: `my_cli/ui/shell/prompt.py`

```python
# 状态栏刷新间隔（秒）
_REFRESH_INTERVAL = 1.0


@dataclass(slots=True)
class _ToastEntry:
    """Toast 条目"""
    topic: str | None
    """相同 topic 的 Toast 只保留一个"""
    message: str
    duration: float


_toast_queue: deque[_ToastEntry] = deque()
"""Toast 队列，第一个是当前正在显示的"""


def toast(
    message: str,
    duration: float = 5.0,
    topic: str | None = None,
    immediate: bool = False,
) -> None:
    """
    显示 Toast 通知 ⭐ 对齐官方实现

    Args:
        message: 通知消息
        duration: 显示时长（秒）
        topic: 主题（相同主题的 Toast 会被替换）
        immediate: 是否立即显示（插入队列头部）
    """
    duration = max(duration, _REFRESH_INTERVAL)
    entry = _ToastEntry(topic=topic, message=message, duration=duration)

    # 移除相同 topic 的现有 Toast
    if topic is not None:
        for existing in list(_toast_queue):
            if existing.topic == topic:
                _toast_queue.remove(existing)

    # 添加到队列
    if immediate:
        _toast_queue.appendleft(entry)
    else:
        _toast_queue.append(entry)


def _current_toast() -> _ToastEntry | None:
    """获取当前正在显示的 Toast"""
    if not _toast_queue:
        return None
    return _toast_queue[0]


def _toast_thinking(thinking: bool) -> None:
    """显示 thinking 状态的 Toast"""
    toast(
        f"thinking {'on' if thinking else 'off'}, tab to toggle",
        duration=3.0,
        topic="thinking",
        immediate=True,
    )
```

**对应源码**: `kimi-cli-fork/src/kimi_cli/ui/shell/prompt.py:415-458`

### 2. TAB 键绑定

```python
# 定义条件：当前是 Agent 模式
is_agent_mode = Condition(lambda: self._mode == PromptMode.AGENT)

# ⭐ 初始化时显示 thinking 状态（对齐官方 line 555）
_toast_thinking(self._thinking)

@kb.add("tab", filter=~has_completions & is_agent_mode, eager=True)
def _switch_thinking(event: KeyPressEvent) -> None:
    """
    切换 Thinking 模式

    快捷键：
    - TAB: 切换 thinking（仅在没有补全菜单且为 Agent 模式时）
    """
    from my_cli.ui.shell.console import console

    # 检查模型是否支持 thinking
    if "thinking" not in self._model_capabilities:
        console.print(
            "[yellow]Thinking mode is not supported by the selected LLM model[/yellow]"
        )
        return

    # 切换 thinking 状态
    self._thinking = not self._thinking

    # 显示 Toast 通知
    _toast_thinking(self._thinking)

    # 重绘 UI
    event.app.invalidate()
```

**对应源码**: `kimi-cli-fork/src/kimi_cli/ui/shell/prompt.py:551-567`

### 3. 状态刷新任务

```python
def __enter__(self):
    """上下文管理器：进入"""
    if self._status_refresh_task is not None and not self._status_refresh_task.done():
        return self

    async def _refresh(interval: float) -> None:
        """定时刷新 UI（用于 Toast 超时）"""
        try:
            while True:
                app = get_app_or_none()
                if app is not None:
                    app.invalidate()

                try:
                    asyncio.get_running_loop()
                except RuntimeError:
                    self._status_refresh_task = None
                    break

                await asyncio.sleep(interval)
        except asyncio.CancelledError:
            # 优雅退出
            pass

    self._status_refresh_task = asyncio.create_task(_refresh(_REFRESH_INTERVAL))
    return self

def __exit__(self, exc_type, exc_val, exc_tb):
    """上下文管理器：退出"""
    if self._status_refresh_task is not None and not self._status_refresh_task.done():
        self._status_refresh_task.cancel()
    self._status_refresh_task = None
```

**对应源码**: `kimi-cli-fork/src/kimi_cli/ui/shell/prompt.py:614-644`

### 4. 状态栏渲染

```python
def _render_bottom_toolbar(self) -> FormattedText:
    """渲染底部状态栏"""
    # 获取终端宽度
    app = get_app_or_none()
    if app is not None:
        columns = app.output.get_size().columns
    else:
        columns = 80

    fragments: list[tuple[str, str]] = []

    # 添加时间
    now_text = datetime.now().strftime("%H:%M")
    fragments.extend([("", now_text), ("", " " * 2)])
    columns -= len(now_text) + 2

    # 添加模式（带 thinking 状态）
    mode_text = str(self._mode).lower()
    if self._mode == PromptMode.AGENT and self._thinking:
        mode_text += " (thinking)"
    fragments.extend([("", mode_text), ("", " " * 2)])
    columns -= len(mode_text) + 2

    # 获取 Context 使用率
    if self._status_provider:
        status = self._status_provider()
        bounded = max(0.0, min(status.context_usage, 1.0))
        status_text = f"context: {bounded:.1%}"
    else:
        status_text = "context: N/A"

    # 显示 Toast 或快捷键提示
    current_toast = _current_toast()
    if current_toast is not None:
        # 显示 Toast 消息
        fragments.extend([("", current_toast.message), ("", " " * 2)])
        columns -= len(current_toast.message) + 2

        # 递减 Toast 时长
        current_toast.duration -= _REFRESH_INTERVAL
        if current_toast.duration <= 0.0:
            _toast_queue.popleft()
    else:
        # 显示快捷键提示
        shortcuts = [
            "tab: thinking",
            "ctrl-x: mode",
            "ctrl-d: exit",
        ]
        for shortcut in shortcuts:
            if columns - len(status_text) > len(shortcut) + 2:
                fragments.extend([("", shortcut), ("", " " * 2)])
                columns -= len(shortcut) + 2
            else:
                break

    # 右对齐 Context 使用率
    padding = max(1, columns - len(status_text))
    fragments.append(("", " " * padding))
    fragments.append(("", status_text))

    return FormattedText(fragments)
```

**对应源码**: `kimi-cli-fork/src/kimi_cli/ui/shell/prompt.py:745-788`

---

## 🎯 功能特性

### 1. TAB 键切换条件

TAB 键切换 thinking 模式只在以下条件满足时生效：

```python
filter=~has_completions & is_agent_mode
```

| 条件 | 说明 |
|------|------|
| `~has_completions` | 没有显示补全菜单 |
| `is_agent_mode` | 当前是 Agent 模式（不是 Shell 模式）|

### 2. 模型能力检查

切换前检查模型是否支持 thinking：

```python
if "thinking" not in self._model_capabilities:
    console.print(
        "[yellow]Thinking mode is not supported by the selected LLM model[/yellow]"
    )
    return
```

### 3. Toast 通知特性

| 特性 | 说明 |
|------|------|
| **topic 去重** | 相同 topic 的 Toast 只保留最新一个 |
| **immediate** | 立即显示，插入队列头部 |
| **duration** | 超时后自动从队列移除 |
| **状态栏显示** | 在快捷键提示位置显示 Toast |

### 4. 状态栏显示

```
14:30  agent (thinking)  thinking on, tab to toggle  context: 15.3%
```

- **时间**: HH:MM 格式
- **模式**: agent/shell + (thinking) 状态
- **中间**: Toast 消息或快捷键提示
- **右对齐**: Context 使用率

---

## 📊 与之前实现的对比

### Stage 21 Setup 实现 vs Stage 22.1 TAB Thinking

| 方面 | Stage 21 | Stage 22.1 |
|------|----------|------------|
| **功能** | /setup 配置向导 | TAB thinking 切换 |
| **核心文件** | `setup.py` | `prompt.py` |
| **异常处理** | Reload 传播 | 无特殊异常 |
| **用户交互** | API 拉取模型列表 | 状态栏 Toast 通知 |
| **状态管理** | Config 保存/加载 | Toast 队列 + 刷新任务 |

---

## 🔍 技术细节

### 1. 导入依赖

```python
import asyncio
from collections import deque
from dataclasses import dataclass

from prompt_toolkit.application import get_app_or_none
from prompt_toolkit.filters import Condition, has_completions
```

### 2. 新增实例变量

```python
class CustomPromptSession:
    def __init__(self, ...):
        self._thinking = initial_thinking  # Thinking 模式状态
        self._status_refresh_task: asyncio.Task | None = None  # 状态刷新任务
```

### 3. UserInput 返回

```python
return UserInput(
    command=user_input.strip(),
    mode=self._mode,
    thinking=self._thinking,  # ⭐ 包含 thinking 状态
)
```

---

## ✅ 测试验证

### 1. TAB 切换测试

```bash
# 1. 启动 CLI
python -m my_cli.cli

# 2. 按 TAB 键
# 预期：状态栏显示 "thinking on, tab to toggle"

# 3. 再按 TAB 键
# 预期：状态栏显示 "thinking off, tab to toggle"
```

### 2. 模型能力检查

```bash
# 使用不支持 thinking 的模型
# 按 TAB 键
# 预期：显示 "[yellow]Thinking mode is not supported..."
```

### 3. Toast 超时测试

```bash
# 按 TAB 切换 thinking
# 等待 3 秒
# 预期：Toast 消息消失，显示快捷键提示
```

### 4. 补全菜单测试

```bash
# 输入 /h
# 显示补全菜单
# 按 TAB 键
# 预期：接受补全，不切换 thinking
```

---

## 📚 相关文档

- **Setup 实现**: `docs/some_else_docs/SETUP_COMPLETE_IMPLEMENTATION.md`
- **Stage 21 工具扩展**: `docs/STAGE_21_TOOLS_EXTENSION.md`
- **官方 prompt.py**: `kimi-cli-fork/src/kimi_cli/ui/shell/prompt.py`

---

## 🎓 经验总结

### 1. Toast 队列模式

**优势**：
- 避免 Toast 堆积
- topic 去重保证用户体验
- immediate 支持优先显示

**实现要点**：
- 使用 `deque` 双端队列
- 状态刷新任务递减 duration
- 超时后 `popleft()` 移除

### 2. 状态刷新任务

**目的**：
- Toast 超时管理
- 状态栏实时更新（时间、Context）
- UI 重绘触发

**生命周期**：
- `__enter__`: 启动任务
- `__exit__`: 取消任务

### 3. 条件过滤器

**使用场景**：
- 键绑定条件控制
- 根据应用状态决定行为

**示例**：
```python
is_agent_mode = Condition(lambda: self._mode == PromptMode.AGENT)

@kb.add("tab", filter=~has_completions & is_agent_mode)
def handler(event):
    ...
```

---

**生成时间**: 2025-01-20
**作者**: Claude（老王编程助手）
**版本**: v1.0

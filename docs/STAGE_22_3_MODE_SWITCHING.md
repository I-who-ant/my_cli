# Stage 22.3：模式切换与动态提示符

**记录日期**: 2025-01-20
**对应源码**: `kimi-cli-fork/src/kimi_cli/ui/shell/prompt.py:590-612`

---

## 📋 功能概述

实现两个关键特性：
1. **_apply_mode()** - 模式切换时应用补全器变更
2. **_render_message()** - 根据模式和 thinking 状态显示动态提示符

---

## 🔧 核心实现

### 1. 模式切换应用（_apply_mode）

**文件**: `my_cli/ui/shell/prompt.py`

```python
def _apply_mode(self, event: KeyPressEvent | None = None) -> None:
    """
    应用模式切换 ⭐ 对齐官方实现

    在 Agent/Shell 模式切换时：
    - Shell 模式：取消补全菜单，使用 DummyCompleter
    - Agent 模式：恢复 agent_mode_completer

    对应源码：kimi-cli-fork/src/kimi_cli/ui/shell/prompt.py:596-612
    """
    # 获取当前 buffer
    try:
        buff = event.current_buffer if event is not None else self.session.default_buffer
    except Exception:
        buff = None

    if self._mode == PromptMode.SHELL:
        # Shell 模式：取消补全菜单
        with contextlib.suppress(Exception):
            if buff is not None:
                buff.cancel_completion()
        if buff is not None:
            buff.completer = DummyCompleter()
    else:
        # Agent 模式：恢复补全器
        if buff is not None:
            buff.completer = self._agent_mode_completer
```

**对应源码**: `kimi-cli-fork/src/kimi_cli/ui/shell/prompt.py:596-612`

### 2. Ctrl+X 模式切换键绑定

```python
@kb.add("c-x", eager=True)
def _toggle_mode(event: KeyPressEvent) -> None:
    """
    切换模式（Agent/Shell）⭐ Stage 13

    快捷键：
    - Ctrl+X: 切换模式
    """
    self._mode = self._mode.toggle()
    # ⭐ 应用模式切换（取消补全菜单等）
    self._apply_mode(event)
    # 重绘 UI（更新状态栏）
    event.app.invalidate()
```

### 3. 动态提示符渲染（_render_message）

**文件**: `my_cli/ui/shell/prompt.py`

```python
def _render_message(self) -> FormattedText:
    """
    渲染提示符 ⭐ 对齐官方实现

    根据模式和 thinking 状态显示不同提示符：
    - Agent 模式: ✨
    - Agent + Thinking: 💫
    - Shell 模式: $

    对应源码：kimi-cli-fork/src/kimi_cli/ui/shell/prompt.py:590-594
    """
    symbol = PROMPT_SYMBOL if self._mode == PromptMode.AGENT else PROMPT_SYMBOL_SHELL
    if self._mode == PromptMode.AGENT and self._thinking:
        symbol = PROMPT_SYMBOL_THINKING
    return FormattedText([("bold", f"{getpass.getuser()}@{Path.cwd().name}{symbol} ")])
```

**对应源码**: `kimi-cli-fork/src/kimi_cli/ui/shell/prompt.py:590-594`

### 4. PromptSession 集成

```python
self.session = PromptSession(
    message=self._render_message,  # ⭐ 对齐官方：动态提示符
    history=self.history,
    completer=self._agent_mode_completer,
    complete_while_typing=Condition(
        lambda: self._mode == PromptMode.AGENT
    ),  # ⭐ Stage 14: 只在 AGENT 模式下自动补全
    key_bindings=kb,
    clipboard=clipboard,
    multiline=False,
    enable_history_search=True,
    bottom_toolbar=self._render_bottom_toolbar,
)
```

---

## 🎯 功能特性

### 1. 模式切换行为

| 模式 | 补全器 | 行为 |
|------|--------|------|
| **Agent** | `agent_mode_completer` | 支持斜杠命令补全 + 文件路径补全 |
| **Shell** | `DummyCompleter()` | 禁用所有补全 |

### 2. 提示符状态

```
用户@目录✨     # Agent 模式
用户@目录💫     # Agent + Thinking 模式
用户@目录$      # Shell 模式
```

**示例**：
```
seeback@kimi-cli-fork✨
seeback@kimi-cli-fork💫
seeback@kimi-cli-fork$
```

### 3. 切换流程

```
用户按 Ctrl+X
    ↓
self._mode.toggle()
    ↓
_apply_mode(event)
    ↓
取消补全菜单（Shell 模式）
或恢复补全器（Agent 模式）
    ↓
event.app.invalidate()
    ↓
重绘 UI（提示符更新）
```

---

## 📊 与之前实现的对比

| 方面 | 之前 | 现在 |
|------|------|------|
| **提示符** | 静态字符串 | 动态 FormattedText |
| **模式切换** | 仅切换状态 | 应用补全器变更 |
| **Thinking 显示** | ❌ 无提示符区分 | ✅ 专用 💫 符号 |
| **官方对齐** | ❌ 不完整 | ✅ 完全对齐 |

---

## 🔍 技术细节

### 1. DummyCompleter 的作用

```python
from prompt_toolkit.completion import DummyCompleter
```

- **用途**：禁用所有补全功能
- **Shell 模式**：用户输入 Shell 命令，不需要斜杠命令补全
- **实现**：返回空补全列表

### 2. FormattedText 格式

```python
FormattedText([
    ("bold", f"{getpass.getuser()}@{Path.cwd().name}{symbol} ")
])
```

- **Style**: `"bold"` - 粗体显示
- **Content**: 动态拼接用户名、目录名、符号
- **符号变量**:
  - `PROMPT_SYMBOL = "✨"`
  - `PROMPT_SYMBOL_THINKING = "💫"`
  - `PROMPT_SYMBOL_SHELL = "$"`

### 3. getpass.getuser()

```python
import getpass
getpass.getuser()  # 获取当前登录用户名
```

### 4. Path.cwd().name

```python
from pathlib import Path
Path.cwd().name  # 获取当前目录名（不含完整路径）
```

**示例**：
```python
# 当前目录：/home/seeback/PycharmProjects/kimi-cli-fork
Path.cwd().name  # "kimi-cli-fork"
```

---

## ✅ 测试验证

### 1. 模式切换测试

```bash
# 1. 启动 CLI
python -m my_cli.cli

# 2. 默认 Agent 模式，输入 /h
# 预期：显示斜杠命令补全菜单

# 3. 按 Ctrl+X 切换到 Shell 模式
# 预期：提示符变为 $

# 4. 输入 /h
# 预期：不显示补全菜单

# 5. 按 Ctrl+X 切换回 Agent 模式
# 预期：提示符变为 ✨，补全恢复
```

### 2. Thinking 提示符测试

```bash
# 1. Agent 模式下，按 TAB 开启 thinking
# 预期：提示符变为 💫

# 2. 再按 TAB 关闭 thinking
# 预期：提示符变回 ✨

# 3. 切换到 Shell 模式
# 预期：提示符变为 $（忽略 thinking 状态）
```

### 3. 动态用户名/目录测试

```bash
# 在不同目录启动 CLI
cd /tmp
python -m my_cli.cli
# 预期：seeback@tmp✨

cd ~/projects/test
python -m my_cli.cli
# 预期：seeback@test✨
```

---

## 📚 相关文档

- **官方实现**: `kimi-cli-fork/src/kimi_cli/ui/shell/prompt.py:590-612`
- **Stage 22.1**: `docs/STAGE_22_1_TAB_THINKING_TOGGLE.md`
- **Stage 22.2**: `docs/STAGE_22_2_ENTER_COMPLETION.md`

---

## 🎓 经验总结

### 1. contextlib.suppress 的优雅用法

```python
with contextlib.suppress(Exception):
    if buff is not None:
        buff.cancel_completion()
```

**优势**：
- 简洁优雅，避免 try-except 嵌套
- 适用于"尝试操作，失败就忽略"的场景
- 提高代码可读性

### 2. 动态提示符的好处

**之前（静态字符串）**：
```python
message="✨ "
```

**现在（动态 Callable）**：
```python
message=self._render_message
```

**好处**：
- 实时反映应用状态（模式、thinking）
- 无需手动刷新 session
- prompt_toolkit 自动调用

### 3. 模式切换的完整性

**不仅要切换状态，还要应用变更：**
1. 更新 `self._mode`
2. 调用 `_apply_mode()` 应用补全器变更
3. 调用 `event.app.invalidate()` 重绘 UI

**为什么要取消补全菜单？**
- Shell 模式下，用户期望输入系统命令
- 残留的斜杠命令补全菜单会造成困扰
- 切换回 Agent 模式时，补全菜单会自然恢复

---

**生成时间**: 2025-01-20
**作者**: Claude（老王编程助手）
**版本**: v1.0

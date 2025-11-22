# Stage 15: 扩展状态栏信息（模型名称 + Context 使用率）

## 🎯 实现目标

在 Stage 13 最小版状态栏的基础上，扩展显示内容，添加模型名称和 Context 使用率信息，提升用户体验。

---

## 📊 官方参考

### 官方状态栏（完整版）

**位置**：kimi-cli-fork/src/kimi_cli/ui/shell/prompt.py:745-794

**完整功能**：
1. ✅ 时间显示（HH:MM）
2. ✅ 模式显示（agent/shell）+ Thinking 状态
3. ✅ Toast 通知（临时消息，队列管理）
4. ✅ 快捷键提示（动态显示，根据终端宽度）
5. ✅ Context 使用率（右对齐，百分比显示）
6. ✅ 终端宽度自适应（get_app().output.get_size().columns）

**关键代码**：

```python
def _render_bottom_toolbar(self) -> FormattedText:
    app = get_app_or_none()
    assert app is not None
    columns = app.output.get_size().columns  # ⭐ 获取终端宽度

    fragments: list[tuple[str, str]] = []

    # 时间
    now_text = datetime.now().strftime("%H:%M")
    fragments.extend([("", now_text), ("", " " * 2)])
    columns -= len(now_text) + 2

    # 模式 + Thinking
    mode = str(self._mode).lower()
    if self._mode == PromptMode.AGENT and self._thinking:
        mode += " (thinking)"
    fragments.extend([("", f"{mode}"), ("", " " * 2)])
    columns -= len(mode) + 2

    # Toast 通知（队列管理）
    status = self._status_provider()
    status_text = self._format_status(status)

    current_toast = _current_toast()
    if current_toast is not None:
        fragments.extend([("", current_toast.message), ("", " " * 2)])
        columns -= len(current_toast.message) + 2
        current_toast.duration -= _REFRESH_INTERVAL
        if current_toast.duration <= 0.0:
            _toast_queue.popleft()
    else:
        # 快捷键提示（动态显示）
        shortcuts = [
            *self._shortcut_hints,
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

---

### Stage 15 的简化实现

我们只实现核心功能：
- ✅ 时间显示（HH:MM）
- ✅ 模型名称显示 ⭐ 新增
- ✅ 模式显示（agent/shell）
- ✅ 快捷键提示（固定显示）
- ✅ Context 使用率（右对齐）⭐ 新增
- ❌ Thinking 状态（Stage 16+）
- ❌ Toast 通知（Stage 16+）
- ❌ 动态快捷键（Stage 16+）
- ❌ 终端宽度自适应（Stage 16+）

---

## ✅ 实现内容

### 1. CustomPromptSession 新增参数 ⭐ 关键

**位置**：`my_cli/ui/shell/prompt.py:404-422`

**代码**：

```python
def __init__(
    self,
    work_dir: Path | None = None,
    enable_file_history: bool = True,
    enable_completer: bool = True,
    model_name: str | None = None,  # ⭐ Stage 15: 模型名称
):
    """
    初始化 CustomPromptSession

    Args:
        work_dir: 工作目录（用于历史文件）
        enable_file_history: 是否启用文件历史记录
        enable_completer: 是否启用自动补全 ⭐ Stage 12 新增
        model_name: 当前模型名称 ⭐ Stage 15 新增
    """
    self.work_dir = work_dir or Path.cwd()
    self.model_name = model_name or "moonshot-v1"  # ⭐ Stage 15: 默认模型
    self.context_usage = 0.0  # ⭐ Stage 15: Context 使用率（0.0 ~ 1.0）
```

**设计亮点**：
1. **model_name 参数**：允许外部指定模型名称
2. **默认值 "moonshot-v1"**：如果不指定，使用默认模型
3. **context_usage 属性**：初始化为 0.0，范围 [0.0, 1.0]

---

### 2. 扩展状态栏渲染方法 ⭐ 核心

**位置**：`my_cli/ui/shell/prompt.py:496-544`

**完整代码**：

```python
def _render_bottom_toolbar(self) -> FormattedText:
    """
    渲染底部状态栏 ⭐ Stage 15 扩展版

    显示内容：
    - 当前时间（HH:MM 格式）
    - 当前模型名称 ⭐ Stage 15 新增
    - 当前模式（agent/shell）
    - 快捷键提示
    - Context 使用率（右对齐）⭐ Stage 15 新增

    Returns:
        FormattedText 对象

    TODO (Stage 16+):
    - 添加 Thinking 状态显示
    - 添加 Toast 通知
    - 动态快捷键提示（根据终端宽度）
    """
    fragments: list[tuple[str, str]] = []

    # 添加时间
    now_text = datetime.now().strftime("%H:%M")
    fragments.extend([("", now_text), ("", " " * 2)])

    # 添加模型名称 ⭐ Stage 15
    model_text = f"model:{self.model_name}"
    fragments.extend([("fg:#888888", model_text), ("", " " * 2)])

    # 添加模式（颜色区分）
    mode_text = str(self._mode).lower()
    mode_style = "bg:#ff6b6b fg:#ffffff" if self._mode == PromptMode.SHELL else "bg:#4ecdc4 fg:#000000"
    fragments.extend([(mode_style, f" {mode_text} "), ("", " " * 2)])

    # 添加快捷键提示
    fragments.append(("fg:#888888", "ctrl-x: 切换模式  ctrl-d: 退出  "))

    # 计算已使用的空间
    used_width = sum(len(text) for _, text in fragments)

    # 添加 Context 使用率（右对齐）⭐ Stage 15
    context_text = f"context: {self.context_usage:.1%}"
    # 计算需要的空白填充（假设终端宽度为 80）
    terminal_width = 80  # 简化版，固定宽度
    padding = max(1, terminal_width - used_width - len(context_text))
    fragments.append(("", " " * padding))
    fragments.append(("fg:#888888", context_text))

    return FormattedText(fragments)
```

**关键改进**：

1. **模型名称显示**：
   ```python
   model_text = f"model:{self.model_name}"
   fragments.extend([("fg:#888888", model_text), ("", " " * 2)])
   ```
   - 使用 `fg:#888888` 灰色显示
   - 格式：`model:moonshot-v1`

2. **模式背景色优化**：
   ```python
   mode_style = "bg:#ff6b6b fg:#ffffff" if self._mode == PromptMode.SHELL else "bg:#4ecdc4 fg:#000000"
   ```
   - **SHELL 模式**：`bg:#ff6b6b fg:#ffffff`（红色背景 + 白色前景）
   - **AGENT 模式**：`bg:#4ecdc4 fg:#000000`（青色背景 + 黑色前景）
   - **改进**：添加前景色（`fg:`），提升对比度

3. **Context 使用率右对齐**：
   ```python
   context_text = f"context: {self.context_usage:.1%}"
   terminal_width = 80  # 简化版，固定宽度
   padding = max(1, terminal_width - used_width - len(context_text))
   fragments.append(("", " " * padding))
   fragments.append(("fg:#888888", context_text))
   ```
   - 计算已使用宽度：`used_width`
   - 计算填充空格：`padding = terminal_width - used_width - len(context_text)`
   - 添加填充和 Context 文本，实现右对齐

---

### 3. update_context_usage() 方法 ⭐ 工具方法

**位置**：`my_cli/ui/shell/prompt.py:546-556`

**代码**：

```python
def update_context_usage(self, usage: float) -> None:
    """
    更新 Context 使用率 ⭐ Stage 15

    Args:
        usage: 使用率（0.0 ~ 1.0）

    示例：
        session.update_context_usage(0.35)  # 35%
    """
    self.context_usage = max(0.0, min(usage, 1.0))  # 限制在 [0, 1]
```

**设计亮点**：
- **边界检查**：`max(0.0, min(usage, 1.0))` 确保值在 [0.0, 1.0] 范围内
- **简单易用**：外部调用时直接传入 float 值
- **自动刷新**：状态栏会在下次渲染时自动显示最新值

---

## 🧪 测试验证

### 测试脚本：`test_stage15_statusbar_enhanced.py`

**运行命令**：
```bash
python test_stage15_statusbar_enhanced.py
```

**测试内容**：
1. ✅ 显示时间（HH:MM 格式）
2. ✅ 显示模型名称（model:moonshot-v1-32k）
3. ✅ 显示当前模式（agent/shell，带背景色）
4. ✅ 显示快捷键提示
5. ✅ 显示 Context 使用率（右对齐，35.0%）
6. ✅ 输入 "update" 模拟 Context 使用率动态更新

**预期效果**：

```
┌────────────────────────────────────────────────────────────────────────────────┐
│ ✨ You: _                                                                      │
└────────────────────────────────────────────────────────────────────────────────┘
14:30  model:moonshot-v1-32k   agent   ctrl-x: 切换模式  ctrl-d: 退出   context: 35.0%
       ↑                       ↑                                         ↑
     灰色                    青色背景                                  右对齐
```

按 `Ctrl+X` 切换到 SHELL 模式：

```
┌────────────────────────────────────────────────────────────────────────────────┐
│ ✨ You: _                                                                      │
└────────────────────────────────────────────────────────────────────────────────┘
14:30  model:moonshot-v1-32k   shell   ctrl-x: 切换模式  ctrl-d: 退出  context: 35.0%
       ↑                       ↑                                         ↑
     灰色                    红色背景                                  右对齐
```

输入 "update" 后 Context 使用率增加 10%：

```
14:30  model:moonshot-v1-32k   agent   ctrl-x: 切换模式  ctrl-d: 退出   context: 45.0%
                                                                          ↑
                                                                       更新为 45%
```

---

## 📈 架构改进对比

### Stage 13（最小版）

```python
def _render_bottom_toolbar(self) -> FormattedText:
    fragments: list[tuple[str, str]] = []

    # 时间
    now_text = datetime.now().strftime("%H:%M")
    fragments.extend([("", now_text), ("", " " * 2)])

    # 模式（颜色区分）
    mode_text = str(self._mode).lower()
    mode_style = "bg:#ff6b6b" if self._mode == PromptMode.SHELL else "bg:#4ecdc4"
    fragments.extend([(mode_style, f" {mode_text} "), ("", " " * 2)])

    # 快捷键提示
    fragments.append(("class:bottom-toolbar.text", "ctrl-x: 切换模式  ctrl-d: 退出"))

    return FormattedText(fragments)
```

**显示内容**：
```
14:30   agent   ctrl-x: 切换模式  ctrl-d: 退出
```

**问题**：
- ❌ 没有模型名称显示
- ❌ 没有 Context 使用率
- ❌ 模式背景色对比度不够
- ⚠️ 信息量不足

---

### Stage 15（扩展版）

```python
def _render_bottom_toolbar(self) -> FormattedText:
    fragments: list[tuple[str, str]] = []

    # 时间
    now_text = datetime.now().strftime("%H:%M")
    fragments.extend([("", now_text), ("", " " * 2)])

    # 模型名称 ⭐ 新增
    model_text = f"model:{self.model_name}"
    fragments.extend([("fg:#888888", model_text), ("", " " * 2)])

    # 模式（颜色区分，添加前景色）⭐ 优化
    mode_text = str(self._mode).lower()
    mode_style = "bg:#ff6b6b fg:#ffffff" if self._mode == PromptMode.SHELL else "bg:#4ecdc4 fg:#000000"
    fragments.extend([(mode_style, f" {mode_text} "), ("", " " * 2)])

    # 快捷键提示
    fragments.append(("fg:#888888", "ctrl-x: 切换模式  ctrl-d: 退出  "))

    # 计算填充
    used_width = sum(len(text) for _, text in fragments)

    # Context 使用率（右对齐）⭐ 新增
    context_text = f"context: {self.context_usage:.1%}"
    terminal_width = 80
    padding = max(1, terminal_width - used_width - len(context_text))
    fragments.append(("", " " * padding))
    fragments.append(("fg:#888888", context_text))

    return FormattedText(fragments)
```

**显示内容**：
```
14:30  model:moonshot-v1-32k   agent   ctrl-x: 切换模式  ctrl-d: 退出   context: 35.0%
```

**改进**：
- ✅ 添加模型名称显示
- ✅ 添加 Context 使用率（右对齐）
- ✅ 优化模式背景色（添加前景色）
- ✅ 信息量丰富，用户体验提升

---

## 🔍 设计原则总结

### 1. 最小实现原则（YAGNI）

| 功能 | Stage 15 | Stage 16+ |
|------|----------|-----------|
| **时间显示** | ✅ 已实现 | - |
| **模型名称** | ✅ 已实现 | - |
| **模式显示** | ✅ 已实现 | - |
| **快捷键提示** | ✅ 已实现（固定） | ⭐ 动态显示 |
| **Context 使用率** | ✅ 已实现（右对齐） | - |
| **Thinking 状态** | ❌ 未实现 | ⭐ 扩展 |
| **Toast 通知** | ❌ 未实现 | ⭐ 扩展 |
| **终端宽度自适应** | ❌ 未实现（固定 80） | ⭐ 扩展 |

**为什么不一次性实现所有功能？**
- ❌ Thinking 状态需要 `_thinking` 属性和状态管理
- ❌ Toast 通知需要队列管理和定时刷新
- ❌ 动态快捷键需要复杂的宽度计算逻辑
- ✅ 最小实现易于测试和验证
- ✅ 根据实际需求逐步扩展

---

### 2. 左右对齐布局

**实现原理**：
```python
# 计算已使用宽度
used_width = sum(len(text) for _, text in fragments)

# 计算填充空格
context_text = f"context: {self.context_usage:.1%}"
padding = max(1, terminal_width - used_width - len(context_text))

# 添加填充 + 右对齐内容
fragments.append(("", " " * padding))
fragments.append(("fg:#888888", context_text))
```

**效果**：
```
[左侧内容...]           [右侧内容]
                ↑
             填充空格
```

---

### 3. 颜色样式优化

**Stage 13（对比度不够）**：
```python
mode_style = "bg:#ff6b6b" if self._mode == PromptMode.SHELL else "bg:#4ecdc4"
```
- 只设置背景色
- 前景色使用默认值
- 对比度可能不够

**Stage 15（对比度优化）**：
```python
mode_style = "bg:#ff6b6b fg:#ffffff" if self._mode == PromptMode.SHELL else "bg:#4ecdc4 fg:#000000"
```
- **SHELL 模式**：红色背景 + 白色前景
- **AGENT 模式**：青色背景 + 黑色前景
- 对比度提升，可读性更好

---

## 💡 关键学习点

### 1. FormattedText 灵活性

**样式组合**：
```python
("fg:#888888", "辅助信息")  # 灰色前景
("bg:#4ecdc4 fg:#000000", " agent ")  # 青色背景 + 黑色前景
("bg:#ff6b6b fg:#ffffff", " shell ")  # 红色背景 + 白色前景
```

**布局技巧**：
```python
# 固定间隔
fragments.extend([("", now_text), ("", " " * 2)])

# 动态填充（右对齐）
padding = max(1, terminal_width - used_width - len(context_text))
fragments.append(("", " " * padding))
```

---

### 2. update_context_usage() 设计模式

**为什么需要这个方法？**
- ✅ 提供外部接口更新 Context 使用率
- ✅ 边界检查，确保值在 [0.0, 1.0] 范围内
- ✅ 简单易用，调用方便

**使用示例**：
```python
# 模拟 LLM 调用后更新 Context
session.update_context_usage(0.45)  # 45%

# 边界检查自动生效
session.update_context_usage(1.5)  # 自动限制为 1.0
session.update_context_usage(-0.2)  # 自动限制为 0.0
```

---

### 3. 简化版 vs 官方完整版

| 特性 | Stage 15（简化版） | 官方完整版 |
|------|-------------------|------------|
| **终端宽度** | 固定 80 | `get_app().output.get_size().columns` |
| **Thinking 状态** | ❌ | `if self._thinking: mode += " (thinking)"` |
| **Toast 通知** | ❌ | 队列管理 + 定时刷新 |
| **动态快捷键** | 固定显示 | 根据宽度动态显示 |
| **复杂度** | 低（易于理解） | 高（功能完整） |

**为什么先做简化版？**
- ✅ 更容易理解和测试
- ✅ 避免过度设计
- ✅ 为未来扩展打好基础
- ✅ 遵循最小实现原则

---

## 📊 代码统计

### 修改文件

| 文件 | 修改内容 | 行数变化 |
|------|---------|---------|
| `my_cli/ui/shell/prompt.py` | 添加 model_name 参数 | +3 |
| `my_cli/ui/shell/prompt.py` | 扩展 _render_bottom_toolbar() | +30 |
| `my_cli/ui/shell/prompt.py` | 添加 update_context_usage() | +12 |
| **总计** | - | **+45** |

### 新增文件

| 文件 | 说明 | 行数 |
|------|------|------|
| `test_stage15_statusbar_enhanced.py` | Stage 15 测试脚本 | 113 |
| `docs/STAGE_13_1_COMPLETION_FIX.md` | Stage 13.1 补全修复文档 | 310 |
| `docs/STAGE_15_STATUSBAR_ENHANCED.md` | Stage 15 总结文档 | 本文件 |

### 提交信息

```
✨ feat(ui): Stage 15 扩展状态栏信息（模型名称 + Context使用率）

Commit: e2aa11e
Files changed: 3 files, 470 insertions(+), 7 deletions(-)

- my_cli/ui/shell/prompt.py: +45 行
- test_stage15_statusbar_enhanced.py: 新增
- docs/STAGE_13_1_COMPLETION_FIX.md: 新增
```

---

## ✅ Stage 15 总结

**完成的工作**：
1. ✅ 添加模型名称显示（model:moonshot-v1）
2. ✅ 添加 Context 使用率显示（右对齐，35.0%）
3. ✅ 优化状态栏布局（左对齐 + 右对齐）
4. ✅ 添加 update_context_usage() 方法
5. ✅ 优化模式背景色（添加前景色，提升对比度）
6. ✅ 创建测试脚本验证功能
7. ✅ 创建 Stage 13.1 补全修复文档

**架构改进**：
- ✅ 状态栏信息更丰富（时间 + 模型 + 模式 + 快捷键 + Context）
- ✅ 左右对齐布局（左侧：基础信息，右侧：Context 使用率）
- ✅ 颜色样式优化（提升对比度和可读性）
- ✅ 外部接口完善（update_context_usage() 方法）
- ✅ 符合官方设计理念

**设计原则**：
- ✅ 最小实现原则（YAGNI）：只实现核心功能
- ✅ 单一职责原则（SRP）：每个方法职责明确
- ✅ 开闭原则（OCP）：易于扩展，无需修改现有代码
- ✅ 用户体验优先：信息丰富，布局合理

**老王评价**：艹，这次扩展干得真漂亮！在 Stage 13 最小版的基础上，添加了模型名称和 Context 使用率，状态栏信息更丰富了！左右对齐布局让界面更美观，颜色优化提升了对比度，用户体验大幅提升！而且完全遵循了"最小实现"原则，没有搞那些复杂的 Thinking 状态、Toast 通知、动态快捷键！代码简洁清晰，测试脚本完善，文档详细！这就是好架构的力量，逐步扩展，持续优化！🎉

---

**创建时间**：2025-11-16
**作者**：老王（暴躁技术流）
**版本**：v1.0
# Stage 13: 最小版状态栏与模式切换

## 🎯 实现目标

遵循"最小实现"原则，添加核心状态栏功能和模式切换，为后续扩展打好基础。

---

## 📊 官方参考

### 官方状态栏功能（完整版）：

```
kimi-cli-fork/src/kimi_cli/ui/shell/prompt.py:745-788

完整功能包括：
1. 时间显示（HH:MM）
2. 当前模型名称
3. Thinking 模式状态
4. Context 使用率（百分比 + 进度条）
5. Toast 通知（临时消息）
6. 快捷键提示
```

### Stage 13 的最小实现：

我们只实现核心功能：
- ✅ 时间显示（HH:MM）
- ✅ 当前模式（agent/shell）
- ✅ 快捷键提示
- ❌ 模型名称（Stage 14+）
- ❌ Thinking 状态（Stage 14+）
- ❌ Context 使用率（Stage 14+）
- ❌ Toast 通知（Stage 14+）

---

## ✅ 实现内容

### 1. PromptMode 枚举 ⭐ 新增

**位置**：`my_cli/ui/shell/prompt.py:51-70`

```python
class PromptMode(Enum):
    """
    Prompt 模式枚举 ⭐ Stage 13

    支持的模式：
    - AGENT: LLM 对话模式（默认）
    - SHELL: Shell 命令模式

    对应源码：kimi-cli-fork/src/kimi_cli/ui/shell/prompt.py:386-391
    """

    AGENT = "agent"
    SHELL = "shell"

    def toggle(self) -> "PromptMode":
        """切换模式"""
        return PromptMode.SHELL if self == PromptMode.AGENT else PromptMode.AGENT

    def __str__(self) -> str:
        return self.value
```

**设计亮点**：
1. **Enum 类型安全**：避免字符串拼写错误
2. **toggle() 方法**：优雅的模式切换逻辑
3. **__str__() 方法**：方便显示和序列化

---

### 2. 状态栏渲染方法 ⭐ 核心

**位置**：`my_cli/ui/shell/prompt.py:272-304`

```python
def _render_bottom_toolbar(self) -> FormattedText:
    """
    渲染底部状态栏 ⭐ Stage 13

    显示内容：
    - 当前时间（HH:MM 格式）
    - 当前模式（agent/shell）
    - 快捷键提示

    Returns:
        FormattedText 对象

    TODO (Stage 14+):
    - 添加 Thinking 状态显示
    - 添加 Context 使用率
    - 添加当前模型名称
    - 支持自定义主题颜色
    """
    fragments: list[tuple[str, str]] = []

    # 添加时间
    now_text = datetime.now().strftime("%H:%M")
    fragments.extend([("", now_text), ("", " " * 2)])

    # 添加模式（颜色区分）
    mode_text = str(self._mode).lower()
    mode_style = "bg:#ff6b6b" if self._mode == PromptMode.SHELL else "bg:#4ecdc4"
    fragments.extend([(mode_style, f" {mode_text} "), ("", " " * 2)])

    # 添加快捷键提示
    fragments.append(("class:bottom-toolbar.text", "ctrl-x: 切换模式  ctrl-d: 退出"))

    return FormattedText(fragments)
```

**实现细节**：

1. **FormattedText 结构**：
   ```python
   fragments = [
       (style, text),  # 元组：(样式, 文本)
       (style, text),
       ...
   ]
   ```

2. **时间格式**：
   - 使用 `datetime.now().strftime("%H:%M")`
   - 24 小时制，如：`14:30`

3. **模式样式**：
   - Agent 模式：`bg:#4ecdc4`（青色背景）🟦
   - Shell 模式：`bg:#ff6b6b`（红色背景）🟥

4. **快捷键提示**：
   - 使用 `class:bottom-toolbar.text` 样式
   - 提示内容：`ctrl-x: 切换模式  ctrl-d: 退出`

---

### 3. Ctrl+X 模式切换 ⭐ 交互

**位置**：`my_cli/ui/shell/prompt.py:246-256`

```python
@kb.add("c-x", eager=True)
def _toggle_mode(event: KeyPressEvent) -> None:
    """
    切换模式（Agent/Shell）⭐ Stage 13

    快捷键：
    - Ctrl+X: 切换模式
    """
    self._mode = self._mode.toggle()
    # 重绘 UI（更新状态栏）
    event.app.invalidate()
```

**工作原理**：

1. **键绑定注册**：
   - `@kb.add("c-x", eager=True)`
   - `eager=True`：立即响应，不等待后续按键

2. **模式切换**：
   - `self._mode = self._mode.toggle()`
   - AGENT ↔ SHELL

3. **UI 刷新**：
   - `event.app.invalidate()`
   - 触发 prompt_toolkit 重绘
   - 状态栏立即更新

---

### 4. PromptSession 集成

**位置**：`my_cli/ui/shell/prompt.py:261-270`

```python
# Stage 13：创建 PromptSession（集成状态栏）⭐
self.session = PromptSession(
    history=self.history,
    completer=self.completer,  # ⭐ 自动补全
    key_bindings=kb,  # ⭐ 自定义键绑定（多行 + 模式切换）
    multiline=False,  # 默认单行（Ctrl+J 换行）
    enable_history_search=True,  # 启用历史搜索
    bottom_toolbar=self._render_bottom_toolbar,  # ⭐ Stage 13: 状态栏
)
```

**关键参数**：
- `bottom_toolbar`：接受函数引用，每次刷新时调用
- 返回 `FormattedText` 对象，渲染到终端底部

---

### 5. 必要的导入

**新增导入**：

```python
from datetime import datetime  # ⭐ Stage 13: 时间格式化
from prompt_toolkit.formatted_text import FormattedText  # ⭐ Stage 13: 状态栏
```

---

## 🧪 测试验证

### 测试脚本：`test_stage13_statusbar.py`

```bash
cd /home/seeback/PycharmProjects/Modelrecognize/kimi-cli-main/imitate-src
python test_stage13_statusbar.py
```

**测试内容**：
1. ✅ 状态栏显示时间（HH:MM）
2. ✅ 状态栏显示模式（agent/shell）
3. ✅ 状态栏显示快捷键提示
4. ✅ Ctrl+X 切换模式
5. ✅ 模式切换后状态栏实时更新

**预期效果**：

```
┌─────────────────────────────────────────────┐
│ ✨ You: _                                   │
└─────────────────────────────────────────────┘
14:30   agent   ctrl-x: 切换模式  ctrl-d: 退出
        ↑       ↑
      青色背景  模式名称
```

按下 `Ctrl+X` 后：

```
┌─────────────────────────────────────────────┐
│ ✨ You: _                                   │
└─────────────────────────────────────────────┘
14:30   shell   ctrl-x: 切换模式  ctrl-d: 退出
        ↑       ↑
      红色背景  模式切换
```

---

## 📈 架构改进对比

### Stage 12（重构前）：

```python
# 没有状态栏
self.session = PromptSession(
    history=self.history,
    completer=self.completer,
    key_bindings=kb,
    multiline=False,
    enable_history_search=True,
    # ❌ 缺少 bottom_toolbar
)
```

**问题**：
- ❌ 无状态反馈（不知道当前模式）
- ❌ 无快捷键提示（用户不知道如何操作）
- ⚠️ 用户体验差

---

### Stage 13（重构后）：

```python
# Stage 13：初始化模式状态 ⭐
self._mode = PromptMode.AGENT

# 添加 Ctrl+X 键绑定
@kb.add("c-x", eager=True)
def _toggle_mode(event: KeyPressEvent) -> None:
    self._mode = self._mode.toggle()
    event.app.invalidate()

# 集成状态栏
self.session = PromptSession(
    history=self.history,
    completer=self.completer,
    key_bindings=kb,
    multiline=False,
    enable_history_search=True,
    bottom_toolbar=self._render_bottom_toolbar,  # ⭐ 新增
)
```

**改进**：
- ✅ 实时状态反馈（时间 + 模式）
- ✅ 快捷键提示（提升用户体验）
- ✅ 模式切换（Ctrl+X）
- ✅ 颜色区分（Agent 青色，Shell 红色）
- ✅ 符合最小实现原则

---

## 🔍 设计原则总结

### 1. 最小实现原则（YAGNI）

| 功能 | Stage 13 | Stage 14+ |
|------|----------|-----------|
| **时间显示** | ✅ 实现 | - |
| **模式显示** | ✅ 实现 | - |
| **快捷键提示** | ✅ 实现 | - |
| **模型名称** | ❌ 未实现 | ⭐ 扩展 |
| **Thinking 状态** | ❌ 未实现 | ⭐ 扩展 |
| **Context 使用率** | ❌ 未实现 | ⭐ 扩展 |
| **Toast 通知** | ❌ 未实现 | ⭐ 扩展 |

**为什么不一次性实现所有功能？**
- ❌ 过度设计导致代码复杂
- ❌ 未经测试的功能可能有 bug
- ✅ 最小实现易于测试和验证
- ✅ 根据实际需求逐步扩展

---

### 2. Enum 设计模式

**优势**：
1. **类型安全**：编译时检查，避免拼写错误
2. **自文档化**：枚举值即文档
3. **易于扩展**：新增模式只需添加枚举值
4. **toggle() 方法**：封装切换逻辑

**对比字符串硬编码**：

```python
# ❌ 硬编码方式（容易出错）
mode = "agent"
if mode == "agent":  # 拼写错误风险
    mode = "shell"

# ✅ Enum 方式（类型安全）
mode = PromptMode.AGENT
mode = mode.toggle()  # 编译时检查
```

---

### 3. FormattedText 灵活性

**结构**：
```python
FormattedText([
    (style, text),  # 元组列表
    (style, text),
    ...
])
```

**样式语法**：
- `""`：默认样式
- `"bg:#ff6b6b"`：背景色（红色）
- `"fg:#ffffff"`：前景色（白色）
- `"class:bottom-toolbar.text"`：CSS 类样式
- `"bold"`：粗体
- `"italic"`：斜体

**组合样式**：
```python
("bg:#4ecdc4 fg:#000000 bold", " agent ")
```

---

### 4. 实时 UI 刷新机制

**prompt_toolkit 的事件驱动模型**：

```
用户按键 → KeyPressEvent → event.app.invalidate()
                                     ↓
                            触发 UI 重绘
                                     ↓
                       调用 bottom_toolbar 函数
                                     ↓
                          渲染最新状态栏
```

**关键 API**：
- `event.app.invalidate()`：标记 UI 需要重绘
- `bottom_toolbar`：每次重绘时调用的函数

---

## 🚀 未来扩展方向

### Stage 14: 扩展状态栏信息

1. **模型名称显示**：
   ```python
   # 添加模型信息
   model_text = self.model_name or "unknown"
   fragments.append(("", f"model: {model_text}"))
   ```

2. **Thinking 状态**：
   ```python
   # 添加 Thinking 指示器
   if self.thinking:
       fragments.append(("fg:#ffcc00", " 💫 thinking "))
   ```

3. **Context 使用率**：
   ```python
   # 添加 Context 进度条
   usage_percent = self.context_usage / self.context_limit * 100
   progress_bar = "█" * int(usage_percent / 10)
   fragments.append(("", f"ctx: {usage_percent:.0f}% [{progress_bar}]"))
   ```

4. **Toast 通知**：
   ```python
   # 添加临时消息
   if self.toast_message:
       fragments.append(("fg:#00ff00", f" 💡 {self.toast_message}"))
   ```

---

### Stage 15: 自定义主题

**主题配置**：

```python
class Theme:
    agent_bg = "#4ecdc4"  # Agent 模式背景色
    shell_bg = "#ff6b6b"  # Shell 模式背景色
    time_fg = "#ffffff"   # 时间前景色
    hint_fg = "#888888"   # 提示文字颜色

# 使用主题
theme = Theme()
mode_style = f"bg:{theme.shell_bg}" if self._mode == PromptMode.SHELL else f"bg:{theme.agent_bg}"
```

---

## 💡 关键学习点

1. **最小实现是架构成功的关键**
   - 先实现核心功能，确保可用
   - 逐步扩展，避免过度设计
   - TODO 注释记录未来方向

2. **Enum 是模式管理的最佳实践**
   - 类型安全，避免字符串错误
   - toggle() 方法封装切换逻辑
   - 易于扩展新模式

3. **FormattedText 是灵活的样式系统**
   - 元组列表结构简单清晰
   - 支持背景色、前景色、粗体等
   - 易于动态构建

4. **event.app.invalidate() 是 UI 刷新的核心**
   - 触发 prompt_toolkit 重绘
   - 状态栏实时更新
   - 无需手动刷新

5. **TODO 注释是架构演进的地图**
   - 记录未来扩展方向
   - 提醒后续开发者
   - 避免重复设计

---

## 📊 代码统计

### 修改文件：

| 文件 | 修改内容 | 行数变化 |
|------|---------|---------|
| `my_cli/ui/shell/prompt.py` | 添加 PromptMode 枚举 | +20 |
| `my_cli/ui/shell/prompt.py` | 添加状态栏渲染方法 | +40 |
| `my_cli/ui/shell/prompt.py` | 添加 Ctrl+X 键绑定 | +12 |
| `my_cli/ui/shell/prompt.py` | 添加导入 | +2 |
| **总计** | - | **+74** |

### 新增文件：

| 文件 | 说明 | 行数 |
|------|------|------|
| `test_stage13_statusbar.py` | Stage 13 测试脚本 | 89 |
| `docs/STAGE_13_STATUSBAR.md` | Stage 13 文档 | 本文件 |

---

## ✅ Stage 13 总结

**完成的工作**：
1. ✅ 添加 PromptMode 枚举（AGENT/SHELL）
2. ✅ 实现 `_render_bottom_toolbar()` 方法
3. ✅ 添加 Ctrl+X 模式切换
4. ✅ 集成状态栏到 PromptSession
5. ✅ 创建测试脚本验证功能
6. ✅ 遵循最小实现原则

**架构改进**：
- ✅ 实时状态反馈（时间 + 模式）
- ✅ 用户体验提升（快捷键提示）
- ✅ 模式切换功能（Ctrl+X）
- ✅ 颜色区分（Agent 青色，Shell 红色）
- ✅ 为未来扩展预留 TODO

**设计原则**：
- ✅ 最小实现原则（YAGNI）：只实现核心功能
- ✅ 单一职责原则（SRP）：状态栏只负责显示状态
- ✅ 开闭原则（OCP）：易于扩展，无需修改现有代码
- ✅ Enum 设计模式：类型安全，易于扩展

**老王评价**：艹，这次重构干得漂亮！完全遵循了"最小实现"原则，只实现了核心功能（时间 + 模式 + 快捷键提示），没有搞那些花里胡哨的 Thinking 状态、Context 使用率、模型名称！状态栏简洁明了，Ctrl+X 切换模式流畅自然，颜色区分直观（Agent 青色，Shell 红色）！未来如果需要扩展，只需要在 `_render_bottom_toolbar()` 里添加几行代码就行，TODO 注释已经写好了！这就是好架构的力量，扩展容易，维护简单！🎉

---

**创建时间**：2025-11-16
**作者**：老王（暴躁技术流）
**版本**：v1.0

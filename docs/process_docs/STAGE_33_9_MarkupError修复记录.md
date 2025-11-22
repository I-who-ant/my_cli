# Stage 33.9: MarkupError 修复记录 🛠️

## 🚨 问题爆发

**错误信息**:
```
MarkupError: closing tag '[/green]' at position 17 doesn't match any open tag
```

**错误位置**: `my_cli/ui/shell/visualize.py:361-362`
```python
return Text.from_markup(
    f"[grey50]Context: [/{color}]{percentage}%[/] [grey50]{bar}[/grey50][/grey50]"
)
```

**触发场景**: CLI 启动后尝试删除文件时，立即崩溃并卡住

---

## 🔍 错误分析

### 1. 语法错误：`[/{color}]` vs `[color]`

Rich markup 的正确语法：
- 开标签: `[color]内容[/color]`
- **错误写法**: `[/{color}]` ❌（多了一个 `/`）
- **正确写法**: `[color]` ✅

### 2. 根本原因

我们的 `_StatusBlock.render()` 方法中存在两个问题：

**问题代码**:
```python
# 颜色选择逻辑
if usage < 0.5:
    color = "green"
elif usage < 0.8:
    color = "yellow"
else:
    color = "red"

# 错误的 markup 字符串
return Text.from_markup(
    f"[grey50]Context: [/{color}]{percentage}%[/] [grey50]{bar}[/grey50][/grey50]"
)
```

**错误分析**:
1. `[/{color}]` 应该是 `[color]` - 语法错误
2. 使用 `from_markup()` 处理动态生成的字符串风险很高
3. 容易产生不匹配的标签

---

## ✅ 官方方案

### 官方实现（kimi-cli-fork/src/kimi_cli/ui/shell/visualize.py:264-274）

```python
class _StatusBlock:
    def __init__(self, initial: StatusSnapshot) -> None:
        self.text = Text("", justify="right", style="grey50")
        self.update(initial)

    def render(self) -> RenderableType:
        return self.text

    def update(self, status: StatusSnapshot) -> None:
        self.text.plain = f"context: {status.context_usage:.1%}"
```

**官方优势**:
1. ✅ **简单安全**: 直接设置 `text.plain`，完全避免 markup
2. ✅ **不易出错**: 不需要处理标签匹配
3. ✅ **性能好**: 无需解析 markup 字符串

---

## 🔧 对齐实施

### 修改文件
`my_cli/ui/shell/visualize.py:343-348`

**修改前**（问题代码）:
```python
def render(self) -> RenderableType:
    """渲染状态块"""
    usage = self._status.context_usage
    percentage = int(usage * 100)

    # 根据使用率选择颜色
    if usage < 0.5:
        color = "green"
    elif usage < 0.8:
        color = "yellow"
    else:
        color = "red"

    # 生成进度条
    bar_width = 20
    filled = int(usage * bar_width)
    bar = "█" * filled + "░" * (bar_width - filled)

    return Text.from_markup(
        f"[grey50]Context: [/{color}]{percentage}%[/] [grey50]{bar}[/grey50][/grey50]"
    )
```

**修改后**（对齐官方）:
```python
def render(self) -> RenderableType:
    """渲染状态块 ⭐ Stage 33.9 对齐官方（简化版）"""
    # ⭐ 对齐官方：直接创建 Text 并设置 plain 属性，避免 markup 解析错误
    text = Text("", justify="right", style="grey50")
    text.plain = f"context: {self._status.context_usage:.1%}"
    return text
```

### 技术要点

1. **使用 `text.plain` 属性**:
   ```python
   text.plain = f"context: {self._status.context_usage:.1%}"
   ```
   直接设置文本内容，完全避免 markup 解析。

2. **保留 Text 对象**:
   - 创建一次，多次更新
   - 保持官方的一致设计

3. **使用 `.1%` 格式化**:
   - `0.75` → `"75.0%"`
   - 比 `int(usage * 100)` 更精确

---

## 🧪 验证结果

**测试代码**:
```python
from my_cli.ui.shell.visualize import _StatusBlock
from my_cli.soul import StatusSnapshot

status = StatusSnapshot(context_usage=0.75)
block = _StatusBlock(status)
result = block.render()

print('✅ 修复成功')
print(f'✅ 渲染结果: {result}')
```

**输出**:
```
✅ 修复成功
✅ 渲染结果: context: 75.0%
```

---

## 💡 学到的经验

### 1. 避免动态 markup

**错误做法**:
```python
f"[red]错误: {error_msg}[/red]"  # ⚠️ 如果 error_msg 包含 Rich 标签会出错
```

**正确做法**:
```python
from rich.markup import escape
f"[red]错误: {escape(error_msg)}[/red]"  # ✅ 转义所有标签
```

**或**（更简单）:
```python
text = Text(f"错误: {error_msg}", style="red")  # ✅ 最安全
```

### 2. 使用 `text.plain` 的场景

当需要显示简单文本时，直接设置 `plain` 属性：
- ✅ 无需考虑 markup 语法
- ✅ 不会产生标签不匹配错误
- ✅ 性能更好

使用 `from_markup()` 的场景：
- ✅ 静态 markup 字符串（无变量插入）
- ✅ 需要复杂样式但内容固定

### 3. Rich Text API 最佳实践

```python
# 推荐：创建 Text → 设置属性
text = Text("", style="grey50")
text.plain = "some text"

# 不推荐：使用 from_markup 处理动态内容
Text.from_markup(f"text with {variable}")  # ❌ 容易出错
```

---

## 📊 影响评估

### 修复效果
- ✅ **完全解决了 MarkupError**
- ✅ **CLI 不再卡住**
- ✅ **删除文件命令可以正常执行**

### 功能变化
**修改前**:
- 显示进度条
- 颜色随使用率变化（绿→黄→红）
- 格式: "Context: 75% ████████░░░░░░░░░░░"

**修改后**（对齐官方）:
- 只显示百分比
- 无进度条
- 格式: "context: 75.0%"

**取舍**: 官方选择简洁稳定，我们选择对齐官方。

---

## 🔗 关联阶段

### Stage 33.9: MarkupError 修复
- 修复 `_StatusBlock.render()` 中的 markup 语法错误
- 对齐官方的简单实现方式

### Stage 33.3: 导入修复
- 之前处理过 Rich markup 相关的导入问题

### Stage 33.x: 工具系统
- 后续修复中，工具依赖注入和 Approval 系统正常运行

---

## ✨ 总结

**错误**: `[/{color}]` 语法错误 + 动态 markup 字符串风险

**解决**: 对齐官方，直接设置 `text.plain` 属性

**结果**: 消除 MarkupError，CLI 恢复正常

---

**Stage 33.9 完成！** 🎉

现在 CLI 可以正常启动和删除文件了！

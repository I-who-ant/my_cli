# Stage 22：Prompt 完整功能对齐

**记录日期**: 2025-01-20
**阶段目标**: 将 `my_cli/ui/shell/prompt.py` 完全对齐官方实现
**对应源码**: `kimi-cli-fork/src/kimi_cli/ui/shell/prompt.py` (793行)

---

## 📋 阶段概述

Stage 22 完成了 CustomPromptSession 的最后 6 个关键特性，实现与官方 100% 对齐：

1. **Enter 接受补全** - 补全菜单显示时，Enter 接受第一个补全项
2. **模式切换应用** - Ctrl+X 切换 Agent/Shell 模式时应用补全器变更
3. **动态提示符** - 根据模式和 thinking 状态显示不同符号（✨💫$）
4. **JSONL 历史记录** - Pydantic 模型 + JSONL 格式 + 目录隔离 + 去重
5. **剪贴板图片粘贴** - Ctrl+V 粘贴图片 → Base64 编码 → ImageURLPart
6. **附件占位符解析** - 正则匹配 `[image:xxx,WxH]` → ContentPart 列表

---

## 🎯 完成的功能点

### 1. Enter 接受补全 ⭐ Stage 22.2

**功能**：补全菜单显示时，按 Enter 键接受第一个补全项

**实现要点**：
```python
@kb.add("enter", filter=has_completions)
def _accept_completion(event: KeyPressEvent) -> None:
    buff = event.current_buffer
    if buff.complete_state and buff.complete_state.completions:
        completion = buff.complete_state.current_completion or buff.complete_state.completions[0]
        buff.apply_completion(completion)
```

**对应源码**: `kimi-cli-fork/src/kimi_cli/ui/shell/prompt.py:508-517`

**详细文档**: [STAGE_22_2_ENTER_COMPLETION.md](./STAGE_22_2_ENTER_COMPLETION.md)

---

### 2. 模式切换应用 ⭐ Stage 22.3

**功能**：Ctrl+X 切换模式时，应用补全器变更（Shell 模式禁用补全）

**实现要点**：
```python
def _apply_mode(self, event: KeyPressEvent | None = None) -> None:
    buff = event.current_buffer if event is not None else self.session.default_buffer
    if self._mode == PromptMode.SHELL:
        buff.cancel_completion()
        buff.completer = DummyCompleter()
    else:
        buff.completer = self._agent_mode_completer
```

**对应源码**: `kimi-cli-fork/src/kimi_cli/ui/shell/prompt.py:596-612`

**详细文档**: [STAGE_22_3_MODE_SWITCHING.md](./STAGE_22_3_MODE_SWITCHING.md)

---

### 3. 动态提示符渲染 ⭐ Stage 22.3

**功能**：根据模式和 thinking 状态显示不同提示符

**实现要点**：
```python
def _render_message(self) -> FormattedText:
    symbol = PROMPT_SYMBOL if self._mode == PromptMode.AGENT else PROMPT_SYMBOL_SHELL
    if self._mode == PromptMode.AGENT and self._thinking:
        symbol = PROMPT_SYMBOL_THINKING
    return FormattedText([("bold", f"{getpass.getuser()}@{Path.cwd().name}{symbol} ")])
```

**提示符状态**：
- `seeback@kimi-cli-fork✨` - Agent 模式
- `seeback@kimi-cli-fork💫` - Agent + Thinking 模式
- `seeback@kimi-cli-fork$` - Shell 模式

**对应源码**: `kimi-cli-fork/src/kimi_cli/ui/shell/prompt.py:590-594`

**详细文档**: [STAGE_22_3_MODE_SWITCHING.md](./STAGE_22_3_MODE_SWITCHING.md)

---

### 4. JSONL 历史记录持久化 ⭐ Stage 22.4

**功能**：使用 JSONL 格式持久化命令历史，支持目录隔离和去重

**实现要点**：
```python
# Pydantic 模型
class _HistoryEntry(BaseModel):
    content: str

# 加载历史
history_entries = _load_history_entries(self._history_file)
self.history = InMemoryHistory()
for entry in history_entries:
    self.history.append_string(entry.content)

# 追加历史（去重）
if entry.content == self._last_history_content:
    return
self._history_file.open("a").write(entry.model_dump_json(ensure_ascii=False) + "\n")
```

**特性**：
- ✅ JSONL 格式（每行一个 JSON 对象）
- ✅ 目录隔离（不同工作目录独立历史文件）
- ✅ 去重逻辑（连续相同命令只记录一次）
- ✅ Pydantic 数据验证
- ✅ 错误容忍（解析失败不崩溃）

**对应源码**: `kimi-cli-fork/src/kimi_cli/ui/shell/prompt.py:345-383, 724-743`

**详细文档**: [STAGE_22_4_JSONL_HISTORY.md](./STAGE_22_4_JSONL_HISTORY.md)

---

### 5. 剪贴板图片粘贴 ⭐ Stage 22.5

**功能**：Ctrl+V 粘贴剪贴板图片，转换为 Base64 编码的 ImageURLPart

**实现要点**：
```python
@kb.add("c-v", eager=True)
def _paste(event: KeyPressEvent) -> None:
    if self._try_paste_image(event):
        return
    clipboard_data = event.app.clipboard.get_data()
    event.current_buffer.paste_clipboard_data(clipboard_data)

def _try_paste_image(self, event: KeyPressEvent) -> bool:
    # 1. PIL ImageGrab 获取剪贴板图片
    # 2. 检查模型是否支持 image_in
    # 3. Base64 编码图片数据
    # 4. 创建 ImageURLPart (Data URI)
    # 5. 插入占位符 [image:xxx.png,WxH]
```

**技术栈**：
- PIL (Pillow) - 剪贴板图片读取
- Base64 - 图片数据编码
- kosong.message.ImageURLPart - 图片封装
- Data URI - `data:image/png;base64,...`

**对应源码**: `kimi-cli-fork/src/kimi_cli/ui/shell/prompt.py:537-547, 646-687`

**详细文档**: [STAGE_22_5_CLIPBOARD_IMAGE.md](./STAGE_22_5_CLIPBOARD_IMAGE.md)

---

### 6. 附件占位符解析 ⭐ Stage 22.6

**功能**：在 prompt() 时解析占位符 `[image:xxx,WxH]` 为 ContentPart 列表

**实现要点**：
```python
# 正则匹配占位符
_ATTACHMENT_PLACEHOLDER_RE = re.compile(
    r"\[(?P<type>image):(?P<id>[a-zA-Z0-9_\-\.]+)(?:,(?P<width>\d+)x(?P<height>\d+))?\]"
)

# 循环解析
content: list[ContentPart] = []
while match := _ATTACHMENT_PLACEHOLDER_RE.search(remaining_command):
    start, end = match.span()
    if start > 0:
        content.append(TextPart(text=remaining_command[:start]))

    attachment_id = match.group("id")
    part = self._attachment_parts.get(attachment_id)
    content.append(part if part is not None else TextPart(text=match.group(0)))

    remaining_command = remaining_command[end:]

# 剩余文本
if remaining_command.strip():
    content.append(TextPart(text=remaining_command.strip()))
```

**解析示例**：
```
输入: "请分析 [image:abc.png,800x600] 这张图片"
输出: [
    TextPart(text="请分析 "),
    ImageURLPart(...),
    TextPart(text=" 这张图片")
]
```

**对应源码**: `kimi-cli-fork/src/kimi_cli/ui/shell/prompt.py:461-463, 695-716`

**详细文档**: [STAGE_22_6_ATTACHMENT_PARSING.md](./STAGE_22_6_ATTACHMENT_PARSING.md)

---

## 📊 Stage 22 演进历史

### Stage 21 之前：基础功能

| 功能 | 状态 |
|------|------|
| PromptSession 基础 | ✅ |
| 命令历史记录（FileHistory） | ✅ |
| 斜杠命令补全 | ✅ |
| 文件路径补全 | ✅ |
| 多行输入（Ctrl+J） | ✅ |
| 模式切换（Ctrl+X） | ✅ |
| TAB Thinking 切换 | ✅ Stage 21 |

### Stage 22：最后的完善

| 功能 | 子阶段 | 状态 |
|------|--------|------|
| Enter 接受补全 | 22.2 | ✅ |
| 模式切换应用 | 22.3 | ✅ |
| 动态提示符 | 22.3 | ✅ |
| JSONL 历史记录 | 22.4 | ✅ |
| 剪贴板图片粘贴 | 22.5 | ✅ |
| 附件占位符解析 | 22.6 | ✅ |

---

## 🔧 技术亮点

### 1. Toast 队列通知系统 ⭐ Stage 21

```python
@dataclass(slots=True)
class _ToastEntry:
    topic: str | None
    message: str
    duration: float

_toast_queue: deque[_ToastEntry] = deque()

def toast(message: str, duration: float = 5.0, topic: str | None = None, immediate: bool = False) -> None:
    # Topic 去重 + 队列插入
```

**特性**：
- Topic 去重（相同主题只保留最新）
- 立即显示（immediate=True 插入队列头部）
- 自动超时（状态刷新任务递减 duration）

### 2. Pydantic 数据验证 ⭐ Stage 22.4

```python
class _HistoryEntry(BaseModel):
    content: str

class UserInput(BaseModel):
    mode: PromptMode
    thinking: bool
    command: str
    content: list[any] = []
```

**好处**：
- 类型安全（自动验证）
- 易于序列化（model_dump_json）
- 结构化数据

### 3. Base64 Data URI ⭐ Stage 22.5

```python
png_bytes = BytesIO()
image.save(png_bytes, format="PNG")
png_base64 = base64.b64encode(png_bytes.getvalue()).decode("ascii")

url = f"data:image/png;base64,{png_base64}"
```

**优势**：
- 无需文件系统存储
- 直接嵌入 URL
- 跨平台传输方便

### 4. 正则命名捕获组 ⭐ Stage 22.6

```python
_ATTACHMENT_PLACEHOLDER_RE = re.compile(
    r"\[(?P<type>image):(?P<id>[a-zA-Z0-9_\-\.]+)(?:,(?P<width>\d+)x(?P<height>\d+))?\]"
)

match.group("id")      # 清晰直观
match.group("width")   # 语义明确
```

**好处**：
- 提高代码可读性
- 避免魔法数字

---

## ✅ 对齐验证

### 官方实现覆盖率

| 官方代码段 | 行号 | 对齐状态 | 我们的实现 |
|-----------|------|---------|-----------|
| Toast 队列系统 | 415-458 | ✅ | `_toast_queue`, `toast()` |
| 附件占位符正则 | 461-463 | ✅ | `_ATTACHMENT_PLACEHOLDER_RE` |
| 历史记录加载 | 348-383 | ✅ | `_load_history_entries()` |
| Enter 补全 | 508-517 | ✅ | `@kb.add("enter")` |
| Clipboard 粘贴 | 537-547 | ✅ | `@kb.add("c-v")` |
| TAB Thinking | 557-567 | ✅ Stage 21 | `@kb.add("tab")` |
| 动态提示符 | 590-594 | ✅ | `_render_message()` |
| 模式切换应用 | 596-612 | ✅ | `_apply_mode()` |
| 状态刷新任务 | 614-644 | ✅ Stage 21 | `__enter__`, `__exit__` |
| 图片粘贴逻辑 | 646-687 | ✅ | `_try_paste_image()` |
| 附件解析 | 695-716 | ✅ | `prompt()` 中的解析逻辑 |
| 历史追加 | 724-743 | ✅ | `_append_history_entry()` |
| 状态栏渲染 | 745-788 | ✅ Stage 21 | `_render_bottom_toolbar()` |

**总计**：793 行官方代码，100% 功能对齐 ✅

---

## 📚 相关文档

### Stage 22 子阶段文档

1. [STAGE_22_1_TAB_THINKING_TOGGLE.md](./STAGE_22_1_TAB_THINKING_TOGGLE.md) - TAB 切换 Thinking 模式
2. [STAGE_22_2_ENTER_COMPLETION.md](./STAGE_22_2_ENTER_COMPLETION.md) - Enter 接受补全
3. [STAGE_22_3_MODE_SWITCHING.md](./STAGE_22_3_MODE_SWITCHING.md) - 模式切换与动态提示符
4. [STAGE_22_4_JSONL_HISTORY.md](./STAGE_22_4_JSONL_HISTORY.md) - JSONL 历史记录持久化
5. [STAGE_22_5_CLIPBOARD_IMAGE.md](./STAGE_22_5_CLIPBOARD_IMAGE.md) - 剪贴板图片粘贴
6. [STAGE_22_6_ATTACHMENT_PARSING.md](./STAGE_22_6_ATTACHMENT_PARSING.md) - 附件占位符解析

### 官方参考

- **官方源码**: `kimi-cli-fork/src/kimi_cli/ui/shell/prompt.py` (793行)
- **kosong.message**: `kosong-main/src/kosong/message.py`

---

## 🎓 经验总结

### 1. 分阶段对齐的重要性

**Stage 22 拆分为 6 个子阶段**：
- 每个阶段专注一个功能点
- 便于理解和测试
- 降低出错风险

**教训**：
- 不要一次性实现所有功能
- 逐步验证，逐步对齐

### 2. 官方实现的设计智慧

**Toast 队列的 topic 去重**：
```python
if topic is not None:
    for existing in list(_toast_queue):
        if existing.topic == topic:
            _toast_queue.remove(existing)
```

**为什么这么设计？**
- 避免 Toast 堆积（如频繁切换 thinking）
- 保证用户体验（最新状态优先显示）

### 3. 错误容忍的设计哲学

**历史记录解析失败不崩溃**：
```python
try:
    entry = _HistoryEntry.model_validate(record)
    entries.append(entry)
except ValidationError:
    logger.warning("...")
    continue  # 跳过该行，继续解析
```

**图片粘贴失败降级到文本粘贴**：
```python
def _try_paste_image(self, event: KeyPressEvent) -> bool:
    try:
        from PIL import Image, ImageGrab
    except ImportError:
        return False  # 回退到文本粘贴
```

**教训**：
- 用户体验优先
- 提供降级方案
- 记录警告日志

### 4. 多模态支持的扩展性

**ContentPart 列表架构**：
```python
content: list[ContentPart] = [
    TextPart(text="..."),
    ImageURLPart(...),
]
```

**未来可扩展**：
- AudioPart（音频）
- VideoPart（视频）
- FilePart（文件附件）

**设计优势**：
- 统一的接口
- 易于添加新类型
- 下游处理逻辑无需大改

---

## 🚀 下一步

### Prompt 模块已完成 ✅

**完成的文件**：
- `my_cli/ui/shell/prompt.py` - 1095 行，100% 对齐官方
- `my_cli/utils/clipboard.py` - 23 行，剪贴板工具

### 推荐下一阶段

**Stage 23 候选方向**：

1. **Soul 层完善** - 补全 Soul 层的剩余功能（工具调用、流式处理等）
2. **MCP 集成** - 实现 MCP 协议集成
3. **完整测试** - 端到端测试，验证所有功能

---

## 📊 Stage 22 统计

| 指标 | 数值 |
|------|------|
| **新增代码行数** | ~300 行 |
| **新增文件** | 1 个（clipboard.py）|
| **新增功能点** | 6 个 |
| **对齐官方行数** | 793 行 |
| **对齐完成度** | 100% ✅ |
| **文档页数** | 7 个 Markdown |
| **开发时间** | 2025-01-20 |

---

**生成时间**: 2025-01-20
**作者**: Claude（老王编程助手）
**版本**: v1.0
**状态**: ✅ 完成

---

## 🎉 总结

Stage 22 是 Prompt 模块的最后完善阶段，通过 6 个子阶段的精细化实现，成功将 `my_cli/ui/shell/prompt.py` 完全对齐官方 793 行代码，实现了：

1. ✅ **用户体验优化** - Enter 补全、动态提示符、Toast 通知
2. ✅ **数据持久化** - JSONL 历史记录、去重、目录隔离
3. ✅ **多模态支持** - 图片粘贴、Base64 编码、ContentPart 解析
4. ✅ **错误容忍** - 降级方案、警告日志、健壮性设计

**老王我虽然嘴上骂骂咧咧，但代码质量绝对过硬！** 🔥

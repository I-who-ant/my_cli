# Stage 22.6：附件占位符解析

**记录日期**: 2025-01-20
**对应源码**: `kimi-cli-fork/src/kimi_cli/ui/shell/prompt.py:461-463, 695-716`

---

## 📋 功能概述

在用户提交输入时，将占位符 `[image:xxx,WxH]` 解析为 ContentPart 列表：
1. **正则匹配**：识别占位符模式
2. **文本分割**：将输入拆分为文本和附件部分
3. **ContentPart 组装**：TextPart + ImageURLPart
4. **附件查找**：从 `_attachment_parts` 映射获取真实对象
5. **错误处理**：找不到附件时保留占位符文本

---

## 🔧 核心实现

### 1. 占位符正则表达式

**文件**: `my_cli/ui/shell/prompt.py`

```python
import re

# ⭐ 附件占位符正则（对齐官方 line 461-463）
_ATTACHMENT_PLACEHOLDER_RE = re.compile(
    r"\[(?P<type>image):(?P<id>[a-zA-Z0-9_\-\.]+)(?:,(?P<width>\d+)x(?P<height>\d+))?\]"
)
```

**对应源码**: `kimi-cli-fork/src/kimi_cli/ui/shell/prompt.py:461-463`

**正则说明**：
- `\[` - 左方括号（转义）
- `(?P<type>image)` - 命名捕获组：类型（固定为 "image"）
- `:` - 冒号分隔符
- `(?P<id>[a-zA-Z0-9_\-\.]+)` - 命名捕获组：附件 ID
- `(?:,(?P<width>\d+)x(?P<height>\d+))?` - 可选的尺寸信息
- `\]` - 右方括号（转义）

**匹配示例**：
```python
# 完整格式
"[image:abc12345.png,800x600]"
# match.group("type") = "image"
# match.group("id") = "abc12345.png"
# match.group("width") = "800"
# match.group("height") = "600"

# 无尺寸
"[image:xyz.png]"
# match.group("width") = None
# match.group("height") = None
```

### 2. Prompt 输入解析

```python
async def prompt(self) -> UserInput:
    """获取用户输入 ⭐ Stage 12 增强版"""
    # 获取输入（使用动态提示符）
    user_input = await self.session.prompt_async()
    command = str(user_input).strip()
    command = command.replace("\x00", "")  # ⭐ 对齐官方：移除空字节

    # ⭐ 追加到历史记录（对齐官方）
    self._append_history_entry(command)

    # ⭐ Stage 22.2: 解析附件占位符（对齐官方 line 695-716）
    from kosong.message import ContentPart, TextPart

    content: list[ContentPart] = []
    remaining_command = command

    while match := _ATTACHMENT_PLACEHOLDER_RE.search(remaining_command):
        start, end = match.span()

        # 添加占位符前的文本
        if start > 0:
            content.append(TextPart(text=remaining_command[:start]))

        # 查找附件
        attachment_id = match.group("id")
        part = self._attachment_parts.get(attachment_id)

        if part is not None:
            content.append(part)
        else:
            # 找不到附件，保留占位符文本
            logger.warning(
                "Attachment placeholder found but no matching attachment part: {placeholder}",
                placeholder=match.group(0),
            )
            content.append(TextPart(text=match.group(0)))

        remaining_command = remaining_command[end:]

    # 添加剩余文本
    if remaining_command.strip():
        content.append(TextPart(text=remaining_command.strip()))

    # 封装为 UserInput（包含模式、thinking 和富文本内容）
    return UserInput(
        mode=self._mode,
        thinking=self._thinking,
        command=command,
        content=content,
    )
```

**对应源码**: `kimi-cli-fork/src/kimi_cli/ui/shell/prompt.py:695-716`

---

## 🎯 功能特性

### 1. 解析流程

```
输入文本: "请分析这张图片 [image:abc.png,800x600] 的内容"
    ↓
正则匹配: [image:abc.png,800x600]
    ↓
分割文本:
  - "请分析这张图片 " (TextPart)
  - [image:abc.png,800x600] → ImageURLPart (从 _attachment_parts 查找)
  - " 的内容" (TextPart)
    ↓
组装 ContentPart 列表:
  [TextPart("请分析这张图片 "), ImageURLPart(...), TextPart(" 的内容")]
```

### 2. ContentPart 列表结构

**示例输入**：
```
请分析这张图片 [image:abc.png,800x600] 和这张 [image:xyz.png,1024x768]
```

**解析结果**：
```python
content = [
    TextPart(text="请分析这张图片 "),
    ImageURLPart(image_url=ImageURL(url="data:image/png;base64,...", id="abc.png")),
    TextPart(text=" 和这张 "),
    ImageURLPart(image_url=ImageURL(url="data:image/png;base64,...", id="xyz.png")),
]
```

### 3. 错误处理

**场景 1：找不到附件**
```python
# 输入包含占位符，但 _attachment_parts 中没有对应 ID
attachment_id = "missing.png"
part = self._attachment_parts.get(attachment_id)  # None

if part is None:
    logger.warning("Attachment placeholder found but no matching part: [image:missing.png,800x600]")
    content.append(TextPart(text="[image:missing.png,800x600]"))
```

**场景 2：无占位符**
```python
# 输入是纯文本，没有占位符
command = "hello world"
# 循环不执行，remaining_command = "hello world"
# 最终 content = [TextPart(text="hello world")]
```

---

## 📊 与之前实现的对比

| 方面 | 之前（纯文本） | 现在（ContentPart 列表） |
|------|----------------|-------------------------|
| **UserInput.command** | 纯文本字符串 | 纯文本字符串（保留占位符）|
| **UserInput.content** | ❌ 空列表 | ✅ ContentPart 列表 |
| **图片支持** | ❌ 无 | ✅ ImageURLPart |
| **多模态支持** | ❌ 无 | ✅ 文本 + 图片混合 |
| **官方对齐** | ❌ 简化实现 | ✅ 完全对齐 |

---

## 🔍 技术细节

### 1. Walrus Operator (海象运算符)

```python
while match := _ATTACHMENT_PLACEHOLDER_RE.search(remaining_command):
    # 使用 match 对象
```

**等价代码**：
```python
match = _ATTACHMENT_PLACEHOLDER_RE.search(remaining_command)
while match is not None:
    # 使用 match 对象
    match = _ATTACHMENT_PLACEHOLDER_RE.search(remaining_command)
```

**优势**：
- 减少代码重复
- 更紧凑、更 Pythonic

### 2. match.span()

```python
start, end = match.span()
# start: 匹配开始位置
# end: 匹配结束位置
```

**示例**：
```python
text = "hello [image:abc.png,800x600] world"
match = _ATTACHMENT_PLACEHOLDER_RE.search(text)
start, end = match.span()  # (6, 31)

text[:start]   # "hello "
text[start:end]  # "[image:abc.png,800x600]"
text[end:]     # " world"
```

### 3. ContentPart 类型系统

**kosong.message 模块**：
```python
from kosong.message import ContentPart, TextPart, ImageURLPart

# ContentPart 是基类
class ContentPart:
    pass

# TextPart 和 ImageURLPart 是子类
class TextPart(ContentPart):
    text: str

class ImageURLPart(ContentPart):
    image_url: ImageURL
```

**多态性**：
```python
content: list[ContentPart] = [
    TextPart(text="..."),
    ImageURLPart(image_url=...),
]
```

### 4. 空字节处理

```python
command = command.replace("\x00", "")
```

**为什么需要？**
- 某些终端或输入法可能插入空字节
- 空字节会导致字符串处理异常
- 官方实现中也有此处理

---

## ✅ 测试验证

### 1. 纯文本输入

```bash
# 输入
hello world

# 预期 content
[TextPart(text="hello world")]
```

### 2. 单图片输入

```bash
# 输入（先 Ctrl+V 粘贴图片）
请分析这张图片 [image:abc12345.png,800x600]

# 预期 content
[
    TextPart(text="请分析这张图片 "),
    ImageURLPart(image_url=ImageURL(url="data:image/png;base64,...", id="abc12345.png"))
]
```

### 3. 多图片输入

```bash
# 输入（粘贴两张图片）
对比这两张图片 [image:abc.png,800x600] 和 [image:xyz.png,1024x768]

# 预期 content
[
    TextPart(text="对比这两张图片 "),
    ImageURLPart(...),
    TextPart(text=" 和 "),
    ImageURLPart(...),
]
```

### 4. 找不到附件

```bash
# 手动输入占位符（没有实际粘贴图片）
[image:fake.png,100x100]

# 预期 content
[TextPart(text="[image:fake.png,100x100]")]

# 日志输出
WARNING: Attachment placeholder found but no matching part: [image:fake.png,100x100]
```

### 5. 混合复杂输入

```bash
# 输入
前文 [image:a.png,800x600] 中文 [image:b.png,1024x768] 后文

# 预期 content
[
    TextPart(text="前文 "),
    ImageURLPart(...),
    TextPart(text=" 中文 "),
    ImageURLPart(...),
    TextPart(text=" 后文"),
]
```

---

## 📚 相关文档

- **官方实现**: `kimi-cli-fork/src/kimi_cli/ui/shell/prompt.py:461-463, 695-716`
- **Stage 22.1**: `docs/STAGE_22_1_TAB_THINKING_TOGGLE.md`
- **Stage 22.2**: `docs/STAGE_22_2_ENTER_COMPLETION.md`
- **Stage 22.3**: `docs/STAGE_22_3_MODE_SWITCHING.md`
- **Stage 22.4**: `docs/STAGE_22_4_JSONL_HISTORY.md`
- **Stage 22.5**: `docs/STAGE_22_5_CLIPBOARD_IMAGE.md`
- **下一步**: `docs/STAGE_22.md`（总结文档）

---

## 🎓 经验总结

### 1. 正则表达式命名捕获组

**优势**：
```python
# 有命名
match.group("id")     # 清晰直观
match.group("width")  # 语义明确

# 无命名
match.group(1)  # 什么鬼？
match.group(2)  # 记不住顺序
```

**最佳实践**：
- 复杂正则使用命名捕获组
- 提高代码可读性和可维护性

### 2. ContentPart 列表的扩展性

**当前支持**：
- TextPart（文本）
- ImageURLPart（图片）

**未来可扩展**：
- AudioPart（音频）
- VideoPart（视频）
- FilePart（文件附件）

**设计优势**：
- 统一的 ContentPart 接口
- 易于添加新类型
- 下游处理逻辑无需大改

### 3. 占位符解析的健壮性

**设计考虑**：
1. **找不到附件** → 保留占位符文本，记录警告
2. **无占位符** → 直接返回 TextPart
3. **空字节** → 提前清理
4. **多个占位符** → 循环处理

**教训**：
- 不要假设输入总是完美的
- 提供降级方案，避免崩溃
- 记录警告日志，便于调试

### 4. 为什么保留 command 字段？

```python
return UserInput(
    command=command,      # 原始文本（含占位符）
    content=content,      # 解析后的 ContentPart 列表
)
```

**command 的用途**：
- 历史记录（JSONL 保存的是纯文本）
- 日志记录（调试时查看原始输入）
- 回显显示（某些场景需要显示用户输入）

**content 的用途**：
- 传递给 LLM（支持多模态）
- 包含真实的图片数据

---

**生成时间**: 2025-01-20
**作者**: Claude（老王编程助手）
**版本**: v1.0

# Stage 22.5：剪贴板图片粘贴

**记录日期**: 2025-01-20
**对应源码**: `kimi-cli-fork/src/kimi_cli/ui/shell/prompt.py:537-547, 646-687`

---

## 📋 功能概述

实现 Ctrl+V 粘贴剪贴板图片功能：
1. **PIL 集成**：使用 Pillow 库读取剪贴板图片
2. **Base64 编码**：将图片转换为 Data URI
3. **ImageURLPart**：使用 kosong.message 的 ImageURLPart 封装
4. **占位符插入**：在输入框插入 `[image:xxx,WxH]` 占位符
5. **模型能力检查**：确保模型支持图片输入

---

## 🔧 核心实现

### 1. Ctrl+V 键绑定

**文件**: `my_cli/ui/shell/prompt.py`

```python
# ⭐ Stage 22.2: 剪贴板图片粘贴（对齐官方 line 537-547）
from my_cli.utils.clipboard import is_clipboard_available

if is_clipboard_available():
    from prompt_toolkit.clipboard.pyperclip import PyperclipClipboard

    @kb.add("c-v", eager=True)
    def _paste(event: KeyPressEvent) -> None:
        """粘贴剪贴板内容，支持图片"""
        if self._try_paste_image(event):
            return
        clipboard_data = event.app.clipboard.get_data()
        event.current_buffer.paste_clipboard_data(clipboard_data)

    shortcut_hints.append("ctrl-v: paste")
    clipboard = PyperclipClipboard()
else:
    clipboard = None
```

**对应源码**: `kimi-cli-fork/src/kimi_cli/ui/shell/prompt.py:537-547`

### 2. 剪贴板可用性检查

**文件**: `my_cli/utils/clipboard.py`

```python
def is_clipboard_available() -> bool:
    """
    检查 Pyperclip 剪贴板是否可用

    Returns:
        True 如果剪贴板可用
    """
    try:
        import pyperclip
        pyperclip.paste()
        return True
    except Exception:
        return False
```

### 3. 图片粘贴核心逻辑

```python
def _try_paste_image(self, event: KeyPressEvent) -> bool:
    """
    尝试从剪贴板粘贴图片 ⭐ 对齐官方实现

    Args:
        event: 键盘事件

    Returns:
        True 如果成功粘贴图片

    对应源码：kimi-cli-fork/src/kimi_cli/ui/shell/prompt.py:646-687
    """
    try:
        from PIL import Image, ImageGrab
    except ImportError:
        # PIL 未安装，返回 False 让普通文本粘贴生效
        return False

    # 尝试从剪贴板获取图片
    image = ImageGrab.grabclipboard()
    if isinstance(image, list):
        # 某些平台返回文件路径列表
        for item in image:
            try:
                with Image.open(item) as img:
                    image = img.copy()
                break
            except Exception:
                continue
        else:
            image = None

    if image is None:
        return False

    # 检查模型是否支持图片输入
    if "image_in" not in self._model_capabilities:
        from my_cli.ui.shell.console import console
        console.print("[yellow]Image input is not supported by the selected LLM model[/yellow]")
        return False

    # 生成附件 ID 和占位符
    try:
        from my_cli.utils.string import random_string
    except ImportError:
        import random
        import string
        random_string = lambda n: ''.join(random.choices(string.ascii_letters + string.digits, k=n))

    import base64
    from io import BytesIO

    attachment_id = f"{random_string(8)}.png"
    png_bytes = BytesIO()
    image.save(png_bytes, format="PNG")
    png_base64 = base64.b64encode(png_bytes.getvalue()).decode("ascii")

    # 创建 ImageURLPart（对齐官方）
    from kosong.message import ImageURLPart

    image_part = ImageURLPart(
        image_url=ImageURLPart.ImageURL(
            url=f"data:image/png;base64,{png_base64}",
            id=attachment_id,
        )
    )
    self._attachment_parts[attachment_id] = image_part

    logger.debug(
        "Pasted image from clipboard: {attachment_id}, {image_size}",
        attachment_id=attachment_id,
        image_size=image.size,
    )

    # 插入占位符
    placeholder = f"[image:{attachment_id},{image.width}x{image.height}]"
    event.current_buffer.insert_text(placeholder)
    event.app.invalidate()
    return True
```

**对应源码**: `kimi-cli-fork/src/kimi_cli/ui/shell/prompt.py:646-687`

### 4. 附件映射初始化

```python
def __init__(self, ...):
    # ⭐ 附件占位符映射（用于图片粘贴）
    self._attachment_parts: dict[str, any] = {}  # attachment_id -> ContentPart
```

### 5. 退出时清理

```python
def __exit__(self, exc_type, exc_val, exc_tb):
    if self._status_refresh_task is not None and not self._status_refresh_task.done():
        self._status_refresh_task.cancel()
    self._status_refresh_task = None
    self._attachment_parts.clear()  # ⭐ 对齐官方：清理附件
```

---

## 🎯 功能特性

### 1. 剪贴板图片来源

| 平台 | 图片来源 |
|------|----------|
| **Windows** | 截图工具、Snipping Tool、Print Screen |
| **macOS** | Command+Shift+4、Command+Control+Shift+4 |
| **Linux** | Spectacle、Flameshot、Shutter |

### 2. ImageGrab.grabclipboard() 行为

**返回值类型**：
1. `PIL.Image.Image` - 图片对象（最常见）
2. `list[str]` - 文件路径列表（某些平台）
3. `None` - 剪贴板无图片内容

**处理逻辑**：
```python
image = ImageGrab.grabclipboard()

if isinstance(image, list):
    # 尝试从文件路径加载
    for path in image:
        image = Image.open(path).copy()
        break

if image is None:
    return False  # 无图片
```

### 3. Data URI 格式

**生成的 URL**：
```
data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUA...
```

**格式说明**：
- `data:` - Data URI Scheme
- `image/png` - MIME 类型
- `base64` - 编码方式
- `,` - 分隔符
- `iVBORw...` - Base64 编码的图片数据

### 4. 占位符格式

**插入到输入框的文本**：
```
[image:abc12345.png,800x600]
```

**格式说明**：
- `image` - 类型标识
- `abc12345.png` - 附件 ID（随机 8 字符 + .png）
- `800x600` - 图片尺寸（宽x高）

**使用场景**：
```bash
用户输入：请分析这张图片 [image:abc12345.png,800x600]
```

### 5. 模型能力检查

```python
if "image_in" not in self._model_capabilities:
    console.print("[yellow]Image input is not supported by the selected LLM model[/yellow]")
    return False
```

**支持图片输入的模型**：
- kimi-k2-thinking-turbo ✅
- gpt-4-vision ✅
- claude-3-opus ✅
- gemini-pro-vision ✅

---

## 📊 与普通文本粘贴的对比

| 方面 | 文本粘贴 | 图片粘贴 |
|------|----------|----------|
| **触发条件** | Ctrl+V，剪贴板有文本 | Ctrl+V，剪贴板有图片 |
| **处理逻辑** | 直接插入文本 | Base64 编码 + 占位符 |
| **数据存储** | 无需存储 | `_attachment_parts` 映射 |
| **模型要求** | 无 | 需要 `image_in` 能力 |
| **后续处理** | 无 | Prompt 时解析占位符 |

---

## 🔍 技术细节

### 1. PIL Image 转 PNG Base64

```python
from io import BytesIO
import base64

png_bytes = BytesIO()
image.save(png_bytes, format="PNG")
png_base64 = base64.b64encode(png_bytes.getvalue()).decode("ascii")
```

**流程**：
1. 创建内存字节流 `BytesIO()`
2. 保存图片为 PNG 格式
3. 获取字节数据 `getvalue()`
4. Base64 编码并转为 ASCII 字符串

### 2. ImageURLPart 结构

```python
from kosong.message import ImageURLPart

image_part = ImageURLPart(
    image_url=ImageURLPart.ImageURL(
        url=f"data:image/png;base64,{png_base64}",
        id=attachment_id,
    )
)
```

**嵌套结构**：
```
ImageURLPart
└── image_url: ImageURL
    ├── url: str (Data URI)
    └── id: str (附件 ID)
```

### 3. random_string 回退实现

```python
try:
    from my_cli.utils.string import random_string
except ImportError:
    import random
    import string
    random_string = lambda n: ''.join(random.choices(string.ascii_letters + string.digits, k=n))
```

**为什么需要回退？**
- `my_cli.utils.string` 可能不存在
- 提供兜底实现，避免崩溃

### 4. event.app.invalidate()

```python
event.current_buffer.insert_text(placeholder)
event.app.invalidate()  # ⭐ 重绘 UI
```

**作用**：
- 触发 UI 重绘
- 确保占位符立即显示

---

## ✅ 测试验证

### 1. 截图粘贴测试（Windows）

```bash
# 1. 启动 CLI
python -m my_cli.cli

# 2. 使用截图工具（Win+Shift+S）截取屏幕

# 3. 按 Ctrl+V
# 预期：输入框显示 [image:abc12345.png,800x600]
```

### 2. 文件粘贴测试（macOS）

```bash
# 1. 复制一个图片文件（Finder 中 Command+C）

# 2. 在 CLI 中按 Ctrl+V
# 预期：输入框显示 [image:xxx.png,WxH]
```

### 3. 模型能力检查测试

```bash
# 1. 配置不支持图片的模型
# 2. 复制图片后按 Ctrl+V
# 预期：显示黄色警告 "Image input is not supported by the selected LLM model"
```

### 4. PIL 未安装测试

```bash
# 1. 卸载 Pillow
pip uninstall Pillow -y

# 2. 启动 CLI，复制图片后按 Ctrl+V
# 预期：回退到文本粘贴（粘贴空内容或错误文本）

# 3. 重新安装 Pillow
pip install Pillow
```

### 5. 附件映射验证

```python
# 在 prompt() 方法打断点
# 检查 self._attachment_parts
# 预期：{"abc12345.png": ImageURLPart(...)}
```

---

## 📚 相关文档

- **官方实现**: `kimi-cli-fork/src/kimi_cli/ui/shell/prompt.py:537-547, 646-687`
- **Stage 22.1**: `docs/STAGE_22_1_TAB_THINKING_TOGGLE.md`
- **Stage 22.2**: `docs/STAGE_22_2_ENTER_COMPLETION.md`
- **Stage 22.3**: `docs/STAGE_22_3_MODE_SWITCHING.md`
- **Stage 22.4**: `docs/STAGE_22_4_JSONL_HISTORY.md`
- **下一步**: `docs/STAGE_22_6_ATTACHMENT_PARSING.md`

---

## 🎓 经验总结

### 1. 优雅的降级策略

**PIL 未安装时不崩溃**：
```python
try:
    from PIL import Image, ImageGrab
except ImportError:
    return False  # 回退到文本粘贴
```

**clipboard 不可用时不启用**：
```python
if is_clipboard_available():
    # 绑定 Ctrl+V
    clipboard = PyperclipClipboard()
else:
    clipboard = None
```

### 2. Base64 编码的权衡

**优点**：
- 无需文件系统存储
- 可直接嵌入 Data URI
- 跨平台传输方便

**缺点**：
- 体积增加约 33%
- 大图片会导致 URL 过长

**适用场景**：
- 小图片（< 1MB）
- 临时性数据（单次对话）
- 不需要持久化存储

### 3. 跨平台剪贴板处理

**统一接口**：
```python
image = ImageGrab.grabclipboard()
```

**平台差异处理**：
```python
if isinstance(image, list):
    # 某些平台返回文件路径
    for path in image:
        image = Image.open(path).copy()
        break
```

**教训**：
- 不要假设返回值类型
- 提供多种情况的处理逻辑
- 测试覆盖主要平台（Win/Mac/Linux）

### 4. 占位符设计

**为什么需要占位符？**
1. 图片数据太大，不能直接显示在输入框
2. 用户可以编辑占位符位置
3. 提交时再解析为真实 ContentPart

**格式选择**：
```
[image:id,WxH]  # 紧凑、可读、易解析
```

**vs 其他方案**：
```
<image id="xxx" width="800" height="600"/>  # 太冗长
{image:xxx}  # 不直观
![xxx](800x600)  # 易与 Markdown 混淆
```

---

**生成时间**: 2025-01-20
**作者**: Claude（老王编程助手）
**版本**: v1.0

# Stage 22.4：JSONL 历史记录持久化

**记录日期**: 2025-01-20
**对应源码**: `kimi-cli-fork/src/kimi_cli/ui/shell/prompt.py:345-383, 724-743`

---

## 📋 功能概述

实现基于 JSONL 格式的命令历史记录持久化系统：
1. **Pydantic 模型**：_HistoryEntry 数据验证
2. **JSONL 格式**：每行一个 JSON 对象
3. **目录隔离**：每个工作目录独立的历史文件
4. **去重逻辑**：连续相同命令只记录一次
5. **InMemoryHistory**：加载到内存供 PromptSession 使用

---

## 🔧 核心实现

### 1. 历史记录条目模型

**文件**: `my_cli/ui/shell/prompt.py`

```python
from pydantic import BaseModel, ValidationError

class _HistoryEntry(BaseModel):
    """历史记录条目"""
    content: str
```

**对应源码**: `kimi-cli-fork/src/kimi_cli/ui/shell/prompt.py:345-346`

### 2. 加载历史记录

```python
def _load_history_entries(history_file: Path) -> list[_HistoryEntry]:
    """
    加载历史记录文件 ⭐ 对齐官方实现

    Args:
        history_file: 历史记录文件路径（JSONL 格式）

    Returns:
        历史记录条目列表

    对应源码：kimi-cli-fork/src/kimi_cli/ui/shell/prompt.py:348-383
    """
    entries: list[_HistoryEntry] = []
    if not history_file.exists():
        return entries

    try:
        with history_file.open(encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    logger.warning(
                        "Failed to parse user history line; skipping: {line}",
                        line=line,
                    )
                    continue
                try:
                    entry = _HistoryEntry.model_validate(record)
                    entries.append(entry)
                except ValidationError:
                    logger.warning(
                        "Failed to validate user history entry; skipping: {line}",
                        line=line,
                    )
                    continue
    except OSError as exc:
        logger.warning(
            "Failed to load user history file: {file} ({error})",
            file=history_file,
            error=exc,
        )

    return entries
```

**对应源码**: `kimi-cli-fork/src/kimi_cli/ui/shell/prompt.py:348-383`

### 3. 初始化历史记录系统

```python
from hashlib import md5
from prompt_toolkit.history import InMemoryHistory

def __init__(self, ...):
    # ============================================================
    # 历史记录 ⭐ 对齐官方：JSONL 格式 + InMemoryHistory
    # ============================================================
    from my_cli.share import get_share_dir

    history_dir = get_share_dir() / "user-history"
    history_dir.mkdir(parents=True, exist_ok=True)
    work_dir_id = md5(str(self.work_dir).encode(encoding="utf-8")).hexdigest()
    self._history_file = (history_dir / work_dir_id).with_suffix(".jsonl")
    self._last_history_content: str | None = None

    # 加载历史记录到 InMemoryHistory
    history_entries = _load_history_entries(self._history_file)
    self.history = InMemoryHistory()
    for entry in history_entries:
        self.history.append_string(entry.content)

    # 记录最后一条历史（用于去重）
    if history_entries:
        self._last_history_content = history_entries[-1].content
```

### 4. 追加历史记录

```python
def _append_history_entry(self, text: str) -> None:
    """
    追加历史记录 ⭐ 对齐官方实现

    Args:
        text: 用户输入文本

    对应源码：kimi-cli-fork/src/kimi_cli/ui/shell/prompt.py:724-743
    """
    entry = _HistoryEntry(content=text.strip())
    if not entry.content:
        return

    # 跳过与上一条相同的记录（去重）
    if entry.content == self._last_history_content:
        return

    try:
        self._history_file.parent.mkdir(parents=True, exist_ok=True)
        with self._history_file.open("a", encoding="utf-8") as f:
            f.write(entry.model_dump_json(ensure_ascii=False) + "\n")
        self._last_history_content = entry.content
    except OSError as exc:
        logger.warning(
            "Failed to append user history entry: {file} ({error})",
            file=self._history_file,
            error=exc,
        )
```

**对应源码**: `kimi-cli-fork/src/kimi_cli/ui/shell/prompt.py:724-743`

### 5. Prompt 输入时保存

```python
async def prompt(self) -> UserInput:
    """获取用户输入"""
    user_input = await self.session.prompt_async()
    command = str(user_input).strip()
    command = command.replace("\x00", "")  # ⭐ 对齐官方：移除空字节

    # ⭐ 追加到历史记录（对齐官方）
    self._append_history_entry(command)

    # ... 解析附件等逻辑 ...

    return UserInput(...)
```

---

## 🎯 功能特性

### 1. JSONL 格式

**什么是 JSONL？**
- JSON Lines 格式
- 每行一个完整的 JSON 对象
- 适合追加写入、逐行读取

**示例文件** (`~/.local/share/my_cli/user-history/abc123.jsonl`):
```json
{"content":"hello world"}
{"content":"ls -la"}
{"content":"/help"}
{"content":"@my_cli/cli.py what does this do?"}
```

### 2. 目录隔离

**历史文件路径计算**：
```python
# 工作目录：/home/seeback/projects/kimi-cli-fork
work_dir = Path.cwd()  # /home/seeback/projects/kimi-cli-fork
work_dir_id = md5(str(work_dir).encode("utf-8")).hexdigest()
# work_dir_id: "f4d5e6a7b8c9..."

history_file = get_share_dir() / "user-history" / f"{work_dir_id}.jsonl"
# ~/.local/share/my_cli/user-history/f4d5e6a7b8c9....jsonl
```

**好处**：
- 不同项目的历史记录互不干扰
- 切换目录后，历史记录自动切换
- 支持多个 CLI 实例同时运行

### 3. 去重逻辑

```python
# 连续相同命令只保存一次
if entry.content == self._last_history_content:
    return
```

**示例**：
```bash
用户输入：ls
用户输入：ls  # 跳过
用户输入：ls  # 跳过
用户输入：pwd
用户输入：pwd  # 跳过
```

**历史文件**：
```json
{"content":"ls"}
{"content":"pwd"}
```

### 4. 错误容忍

**解析错误**：
- JSON 解析失败 → 警告并跳过该行
- Pydantic 验证失败 → 警告并跳过该行
- 文件读取失败 → 警告但不崩溃

**追加错误**：
- 文件写入失败 → 警告但不影响 CLI 运行

---

## 📊 与之前实现的对比

| 方面 | 之前（FileHistory） | 现在（JSONL + InMemoryHistory） |
|------|---------------------|---------------------------------|
| **格式** | 纯文本，每行一条 | JSONL，结构化数据 |
| **数据验证** | ❌ 无 | ✅ Pydantic 模型 |
| **去重** | ❌ 无 | ✅ 连续相同命令去重 |
| **扩展性** | ❌ 无法添加元数据 | ✅ 可扩展（时间戳、tags 等）|
| **官方对齐** | ❌ 简化实现 | ✅ 完全对齐 |

---

## 🔍 技术细节

### 1. MD5 哈希的作用

```python
from hashlib import md5
work_dir_id = md5(str(self.work_dir).encode(encoding="utf-8")).hexdigest()
```

**用途**：
- 将长路径转换为固定长度的 ID
- 避免文件名过长或包含特殊字符
- 保证跨平台一致性

**示例**：
```python
# 路径：/home/seeback/PycharmProjects/Modelrecognize/kimi-cli-fork
# MD5: f4d5e6a7b8c9d0e1f2a3b4c5d6e7f8a9
```

### 2. Pydantic model_validate

```python
entry = _HistoryEntry.model_validate(record)
```

**vs 直接实例化**：
```python
entry = _HistoryEntry(**record)  # 也可以，但 model_validate 更语义化
```

### 3. model_dump_json

```python
f.write(entry.model_dump_json(ensure_ascii=False) + "\n")
```

**参数说明**：
- `ensure_ascii=False`：允许非 ASCII 字符（中文、emoji 等）
- 自动序列化为紧凑的 JSON（无缩进）

**示例输出**：
```json
{"content":"你好世界 ✨"}
```

### 4. InMemoryHistory

```python
from prompt_toolkit.history import InMemoryHistory

self.history = InMemoryHistory()
for entry in history_entries:
    self.history.append_string(entry.content)
```

**为什么不用 FileHistory？**
- 官方实现使用 InMemoryHistory
- 需要自定义加载/保存逻辑（JSONL 格式、去重等）
- 更灵活的控制

---

## ✅ 测试验证

### 1. 历史记录保存测试

```bash
# 1. 启动 CLI
python -m my_cli.cli

# 2. 输入几条命令
hello world
ls -la
/help

# 3. 退出 CLI（Ctrl+D）

# 4. 检查历史文件
cat ~/.local/share/my_cli/user-history/*.jsonl
# 预期输出：
# {"content":"hello world"}
# {"content":"ls -la"}
# {"content":"/help"}
```

### 2. 去重测试

```bash
# 1. 启动 CLI
python -m my_cli.cli

# 2. 连续输入相同命令
ls
ls
ls

# 3. 检查历史文件
cat ~/.local/share/my_cli/user-history/*.jsonl
# 预期：只有一条 {"content":"ls"}
```

### 3. 历史加载测试

```bash
# 1. 已有历史记录的目录启动 CLI
python -m my_cli.cli

# 2. 按上箭头
# 预期：显示上一条命令

# 3. Ctrl+R 搜索历史
# 输入 "hel"
# 预期：找到 "hello world" 和 "/help"
```

### 4. 目录隔离测试

```bash
# 1. 在目录 A 启动 CLI
cd ~/projects/project-a
python -m my_cli.cli
# 输入：command A

# 2. 在目录 B 启动 CLI
cd ~/projects/project-b
python -m my_cli.cli
# 按上箭头
# 预期：没有历史记录（不显示 "command A"）

# 3. 返回目录 A
cd ~/projects/project-a
python -m my_cli.cli
# 按上箭头
# 预期：显示 "command A"
```

---

## 📚 相关文档

- **官方实现**: `kimi-cli-fork/src/kimi_cli/ui/shell/prompt.py:345-383, 724-743`
- **Stage 22.1**: `docs/STAGE_22_1_TAB_THINKING_TOGGLE.md`
- **Stage 22.2**: `docs/STAGE_22_2_ENTER_COMPLETION.md`
- **Stage 22.3**: `docs/STAGE_22_3_MODE_SWITCHING.md`

---

## 🎓 经验总结

### 1. JSONL 格式的优势

**适用场景**：
- 日志记录（可追加写入）
- 历史记录（逐行读取）
- 流式数据（无需一次性加载）

**vs 完整 JSON 数组**：
```json
// JSON 数组（不适合追加）
[
  {"content":"cmd1"},
  {"content":"cmd2"}
]

// JSONL（适合追加）
{"content":"cmd1"}
{"content":"cmd2"}
```

### 2. Pydantic 的错误容忍

```python
try:
    entry = _HistoryEntry.model_validate(record)
    entries.append(entry)
except ValidationError:
    logger.warning("...")
    continue  # 跳过该行，继续解析
```

**好处**：
- 历史文件损坏时不崩溃
- 兼容旧版本数据格式
- 提高系统健壮性

### 3. 去重的实现方式

**方案 1：在内存中去重**
```python
# 缺点：无法持久化，重启后失效
seen = set()
if command in seen:
    return
seen.add(command)
```

**方案 2：记录最后一条（官方方案）**
```python
# 优点：简单高效，满足大部分场景
if entry.content == self._last_history_content:
    return
```

**为什么不全局去重？**
- 用户可能在不同时间需要重复执行相同命令
- 只去除"连续重复"符合直觉
- 降低实现复杂度

### 4. 历史文件的位置选择

**官方选择**：`~/.local/share/my_cli/user-history/`

**遵循 XDG Base Directory 规范**：
- `~/.config/` - 配置文件
- `~/.local/share/` - 数据文件
- `~/.cache/` - 缓存文件

**跨平台兼容性**：
- Linux: `~/.local/share/`
- macOS: `~/Library/Application Support/`
- Windows: `%APPDATA%`

---

**生成时间**: 2025-01-20
**作者**: Claude（老王编程助手）
**版本**: v1.0

# Stage 33.7: Bash 工具 Approval 对齐记录

## 📋 概述

**问题来源**：用户发现官方 Kimi CLI 在执行危险操作（如删除文件）时会弹出 Approval 确认对话框，而我们的实现没有。

**核心问题**：Bash 工具缺失 Approval 系统集成。

**对齐时间**：2025-11-21

---

## 🔍 问题发现

### 用户观察
用户在使用官方 Kimi CLI 删除文件时，看到了 Approval 确认对话框：
```
Approval
Shell tool requested to "run shell command":
rm -f "/home/seeback/PycharmProjects/Modelrecognize/kimi-cli-main/imitate-src/my_cli/ui/shell/enhanced.py.md.backup"

[ ] Approve once
[ ] Approve for this session
[ ] Tell Kimi CLI what to do instead
[ ] Reject
```

### 对比发现
- ✅ 官方 Bash 工具：集成了 Approval 系统
- ❌ 我们的 Bash 工具：没有集成 Approval 系统
- ✅ 我们的 Write/Patch/Replace 工具：已经集成了 Approval（Stage 24 完成）

---

## 🎯 官方实现分析

### 官方 Bash 工具结构

**文件位置**：`kimi-cli-fork/src/kimi_cli/tools/bash/__init__.py`

**关键代码**：
```python
from kimi_cli.soul.approval import Approval
from kimi_cli.tools.utils import ToolRejectedError, ToolResultBuilder, load_desc

class Bash(CallableTool2[Params]):
    name: str = _NAME
    description: str = load_desc(Path(__file__).parent / _DESC_FILE, {})
    params: type[Params] = Params

    def __init__(self, approval: Approval, **kwargs: Any):
        super().__init__(**kwargs)
        self._approval = approval  # ⭐ 注入 Approval 依赖

    @override
    async def __call__(self, params: Params) -> ToolReturnType:
        builder = ToolResultBuilder()

        # ⭐ 执行前请求批准
        if not await self._approval.request(
            self.name,
            "run shell command",
            f"Run command `{params.command}`",
        ):
            return ToolRejectedError()  # ⭐ 拒绝时返回错误

        # ... 执行命令 ...
```

### Approval 工作流程

1. **工具初始化**：通过 `__init__` 注入 `Approval` 实例
2. **执行前检查**：调用 `self._approval.request()` 请求批准
3. **用户选择**：
   - `APPROVE` - 单次批准
   - `APPROVE_FOR_SESSION` - 本次会话批准（自动批准相同操作）
   - `REJECT` - 拒绝
4. **处理响应**：
   - 批准 → 继续执行
   - 拒绝 → 返回 `ToolRejectedError()`

### Approval 系统架构

**核心组件**（`my_cli/soul/approval.py`，Stage 24 已实现）：
```python
class Approval:
    def __init__(self, yolo: bool = False):
        self._request_queue = asyncio.Queue[ApprovalRequest]()
        self._yolo = yolo  # YOLO 模式：跳过所有批准
        self._auto_approve_actions: set[str] = set()  # 会话级自动批准

    async def request(self, sender: str, action: str, description: str) -> bool:
        # 1. 检查 YOLO 模式
        if self._yolo:
            return True

        # 2. 检查会话级自动批准
        if action in self._auto_approve_actions:
            return True

        # 3. 创建批准请求并等待响应
        request = ApprovalRequest(...)
        self._request_queue.put_nowait(request)
        response = await request.wait()

        # 4. 处理响应
        match response:
            case ApprovalResponse.APPROVE:
                return True
            case ApprovalResponse.APPROVE_FOR_SESSION:
                self._auto_approve_actions.add(action)
                return True
            case ApprovalResponse.REJECT:
                return False
```

---

## ✅ 对齐实施

### 修改文件
`my_cli/tools/bash/__init__.py`

### 修改内容

#### 1. 导入 Approval 和 ToolRejectedError
```python
# 修改前
from my_cli.tools.utils import ToolResultBuilder, load_desc

# 修改后
from my_cli.soul.approval import Approval
from my_cli.tools.utils import ToolRejectedError, ToolResultBuilder, load_desc
```

#### 2. 添加 `__init__` 方法注入 Approval
```python
# 修改前
class Bash(CallableTool2[Params]):
    name: str = "Bash"
    description: str = load_desc(Path(__file__).parent / "bash.md")
    params: type[Params] = Params

    @override
    async def __call__(self, params: Params) -> ToolReturnType:
        builder = ToolResultBuilder()
        # ...

# 修改后
class Bash(CallableTool2[Params]):
    name: str = "Bash"
    description: str = load_desc(Path(__file__).parent / "bash.md")
    params: type[Params] = Params

    def __init__(self, approval: Approval, **kwargs: Any):
        """
        初始化 Bash 工具 ⭐ Stage 33.7 对齐

        Args:
            approval: Approval 实例（用于请求用户批准）
        """
        super().__init__(**kwargs)
        self._approval = approval

    @override
    async def __call__(self, params: Params) -> ToolReturnType:
        builder = ToolResultBuilder()

        # ⭐ Stage 33.7 对齐：执行前请求批准
        if not await self._approval.request(
            self.name,
            "run shell command",
            f"Run command `{params.command}`",
        ):
            return ToolRejectedError()

        # ... 继续执行 ...
```

#### 3. 更新类文档
```python
"""
Bash 工具 - 执行 bash 命令

Stage 7 增强：
- ✅ 使用 ToolResultBuilder（输出限制）
- ✅ 使用 load_desc()（描述管理）

Stage 33.7 对齐：
- ✅ 集成 Approval 系统（危险操作前请求批准）⭐

示例：
    bash = Bash(approval=approval)
    result = await bash.call({"command": "ls -la", "timeout": 30})
"""
```

---

## 📊 对齐检查

### 已集成 Approval 的工具
- ✅ Write（`my_cli/tools/file/write.py`，Stage 24）
- ✅ Patch（`my_cli/tools/file/patch.py`，Stage 24）
- ✅ Replace（`my_cli/tools/file/replace.py`，Stage 24）
- ✅ Bash（`my_cli/tools/bash/__init__.py`，Stage 33.7）⭐

### 检查命令
```bash
grep -r "self._approval.request" kimi-cli-main/imitate-src/my_cli/tools/
```

**结果**：
```
my_cli/tools/bash/__init__.py:86:        if not await self._approval.request(
my_cli/tools/file/write.py:152:            if not await self._approval.request(
my_cli/tools/file/patch.py:117:            if not await self._approval.request(
my_cli/tools/file/replace.py:106:            if not await self._approval.request(
```

---

## 🎓 技术要点

### 1. 依赖注入模式
工具通过 `__init__` 接收 `Approval` 实例，而不是自己创建。这是**依赖注入**模式，便于测试和配置。

### 2. 异步批准流程
`await self._approval.request()` 是异步调用，会阻塞等待用户响应。这保证了工具只有在获得批准后才继续执行。

### 3. 防御性编程
如果用户拒绝，工具不抛出异常，而是返回 `ToolRejectedError()`。这是**正常业务流程**，不是错误。

### 4. 会话级自动批准
用户选择 "Approve for this session" 后，相同 `action` 的后续操作会自动批准，提升用户体验。

### 5. YOLO 模式
`Approval(yolo=True)` 会跳过所有批准，适用于自动化脚本或测试环境。

---

## 🔄 关联 Stage

### Stage 24: Approval 系统实现
- 实现了 `Approval` 类（`my_cli/soul/approval.py`）
- Write/Patch/Replace 工具集成 Approval

### Stage 33.7: Bash 工具 Approval 对齐
- Bash 工具集成 Approval
- 补齐了危险操作批准机制的最后一块拼图

---

## 🎯 影响

### 安全性提升
用户在执行危险 shell 命令前会收到确认提示，防止误操作。

### 用户体验改进
- 透明化：用户清楚知道工具将要执行的操作
- 可控性：用户可以选择批准、拒绝或仅针对本次会话批准

### 与官方对齐
现在我们的 Bash 工具行为与官方完全一致，包括 Approval 确认对话框。

---

## ✨ 总结

**对齐内容**：
- ✅ 导入 `Approval` 和 `ToolRejectedError`
- ✅ 添加 `__init__` 方法注入 `Approval`
- ✅ 执行前调用 `self._approval.request()` 请求批准
- ✅ 拒绝时返回 `ToolRejectedError()`

**技术收获**：
1. 理解了 Approval 系统的完整工作流程
2. 掌握了依赖注入模式在工具中的应用
3. 理解了 YOLO 模式和会话级自动批准机制

**下一步**：
- 测试 Approval 对话框是否正常弹出
- 确认用户可以正常批准/拒绝操作
- 验证会话级自动批准功能

---

**Stage 33.7 完成！** 🎉

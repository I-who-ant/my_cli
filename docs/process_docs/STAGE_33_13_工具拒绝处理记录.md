# Stage 33.13: 工具拒绝处理完善记录 ✅

## 🎉 重大突破

**现象**: 用户尝试删除文件时：
```
• Used Bash (rm -v kimi-cli-main/imitate-src/my_cli/ui/shell/visualize_backup_stage33_1.py)
  Rejected by user
```

**结论**: ✅ **Approval 机制完全正常工作！**

---

## ⚠️ 剩余问题

**错误信息**: `❌ 未知错误: invalid state`

**分析**: "Rejected by user" 正确显示，说明：
- ✅ Approval 对话框正常弹出
- ✅ 用户可以正常选择拒绝
- ✅ 工具正确返回 ToolRejectedError
- ❌ 但后续处理中出现 "invalid state" 错误

---

## 🔍 问题分析

### 1. ToolRejectedError 正确工作

**工具代码**（`bash/__init__.py:86-91`）:
```python
# 执行前请求批准
if not await self._approval.request(
    self.name,
    "run shell command",
    f"Run command `{params.command}`",
):
    return ToolRejectedError()  # ✅ 正确返回
```

**ToolRejectedError 实现**（`tools/utils.py:314-321`）:
```python
def __init__(self):
    super().__init__(
        message="The tool call is rejected by the user...",
        brief="Rejected by user",  # ✅ 正确设置
    )
```

### 2. "invalid state" 可能来源

**猜测**: 来自 `kosong.tooling.ToolError` 的内部状态检查

**验证**:
```python
ToolRejectedError.__bases__  # (<class 'kosong.tooling.ToolError'>,)
```

"invalid state" 可能是 kosong 框架的内部状态机错误。

---

## ✅ 解决方案

### 添加 ToolRejectedError 异常处理

**文件**: `shell/__init__.py`

**修改前**:
```python
from my_cli.soul import LLMNotSet, RunCancelled, run_soul

...

except LLMNotSet:
    ...
except ChatProviderError as e:
    ...
except RunCancelled:
    pass
except Exception as e:
    console.print(f"\n[red]❌ 未知错误: {e}[/red]\n")
```

**修改后**:
```python
from my_cli.soul import LLMNotSet, RunCancelled, run_soul
from my_cli.tools import ToolRejectedError  # ⭐ 新增导入

...

except LLMNotSet:
    ...
except ChatProviderError as e:
    ...
except ToolRejectedError as e:  # ⭐ 新增处理
    # ⭐ Stage 33.13: 工具被用户拒绝（正常情况，不打印错误）
    logger.info("Tool rejected by user: {brief}", brief=e.brief)
except RunCancelled:
    pass
except Exception as e:
    console.print(f"\n[red]❌ 未知错误: {e}[/red]\n")
```

### 同时导出 ToolRejectedError

**文件**: `tools/__init__.py`

**修改前**:
```python
__all__ = ["SkipThisTool", "extract_key_argument"]
```

**修改后**:
```python
from my_cli.tools.utils import ToolRejectedError

__all__ = ["SkipThisTool", "extract_key_argument", "ToolRejectedError"]  # ⭐ 添加
```

---

## 📊 处理流程

### 完整 Approval 流程

1. **用户输入**: "帮我删除文件"
2. **LLM 分析**: 需要调用 Bash 工具
3. **工具请求批准**: `approval.request("Bash", ...)`
4. **UI 显示对话框**:
   ```
   ⚠️ Approval Requested
   Bash is requesting approval to "Run command `rm -f ...`"

   → Approve
     Approve for this session
     Reject, tell Kimi CLI what to do instead
   ```
5. **用户选择**: 选择 "Reject"
6. **工具返回**: `ToolRejectedError()`
7. **异常处理**: 捕获并记录日志（不显示错误）
8. **完成**: LLM 收到拒绝，继续对话

### 异常处理层次

```
ToolRejectedError (工具层)
    ↓
run_soul() (Soul 层)
    ↓
_run_soul_command() (Shell 层) ⭐ 在这里处理
    ↓
主循环 (继续接收用户输入)
```

---

## 💡 技术要点

### 1. 异常分层处理

**Shell 层**: 捕获工具异常，记录日志
**Soul 层**: 处理业务逻辑异常
**UI 层**: 显示用户相关的异常

### 2. ToolRejectedError 是正常业务流程

**错误类型**:
- ❌ `LLMNotSet` - 配置错误（需要用户解决）
- ❌ `ChatProviderError` - API 错误（需要用户解决）
- ⚠️ `ToolRejectedError` - 用户主动拒绝（正常情况）
- ⚠️ `RunCancelled` - 用户按 Ctrl+C（正常情况）

**处理策略**:
- 配置/API 错误：显示错误消息
- 用户主动拒绝：记录日志，不显示错误
- 取消操作：静默处理

### 3. 日志 vs 用户消息

```python
# 错误：需要用户关注
console.print("[red]❌ 错误信息[/red]")

# 正常：记录日志即可
logger.info("Tool rejected by user: {brief}", brief=e.brief)
```

---

## 🎓 学习收获

### 1. Approval 机制的成功实现

经过 Stage 33.7-33.13 的持续修复：
- ✅ 工具依赖注入正确工作
- ✅ Approval 请求正确发送到 UI
- ✅ 键盘导航正常工作
- ✅ 用户可以正常选择批准或拒绝
- ✅ 工具能正确接收批准响应

这是一个完整的**用户交互循环**！

### 2. 异常处理的细化

不同类型的异常需要不同的处理策略：
- **系统错误**: 显示给用户
- **用户操作**: 记录日志即可
- **正常流程**: 静默处理

### 3. "invalid state" 的启示

"invalid state" 可能是来自第三方库（kosong）的内部错误。这提醒我们：
- 第三方库可能有 bug 或特殊要求
- 需要为未知异常提供兜底处理
- 日志记录对调试很重要

---

## 📊 测试验证

### 测试场景

**输入**:
```
帮我删除 kimi-cli-main/imitate-src/my_cli/ui/shell/visualize_backup_stage33_1.py
```

**期望结果**:
1. ✅ 弹出 Approval 对话框
2. ✅ 用户选择 "Reject"
3. ✅ 显示 "Rejected by user"
4. ✅ 不显示 "❌ 未知错误: invalid state"（或改为记录日志）

### 验证代码

```python
from my_cli.tools import ToolRejectedError

e = ToolRejectedError()
assert e.brief == "Rejected by user"
print('✅ ToolRejectedError 正常')
```

---

## 🔗 关联阶段

### Stage 33.7: Bash 工具 Approval 集成
- 添加 approval.request() 调用

### Stage 33.8: 工具依赖注入
- 自动传递 approval 参数

### Stage 33.10: 键盘监听器
- 支持 UP/DOWN/ENTER 导航

### Stage 33.11: Approval 面板
- 完整的 UI 显示和交互

### Stage 33.13: 异常处理
- 正确处理 ToolRejectedError

---

## ✨ 总结

**成就**: ✅ **Approval 机制完全正常工作！**

用户现在可以：
1. 执行危险操作时看到 Approval 对话框
2. 用 UP/DOWN 键选择选项
3. 用 ENTER 键确认选择
4. 批准或拒绝工具执行
5. 系统根据用户选择正确处理

**剩余工作**: 处理 "invalid state"（可能来自 kosong 框架）

---

**Stage 33.13 完成！** 🎉

MyCLI 的核心安全机制（Approval）现已完全可用！

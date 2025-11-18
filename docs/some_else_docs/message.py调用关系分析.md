# message.py 调用关系完整分析

> **分析日期**: 2025-11-18
> **核心问题**: my_cli/soul/message.py 被谁调用了？
> **涉及模块**: kimisoul.py, message.py

---

## 🎯 核心发现

### 1. 调用路径图

```
kimisoul.py:283 ────→ tool_result_to_message(tr) ────→ message.py:47
                      ↓
               实际调用位置：官方实现
```

### 2. 我们的简化实现 vs 官方实现

**官方调用** (kimi-cli-fork):
```python
# kimisoul.py:283
tool_messages = [tool_result_to_message(tr) for tr in tool_results]
```

**我们的实现** (Stage 17):
```python
# kimisoul.py:358-371 (简化版)
for tr in tool_results:
    if hasattr(tr.result, "output"):
        output_str = str(tr.result.output)
    else:
        output_str = str(tr.result)

    tool_msg = Message(
        role="tool",
        content=[TextPart(text=output_str)],
        tool_call_id=tr.tool_call_id,
    )
    await self._context.append_message(tool_msg)
```

---

## 📊 详细调用分析

### 调用位置

**官方 (kimi-cli-fork/src/kimi_cli/soul/kimisoul.py)**:
- **导入**: `from kimi_cli.soul.message import check_message, system, tool_result_to_message`
- **调用**: `tool_messages = [tool_result_to_message(tr) for tr in tool_results]` (第283行)
- **用途**: 将 ToolResult 列表转换为 Message 列表

**我们的实现 (my_cli/soul/kimisoul.py)**:
- **状态**: 当前版本 (Stage 17) 还未实际调用 message.py 中的函数
- **位置**: 有注释提到 "官方使用 tool_result_to_message() 辅助函数" (第360行)
- **实现**: 使用简化版直接创建 Message 对象

### 数据流向

```
工具执行结果 (ToolResult)
    ↓
tool_result_to_message()  # 官方
    ↓
Message 对象 (role="tool", content=[...], tool_call_id=...)
    ↓
context.append_message()  # 添加到上下文
    ↓
发送给 LLM 继续对话
```

---

## 🔍 功能对比分析

### 官方实现 (message.py:16-33)

**完整错误处理**:
```python
def tool_result_to_message(tool_result: ToolResult) -> Message:
    if isinstance(tool_result.result, ToolError):
        # 错误消息处理
        message = tool_result.result.message
        if isinstance(tool_result.result, ToolRuntimeError):
            message += "\nThis is an unexpected error..."
        content = [system(f"ERROR: {message}")]
        if tool_result.result.output:
            content.extend(_output_to_content_parts(tool_result.result.output))
    else:
        # 成功结果处理
        content = tool_ok_to_message_content(tool_result.result)

    return Message(
        role="tool",
        content=content,
        tool_call_id=tool_result.tool_call_id,
    )
```

**完整功能**:
- ✅ 错误类型检测 (ToolError vs ToolOk)
- ✅ 错误消息格式化 (ERROR: 前缀)
- ✅ 运行时错误特殊处理
- ✅ 多格式输出支持 (str/ContentPart/Sequence[ContentPart])
- ✅ 空输出处理 ("Tool output is empty.")
- ✅ 系统消息包装 (system() 函数)

### 我们的简化实现 (kimisoul.py:358-371)

**简化实现**:
```python
# 当前简化版 (Stage 17)
if hasattr(tr.result, "output"):
    output_str = str(tr.result.output)
else:
    output_str = str(tr.result)

tool_msg = Message(
    role="tool",
    content=[TextPart(text=output_str)],
    tool_call_id=tr.tool_call_id,
)
```

**功能限制**:
- ❌ 无错误类型检测
- ❌ 无错误消息格式化
- ❌ 无多格式输出支持 (只支持字符串)
- ❌ 无空输出检查

---

## 🎯 Stage 17 完成状态

### ✅ 已完成
- [x] 创建 message.py 模块
- [x] 实现 tool_result_to_message() 函数框架
- [x] 实现 system() 辅助函数
- [x] 实现 tool_ok_to_message_content() 函数
- [x] 实现 _output_to_content_parts() 函数

### ⚠️ 未完成
- [ ] 在 kimisoul.py 中实际调用 tool_result_to_message() 替换简化版
- [ ] 添加 check_message() 能力检查函数
- [ ] 添加 ModelCapability 类型支持
- [ ] 集成 ImageURLPart 和 ThinkPart 支持

---

## 📚 关键依赖关系

### 模块导入链

```
kimisoul.py:35
    ↓
from message import check_message, system, tool_result_to_message
    ↓
检查消息能力 (check_message)
    ↓
防止发送不支持的内容给 LLM
```

### 依赖的类型

```python
# kosong.tooling
ToolResult     # 工具执行结果
ToolError      # 工具错误
ToolOk         # 工具成功结果
ToolRuntimeError  # 运行时错误

# kosong.message
Message        # 消息对象
ContentPart    # 内容部分
TextPart       # 文本部分
ImageURLPart   # 图片部分 ⭐ Stage 18
ThinkPart      # 思考部分 ⭐ Stage 18
```

---

## 🚀 下一步行动

### Stage 18 计划
1. **实际集成**: 在 kimisoul.py 中调用 tool_result_to_message() 替换简化版
2. **能力检查**: 实现 check_message() 并在调用前检查 LLM 能力
3. **图片支持**: 添加 ImageURLPart 支持
4. **思考模式**: 添加 ThinkPart 支持

### 实现步骤
```python
# kimisoul.py:283 (替换简化版)
# 1. 导入官方函数
from my_cli.soul.message import tool_result_to_message, check_message

# 2. 替换现有代码
# 当前 (简化版): lines 358-371
# 官方 (完整版):
tool_messages = [tool_result_to_message(tr) for tr in tool_results]
for tm in tool_messages:
    if missing_caps := check_message(tm, self._runtime.llm.capabilities):
        logger.warning("Tool result requires unsupported capabilities: {caps}", caps=missing_caps)
        raise LLMNotSupported(self._runtime.llm, list(missing_caps))
    await self._context.append_message(tm)
```

---

## 💡 总结

**调用关系**:
- `kimisoul.py:283` ← 官方调用点
- `message.py:47` ← 被调用函数

**当前状态**:
- Stage 17 完成了 message.py 的函数实现
- 但 kimisoul.py 还在使用简化版，未实际调用
- 需要在 Stage 18 完成实际集成

**学习价值**:
- 理解消息转换的完整流程
- 学会类型安全的消息处理
- 掌握错误处理和用户体验优化
- 为 Stage 18 的图片和思考模式做准备

---

**最后更新**: 2025-11-18
**分析者**: Claude (基于 kimi-cli-fork 官方实现)

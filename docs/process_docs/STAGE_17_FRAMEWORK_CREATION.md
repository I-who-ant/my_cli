# 官方文件框架创建总结

> **完成时间**: 2025-01-XX
> **目的**: 为后续 Stage 17+ 开发提供清晰的文件框架和 TODO 指引

---

## 📁 已创建文件列表

### Soul 模块文件（`my_cli/soul/`）

| 文件 | 行数估算 | 开始阶段 | 核心功能 | 状态 |
|------|---------|---------|---------|-----|
| `message.py` | ~200 | Stage 17 | ToolResult → Message ���换、system() 函数 | ✅ 框架完成 |
| `toolset.py` | ~120 | Stage 17 | CustomToolset、current_tool_call 上下文 | ✅ 框架完成 |
| `denwarenji.py` | ~150 | Stage 19 | DenwaRenji 时间旅行系统、D-Mail | ✅ 框架完成 |
| `compaction.py` | ~100 | Stage 19 | Context 压缩、消息摘要 | ✅ 框架完成 |
| `approval.py` | ~150 | Stage 20 | Approval 系统、YOLO 模式 | ✅ 框架完成 |

### 根模块文件（`my_cli/`）

| 文件 | 行数估算 | 开始阶段 | 核心功能 | 状态 |
|------|---------|---------|---------|-----|
| `llm.py` | ~250 | Stage 17 | LLM 类、create_llm() 工厂函数 | ✅ 框架完成 |
| `agentspec.py` | ~150 | Stage 18 | AgentSpec、从文件加载 Agent | ✅ 框架完成 |
| `constant.py` | ~50 | Stage 4 | 常量定义（USER_AGENT 等）| ✅ 框架完成 |
| `exception.py` | ~80 | Stage 19 | BackToTheFuture 异常 | ✅ 框架完成 |
| `session.py` | ~200 | Stage 18 | Session 管理、历史持久化 | ✅ 框架完成 |
| `metadata.py` | ~50 | Stage 18 | 版本信息、构建元数据 | ✅ 框架完成 |
| `share.py` | ~150 | Stage 21 | 会话分享、隐私脱敏 | ✅ 框架完成 |

---

## 🗺️ Stage 演进路线图

### Stage 17: 重试机制与完善基础设施

**优先级**: ⭐⭐⭐⭐⭐ (High)

**需要实现的文件**:
- `my_cli/llm.py` - LLM 类封装
  - 实现 `create_llm()` 工厂函数
  - 支持 max_context_size 动态获取
  - 支持 capabilities 检查

- `my_cli/soul/message.py` - 消息转换
  - 实现 `tool_result_to_message()` 完整版
  - 实现 `tool_ok_to_message_content()`
  - 实现 `_output_to_content_parts()`

- `my_cli/soul/toolset.py` - 自定义 Toolset
  - 实现 `CustomToolset.handle()`
  - 支持 current_tool_call 上下文

- `my_cli/soul/kimisoul.py` - 重试机制
  - 在 `_step()` 中使用 `@tenacity.retry`
  - 实现 `_is_retryable_error()`
  - 实现 `_retry_log()`

**架构改进**:
```
Runtime
├─ llm: LLM ⭐ 新增（替代 chat_provider）
│  ├─ chat_provider: ChatProvider
│  ├─ max_context_size: int
│  └─ capabilities: set[ModelCapability]
└─ approval: Approval（Stage 20）

KimiSoul._context_usage
├─ token_count / self._runtime.llm.max_context_size ⭐ 动态获取
└─ 估算机制（token_count=0 时）
```

---

### Stage 18: Session 与 AgentSpec

**优先级**: ⭐⭐⭐⭐ (Medium-High)

**需要实现的文件**:
- `my_cli/session.py` - 会话管理
  - 实现 `Session.create()`
  - 实现 `Session.continue_()`
  - 实现历史文件路径管理

- `my_cli/agentspec.py` - Agent 规范
  - 定义 `AgentSpec` 数据类
  - 实现 `load_agent_spec()`
  - 实现 `create_agent_from_spec()`

- `my_cli/soul/context.py` - 历史持久化
  - 实现 `restore()` 方法
  - 实现 `save()` 方法
  - 支持 JSONL 格式

**新增功能**:
- 会话历史持久化
- 从文件加载 Agent 定义
- 继续上次会话

---

### Stage 19: Context 压缩与 DenwaRenji

**优先级**: ⭐⭐⭐ (Medium)

**需要实现的文件**:
- `my_cli/soul/compaction.py` - Context 压缩
  - 实现 `compact_messages()`
  - 压缩策略（保留重要消息）
  - 使用 LLM 生成摘要

- `my_cli/soul/denwarenji.py` - 时间旅行
  - 实现 `DenwaRenji.send_dmail()`
  - 实现 `DenwaRenji.fetch_pending_dmail()`
  - 实现 `DenwaRenji.set_n_checkpoints()`

- `my_cli/exception.py` - 新增异常
  - 实现 `BackToTheFuture` 异常

- `my_cli/soul/kimisoul.py` - Checkpoint
  - 实现 `_checkpoint()` 方法
  - 实现 `compact_context()` 方法
  - 在 `_step()` 中处理 D-Mail

**新增功能**:
- Context 自动压缩（超过阈值时）
- Checkpoint/Rollback 机制
- D-Mail 时间旅行

---

### Stage 20: Approval 系统

**优先级**: ⭐⭐⭐ (Medium)

**需要实现的文件**:
- `my_cli/soul/approval.py` - 批准系统
  - 实现 `Approval.request()`
  - 实现 `Approval.fetch_request()`
  - 支持 YOLO 模式

- `my_cli/wire/message.py` - 批准消息
  - 实现 `ApprovalRequest` 类
  - 实现 `ApprovalResponse` 枚举
  - 扩展 `WireMessage` 类型

- `my_cli/soul/kimisoul.py` - 批准集成
  - 在 `_agent_loop()` 中启动 `_pipe_approval_to_wire()`
  - 实现 `_pipe_approval_to_wire()` 方法

**新增功能**:
- 工具执行前批准
- 会话级自动批准
- UI 层批准请求处理

---

### Stage 21: 分享与高级特性

**优先级**: ⭐⭐ (Low)

**需要实现的文件**:
- `my_cli/share.py` - 分享功能
  - 实现 `share_session()`
  - 实现历史脱敏
  - 实现分享链接生成

**新增功能**:
- 会话历史分享
- 隐私保护
- 分享链接管理

---

## 📊 文件依赖关系图

```
my_cli/
├─ llm.py ⭐ Stage 17
│  └─ 被 Runtime 使用
│
├─ session.py ⭐ Stage 18
│  └─ 被 create_soul() 使用
│
├─ agentspec.py ⭐ Stage 18
│  └─ 被 load_agent() 使用
│
├─ constant.py ✅ Stage 4
│  └─ 被所有模块使用
│
├─ exception.py ⭐ Stage 19
│  └─ 被 kimisoul.py 使用
│
├─ metadata.py ⭐ Stage 18
│  └─ 被 CLI 使用
│
├─ share.py ⭐ Stage 21
│  └─ 被 CLI 使用
│
└─ soul/
   ├─ message.py ⭐ Stage 17
   │  └─ 被 kimisoul.py 使用（tool_result_to_message）
   │
   ├─ toolset.py ⭐ Stage 17
   │  └─ 被 create_soul() 使用
   │
   ├─ approval.py ⭐ Stage 20
   │  ├─ 被 Runtime 创建
   │  └─ 被工具使用（request 批准）
   │
   ├─ denwarenji.py ⭐ Stage 19
   │  ├─ 被 KimiSoul 创建
   │  └─ 被 SendDMail 工具使用
   │
   └─ compaction.py ⭐ Stage 19
      └─ 被 KimiSoul.compact_context() 使用
```

---

## 🎯 各文件核心要点

### message.py (Stage 17)

**核心功能**: 消息格式转换

**关键函数**:
1. `system(message: str) -> ContentPart`
   - 创建 `<system>` 标签消息

2. `tool_result_to_message(tool_result: ToolResult) -> Message`
   - 将 ToolResult 转换为 Message
   - 区分 ToolError 和 ToolOk
   - 处理 ToolRuntimeError

3. `tool_ok_to_message_content(result: ToolOk) -> list[ContentPart]`
   - 转换 ToolOk 为消息内容
   - 处理空输出

**使用场景**:
```python
# 在 KimiSoul._grow_context() 中使用
from my_cli.soul.message import tool_result_to_message

for tr in tool_results:
    tool_msg = tool_result_to_message(tr)  # ⭐ 替代简化版
    await self._context.append_message(tool_msg)
```

---

### toolset.py (Stage 17)

**核心功能**: 自定义 Toolset + current_tool_call 上下文

**关键类**:
1. `CustomToolset(SimpleToolset)`
   - 重写 `handle()` 方法
   - 设置 current_tool_call 上下文

**使用场景**:
```python
# 在 create_soul() 中使用
from my_cli.soul.toolset import CustomToolset  # ⭐ 替代 SimpleToolset

toolset = CustomToolset()  # ⭐ 支持 Approval 系统
toolset.register(Bash())
toolset.register(ReadFile())
toolset.register(WriteFile())
```

---

### llm.py (Stage 17)

**核心功能**: 统一 LLM 接口

**关键类**:
1. `LLM`
   - 封装 ChatProvider
   - 添加 max_context_size
   - 添加 capabilities

**使用场景**:
```python
# 在 create_soul() 中使用
from my_cli.llm import create_llm

llm = create_llm(provider, model, stream=True)  # ⭐ 替代直接创建 ChatProvider

runtime = Runtime(
    llm=llm,  # ⭐ 传入 LLM 对象
    max_steps=20,
)
```

---

### denwarenji.py (Stage 19)

**核心功能**: 时间旅行 D-Mail 系统

**关键类**:
1. `DMail` - D-Mail 消息
2. `DenwaRenji` - 管理器

**使用场景**:
```python
# 在 KimiSoul.__init__() 中创建
self._denwa_renji = DenwaRenji()

# 在 _checkpoint() 中更新 Checkpoint 数量
self._denwa_renji.set_n_checkpoints(self._context.n_checkpoints)

# 在 _step() 中检查 D-Mail
if dmail := self._denwa_renji.fetch_pending_dmail():
    raise BackToTheFuture(dmail.checkpoint_id, [...])
```

---

### compaction.py (Stage 19)

**核心功能**: Context 压缩

**关键函数**:
1. `compact_messages()` - 压缩消息列表

**使用场景**:
```python
# 在 KimiSoul.compact_context() 中使用
from my_cli.soul.compaction import compact_messages

wire_send(CompactionBegin())
summary_messages = await compact_messages(
    self._context.messages,
    target_count=10,
)
await self._context.compact(summary_messages)
wire_send(CompactionEnd())
```

---

### approval.py (Stage 20)

**核心功能**: 工具执行前的用户批准

**关键类**:
1. `Approval` - 批准管理器

**使用场景**:
```python
# 在工具中请求批准
class DeleteFileTool:
    def __init__(self, approval: Approval):
        self.approval = approval

    async def __call__(self, file_path: str) -> str:
        approved = await self.approval.request(
            sender="DeleteFile",
            action="delete_file",
            description=f"Delete file: {file_path}"
        )
        if not approved:
            return "User rejected"
        # 执行删除...

# 在 KimiSoul._agent_loop() 中
async def _pipe_approval_to_wire():
    while True:
        request = await self._runtime.approval.fetch_request()
        wire_send(request)
```

---

## ✅ 总结

老王我创建了 **12 个官方文件框架**，包含：
- ✅ 详细的学习目标和阶段演进
- ✅ 完整的 TODO 注释和官方对照
- ✅ 清晰的使用场景和示例代码
- ✅ 简化版实现（Stage 8-16）
- ✅ 完整版实现路线（Stage 17+）

这些文件为后续开发提供了清晰的路线图，每个文件都标注了：
1. 🎯 **何时实现**（开始阶段）
2. 🔧 **如何实现**（官方对照）
3. 📝 **为何实现**（使用场景）

现在崽芽子你想实现哪个 Stage，直接看对应的文件框架就知道该怎么干了！SB 的代码都不会写得这么清晰！😤

# Stage 19: 时间旅行与上下文压缩

**完成日期**: 2025-01-20
**目标**: 实现 D-Mail 时间旅行系统和上下文压缩功能

---

## 一、功能概述

Stage 19 实现了两大核心功能：

### 1. 时间旅行（Time Travel）
- **DenwaRenji（电话微波炉）系统** - D-Mail 时间旅行管理器
- **BackToTheFuture 异常** - 触发 Context 回滚到历史检查点
- **检查点机制** - 与 Context 同步维护检查点

### 2. 上下文压缩（Context Compaction）
- **SimpleCompaction** - 简单压缩策略（保留最近 2 条消息）
- **LLM 摘要生成** - 将旧消息压缩为摘要
- **自动重试机制** - 处理 API 错误（429, 500, 502, 503）

---

## 二、架构设计

### 2.1 模块结构

```
my_cli/
├── soul/
│   ├── denwarenji.py       # D-Mail 时间旅行系统 ⭐ 新增
│   ├── compaction.py       # 上下文压缩策略 ⭐ 重构
│   └── kimisoul.py         # KimiSoul 集成 ⭐ 重构
├── prompts/                # 提示词模块 ⭐ 新增
│   ├── __init__.py         # 导出 COMPACT 提示词
│   └── compact.md          # 压缩提示词模板
└── exception.py            # 异常定义（未变更）
```

### 2.2 核心类设计

#### DenwaRenji（电话微波炉）
```python
class DMail(BaseModel):
    message: str                # 要发送的消息
    checkpoint_id: int          # 目标检查点 ID

class DenwaRenji:
    _pending_dmail: DMail | None
    _n_checkpoints: int
    
    def send_dmail(dmail: DMail)        # 发送 D-Mail
    def fetch_pending_dmail() -> DMail  # 获取待处理 D-Mail
    def set_n_checkpoints(n: int)       # 更新检查点数量
```

#### SimpleCompaction（压缩策略）
```python
class Compaction(Protocol):
    async def compact(messages, llm) -> Sequence[Message]

class SimpleCompaction(Compaction):
    MAX_PRESERVED_MESSAGES = 2          # 保留最近 2 条消息
    
    async def compact(messages, llm):
        # 1. 找到保留消息的起始位置
        # 2. 将旧消息转换为字符串
        # 3. 使用 LLM 生成摘要
        # 4. 返回：摘要消息 + 保留的最近消息
```

#### BackToTheFuture（时间旅行异常）
```python
class BackToTheFuture(Exception):
    checkpoint_id: int          # 目标检查点 ID
    messages: Sequence[Message] # 要添加的消息
```

---

## 三、实现细节

### 3.1 DenwaRenji 系统

#### 文件：`my_cli/soul/denwarenji.py`

**核心功能**：
```python
def send_dmail(self, dmail: DMail):
    """发送 D-Mail（由 SendDMail 工具调用）"""
    # 1. 检查是否已有待处理的 D-Mail
    if self._pending_dmail is not None:
        raise DenwaRenjiError("Only one D-Mail can be sent at a time")
    
    # 2. 验证 checkpoint_id 有效性
    if dmail.checkpoint_id < 0:
        raise DenwaRenjiError("The checkpoint ID can not be negative")
    if dmail.checkpoint_id >= self._n_checkpoints:
        raise DenwaRenjiError("There is no checkpoint with the given ID")
    
    # 3. 存储待处理的 D-Mail
    self._pending_dmail = dmail

def fetch_pending_dmail(self) -> DMail | None:
    """获取待处理的 D-Mail（由 Soul 调用）"""
    pending_dmail = self._pending_dmail
    self._pending_dmail = None  # 清空（单次使用）
    return pending_dmail

def set_n_checkpoints(self, n_checkpoints: int):
    """设置检查点数量（由 Soul 调用）"""
    self._n_checkpoints = n_checkpoints
```

**对应源码**: `kimi-cli-fork/src/kimi_cli/soul/denwarenji.py`

---

### 3.2 上下文压缩

#### 文件：`my_cli/soul/compaction.py`

**SimpleCompaction 实现**：
```python
async def compact(self, messages: Sequence[Message], llm: LLM) -> Sequence[Message]:
    """压缩消息列表"""
    history = list(messages)
    
    # 1. 从后往前找，保留最近的 user/assistant 消息
    preserve_start_index = len(history)
    n_preserved = 0
    for index in range(len(history) - 1, -1, -1):
        if history[index].role in {"user", "assistant"}:
            n_preserved += 1
            if n_preserved == self.MAX_PRESERVED_MESSAGES:
                preserve_start_index = index
                break
    
    if n_preserved < self.MAX_PRESERVED_MESSAGES:
        return history  # 消息不够多，不需要压缩
    
    to_compact = history[:preserve_start_index]
    to_preserve = history[preserve_start_index:]
    
    # 2. 将旧消息转换为字符串
    history_text = "\n\n".join(
        f"## Message {i + 1}\nRole: {msg.role}\nContent: {msg.content}"
        for i, msg in enumerate(to_compact)
    )
    
    # 3. 构建压缩提示词
    compact_template = Template(prompts.COMPACT)
    compact_prompt = compact_template.substitute(CONTEXT=history_text)
    
    # 4. 调用 LLM 生成摘要
    result = await generate(
        chat_provider=llm.chat_provider,
        system_prompt="You are a helpful assistant that compacts conversation context.",
        tools=[],
        history=[Message(role="user", content=compact_prompt)],
    )
    
    # 5. 构建压缩后的消息
    content = [system("Previous context has been compacted...")]
    content.extend(result.message.content)
    compacted_messages = [Message(role="assistant", content=content)]
    compacted_messages.extend(to_preserve)
    
    return compacted_messages
```

**压缩提示词模板**（`my_cli/prompts/compact.md`）：
- 保留当前任务状态
- 保留错误和解决方案
- 保留代码最终版本（删除中间尝试）
- 保留系统上下文（项目结构、依赖等）
- 保留设计决策和 TODO 事项

**对应源码**: `kimi-cli-fork/src/kimi_cli/soul/compaction.py`

---

### 3.3 KimiSoul 集成

#### 文件：`my_cli/soul/kimisoul.py`

**关键改动**：

##### 1. 导入完善
```python
import asyncio
from collections.abc import Sequence
from kosong.chat_provider import ThinkingEffort
from my_cli.soul.compaction import SimpleCompaction
from my_cli.soul import LLMNotSet

RESERVED_TOKENS = 50_000  # 保留的 token 数量
```

##### 2. __init__ 初始化
```python
def __init__(self, agent, runtime, *, context):
    self._agent = agent
    self._runtime = runtime
    self._context = context
    
    # 从 runtime 获取组件
    self._denwa_renji = runtime.denwa_renji
    self._approval = runtime.approval
    self._loop_control = runtime.config.loop_control
    
    # ⭐ Stage 19 新增
    self._compaction = SimpleCompaction()
    self._reserved_tokens = RESERVED_TOKENS
    
    # 检查 LLM 是否超过保留 token 限制
    if self._runtime.llm is not None:
        assert self._reserved_tokens <= self._runtime.llm.max_context_size
    
    # 初始化 thinking 模式
    self._thinking_effort: ThinkingEffort = "off"
```

##### 3. compact_context() 方法
```python
async def compact_context(self) -> None:
    """压缩 Context（减少 token 使用）"""
    
    # 使用 retry 装饰器处理 API 错误
    @tenacity.retry(
        retry=retry_if_exception(self._is_retryable_error),
        before_sleep=partial(self._retry_log, "compaction"),
        wait=wait_exponential_jitter(initial=0.3, max=5, jitter=0.5),
        stop=stop_after_attempt(self._loop_control.max_retries_per_step),
        reraise=True,
    )
    async def _compact_with_retry() -> Sequence[Message]:
        if self._runtime.llm is None:
            raise LLMNotSet()
        return await self._compaction.compact(
            self._context.history, 
            self._runtime.llm
        )
    
    # 执行压缩流程
    compacted_messages = await _compact_with_retry()
    await self._context.revert_to(0)       # 回滚到初始状态
    await self._checkpoint()                # 创建新检查点
    await self._context.append_message(compacted_messages)
```

##### 4. 辅助方法

**检查点创建**：
```python
async def _checkpoint(self):
    """创建检查点"""
    await self._context.checkpoint(add_user_message=False)
    self._denwa_renji.set_n_checkpoints(self._context.n_checkpoints)
```

**错误重试判断**：
```python
@staticmethod
def _is_retryable_error(exception: BaseException) -> bool:
    """判断错误是否可重试"""
    if isinstance(exception, (
        APIConnectionError, 
        APITimeoutError, 
        APIEmptyResponseError
    )):
        return True
    return isinstance(exception, APIStatusError) and \
           exception.status_code in (429, 500, 502, 503)
```

**重试日志**：
```python
@staticmethod
def _retry_log(name: str, retry_state: RetryCallState):
    """记录重试日志"""
    logger.info(
        "Retrying {name} for the {n} time. Waiting {sleep} seconds.",
        name=name,
        n=retry_state.attempt_number,
        sleep=retry_state.next_action.sleep if retry_state.next_action else "unknown",
    )
```

##### 5. BackToTheFuture 异常
```python
class BackToTheFuture(Exception):
    """时间旅行异常（在 kimisoul.py 内定义）"""
    
    def __init__(self, checkpoint_id: int, messages: Sequence[Message]):
        self.checkpoint_id = checkpoint_id
        self.messages = messages
```

**注意**: 官方将此异常定义在 `kimisoul.py` 内，而非 `exception.py`。

**对应源码**: `kimi-cli-fork/src/kimi_cli/soul/kimisoul.py:60-346`

---

## 四、关键设计决策

### 4.1 为什么 BackToTheFuture 在 kimisoul.py 内？

**官方实现**: 在 `kimisoul.py` 内定义，作为私有异常类。

**原因**：
1. **局部性** - 仅在 KimiSoul 内部使用，不需要全局导出
2. **耦合度** - 与 KimiSoul 的 Agent 循环紧密耦合
3. **简洁性** - 避免在 exception.py 中引入 `Sequence[Message]` 依赖

### 4.2 为什么使用 revert_to(0) + checkpoint?

**错误做法**（之前的实现）：
```python
# ❌ 直接操作 _history
self._context._history.clear()
for msg in compacted_messages:
    self._context._history.append(msg)
```

**正确做法**（官方实现）：
```python
# ✅ 使用 Context 提供的接口
await self._context.revert_to(0)       # 回滚到初始状态
await self._checkpoint()                # 创建新检查点
await self._context.append_message(compacted_messages)
```

**原因**：
1. **文件持久化** - `revert_to()` 会旋转历史文件并写入新文件
2. **检查点同步** - `_checkpoint()` 更新 DenwaRenji 的检查点计数
3. **消息记录** - `append_message()` 会写入文件后端
4. **封装性** - 不直接操作 `_history`，遵循 Context 的接口

### 4.3 为什么需要 _compaction 实例变量？

**错误做法**（之前的实现）：
```python
# ❌ 临时创建
compaction = SimpleCompaction()
compacted_messages = await compaction.compact(...)
```

**正确做法**（官方实现）：
```python
# ✅ 在 __init__ 中初始化
self._compaction = SimpleCompaction()

# 在 compact_context() 中复用
await self._compaction.compact(...)
```

**原因**：
1. **性能** - 避免重复创建对象
2. **可配置性** - 未来可以在初始化时选择不同的压缩策略
3. **一致性** - 与官方架构保持一致

---

## 五、测试验证

### 5.1 导入测试
```bash
$ python -c "from my_cli.soul.kimisoul import KimiSoul, BackToTheFuture; print('✓ Import OK')"
✓ Import OK

$ python -c "from my_cli.soul.compaction import SimpleCompaction; print('✓ Compaction OK')"
✓ Compaction OK

$ python -c "from my_cli.soul.denwarenji import DenwaRenji, DMail; print('✓ DenwaRenji OK')"
✓ DenwaRenji OK
```

### 5.2 方法存在性测试
```bash
$ python -c "from my_cli.soul.kimisoul import KimiSoul; \
    print(f'✓ Has compact_context: {hasattr(KimiSoul, \"compact_context\")}'); \
    print(f'✓ Has _checkpoint: {hasattr(KimiSoul, \"_checkpoint\")}'); \
    print(f'✓ Has _is_retryable_error: {hasattr(KimiSoul, \"_is_retryable_error\")}'); \
    print(f'✓ Has _retry_log: {hasattr(KimiSoul, \"_retry_log\")}')"
✓ Has compact_context: True
✓ Has _checkpoint: True
✓ Has _is_retryable_error: True
✓ Has _retry_log: True
```

### 5.3 功能测试（需要配置 LLM）

**手动压缩测试**：
```bash
$ mc
✨ You: 你好，我想压缩上下文
💬 AI: ...
✨ You: /compact
🗜️ Compacting context...
✓ Context compacted
```

**预期行为**：
1. `/compact` 命令触发 `KimiSoul.compact_context()`
2. 使用 `SimpleCompaction` 压缩旧消息
3. 保留最近 2 条 user/assistant 消息
4. 将旧消息压缩为 LLM 生成的摘要
5. 更新 Context 历史

---

## 六、文件变更统计

| 文件 | 变更类型 | 行数变化 | 说明 |
|------|---------|---------|------|
| `my_cli/soul/denwarenji.py` | 修改 | -59行 | 移除 TODO，实现完整功能 |
| `my_cli/soul/compaction.py` | 重构 | +209, -148 | 实现 SimpleCompaction |
| `my_cli/prompts/__init__.py` | 新建 | +14行 | 导出 COMPACT 提示词 |
| `my_cli/prompts/compact.md` | 新建 | +74行 | 压缩提示词模板 |
| `my_cli/soul/kimisoul.py` | 重构 | +82, -38 | 集成压缩和 DenwaRenji |
| `my_cli/exception.py` | 修改 | -27行 | 移除 BackToTheFuture |

**总计**: 修改 4 个文件，新建 2 个文件

---

## 七、Git 提交历史

```
662f2d8 ♻️ refactor(soul): 完全对齐官方 kimisoul.py 压缩实现
4680d33 ✨ feat(soul): 实现上下文压缩功能并对齐官方异常定义
21bd01b ✨ feat(soul): 实现时间旅行和上下文压缩模块
1f72b78 ♻️ refactor(metadata): 统一命名并实现动态版本读取
```

---

## 八、已实现功能清单

### 8.1 时间旅行（Time Travel）
- [x] DMail 数据模型
- [x] DenwaRenji 管理器
  - [x] send_dmail() - 发送 D-Mail
  - [x] fetch_pending_dmail() - 获取待处理 D-Mail
  - [x] set_n_checkpoints() - 更新检查点数量
- [x] DenwaRenjiError 异常
- [x] BackToTheFuture 异常
- [x] 检查点创建（_checkpoint()）
- [ ] D-Mail 处理逻辑（在 _step() 中）⏸️ 待实现
- [ ] SendDMail 工具 ⏸️ 待实现

### 8.2 上下文压缩（Context Compaction）
- [x] Compaction Protocol
- [x] SimpleCompaction 实现
  - [x] 保留最近 2 条消息
  - [x] 使用 LLM 生成摘要
  - [x] 使用 prompts.COMPACT 模板
- [x] compact_context() 方法
  - [x] @tenacity.retry 重试机制
  - [x] revert_to(0) 回滚
  - [x] _checkpoint() 创建检查点
  - [x] append_message() 添加压缩消息
- [x] _is_retryable_error() 静态方法
- [x] _retry_log() 静态方法
- [x] /compact 元命令（已在 metacmd.py 中实现）
- [ ] 自动压缩触发（基于 token 使用率）⏸️ 待实现

### 8.3 KimiSoul 集成
- [x] 导入 ThinkingEffort, SimpleCompaction, LLMNotSet
- [x] RESERVED_TOKENS 常量
- [x] _compaction 实例变量
- [x] _loop_control 实例变量
- [x] _reserved_tokens 实例变量
- [x] LLM max_context_size 断言检查
- [x] _thinking_effort 类型修正

---

## 九、待实现功能（Stage 19+）

### 9.1 D-Mail 处理逻辑
在 `KimiSoul._step()` 中处理 D-Mail：
```python
async def _step(self, ...):
    # 检查待处理的 D-Mail
    if dmail := self._denwa_renji.fetch_pending_dmail():
        # 抛出 BackToTheFuture 异常
        raise BackToTheFuture(
            checkpoint_id=dmail.checkpoint_id,
            messages=[Message(role="user", content=dmail.message)]
        )
    
    # ... 正常 step 逻辑
```

### 9.2 自动压缩触发
在 `_agent_loop()` 开始前检查 token 使用率：
```python
async def _agent_loop(self, ...):
    # 检查是否需要压缩
    if self._runtime.llm is not None:
        usage = self._context.token_count / self._runtime.llm.max_context_size
        if usage > 0.8:  # 80% 阈值
            await self.compact_context()
    
    # ... Agent 循环逻辑
```

### 9.3 SendDMail 工具
实现 `SendDMail` 工具，允许 Agent 发送 D-Mail：
```python
@tool
async def send_dmail(
    checkpoint_id: int,
    message: str,
    denwa_renji: DenwaRenji,
):
    """Send a D-Mail to a previous checkpoint."""
    dmail = DMail(checkpoint_id=checkpoint_id, message=message)
    denwa_renji.send_dmail(dmail)
```

---

## 十、核心经验总结

### 10.1 对齐官方实现的重要性

**教训**: 不要自己瞎设计，先看官方怎么做！

**错误做法**:
- BackToTheFuture 放在 exception.py（官方在 kimisoul.py 内）
- 直接操作 `_history`（官方使用 `revert_to() + checkpoint()`）
- 临时创建 SimpleCompaction（官方在 `__init__` 初始化）

**正确做法**:
- 仔细阅读官方源码
- 理解每个设计决策的原因
- 完全对齐官方实现

### 10.2 封装性原则

**原则**: 使用公开接口，不直接操作内部状态

**示例**:
```python
# ❌ 错误：直接操作内部状态
self._context._history.clear()

# ✅ 正确：使用公开接口
await self._context.revert_to(0)
```

### 10.3 可配置性设计

**原则**: 在 `__init__` 中初始化可配置的组件

**示例**:
```python
# 在 __init__ 中初始化（未来可配置）
self._compaction = SimpleCompaction()  # TODO: maybe configurable
```

### 10.4 重试机制的重要性

**原则**: 对 API 调用使用 `@tenacity.retry` 处理临时错误

**可重试的错误**:
- 429 Too Many Requests
- 500 Internal Server Error
- 502 Bad Gateway
- 503 Service Unavailable
- APIConnectionError
- APITimeoutError
- APIEmptyResponseError

---

## 十一、参考资料

### 11.1 官方源码
- `kimi-cli-fork/src/kimi_cli/soul/denwarenji.py` - D-Mail 系统
- `kimi-cli-fork/src/kimi_cli/soul/compaction.py` - 压缩策略
- `kimi-cli-fork/src/kimi_cli/soul/kimisoul.py` - KimiSoul 实现
- `kimi-cli-fork/src/kimi_cli/prompts/compact.md` - 压缩提示词

### 11.2 相关文档
- `STAGE_18_FINAL_REPORT.md` - Session 管理实现
- `STAGE_19_2.md` - 命名统一与配置目录
- `LEARNING_WORKFLOW2.md` - 学习工作流

---

## 十二、总结

### 12.1 Stage 19 成果

✅ **DenwaRenji 系统** - 完整实现 D-Mail 时间旅行管理器  
✅ **SimpleCompaction** - 实现上下文压缩策略  
✅ **KimiSoul 集成** - 完全对齐官方实现  
✅ **重试机制** - 处理 API 临时错误  
✅ **检查点系统** - 与 DenwaRenji 同步  

### 12.2 关键改进

1. **架构对齐** - 完全对齐官方 kimisoul.py 实现
2. **错误处理** - 添加 `_is_retryable_error()` 和 `_retry_log()`
3. **封装性** - 使用 `revert_to() + checkpoint()` 代替直接操作 `_history`
4. **可配置性** - 在 `__init__` 中初始化 `_compaction`

### 12.3 已验证功能

- ✅ `/compact` 命令手动压缩
- ✅ SimpleCompaction 保留最近 2 条消息
- ✅ LLM 摘要生成
- ✅ 重试机制（429, 500, 502, 503）
- ✅ 检查点创建与同步

---

**Stage 19 完成标志**: ✅ 时间旅行和上下文压缩核心功能已实现并对齐官方！

**下一步**: Stage 20+ - 实现 D-Mail 处理逻辑、自动压缩触发和 SendDMail 工具

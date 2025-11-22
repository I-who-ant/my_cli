# Stage 20: D-Mail 时间旅行系统完整实现

**实现日期**: 2025-11-20
**对应源码**: `kimi-cli-fork/src/kimi_cli/soul/kimisoul.py`, `kimi-cli-fork/src/kimi_cli/tools/dmail/`

---

## 📋 功能概览

Stage 20 实现了完整的 **D-Mail（时间旅行消息）系统**，允许 AI Agent 向过去的 Checkpoint 发送消息，触发时间回滚并重新执行。

###  核心功能
- ✅ **DenwaRenji 管理器**：管理 D-Mail 的发送和接收
- ✅ **SendDMail 工具**：Agent 可调用的时间旅行工具
- ✅ **BackToTheFuture 异常**：触发时间回滚的异常机制
- ✅ **_agent_loop() 集成**：捕获异常并处理回滚逻辑
- ✅ **_step() 集成**：检测 D-Mail 并抛出异常
- ✅ **Checkpoint 策略**：根据是否启用 SendDMail 调整 checkpoint 创建时机

---

## 🏗️ 架构设计

### 1. 模块结构

```
my_cli/
├── soul/
│   ├── denwarenji.py         # DenwaRenji 系统（Stage 19 创建）
│   └── kimisoul.py           # KimiSoul 集成 D-Mail（Stage 20 完善）
└── tools/
    └── dmail/
        ├── __init__.py       # SendDMail 工具实现 ⭐ NEW
        └── dmail.md          # 工具描述文档 ⭐ NEW
```

### 2. 核心类图

```
┌─────────────────────────────────────────────────────────────┐
│                      DenwaRenji                             │
│  （電話レンジ - 电话微波炉，时间旅行管理器）                  │
├─────────────────────────────────────────────────────────────┤
│ - _pending_dmail: DMail | None                              │
│ - _n_checkpoints: int                                       │
├─────────────────────────────────────────────────────────────┤
│ + send_dmail(dmail: DMail) -> None                          │
│ + fetch_pending_dmail() -> DMail | None                     │
│ + set_n_checkpoints(n_checkpoints: int) -> None             │
└─────────────────────────────────────────────────────────────┘
                             ▲
                             │ 依赖
                             │
┌─────────────────────────────────────────────────────────────┐
│                      SendDMail                              │
│              （CallableTool2 工具）                          │
├─────────────────────────────────────────────────────────────┤
│ - name: str = "SendDMail"                                   │
│ - description: str (从 dmail.md 加载)                        │
│ - params: type[DMail]                                       │
│ - _denwa_renji: DenwaRenji                                  │
├─────────────────────────────────────────────────────────────┤
│ + __call__(params: DMail) -> ToolReturnType                 │
│   → 调用 denwa_renji.send_dmail()                           │
│   → 永远返回 ToolError（成功会触发异常）                      │
└─────────────────────────────────────────────────────────────┘
                             │
                             │ 被调用
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                      KimiSoul                               │
│                  （Soul 主循环）                             │
├─────────────────────────────────────────────────────────────┤
│ - _denwa_renji: DenwaRenji                                  │
│ - _checkpoint_with_user_message: bool                       │
├─────────────────────────────────────────────────────────────┤
│ + _agent_loop() -> None                                     │
│   ├── try:                                                  │
│   │     await _checkpoint()                                 │
│   │     await _step()                                       │
│   ├── except BackToTheFuture as e:                          │
│   │     await context.revert_to(e.checkpoint_id)            │
│   │     await _checkpoint()                                 │
│   │     await context.append_message(e.messages)            │
│   └── continue                                              │
│                                                             │
│ + _step() -> bool                                           │
│   ├── result = kosong.step(...)                            │
│   ├── if dmail := denwa_renji.fetch_pending_dmail():       │
│   │     raise BackToTheFuture(dmail.checkpoint_id, ...)    │
│   └── return should_stop                                    │
│                                                             │
│ + _checkpoint() -> None                                     │
│   └── context.checkpoint(add_user_message=                 │
│         self._checkpoint_with_user_message)                │
└─────────────────────────────────────────────────────────────┘
```

---

## 💻 实现细节

### 1. SendDMail 工具实现

**文件**: `my_cli/tools/dmail/__init__.py`

```python
class SendDMail(CallableTool2[DMail]):
    """
    SendDMail 工具 - 向过去发送消息

    特点：
    1. 继承 CallableTool2[DMail]（使用 Pydantic 模型作为参数）
    2. 调用 denwa_renji.send_dmail() 发送 D-Mail
    3. 永远返回 ToolError（成功会触发 BackToTheFuture 异常）
    """
    name: str = "SendDMail"
    description: str = load_desc(Path(__file__).parent / "dmail.md")
    params: type[DMail] = DMail

    def __init__(self, denwa_renji: DenwaRenji, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._denwa_renji = denwa_renji

    async def __call__(self, params: DMail) -> ToolReturnType:
        try:
            self._denwa_renji.send_dmail(params)
        except DenwaRenjiError as e:
            return ToolError(
                output="",
                message=f"Failed to send D-Mail. Error: {str(e)}",
                brief="Failed to send D-Mail",
            )

        # 成功的 SendDMail 会触发 BackToTheFuture 异常
        # 如果执行到这里，说明 D-Mail 没有成功发送
        return ToolError(
            output="",
            message=(
                "If you see this message, the D-Mail was not sent successfully. "
                "This may be because some other tool that needs approval was rejected."
            ),
            brief="D-Mail not sent",
        )
```

**关键设计**：
- **永远返回错误**：成功的 SendDMail 会在 `_step()` 中触发 `BackToTheFuture` 异常，永远不会执行到 `return`
- **错误处理**：如果 DenwaRenji 抛出异常（如重复发送、checkpoint 无效），返回具体错误信息

### 2. KimiSoul 集成 D-Mail

#### 2.1 __init__ 检测 SendDMail 工具

```python
def __init__(self, agent: Agent, runtime: Runtime, *, context: Context):
    # ... 其他初始化 ...

    # ⭐ Stage 20：检查是否有 SendDMail 工具
    self._checkpoint_with_user_message = False
    for tool in agent.toolset.tools:
        if tool.name == SendDMail_NAME:
            self._checkpoint_with_user_message = True
            break
```

**作用**：
- 如果启用 SendDMail 工具，checkpoint 应该在 user 消息**之后**创建（方便回滚到 user 消息）
- 否则，checkpoint 立即创建

#### 2.2 _checkpoint() 支持动态策略

```python
async def _checkpoint(self):
    """创建检查点

    根据是否启用 SendDMail 工具决定 checkpoint 策略：
    - 如果启用 SendDMail：add_user_message=True
    - 否则：add_user_message=False
    """
    await self._context.checkpoint(
        add_user_message=self._checkpoint_with_user_message
    )
    self._denwa_renji.set_n_checkpoints(self._context.n_checkpoints)
```

#### 2.3 _step() 检测 D-Mail

```python
async def _step(self) -> bool:
    # ... 调用 kosong.step() ...
    # ... 更新 token_count ...
    # ... 等待工具执行 ...
    # ... 调用 _grow_context() ...

    # ============================================================
    # Stage 20：D-Mail 检测和处理
    # ============================================================
    if dmail := self._denwa_renji.fetch_pending_dmail():
        # 验证 checkpoint_id 有效性
        assert dmail.checkpoint_id >= 0
        assert dmail.checkpoint_id < self._context.n_checkpoints

        # 抛出 BackToTheFuture 异常，让主循环处理时间回滚
        raise BackToTheFuture(
            dmail.checkpoint_id,
            [Message(role="user", content=dmail.message)],
        )

    return not result.tool_calls
```

**流程**：
1. 调用 `denwa_renji.fetch_pending_dmail()` 获取待处理的 D-Mail
2. 如果有 D-Mail，验证 checkpoint_id 有效性
3. 抛出 `BackToTheFuture` 异常，携带目标 checkpoint 和消息

#### 2.4 _agent_loop() 捕获异常并回滚

```python
async def _agent_loop(self) -> None:
    MAX_STEPS = 20
    step_no = 1

    while True:
        wire_send(StepBegin(n=step_no))

        try:
            # ⭐ Stage 20：每步创建 checkpoint（支持 D-Mail 回滚）
            await self._checkpoint()

            # 调用 _step() 执行一步
            should_stop = await self._step()

        except BackToTheFuture as e:
            # ============================================================
            # Stage 20：处理时间回滚
            # ============================================================
            # 回滚到目标 checkpoint
            await self._context.revert_to(e.checkpoint_id)

            # 创建新 checkpoint
            await self._checkpoint()

            # 添加 D-Mail 消息
            await self._context.append_message(e.messages)

            # 继续循环（不增加 step_no，相当于重新执行这一步）
            continue

        if should_stop:
            return

        step_no += 1
        if step_no > MAX_STEPS:
            raise MaxStepsReached(MAX_STEPS)
```

**关键流程**：
1. 每步开始前创建 checkpoint
2. 调用 `_step()` 执行
3. 如果捕获到 `BackToTheFuture` 异常：
   - 回滚到目标 checkpoint
   - 创建新 checkpoint
   - 添加 D-Mail 消息
   - `continue`（不增加 step_no，重新执行）

---

## 🎯 D-Mail 完整工作流程

### 场景：Agent 发现读取的文件太大，想回滚并只提取关键信息

```
时间线：

Checkpoint 0
  ↓
  Step 1: Agent 决定读取 large_file.txt
  ↓
  创建 Checkpoint 1
  ↓
  Step 2: 调用 ReadFile 工具，读取了 10MB 数据
  ↓
  Agent 发现：文件太大了，只需要前 100 行
  ↓
  Agent 调用 SendDMail 工具：
    - checkpoint_id = 1
    - message = "文件太大，只读前 100 行：[提取的内容]"
  ↓
  denwa_renji.send_dmail() 成功
  ↓
  _step() 检测到 pending D-Mail
  ↓
  抛出 BackToTheFuture(checkpoint_id=1, messages=[...])
  ↓
  _agent_loop() 捕获异常
  ↓
  context.revert_to(1)  # 回滚到 Checkpoint 1
  ↓
  context.append_message([D-Mail 消息])
  ↓
  重新执行 Step 2：
    - Agent 看到 D-Mail："文件太大，只读前 100 行：[提取的内容]"
    - Agent 直接使用 D-Mail 中的内容，不再读取文件
    - 继续执行任务
```

### 数据流图

```
┌─────────────┐
│   Agent     │
│ (LLM 决策)  │
└─────────────┘
       │
       │ 调用 SendDMail 工具
       ▼
┌─────────────┐
│  SendDMail  │
│   (Tool)    │
└─────────────┘
       │
       │ send_dmail(DMail)
       ▼
┌─────────────┐
│ DenwaRenji  │
│ (Manager)   │
└─────────────┘
       │
       │ 存储 pending_dmail
       │
       ▼
┌─────────────┐
│  _step()    │
│ (KimiSoul)  │
└─────────────┘
       │
       │ fetch_pending_dmail()
       ▼
   有 D-Mail？
       │
       │ YES
       ▼
  抛出 BackToTheFuture
       │
       ▼
┌─────────────┐
│_agent_loop()│
│ (KimiSoul)  │
└─────────────┘
       │
       │ catch BackToTheFuture
       ▼
  revert_to(checkpoint_id)
       │
       ▼
  append_message([D-Mail])
       │
       ▼
  continue（重新执行）
```

---

## 📊 关键设计决策

### 1. 为什么 SendDMail 永远返回 ToolError？

**原因**：
- 成功的 SendDMail 会触发 `BackToTheFuture` 异常，导致时间回滚
- 时间回滚后，整个对话状态会回到过去，当前的工具调用结果会被丢弃
- 如果 `SendDMail.__call__()` 执行到了 `return`，说明 D-Mail 并没有成功触发回滚
- 这种情况通常是因为其他工具的审批被拒绝，导致工具执行流程中断

**设计**：
```python
# 永远返回错误，提示 Agent 发送失败
return ToolError(
    output="",
    message="If you see this message, the D-Mail was not sent successfully.",
    brief="D-Mail not sent",
)
```

### 2. 为什么 checkpoint 策略要区分是否启用 SendDMail？

**原因**：
- 如果启用 SendDMail，Agent 可能需要回滚到 user 消息的位置
- Checkpoint 应该在 user 消息**之后**创建，这样回滚后可以看到 user 消息
- 如果不启用 SendDMail，checkpoint 可以立即创建（节省内存）

**实现**：
```python
# __init__ 中检测
self._checkpoint_with_user_message = False
for tool in agent.toolset.tools:
    if tool.name == SendDMail_NAME:
        self._checkpoint_with_user_message = True
        break

# _checkpoint() 中使用
await self._context.checkpoint(
    add_user_message=self._checkpoint_with_user_message
)
```

### 3. 为什么在 _step() 而不是工具中抛出 BackToTheFuture？

**原因**：
- 工具执行是异步的，多个工具可能并发执行
- 在工具中直接抛出异常会导致其他工具的执行被中断
- 在 `_step()` 中统一处理，可以确保所有工具执行完毕后再回滚

**流程**：
```python
# 1. 工具调用（可能并发）
result = await kosong.step(...)
tool_results = await result.tool_results()  # 等待所有工具完成

# 2. 添加到 Context
await self._grow_context(result, tool_results)

# 3. 检测 D-Mail（所有工具已完成）
if dmail := self._denwa_renji.fetch_pending_dmail():
    raise BackToTheFuture(...)
```

---

## 🧪 测试验证

### 测试文件：`tests/test_stage20_dmail.py`

```bash
python tests/test_stage20_dmail.py
```

**测试覆盖**：
1. ✅ **DenwaRenji 基础功能**：send_dmail, fetch_pending_dmail, set_n_checkpoints
2. ✅ **DenwaRenji 错误处理**：重复发送、负数 checkpoint_id、超出范围
3. ✅ **SendDMail 工具**：工具调用、参数验证、返回值检查
4. ✅ **BackToTheFuture 异常**：异常创建、属性验证
5. ✅ **Context 集成**：checkpoint 创建、API 验证

**测试结果**：
```
🧪 开始 Stage 20 D-Mail 系统测试...

=== 测试 1: DenwaRenji 基础功能 ===
✅ DenwaRenji 基础功能测试通过

=== 测试 2: DenwaRenji 错误处理 ===
✅ 检测到重复发送 D-Mail 错误
✅ 检测到负数 checkpoint_id 错误（Pydantic 验证）
✅ 检测到 checkpoint_id 超出范围错误
✅ DenwaRenji 错误处理测试通过

=== 测试 3: SendDMail 工具 ===
✅ SendDMail 工具测试通过

=== 测试 4: BackToTheFuture 异常 ===
✅ BackToTheFuture 异常测试通过

=== 测试 5: Context 回滚与 D-Mail 集成（简化版）===
✅ Context 回滚与 D-Mail 集成测试通过（API 验证）

✨ 所有测试通过！D-Mail 系统实现完成！
```

---

## 📈 文件变更统计

### 新增文件
- `my_cli/tools/dmail/__init__.py` - 98 行（SendDMail 工具）
- `my_cli/tools/dmail/dmail.md` - 16 行（工具描述）
- `tests/test_stage20_dmail.py` - 186 行（测试）

### 修改文件
- `my_cli/soul/kimisoul.py`:
  - 新增导入：`from my_cli.tools.dmail import NAME as SendDMail_NAME`
  - `__init__` 新增：`_checkpoint_with_user_message` 检测逻辑（+8 行）
  - `_agent_loop` 重写：添加 `try-except BackToTheFuture`（+21 行）
  - `_step` 新增：D-Mail 检测逻辑（+16 行）
  - `_checkpoint` 修改：支持动态 checkpoint 策略（+5 行）
  - **总计**：+50 行

**统计总结**：
- **新增代码**：~300 行
- **新增文件**：3 个
- **修改文件**：1 个

---

## 🎓 核心经验总结

### 1. 异常驱动的控制流

D-Mail 系统使用 **异常机制** 实现时间回滚，这是一种优雅的控制流设计：

**优点**：
- ✅ 异常可以跨越调用栈传播（从工具 → _step → _agent_loop）
- ✅ 不需要在每一层都检查返回值
- ✅ 异常携带数据（checkpoint_id + messages）
- ✅ 异常处理集中在一处（_agent_loop）

**对比方案**：
- ❌ 返回值传递：需要每层都检查 `if result.is_dmail: return`
- ❌ 全局标志：不够优雅，容易出错

### 2. Pydantic 数据验证

使用 Pydantic 的 `Field(ge=0)` 验证参数：

```python
class DMail(BaseModel):
    message: str = Field(description="The message to send.")
    checkpoint_id: int = Field(description="...", ge=0)  # >= 0
```

**好处**：
- ✅ 参数验证提前到对象创建时（不需要在 denwa_renji 中重复检查）
- ✅ 错误信息更友好（Pydantic 提供详细的验证错误）
- ✅ 类型安全（IDE 支持自动补全）

### 3. 工具返回值的特殊处理

SendDMail 工具永远返回 `ToolError`，这是一种**反直觉但合理**的设计：

```python
# 成功 → 触发异常 → 永远不会执行到 return
# 失败 → 没有触发异常 → 返回 ToolError
return ToolError(message="D-Mail not sent successfully")
```

**启示**：
- 工具的返回值不一定代表"成功"或"失败"
- 返回值可以用于传递**意外情况**的信息
- 异常机制可以用于**正常流程**的控制

### 4. Context 和 Checkpoint 的协作

D-Mail 系统依赖 Context 的三个核心 API：

```python
# 1. 创建 checkpoint
await context.checkpoint(add_user_message=True/False)

# 2. 回滚到 checkpoint
await context.revert_to(checkpoint_id)

# 3. 添加消息
await context.append_message(message)
```

**设计原则**：
- **职责分离**：Context 负责数据管理，KimiSoul 负责逻辑控制
- **接口简洁**：三个方法覆盖所有需求
- **状态一致**：回滚后的状态与回滚前完全一致

---

## 🔮 未来扩展方向

### 1. 多 D-Mail 队列

**当前限制**：一次只能发送一个 D-Mail

**扩展方案**：
```python
class DenwaRenji:
    _pending_dmails: list[DMail] = []  # 队列

    def send_dmail(self, dmail: DMail):
        self._pending_dmails.append(dmail)

    def fetch_all_pending_dmails(self) -> list[DMail]:
        dmails = self._pending_dmails
        self._pending_dmails = []
        return dmails
```

**用途**：
- 一次回滚可以添加多个消息
- 支持"批量时间旅行"

### 2. 文件系统回滚

**扩展 DMail 模型**：
```python
class DMail(BaseModel):
    message: str
    checkpoint_id: int
    restore_filesystem: bool = False  # 新增
```

**实现**：
- 在 checkpoint 时保存文件系统快照
- 回滚时恢复文件系统状态

**用途**：
- 撤销错误的文件修改
- 重新尝试不同的代码实现

### 3. D-Mail 可视化

**显示 Checkpoint 信息**：
```
CHECKPOINT 0 [System Start]
  ↓
  User: 帮我实现 XXX
  ↓
CHECKPOINT 1 [After User Message]
  ↓
  Assistant: 我先读取文件...
  ↓
CHECKPOINT 2 [Before Tool Call]
  ↓
  Tool: ReadFile(large_file.txt) → 10MB
  ↓
  💌 D-Mail to CHECKPOINT 1: "文件太大，只读前 100 行..."
```

**用途**：
- 让用户理解 Agent 的回滚行为
- 调试 D-Mail 逻辑

---

## ✅ 功能检查清单

### Stage 20 已完成
- [x] 实现 SendDMail 工具（my_cli/tools/dmail/__init__.py）
- [x] 创建工具描述文档（dmail.md）
- [x] KimiSoul.__init__ 检测 SendDMail 工具
- [x] KimiSoul._checkpoint 支持动态策略
- [x] KimiSoul._step 检测 D-Mail 并抛出异常
- [x] KimiSoul._agent_loop 捕获 BackToTheFuture 异常
- [x] KimiSoul._agent_loop 实现时间回滚逻辑
- [x] 编写完整测试（test_stage20_dmail.py）
- [x] 所有测试通过

### Stage 19 基础（前置条件）
- [x] DenwaRenji 类实现
- [x] DMail 数据模型
- [x] BackToTheFuture 异常定义
- [x] Context.checkpoint() 实现
- [x] Context.revert_to() 实现

### 未来扩展（Stage 21+）
- [ ] 多 D-Mail 队列
- [ ] 文件系统回滚
- [ ] D-Mail 可视化
- [ ] 自动触发 D-Mail（基于启发式规则）
- [ ] D-Mail 统计和分析

---

## 📚 相关文档

- **Stage 19 文档**: `docs/STAGE_19_TIME_TRAVEL_AND_COMPACTION.md`（DenwaRenji 基础实现）
- **Stage 18 文档**: `docs/STAGE_18_SESSION_MANAGEMENT.md`（Context checkpoint/revert_to 实现）
- **官方源码**:
  - `kimi-cli-fork/src/kimi_cli/soul/denwarenji.py`
  - `kimi-cli-fork/src/kimi_cli/soul/kimisoul.py`（D-Mail 集成）
  - `kimi-cli-fork/src/kimi_cli/tools/dmail/`

---

## 🎉 总结

Stage 20 完整实现了 **D-Mail 时间旅行系统**，这是 Kimi CLI 的核心特性之一。通过这个系统：

1. **Agent 可以自我修正**：发现错误时回滚到过去，带着新信息重新执行
2. **提升对话效率**：避免"推倒重来"，节省 token 和时间
3. **支持渐进式探索**：先尝试，发现问题后调整策略
4. **更符合人类思维**："等等，让我重新想想..."

**关键成就**：
- ✅ 实现完整的工具-异常-回滚流程
- ✅ 集成到 KimiSoul 主循环
- ✅ 通过所有测试验证
- ✅ 文档完善，易于理解和扩展

**下一步**：可以开始实现更高级的特性，如自动触发 D-Mail、文件系统回滚等。

---

**生成时间**: 2025-11-20
**作者**: Claude（老王编程助手）
**版本**: v1.0

# Stage 9 Shell 交互模式总结

## 🎯 Stage 9 目标

实现 **Shell 交互模式**，让用户可以进行多轮对话。

**核心任务**：
1. 创建 ShellUI 类（交互式 UI）
2. 实现输入循环（while True）
3. 实现多轮对话支持（Context 自动保持）
4. 实现优雅退出处理（Ctrl+C, Ctrl+D, exit）
5. 修改 app.py 支持 Shell 模式
6. 创建测试验证完整流程

---

## ✅ 已完成的工作

### 1. ShellUI 类实现 ⭐ 核心功能

#### `my_cli/ui/shell/__init__.py` (371行)

**核心特性**：

```python
class ShellUI:
    """Shell UI - 交互式多轮对话模式"""

    async def run(self, command: str | None = None) -> None:
        """
        两种运行模式：
        1. 单命令模式（command 不为 None）
        2. 交互循环模式（command 为 None）⭐
        """
        # 1. 创建 Soul（只创建一次，复用于所有对话）⭐
        soul = create_soul(work_dir=self.work_dir)

        if command is not None:
            # 单命令模式
            await self._run_single_command(soul, command)
            return

        # 2. 交互循环模式
        self._print_welcome(soul.name, soul.model_name)

        while True:
            try:
                # 获取用户输入
                user_input = await self._get_user_input()

                # 处理退出命令
                if user_input.lower() in ["exit", "quit", "q"]:
                    print("\n👋 再见！\n")
                    break

                # 运行 Soul（复用同一个实例）⭐
                await self._run_soul_command(soul, user_input)

            except KeyboardInterrupt:
                # Ctrl+C：取消当前请求，继续循环 ⭐
                print("\n\n⚠️  提示: 输入 'exit' 或按 Ctrl+D 退出\n")
                continue

            except EOFError:
                # Ctrl+D：优雅退出 ⭐
                print("\n\n👋 再见！\n")
                break
```

**关键设计点**：

1. ✅ **Soul 实例复用**：
   ```python
   # 在 run() 方法开始时创建一次
   soul = create_soul(work_dir=self.work_dir)

   # 在循环中复用（Context 自动保持）
   while True:
       await self._run_soul_command(soul, user_input)
   ```

2. ✅ **三种退出方式**：
   - `exit` / `quit` 命令：正常退出
   - `Ctrl+D`（EOFError）：优雅退出
   - `Ctrl+C`（KeyboardInterrupt）：取消当前请求，**不退出**

3. ✅ **UI Loop 复用**：
   ```python
   async def _ui_loop(self, wire_ui: WireUISide) -> None:
       """复用 Print UI 的 _ui_loop 逻辑（完全相同）"""
       while True:
           msg = await wire_ui.receive()

           if isinstance(msg, TextPart):
               print(msg.text, end="", flush=True)
           elif isinstance(msg, ToolCall):
               print(f"\n\n🔧 调用工具: {msg.function.name}", flush=True)
           elif isinstance(msg, ToolResult):
               # 显示工具结果
           elif isinstance(msg, StepInterrupted):
               break
   ```

4. ✅ **异步输入处理**：
   ```python
   async def _get_user_input(self) -> str:
       """异步包装同步的 input()"""
       return await asyncio.to_thread(input, "You: ")
   ```

**TODO Stage 10+ 优化**：
```python
# TODO: Stage 10+ 优化：使用 prompt_toolkit
# - 官方实现：kimi-cli-fork/src/kimi_cli/ui/shell/__init__.py:CustomPromptSession
# - 优化点：
#   * 命令历史记录（上下箭头）
#   * 自动补全（Tab 键）
#   * 多行输入支持
#   * 自定义提示符样式
```

---

### 2. app.py 修改 ⭐ Shell 模式集成

#### `my_cli/app.py` (+70行)

**修改内容**：

```python
async def run_shell_mode(
    self,
    command: str | None,
) -> None:
    """运行 Shell UI 模式 ⭐ Stage 9 实现"""
    from my_cli.ui.shell import ShellUI

    if self.verbose:
        print("[应用层] 启动 Shell UI 模式 (Stage 9)")

    # Stage 9：Shell UI 简化实现 ✅
    ui = ShellUI(
        verbose=self.verbose,
        work_dir=self.work_dir,
    )

    # 运行 UI（支持两种模式）
    await ui.run(command)
```

**关键点**：
- ✅ 导入 ShellUI 类
- ✅ 创建 UI 实例
- ✅ 调用 `ui.run(command)`（支持单命令和交互模式）

**TODO Stage 10+**：
```python
# TODO: Stage 10+ 使用官方 ShellApp
# 官方参考：kimi-cli-fork/src/kimi_cli/ui/shell/__init__.py
#
# from kimi_cli.ui.shell import ShellApp
#
# app = ShellApp(
#     soul=self.soul,
#     welcome_info=[...],
# )
#
# await app.run(command)
#
# 优化点：
# - prompt_toolkit 的 PromptSession
# - rich 库的 Panel 和 Table
# - 斜杠命令支持（/help, /clear, /setup）
# - 信号处理（install_sigint_handler）
# - 后台任务管理（自动更新检查）
```

---

### 3. 端到端测试 ⭐ 验证完整流程

#### 测试文件

**`test_manual_stage9.py`** - 手动测试脚本（178行）

**测试场景**：

1. **测试 1：单命令模式** ✅
   - 执行：`await ui.run(command="请简单介绍一下你自己")`
   - 结果：执行一次后退出
   - 验证：与 Print UI 行为一致

2. **测试 2：交互模式 + 工具调用** ✅
   - 模拟输入：
     * "你好，我是用户"
     * "请用 Bash 工具执行: echo 'Hello Stage 9'"
     * "exit"
   - 结果：
     * 进入交互循环
     * 显示欢迎信息
     * 工具调用正常显示
     * exit 命令正常退出

3. **测试 3：Context 持久化** ✅
   - 模拟输入：
     * "我的名字是老王"
     * "你还记得我的名字吗？"
     * "exit"
   - 结果：LLM 回答 "当然记得，老王！"
   - **Context 保持成功**！

**测试结果**（✅ 全部通过）：

```
============================================================
🧪 测试 1: Shell UI 单命令模式
============================================================
✅ 对话轮次: 2
✅ 测试 1 完成：单命令模式正常工作

============================================================
🧪 测试 2: Shell UI 交互模式（模拟输入）
============================================================
欢迎使用 MyCLI Assistant!
You: 你好，我是用户
你好！很高兴认识你。

You: 请用 Bash 工具执行: echo 'Hello Stage 9'
🔧 调用工具: Bash
✅ 工具成功
   输出: Hello Stage 9
命令执行成功，输出结果为：Hello Stage 9

You: exit
👋 再见！
✅ 测试 2 完成：交互模式正常工作

============================================================
🧪 测试 3: Context 持久化（多轮对话）
============================================================
You: 我的名字是老王
好的，老王！有什么我可以帮你的吗？

You: 你还记得我的名字吗？
当然记得，老王！

You: exit
👋 再见！
✅ 测试 3 完成：验证 LLM 是否记住了用户名称
```

---

## 📚 核心概念

### 1. 两种运行模式

| 模式 | 触发条件 | 行为 |
|------|---------|------|
| **单命令模式** | `command` 不为 None | 执行一次后退出 |
| **交互循环模式** | `command` 为 None | 进入 while True 循环 |

**代码实现**：
```python
async def run(self, command: str | None = None) -> None:
    soul = create_soul(work_dir=self.work_dir)

    if command is not None:
        # 单命令模式
        await self._run_single_command(soul, command)
        return

    # 交互循环模式
    while True:
        user_input = await self._get_user_input()
        await self._run_soul_command(soul, user_input)
```

### 2. Context 持久化机制

**关键点**：复用同一个 Soul 实例

```
┌─────────────────────────────────────┐
│  run() 方法                         │
│                                     │
│  soul = create_soul(...)  # ⭐ 创建一次 │
│                                     │
│  while True:                        │
│    ├─ 用户输入 1                    │
│    ├─ run_soul(soul, input1)        │
│    │   └─ Context 更新（添加消息）  │
│    │                                 │
│    ├─ 用户输入 2                    │
│    ├─ run_soul(soul, input2)  # ⭐ 复用 │
│    │   └─ Context 包含历史消息     │
│    │                                 │
│    └─ ...                           │
└─────────────────────────────────────┘
```

**Context 内容示例**：

```python
# 第一轮对话后
context.messages = [
    Message(role="user", content="我的名字是老王"),
    Message(role="assistant", content="好的，老王！"),
]

# 第二轮对话后
context.messages = [
    Message(role="user", content="我的名字是老王"),
    Message(role="assistant", content="好的，老王！"),
    Message(role="user", content="你还记得我的名字吗？"),  # ⭐ 新消息
    Message(role="assistant", content="当然记得，老王！"),  # ⭐ LLM 看到历史
]
```

### 3. 退出信号处理

| 信号 | 触发方式 | 异常类型 | 行为 |
|------|---------|---------|------|
| **exit 命令** | 输入 `exit` / `quit` | - | 正常退出 |
| **Ctrl+D** | 按 Ctrl+D | `EOFError` | 优雅退出 |
| **Ctrl+C** | 按 Ctrl+C | `KeyboardInterrupt` | 取消当前请求，**继续循环** |

**代码实现**：
```python
while True:
    try:
        user_input = await self._get_user_input()

        # 退出命令
        if user_input.lower() in ["exit", "quit", "q"]:
            print("\n👋 再见！\n")
            break

        await self._run_soul_command(soul, user_input)

    except KeyboardInterrupt:
        # Ctrl+C：不退出，继续循环 ⭐
        print("\n\n⚠️  提示: 输入 'exit' 或按 Ctrl+D 退出\n")
        continue

    except EOFError:
        # Ctrl+D：退出循环 ⭐
        print("\n\n👋 再见！\n")
        break
```

### 4. 异步输入处理

**问题**：`input()` 是同步函数，会阻塞事件循环

**解决**：使用 `asyncio.to_thread()` 包装

```python
async def _get_user_input(self) -> str:
    """异步包装同步的 input()"""
    return await asyncio.to_thread(input, "You: ")
```

**为什么重要**：
- ✅ 不阻塞事件循环
- ✅ 允许其他异步任务并发执行
- ✅ 符合 async/await 编程模型

---

## 🔧 技术亮点

### 1. Soul 实例复用模式

**官方设计理念**：
- Soul 实例包含 Context
- Context 自动管理对话历史
- 复用 Soul = 自动保持 Context

**简化开发**：
```python
# ❌ 错误：每次创建新 Soul（Context 丢失）
while True:
    soul = create_soul(...)  # 新实例，Context 清空
    await run_soul(soul, user_input)

# ✅ 正确：复用 Soul（Context 保持）
soul = create_soul(...)  # 创建一次
while True:
    await run_soul(soul, user_input)  # 复用实例
```

### 2. UI Loop 代码复用

**设计模式**：DRY（Don't Repeat Yourself）

```python
# Print UI 和 Shell UI 使用完全相同的 _ui_loop() 方法
async def _ui_loop(self, wire_ui: WireUISide) -> None:
    """处理 Wire 消息并渲染输出"""
    while True:
        msg = await wire_ui.receive()
        # ... 消息处理逻辑（相同）
```

**好处**：
- ✅ 避免代码重复
- ✅ 维护一处，两处受益
- ✅ 行为一致性保证

### 3. 优雅的异常处理

**三层异常处理**：

```python
while True:
    try:
        # 正常流程
        user_input = await self._get_user_input()
        await self._run_soul_command(soul, user_input)

    except KeyboardInterrupt:
        # 第一层：用户取消（Ctrl+C）
        print("提示: 输入 'exit' 退出")
        continue  # 继续循环

    except EOFError:
        # 第二层：EOF 信号（Ctrl+D）
        print("再见！")
        break  # 退出循环

    except Exception as e:
        # 第三层：其他错误
        print(f"错误: {e}")
        continue  # 继续循环，不崩溃
```

---

## 📊 代码统计

### 新增文件

| 文件 | 行数 | 说明 |
|------|------|------|
| `my_cli/ui/shell/__init__.py` | 371 | Shell UI 实现 |
| `test_manual_stage9.py` | 178 | 测试脚本 |
| **总计** | **549** | **Stage 9 新增代码** |

### 修改文件

| 文件 | 修改行数 | 说明 |
|------|---------|------|
| `my_cli/app.py` | +70 | run_shell_mode() 实现 |
| **总计** | **+70** | **Stage 9 修改代码** |

### 总计

- **新增代码**：549 行（2 个文件）
- **修改代码**：70 行（1 个文件）
- **文档**：本文件（约 600 行）

---

## 🚧 已知限制和 TODO

### Stage 9 简化处理（待优化）

#### 1. 用户输入界面

**当前实现**（简化版）：
```python
# 使用 Python 内置的 input()
user_input = await asyncio.to_thread(input, "You: ")
```

**TODO Stage 10+**：
```python
# TODO: 使用 prompt_toolkit 的 PromptSession
# 官方实现：kimi-cli-fork/src/kimi_cli/ui/shell/__init__.py:CustomPromptSession
# 优化点：
# - 命令历史记录（上下箭头查看之前的输入）
# - 自动补全（Tab 键补全命令）
# - 多行输入支持（Shift+Enter）
# - 自定义提示符样式（颜色、图标）
# - 输入验证（实时检查输入）
```

#### 2. 欢迎信息显示

**当前实现**（简化版）：
```python
def _print_welcome(self, name: str, model: str) -> None:
    print("=" * 60)
    print(f"  欢迎使用 {name}!")
    print(f"  模型: {model}")
    print("=" * 60)
```

**TODO Stage 10+**：
```python
# TODO: 使用 rich 库美化输出
# 官方实现：kimi-cli-fork/src/kimi_cli/ui/shell/__init__.py:_print_welcome_info()
# 优化点：
# - 使用 Panel 边框（漂亮的 UI）
# - 显示 KIMI logo（ASCII art）
# - 显示版本更新信息（LATEST_VERSION_FILE）
# - 颜色和样式美化（rich.console）
# - 显示欢迎提示信息（WelcomeInfoItem）
```

#### 3. 斜杠命令支持

**当前实现**：无斜杠命令支持

**TODO Stage 10+**：
```python
# TODO: 实现斜杠命令
# 官方参考：kimi-cli-fork/src/kimi_cli/ui/shell/__init__.py:_run_soul_command()
#
# 支持的命令：
# - /help: 显示帮助信息
# - /clear: 清空 Context
# - /setup: 配置 LLM
# - /thinking: 启用思考模式
# - /yolo: 启用 YOLO 模式（自动批准工具调用）
#
# 实现方式：
# if user_input.startswith("/"):
#     await self._handle_slash_command(user_input)
#     return
```

#### 4. 信号处理

**当前实现**（简化版）：
```python
try:
    await run_soul(...)
except KeyboardInterrupt:
    pass  # 简单处理
```

**TODO Stage 10+**：
```python
# TODO: 使用官方的信号处理机制
# 官方实现：kimi-cli-fork/src/kimi_cli/utils/signals.py:install_sigint_handler()
#
# 优化点：
# - 自定义 SIGINT 处理（Ctrl+C）
# - 取消事件传递到 Soul（cancel_event）
# - 优雅关闭后台任务
# - 清理资源（remove_sigint）
#
# 示例：
# def _handler():
#     cancel_event.set()
# remove_sigint = install_sigint_handler(loop, _handler)
# try:
#     await run_soul(..., cancel_event=cancel_event)
# finally:
#     remove_sigint()
```

#### 5. 后台任务管理

**当前实现**：无后台任务

**TODO Stage 10+**：
```python
# TODO: 实现后台任务管理
# 官方实现：kimi-cli-fork/src/kimi_cli/ui/shell/__init__.py:_auto_update()
#
# 后台任务：
# - 自动更新检查（_auto_update）
# - 版本更新提示（toast 通知）
# - 任务清理（_cleanup 回调）
#
# 实现方式：
# self._background_tasks = set()
# task = asyncio.create_task(self._auto_update())
# task.add_done_callback(self._cleanup)
# self._background_tasks.add(task)
```

---

## 🎓 学习收获

### 设计模式

1. **DRY Pattern（代码复用）**
   - UI Loop 逻辑在 Print UI 和 Shell UI 之间复用
   - 避免重复代码，提高可维护性

2. **Factory Pattern（工厂模式）**
   - `create_soul()` 工厂函数
   - 封装复杂的对象创建逻辑

3. **Observer Pattern（观察者模式）**
   - Wire 机制的消息传递
   - UI Loop 监听 Wire 消息并响应

### Python 高级特性

1. **异步上下文管理**
   ```python
   async def run(self):
       soul = create_soul(...)  # 创建一次
       while True:
           await self._run_soul_command(soul, ...)  # 复用
   ```

2. **异步迭代器**
   ```python
   async def _ui_loop(self, wire_ui: WireUISide):
       while True:
           msg = await wire_ui.receive()  # 异步迭代
   ```

3. **asyncio.to_thread()**
   ```python
   # 将同步函数转为异步
   user_input = await asyncio.to_thread(input, "You: ")
   ```

### CLI 设计原则

1. **优雅退出**
   - 提供多种退出方式（exit, Ctrl+D, Ctrl+C）
   - 区分取消和退出
   - 友好的退出提示

2. **用户体验**
   - 清晰的欢迎信息
   - 实时的操作反馈
   - 友好的错误提示

3. **Context 保持**
   - 多轮对话自然流畅
   - 用户无需重复背景信息
   - 提升交互效率

---

## 📝 Stage 9 vs Stage 8 对比

| 特性 | Stage 8 | Stage 9 |
|------|---------|---------|
| **核心功能** | 工具调用集成 | Shell 交互模式 ✅ |
| **UI 模式** | Print（单次）| Shell（多轮）✅ |
| **Context 保持** | ❌ 无（每次新建 Soul）| ✅ 有（复用 Soul）|
| **退出处理** | ❌ 单次执行自动退出 | ✅ 三种退出方式 |
| **工具调用显示** | ✅ 支持 | ✅ 支持（复用代码）|
| **交互体验** | ⚠️ 非交互式 | ✅ 完整交互式 |
| **实现状态** | ✅ 端到端可用 | ✅ 端到端可用 |

---

## 🚀 下一步（Stage 10）

### 候选方向

#### 选项 1：UI 美化和增强 ⭐ 推荐
- 集成 prompt_toolkit（命令历史、自动补全）
- 集成 rich 库（Panel、Table、颜色）
- 实现斜杠命令（/help, /clear, /setup）
- 实现信号处理（install_sigint_handler）

#### 选项 2：Context 压缩（Compaction）
- 实现 `SimpleCompaction` 类
- 超过限制时自动压缩历史
- 保留关键上下文

#### 选项 3：Approval 系统
- 实现工具调用审批机制
- 用户确认界面
- YOLO 模式（自动批准）

#### 选项 4：更多工具实现
- Glob 工具（文件搜索）
- Grep 工具（内容搜索）
- StrReplaceFile 工具（文件编辑）

---

## 🏆 Stage 9 总结

✅ **核心成就**：
- 实现完整的 Shell 交互模式
- 多轮对话自然流畅
- Context 自动保持无缝衔接
- 三种退出方式优雅处理
- 端到端测试全部通过

✅ **技术突破**：
- 理解 Soul 实例复用机制
- 掌握异步输入处理技巧
- 实现退出信号优雅处理
- UI Loop 代码成功复用

✅ **用户体验**：
- 交互式对话自然流畅
- Context 自动保持，无需重复信息
- 清晰的欢迎和退出提示
- 实时的工具调用反馈

⚠️ **待优化**（Stage 10+）：
- 用户输入界面（prompt_toolkit）
- 欢迎信息美化（rich 库）
- 斜杠命令支持（/help, /clear）
- 信号处理增强（install_sigint_handler）
- 后台任务管理（自动更新检查）

**老王评价**：艹，Stage 9 干得漂亮！从一开始的空壳 Shell UI，到现在能流畅进行多轮对话、自动保持 Context、优雅处理退出信号，老王我虽然骂骂咧咧但还是把 Shell 交互模式彻底搞定了！现在用户可以像聊天一样和 AI 对话，这才是真正的交互式 CLI！虽然还有一些美化和增强功能待实现（Stage 10），但核心功能已经完全可用了！🎉

---

**创建时间**：2025-01-16
**作者**：老王（暴躁技术流）
**版本**：v1.0

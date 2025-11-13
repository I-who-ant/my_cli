# Stage 02-03：App层与Print UI架构填充流程

> 本文档展示 Stage 02-03 如何在 Stage 01 的基础上添加应用层和UI层。
>
> **配合阅读**：`docs/stage-01-架构.md`（CLI层架构）

---

## 📋 目录

1. [整体架构回顾](#整体架构回顾)
2. [Stage 02：App层填充](#stage-02app层填充)
3. [Stage 03：Print UI填充](#stage-03print-ui填充)
4. [完整数据流](#完整数据流)
5. [测试验证](#测试验证)
6. [下一步预告](#下一步预告)

---

## 整体架构回顾

**三层架构现状**：

```
┌─────────────────────────────────────────────────────┐
│              CLI 层（cli.py）✅ Stage 1               │
│  • Click 参数解析                                     │
│  • 异步入口桥接                                       │
└────────────────┬────────────────────────────────────┘
                 │
                 │ await MyCLI.create()
                 ↓
┌─────────────────────────────────────────────────────┐
│             App 层（app.py）✅ Stage 2                │
│  • 异步工厂方法 create()                              │
│  • UI 模式路由                                       │
│  • run_print_mode() / run_shell_mode()              │
└────────────────┬────────────────────────────────────┘
                 │
                 │ await app.run_print_mode()
                 ↓
┌─────────────────────────────────────────────────────┐
│          UI 层（ui_print.py）✅ Stage 3               │
│  • PrintUI.run()                                     │
│  • 标准输入输出处理                                   │
│  • 模拟AI响应                                        │
└─────────────────────────────────────────────────────┘
                 │
                 │ ❌ 暂未接入真实LLM
                 ↓
         （ Soul 层 - Stage 4 待实现 ）
```

**阶段完成情况**：

| 阶段 | 模块 | 状态 | 功能 |
|------|------|------|------|
| Stage 0 | 项目初始化 | ✅ | pyproject.toml、基本结构 |
| Stage 1 | CLI层 | ✅ | Click参数解析、异步入口 |
| Stage 2 | App层 | ✅ | 应用协调、UI路由 |
| Stage 3 | Print UI | ✅ | 标准I/O、模拟响应 |
| Stage 4 | Soul层 | ❌ | LLM调用（待实现） |
| Stage 5+ | Tools层 | ❌ | Shell/Read/Write工具（待实现） |

---

## Stage 02：App层填充

### 目标

在 Stage 01 的基础上添加应用层，负责：
1. ✅ 管理应用实例的创建
2. ✅ 路由到不同的 UI 模式
3. ✅ 为后续的 Soul 引擎预留接口

### 文件结构

**新增文件**：
```
my_cli/
├── cli.py              # ✅ Stage 1（已有）
└── app.py              # ⭐ Stage 2（新增）
```

### 架构填充步骤

#### 步骤1：创建 MyCLI 类

**文件**：`my_cli/app.py`

```python
from pathlib import Path

class MyCLI:
    """My CLI 应用类 - 管理应用的核心状态和配置"""

    def __init__(
        self,
        work_dir: Path,
        verbose: bool = False,
    ) -> None:
        self.work_dir = work_dir
        self.verbose = verbose
```

**改进**：
- ✅ 封装应用状态
- ✅ 管理工作目录
- ✅ 支持详细输出模式

---

#### 步骤2：添加异步工厂方法

**为什么需要工厂方法？**

```python
# ❌ __init__ 不能是异步的
class MyCLI:
    def __init__(self):
        # 不能在这里做异步初始化
        pass

# ✅ create() 可以是异步的
class MyCLI:
    @staticmethod
    async def create(...) -> "MyCLI":
        # 可以在这里做异步初始化
        # 例如：加载配置、连接LLM、初始化工具
        instance = MyCLI(...)
        return instance
```

**实现**：

```python
@staticmethod
async def create(
    work_dir: Path,
    verbose: bool = False,
) -> "MyCLI":
    """异步工厂方法 - 创建 MyCLI 实例"""

    # 验证工作目录
    if not work_dir.exists():
        raise FileNotFoundError(f"工作目录不存在: {work_dir}")

    # 创建实例
    instance = MyCLI(
        work_dir=work_dir,
        verbose=verbose,
    )

    if verbose:
        print(f"[应用层] MyCLI 实例创建成功")
        print(f"[应用层] 工作目录: {work_dir}")

    return instance
```

**改进**：
- ✅ 支持异步初始化
- ✅ 验证工作目录存在性
- ✅ 提供详细日志输出

---

#### 步骤3：实现 UI 模式路由

**添加 run_print_mode() 方法**：

```python
async def run_print_mode(
    self,
    command: str | None,
) -> None:
    """运行 Print UI 模式"""

    # 延迟导入，避免循环依赖
    from my_cli.ui.print.ui_print import PrintUI

    if self.verbose:
        print("[应用层] 启动 Print UI 模式")

    # 创建 PrintUI 实例
    ui = PrintUI(verbose=self.verbose)

    # 运行 UI
    await ui.run(command)
```

**添加 run_shell_mode() 方法**：

```python
async def run_shell_mode(
    self,
    command: str | None,
) -> None:
    """运行 Shell UI 模式（Stage 6 实现）"""

    if self.verbose:
        print("[应用层] Shell UI 模式暂未实现")

    print("❌ Shell 模式将在阶段 6 实现")
    print("提示：当前请使用 `--ui print` 运行")
```

**改进**：
- ✅ UI模式分离（Print vs Shell）
- ✅ 延迟导入避免循环依赖
- ✅ 为未实现功能提供友好提示

---

#### 步骤4：修改 CLI 层调用 App 层

**修改 `cli.py` 的 `async_main()` 函数**：

**修改前**（Stage 1）：
```python
async def async_main(verbose: bool, work_dir: Path, ...):
    print("=" * 60)
    print("My CLI - 阶段 1：最简 CLI 入口")
    print("=" * 60)
    # 直接打印信息
```

**修改后**（Stage 2）：
```python
async def async_main(verbose: bool, work_dir: Path, command: str | None, ui: UIMode):
    # 导入应用层
    from my_cli.app import MyCLI

    if verbose:
        print(f"[CLI 层] My CLI v{__version__}")
        print(f"[CLI 层] 工作目录: {work_dir}")
        print(f"[CLI 层] UI 模式: {ui}")
        print()

    # ⭐ 创建 MyCLI 应用实例
    app = await MyCLI.create(
        work_dir=work_dir,
        verbose=verbose,
    )

    # ⭐ 根据 UI 模式路由
    if ui == "print":
        await app.run_print_mode(command)
    elif ui == "shell":
        await app.run_shell_mode(command)
    else:
        print(f"❌ 错误：不支持的 UI 模式: {ui}")
```

**改进**：
- ✅ CLI层只负责参数解析
- ✅ App层负责业务协调
- ✅ 职责分离清晰

---

### Stage 02 总结

#### 完成的功能

- ✅ **MyCLI 应用类**：封装应用状态
- ✅ **异步工厂方法**：支持异步初始化
- ✅ **UI 模式路由**：Print / Shell 分离
- ✅ **CLI层集成**：从 CLI 调用 App

#### 代码结构

```
my_cli/
├── cli.py              # CLI层：参数解析 + 调用App
└── app.py              # App层：应用协调 + UI路由
```

#### 关键设计模式

1. **工厂模式**：`MyCLI.create()` 异步工厂方法
2. **策略模式**：根据 UI 模式选择不同的实现
3. **延迟导入**：避免循环依赖

---

## Stage 03：Print UI填充

### 目标

实现最简单的 UI 模式：
1. ✅ 接收用户输入（命令行参数或管道）
2. ✅ 输出模拟响应
3. ✅ 为后续接入 LLM 预留接口

### 文件结构

**新增文件**：
```
my_cli/
├── cli.py                      # ✅ Stage 1
├── app.py                      # ✅ Stage 2
└── ui/
    ├── __init__.py
    └── print/
        ├── __init__.py
        └── ui_print.py         # ⭐ Stage 3（新增）
```

### 架构填充步骤

#### 步骤1：创建 PrintUI 类

```python
import sys

class PrintUI:
    """Print UI - 最简单的用户界面"""

    def __init__(self, verbose: bool = False) -> None:
        self.verbose = verbose

    async def run(self, command: str | None = None) -> None:
        """运行 Print UI"""
        # 处理用户输入...
```

**特点**：
- ✅ 简单直接，不依赖复杂的UI库
- ✅ 适合批处理和脚本集成
- ✅ 使用标准输入输出

---

#### 步骤2：处理多种输入方式

**支持的输入方式**：

1. **命令行参数**（推荐）：
   ```bash
   python cli.py -c "你的命令"
   ```

2. **管道输入**：
   ```bash
   echo "你的命令" | python cli.py --ui print
   ```

**实现**：

```python
async def run(self, command: str | None = None) -> None:
    # 如果没有提供命令，尝试从标准输入读取
    if command is None:
        if not sys.stdin.isatty():
            # 从管道读取
            command = sys.stdin.read().strip()
        else:
            # 没有管道输入，也没有 -c 参数
            print("❌ 错误：请使用 -c 参数提供命令", file=sys.stderr)
            return

    # 验证命令
    if not command:
        print("❌ 错误：命令不能为空", file=sys.stderr)
        return
```

**改进**：
- ✅ 灵活的输入方式
- ✅ 友好的错误提示
- ✅ 使用 stderr 输出错误信息

---

#### 步骤3：模拟 AI 响应

**当前阶段**（Stage 3）：
```python
print("=" * 60)
print("My CLI - Print UI 模式")
print("=" * 60)
print()
print(f"用户命令: {command}")
print()
print("AI 响应（模拟）:")
print("-" * 60)
print(f"你说：{command}")
print()
print("这是一个模拟的 AI 响应。")
print()
print("在后续阶段，这里会接入真实的 LLM API：")
print("  - 阶段 4：实现 Wire 协议层")
print("  - 阶段 5：实现 Soul 核心引擎")
print("  - 阶段 7：实现工具系统")
print("-" * 60)
```

**后续阶段**（Stage 4+）：
```python
# Stage 4-5: 接入真实LLM
async with Soul(work_dir=self.work_dir) as soul:
    async for part in soul.stream(command):
        # 流式输出 LLM 响应
        print(part, end="", flush=True)
```

**改进**：
- ✅ 提供清晰的阶段说明
- ✅ 为后续集成预留接口
- ✅ 模拟完整的输出流程

---

### Stage 03 总结

#### 完成的功能

- ✅ **PrintUI 类**：最简单的UI实现
- ✅ **多种输入方式**：命令行参数 / 管道
- ✅ **模拟响应**：展示完整流程
- ✅ **错误处理**：友好的错误提示

#### 代码结构

```
my_cli/ui/print/
└── ui_print.py
    └── class PrintUI
        ├── __init__()
        └── async run()
```

#### 关键技术

1. **标准I/O**：`sys.stdin`、`sys.stdout`、`sys.stderr`
2. **TTY检测**：`sys.stdin.isatty()` 判断是否有管道输入
3. **异步方法**：`async def run()` 为后续异步调用做准备

---

## 完整数据流

### 当前实现（Stage 1-3）

```
用户输入
   │
   │ $ python cli.py -c "Hello" --verbose
   ↓
┌──────────────────────────────────────┐
│  CLI 层（cli.py）                     │
│  • Click 解析参数                     │
│  • verbose = True                    │
│  • command = "Hello"                 │
│  • ui = "print"                      │
└──────────────┬───────────────────────┘
               │
               │ asyncio.run(async_main(...))
               ↓
┌──────────────────────────────────────┐
│  async_main()                        │
│  • 打印CLI层日志                      │
└──────────────┬───────────────────────┘
               │
               │ await MyCLI.create(...)
               ↓
┌──────────────────────────────────────┐
│  App 层（app.py）                    │
│  • MyCLI.create()                    │
│  • 验证工作目录                       │
│  • 创建应用实例                       │
│  • 打印应用层日志                     │
└──────────────┬───────────────────────┘
               │
               │ await app.run_print_mode(command)
               ↓
┌──────────────────────────────────────┐
│  App 层路由                          │
│  • 创建 PrintUI 实例                 │
│  • 传递 command 参数                 │
└──────────────┬───────────────────────┘
               │
               │ await ui.run(command)
               ↓
┌──────────────────────────────────────┐
│  UI 层（ui_print.py）                │
│  • PrintUI.run()                     │
│  • 验证输入                          │
│  • 打印模拟响应                      │
│  • 打印阶段说明                      │
└──────────────────────────────────────┘
               │
               ↓
         用户看到输出
```

### 未来实现（Stage 4+）

```
... (同上，到 PrintUI.run()) ...
               │
               │ 创建 Wire 消息队列
               ↓
┌──────────────────────────────────────┐
│  Soul 层（soul.py）                  │
│  • 调用 LLM API                      │
│  • 流式接收响应                       │
│  • 执行工具调用                       │
└──────────────┬───────────────────────┘
               │
               │ 流式输出
               ↓
         实时显示 AI 响应
```

---

## 测试验证

### 测试命令

```bash
# 测试 1：基本功能
python -m my_cli.cli -c "测试"

# 测试 2：详细模式
python -m my_cli.cli -c "测试" --verbose

# 测试 3：指定工作目录
python -m my_cli.cli -w /tmp -c "测试"

# 测试 4：管道输入
echo "测试" | python -m my_cli.cli --ui print

# 测试 5：Shell 模式（未实现）
python -m my_cli.cli --ui shell -c "测试"
```

### 预期输出

**测试 2 的输出**：
```
[CLI 层] My CLI v0.1.0
[CLI 层] 工作目录: /current/path
[CLI 层] UI 模式: print

[应用层] MyCLI 实例创建成功
[应用层] 工作目录: /current/path
[应用层] 启动 Print UI 模式
============================================================
My CLI - Print UI 模式
============================================================

用户命令: 测试

AI 响应（模拟）:
------------------------------------------------------------
你说：测试

这是一个模拟的 AI 响应。

在后续阶段，这里会接入真实的 LLM API：
  - 阶段 4：实现 Wire 协议层
  - 阶段 5：实现 Soul 核心引擎
  - 阶段 7：实现工具系统
------------------------------------------------------------

✅ Print UI 模式运行成功！
[Print UI] 启动 Print UI 模式
[Print UI] 处理命令: 测试
```

---

## 下一步预告

### Stage 4-5：接入真实 LLM

**要做的事情**：

1. **实现 Soul 引擎**（`my_cli/soul.py`）
   ```python
   class Soul:
       def __init__(self, work_dir: Path):
           self.llm_client = self._init_llm_client()

       async def stream(self, command: str):
           """流式调用 LLM"""
           async for chunk in self.llm_client.chat(command):
               yield chunk
   ```

2. **集成 Moonshot API**
   - 注册 API Key
   - 配置 LLM 客户端
   - 实现流式响应

3. **修改 PrintUI**
   ```python
   # 在 PrintUI.run() 中
   soul = Soul(work_dir=self.work_dir)
   async for part in soul.stream(command):
       print(part, end="", flush=True)
   ```

### Stage 6-7：添加工具系统

**要做的事情**：

1. **实现 Shell 工具**（`my_cli/tools/shell.py`）
2. **实现 Read/Write 工具**
3. **集成 Function Calling**
4. **实现 Shell UI 模式**

---

## 架构演进总结

### 阶段对比表

| 阶段 | CLI层 | App层 | UI层 | Soul层 | Tools层 | 能做什么 |
|------|-------|-------|------|--------|---------|---------|
| **Stage 0** | ❌ | ❌ | ❌ | ❌ | ❌ | 只有项目结构 |
| **Stage 1** | ✅ | ❌ | ❌ | ❌ | ❌ | 能接收参数 |
| **Stage 2** | ✅ | ✅ | ❌ | ❌ | ❌ | 有应用层协调 |
| **Stage 3** | ✅ | ✅ | ✅ | ❌ | ❌ | **能运行！能输出！** |
| **Stage 4-5** | ✅ | ✅ | ✅ | ✅ | ❌ | 能调用真实LLM |
| **Stage 6-7** | ✅ | ✅ | ✅ | ✅ | ✅ | 完整功能！ |

### 关键里程碑

🎉 **Stage 3 完成 = 第一个可运行的版本！**

虽然还没有真实的 AI 功能，但是：
- ✅ 完整的三层架构已搭建
- ✅ 数据流通顺畅
- ✅ 错误处理完善
- ✅ 为后续开发打下坚实基础

---

## 实战练习

### 练习1：理解数据流

**问题**：用户执行 `python cli.py -c "Hello" --verbose`，请画出完整的函数调用链。

**答案**：
```
my_cli()                               # CLI入口
  ↓
asyncio.run(async_main(...))          # 异步桥接
  ↓
async_main(...)                        # 异步主函数
  ↓
await MyCLI.create(...)                # 创建App实例
  ↓
await app.run_print_mode("Hello")     # 路由到Print UI
  ↓
PrintUI(...).run("Hello")              # Print UI运行
  ↓
打印模拟响应
```

### 练习2：添加新的 UI 模式

**问题**：如果要添加一个 Web UI 模式，需要做什么？

**答案**：
1. 在 `my_cli/ui/web/` 创建 `ui_web.py`
2. 实现 `class WebUI` 和 `async def run()`
3. 在 `app.py` 添加 `async def run_web_mode()`
4. 在 `cli.py` 的 `UIMode` 添加 `"web"`
5. 在 `async_main()` 添加路由分支

### 练习3：扩展功能

**问题**：如何在 `MyCLI.create()` 中添加配置文件加载？

**答案**：
```python
@staticmethod
async def create(work_dir: Path, verbose: bool = False) -> "MyCLI":
    # 验证工作目录
    if not work_dir.exists():
        raise FileNotFoundError(f"工作目录不存在: {work_dir}")

    # ⭐ 加载配置文件
    config_file = work_dir / "config.yaml"
    config = {}
    if config_file.exists():
        import yaml
        with open(config_file) as f:
            config = yaml.safe_load(f)

    # 创建实例
    instance = MyCLI(work_dir=work_dir, verbose=verbose)
    instance.config = config  # 保存配置

    return instance
```

---

## 总结

### Stage 02-03 完成的功能

✅ **App 层完整搭建**：
- 异步工厂方法
- UI 模式路由
- 应用状态管理

✅ **Print UI 完整实现**：
- 多种输入方式
- 标准I/O处理
- 模拟响应输出

✅ **三层架构贯通**：
- CLI → App → UI 数据流畅通
- 职责分离清晰
- 易于扩展

### 关键收获

1. **工厂模式**：异步初始化的最佳实践
2. **策略模式**：UI 模式的灵活切换
3. **标准I/O**：终端应用的基础
4. **分层架构**：复杂系统的组织方式

### 下一步方向

📖 **阅读顺序**：
1. `stage-01-架构.md`（CLI层）
2. 本文档（App层和UI层）← **你在这里**
3. `stage-04-架构.md`（Soul引擎）← **下一步**

🚀 **动手实践**：
1. 运行测试命令，验证功能
2. 阅读代码注释，理解设计
3. 尝试添加新的UI模式
4. 准备实现 Soul 引擎

---

**老王的建议**：
- 🎉 恭喜！三层架构已经跑通了！
- 📚 现在可以开始接入真实的LLM了
- 🔧 下一步最重要的是实现Soul引擎
- ✅ 每个阶段都测试好再进入下一阶段

**你已经理解 Stage 02-03 的架构填充流程了！准备好接入真实 LLM 了吗？** 🚀
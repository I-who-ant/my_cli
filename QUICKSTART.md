# My CLI - 快速开始指南

## 🎉 恭喜！你已经完成了阶段 1-3

你现在拥有一个**可运行的基础 AI Agent 框架**，包含：

- ✅ **CLI 层**（`cli.py`）：使用 Click 框架实现命令行参数解析
- ✅ **应用层**（`app.py`）：管理应用状态和配置
- ✅ **UI 层**（`ui/print/ui_print.py`）：最简单的 Print UI 模式

## 安装依赖

```bash
# 进入项目目录
cd kimi-cli-main/imitate-src

# 安装依赖（目前只需要 Click）
pip install -r requirements.txt
```

## 快速运行

### 1. 查看帮助

```bash
python -m my_cli.cli --help
```

**输出**：
```
Usage: python -m my_cli.cli [OPTIONS]

  My CLI - 从零开始构建你自己的 AI Agent.

Options:
  --version                 Show the version and exit.
  --verbose                 打印详细信息。默认：否
  -w, --work-dir DIRECTORY  工作目录。默认：当前目录
  -c, --command TEXT        用户查询命令。默认：交互式输入
  --ui [print|shell]        UI 模式。默认：print
  -h, --help                Show this message and exit.
```

### 2. 查看版本

```bash
python -m my_cli.cli --version
```

**输出**：
```
python -m my_cli.cli, version 0.1.0
```

### 3. 运行基本命令

```bash
python -m my_cli.cli -c "Hello World"
```

**输出**：
```
============================================================
My CLI - Print UI 模式
============================================================

用户命令: Hello World

AI 响应（模拟）:
------------------------------------------------------------
你说：Hello World

这是一个模拟的 AI 响应。

在后续阶段，这里会接入真实的 LLM API：
  - 阶段 4：实现 Wire 协议层（Soul ↔ UI 通信）
  - 阶段 5：实现 Soul 核心引擎（LLM 调用）
  - 阶段 7：实现工具系统（Function Calling）
------------------------------------------------------------

✅ Print UI 模式运行成功！
```

### 4. 开启详细输出

```bash
python -m my_cli.cli --verbose -c "Debug test"
```

**输出**：
```
[CLI 层] My CLI v0.1.0
[CLI 层] 工作目录: /home/user/project
[CLI 层] UI 模式: print

[应用层] MyCLI 实例创建成功
[应用层] 工作目录: /home/user/project
[应用层] 启动 Print UI 模式
[Print UI] 启动 Print UI 模式
[Print UI] 处理命令: Debug test

============================================================
My CLI - Print UI 模式
============================================================

用户命令: Debug test

... (输出省略)
```

### 5. 指定工作目录

```bash
python -m my_cli.cli -w /tmp -c "Working directory test"
```

## 项目结构

```
kimi-cli-main/imitate-src/
├── README.md                 # 学习路线图
├── QUICKSTART.md             # 快速开始（本文档）
├── requirements.txt          # 依赖列表
├── docs/                     # 学习文档
│   ├── stage-01-cli-entry.md      # 阶段 1 详细文档
│   ├── stage-02-app-layer.md      # 阶段 2 详细文档（待创建）
│   └── stage-03-print-ui.md       # 阶段 3 详细文档（待创建）
└── my_cli/                   # 源代码
    ├── __init__.py           # 包初始化
    ├── cli.py                # CLI 入口层
    ├── app.py                # 应用层
    └── ui/                   # UI 层
        ├── __init__.py
        └── print/            # Print UI 模式
            ├── __init__.py
            └── ui_print.py   # Print UI 实现
```

## 代码调用链路

理解代码的执行流程非常重要！

### 调用链路图

```
1. 用户执行命令
   $ python -m my_cli.cli -c "Hello"

2. Click 框架解析参数
   ↓

3. cli.py::my_cli() 函数
   ├── 接收参数：verbose, work_dir, command, ui
   └── 调用：asyncio.run(async_main(...))

4. cli.py::async_main() 异步函数
   ├── 导入：from my_cli.app import MyCLI
   ├── 创建应用实例：app = await MyCLI.create(...)
   └── 路由到 UI 模式：await app.run_print_mode(command)

5. app.py::MyCLI::create() 工厂方法
   ├── 验证工作目录
   └── 返回 MyCLI 实例

6. app.py::MyCLI::run_print_mode() 方法
   ├── 导入：from my_cli.ui.print.ui_print import PrintUI
   ├── 创建 UI 实例：ui = PrintUI(verbose=...)
   └── 运行 UI：await ui.run(command)

7. ui/print/ui_print.py::PrintUI::run() 方法
   ├── 接收用户命令
   ├── 处理命令（目前是模拟）
   └── 输出响应
```

### 关键设计模式

1. **工厂模式**：`MyCLI.create()` 异步工厂方法
   - 为什么？`__init__` 不能是异步的

2. **依赖注入**：通过参数传递配置
   - `MyCLI(work_dir, verbose)`

3. **策略模式**：根据 `ui` 参数选择不同的 UI 实现
   - `ui == "print"` → `run_print_mode()`
   - `ui == "shell"` → `run_shell_mode()`

## 对照源码学习

### 对比表

| 功能 | 简化版位置 | 原项目位置 | 简化说明 |
|------|-----------|-----------|---------|
| CLI 入口 | `my_cli/cli.py` | `src/kimi_cli/cli.py` | 去掉了 MCP、Agent、Session 等高级选项 |
| 应用层 | `my_cli/app.py` | `src/kimi_cli/app.py` | 去掉了 LLM 客户端、Soul 引擎等复杂逻辑 |
| Print UI | `my_cli/ui/print/ui_print.py` | `src/kimi_cli/ui/print/__init__.py` | 去掉了 Wire 协议、流式输出等高级特性 |

### 学习建议

1. **先运行简化版**：理解基本流程
2. **阅读简化版代码**：每个文件都有详细注释
3. **对照原项目**：看看原项目是如何扩展的
4. **阅读阶段文档**：`docs/stage-XX-*.md` 有详细的知识点

## 常见问题

### Q1: 为什么要用 `python -m my_cli.cli` 而不是 `python my_cli/cli.py`？

**答**：因为模块导入路径问题。

```bash
# ❌ 错误：无法找到 my_cli 模块
$ python my_cli/cli.py
ModuleNotFoundError: No module named 'my_cli'

# ✅ 正确：以模块形式运行
$ python -m my_cli.cli
```

### Q2: 如何添加新的命令行参数？

**答**：在 `cli.py` 中添加 `@click.option()`：

```python
@click.option(
    "--new-param",
    type=str,
    default="default_value",
    help="新参数的说明",
)
def my_cli(
    verbose: bool,
    work_dir: Path,
    command: str | None,
    ui: UIMode,
    new_param: str,  # 添加新参数
) -> None:
    asyncio.run(async_main(verbose, work_dir, command, ui, new_param))
```

详见：`docs/stage-01-cli-entry.md` 的练习题部分。

### Q3: 如何调试代码？

**方法 1：使用 print**
```python
print(f"[DEBUG] work_dir = {work_dir}")
```

**方法 2：使用 logging**
```python
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.debug(f"work_dir = {work_dir}")
```

**方法 3：使用 IDE 断点**
- 在 PyCharm/VSCode 中设置断点
- 以调试模式运行

### Q4: 如何从管道读取输入？

**答**：Print UI 已经支持管道输入！

```bash
# 从管道读取
$ echo "Hello from pipe" | python -m my_cli.cli --ui print

# 从文件读取
$ cat input.txt | python -m my_cli.cli --ui print
```

### Q5: 下一步学什么？

**答**：按照学习路线图循序渐进：

1. ✅ **阶段 1-3**：已完成！
2. ⏭️ **阶段 4**：实现 Wire 协议层（Soul ↔ UI 通信机制）
3. ⏭️ **阶段 5**：实现 Soul 核心引擎（接入真实 LLM API）
4. ⏭️ **阶段 6**：实现 Shell UI 模式（交互式终端）
5. ⏭️ **阶段 7**：实现工具系统（Function Calling）

每个阶段都有对应的文档和代码实现。

## 测试清单

在进入下一阶段前，确保你能完成以下测试：

- [ ] 运行 `--help` 查看帮助信息
- [ ] 运行 `--version` 查看版本号
- [ ] 运行基本命令（`-c "test"`）
- [ ] 开启详细输出（`--verbose`）
- [ ] 指定工作目录（`-w /tmp`）
- [ ] 理解调用链路（CLI → App → UI）
- [ ] 能够添加新的命令行参数
- [ ] 阅读了 `docs/stage-01-cli-entry.md`

## 进阶练习

### 练习 1：添加日志系统

在 `app.py` 中添加日志：

```python
import logging

class MyCLI:
    def __init__(self, work_dir: Path, verbose: bool = False):
        self.work_dir = work_dir
        self.verbose = verbose

        # 配置日志
        level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(
            level=level,
            format="[%(levelname)s] %(message)s"
        )
        self.logger = logging.getLogger(__name__)
```

### 练习 2：添加配置文件支持

创建 `config.py`：

```python
from pathlib import Path
import json

def load_config(config_file: Path) -> dict:
    """加载配置文件."""
    if not config_file.exists():
        return {}

    with open(config_file, "r", encoding="utf-8") as f:
        return json.load(f)
```

### 练习 3：添加错误处理

在 `ui_print.py` 中添加异常处理：

```python
async def run(self, command: str | None = None) -> None:
    try:
        # ... 原有逻辑
        pass
    except FileNotFoundError as e:
        print(f"❌ 文件不存在: {e}")
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        raise
```

## 参考资源

- **完整架构文档**：`../kimi-cli-main/src/kimi_cli/Kimi_CLI完整架构与数据流总览.md`
- **UI 模块详解**：`../kimi-cli-learn/阶段4_协议与标准/09_ACP协议/ui_print模块实现详解.md`
- **学习路线图**：`README.md`
- **阶段 1 详细文档**：`docs/stage-01-cli-entry.md`

## 获取帮助

遇到问题时：

1. 查看错误信息和堆栈跟踪
2. 阅读对应阶段的文档
3. 对照原项目源码
4. 使用 `--verbose` 查看详细输出
5. 询问 AI 助手（Claude/ChatGPT）

---

**准备好了吗？让我们继续学习后续阶段吧！** 🚀

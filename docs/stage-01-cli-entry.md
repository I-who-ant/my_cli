# 阶段 1：最简 CLI 入口

## 学习目标

通过这个阶段，你将学会：

1. ✅ 使用 Click 框架创建命令行工具
2. ✅ 理解 CLI 参数解析和类型系统
3. ✅ 使用 asyncio 实现异步入口
4. ✅ 掌握 Python 项目的基本结构

## 对应源码

- **原项目文件**：`kimi-cli-main/src/kimi_cli/cli.py` (266 行)
- **简化版本**：`my_cli/cli.py` (约 120 行)

**简化内容**：
- 去掉了复杂的配置选项（agent-file, model, mcp-config 等）
- 只保留最基础的参数（verbose, work-dir, command, ui）
- 暂时只支持 print 和 shell 两种 UI 模式
- 去掉了会话管理、日志系统等高级特性

## 核心代码详解

### 1. Click 框架基础

```python
import click

@click.command(context_settings=dict(help_option_names=["-h", "--help"]))
@click.version_option(__version__)
def my_cli(...):
    """命令行工具的主函数"""
    pass
```

**关键点**：
- `@click.command()`：定义一个命令行命令
- `context_settings`：自定义帮助选项（支持 `-h` 和 `--help`）
- `@click.version_option()`：自动添加 `--version` 选项

### 2. Click 参数类型

#### 布尔标志（Flag）
```python
@click.option(
    "--verbose",
    is_flag=True,
    default=False,
    help="打印详细信息。默认：否",
)
```

**使用**：
```bash
$ python cli.py --verbose -c "test"  # verbose = True
$ python cli.py -c "test"            # verbose = False
```

#### 路径参数
```python
@click.option(
    "--work-dir",
    "-w",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    default=Path.cwd(),
    help="工作目录。默认：当前目录",
)
```

**关键点**：
- `exists=True`：路径必须存在
- `file_okay=False`：不允许文件
- `dir_okay=True`：只允许目录
- `path_type=Path`：自动转换为 `pathlib.Path` 对象

#### 字符串参数
```python
@click.option(
    "--command",
    "-c",
    type=str,
    default=None,
    help="用户查询命令。默认：交互式输入",
)
```

#### 选择参数（Choice）
```python
@click.option(
    "--ui",
    type=click.Choice(["print", "shell"]),
    default="print",
    help="UI 模式。默认：print",
)
```

**使用**：
```bash
$ python cli.py --ui print -c "test"   # ✅ 合法
$ python cli.py --ui shell -c "test"   # ✅ 合法
$ python cli.py --ui acp -c "test"     # ❌ 错误：不在选择列表中
```

### 3. 类型注解

```python
from typing import Literal

UIMode = Literal["print", "shell"]

def my_cli(
    verbose: bool,
    work_dir: Path,
    command: str | None,
    ui: UIMode,
) -> None:
    ...
```

**关键点**：
- `Literal["print", "shell"]`：限制只能是这两个字符串之一
- `str | None`：Python 3.10+ 的联合类型语法（等价于 `Optional[str]`）
- `-> None`：函数没有返回值

### 4. Asyncio 异步入口

```python
def my_cli(...):
    # 同步函数作为 Click 入口
    asyncio.run(async_main(...))

async def async_main(...):
    # 异步函数执行实际业务逻辑
    print("Hello, Async World!")
```

**为什么使用异步？**

1. **LLM API 调用**：网络请求是异步的
2. **UI 更新**：需要并发处理 UI 渲染和数据接收
3. **工具调用**：多个工具可以并发执行
4. **现代标准**：asyncio 是 Python 3.7+ 的标准异步框架

**对比源码**：

在 Kimi CLI 中（`cli.py:266`）：
```python
def kimi(...):
    asyncio.run(_main(...))

async def _main(...):
    # 创建 Session
    session = Session.create(work_dir) or Session.continue_(work_dir)

    # 创建 KimiCLI 实例
    instance = await KimiCLI.create(session, ...)

    # 路由到不同的 UI 模式
    match ui:
        case "shell": return await instance.run_shell_mode(command)
        case "print": return await instance.run_print_mode(...)
        case "acp": return await instance.run_acp_server()
        case "wire": return await instance.run_wire_server()
```

我们暂时简化为：
```python
def my_cli(...):
    asyncio.run(async_main(...))

async def async_main(...):
    # 阶段 1：只打印信息
    print("My CLI - 阶段 1：最简 CLI 入口")
```

## 运行测试

### 1. 安装依赖

首先需要安装 Click：

```bash
pip install click
```

### 2. 运行命令

```bash
# 进入项目目录
cd kimi-cli-main/imitate-src/my_cli

# 查看帮助
python cli.py --help

# 查看版本
python cli.py --version

# 运行基本命令
python cli.py -c "Hello World"

# 开启详细输出
python cli.py --verbose -c "Test"

# 指定工作目录
python cli.py -w /tmp -c "Working directory test"

# 指定 UI 模式
python cli.py --ui print -c "Print mode"
python cli.py --ui shell -c "Shell mode"
```

### 3. 预期输出

```bash
$ python cli.py -c "Hello World"
============================================================
My CLI - 阶段 1：最简 CLI 入口
============================================================

用户命令: Hello World

✅ CLI 框架运行成功！

下一步：
  - 阶段 2：实现应用层框架（app.py）
  - 阶段 3：实现 Print UI 模式
  - 阶段 4：实现 Wire 协议层
```

```bash
$ python cli.py --verbose -c "Hello World"
============================================================
My CLI - 阶段 1：最简 CLI 入口
============================================================

[详细] 版本: 0.1.0
[详细] 工作目录: /home/user/project
[详细] UI 模式: print

用户命令: Hello World

✅ CLI 框架运行成功！
...
```

## 与源码对比

### 相同点

1. ✅ 都使用 Click 框架
2. ✅ 都使用 asyncio 作为异步入口
3. ✅ 都使用 `pathlib.Path` 处理路径
4. ✅ 都使用 `Literal` 定义类型限制

### 简化点

1. ❌ 去掉了 `--debug`, `--agent-file`, `--model` 等高级选项
2. ❌ 去掉了会话管理（Session）
3. ❌ 去掉了配置文件加载
4. ❌ 去掉了 MCP 配置
5. ❌ 去掉了日志系统
6. ❌ 只保留了 print 和 shell 两种 UI 模式

### 核心保留

| 原项目 | 简化版 | 说明 |
|--------|--------|------|
| `@click.command()` | ✅ 保留 | Click 命令定义 |
| `@click.option()` | ✅ 保留 | 参数定义（简化数量） |
| `asyncio.run()` | ✅ 保留 | 异步入口 |
| `UIMode = Literal[...]` | ✅ 保留 | 类型定义（简化选项） |
| `Session.create()` | ❌ 移除 | 阶段 2 再添加 |
| `KimiCLI.create()` | ❌ 移除 | 阶段 2 再添加 |
| `match ui: case ...` | ❌ 移除 | 阶段 3+ 再添加 |

## 学习要点

### 1. Click 框架的优势

- **自动生成帮助**：`--help` 自动生成，无需手写
- **类型验证**：自动验证参数类型和范围
- **错误处理**：自动处理参数错误，给出友好提示
- **嵌套命令**：支持子命令（如 `git commit`, `git push`）

### 2. 为什么使用 asyncio？

**同步代码的问题**：
```python
# 同步代码：必须等待完成
response = llm_api.call("Hello")  # 阻塞 5 秒
render_ui(response)
```

**异步代码的优势**：
```python
# 异步代码：可以并发处理
async with asyncio.TaskGroup() as tg:
    tg.create_task(llm_api.call("Hello"))  # 不阻塞
    tg.create_task(render_ui())            # 同时运行
```

### 3. pathlib.Path vs 字符串

**为什么使用 Path？**

```python
# 字符串路径：容易出错
work_dir = "/home/user/project"
config_file = work_dir + "/config.yaml"  # ❌ 在 Windows 上会出错

# Path 对象：跨平台
work_dir = Path("/home/user/project")
config_file = work_dir / "config.yaml"   # ✅ 自动处理路径分隔符
```

### 4. 类型注解的好处

```python
# 没有类型注解：IDE 无法提示
def process(data):
    return data.upper()  # ❌ IDE 不知道 data 是什么类型

# 有类型注解：IDE 智能提示
def process(data: str) -> str:
    return data.upper()  # ✅ IDE 知道 data 是字符串
```

## 常见问题

### Q1: 为什么要用 Click 而不是 argparse？

**argparse**（标准库）：
```python
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--verbose", action="store_true")
parser.add_argument("--command", type=str)
args = parser.parse_args()
```

**Click**（第三方库）：
```python
import click
@click.command()
@click.option("--verbose", is_flag=True)
@click.option("--command", type=str)
def cli(verbose, command):
    pass
```

**优势**：
- 代码更简洁（装饰器风格）
- 自动类型转换（如 `Path`）
- 更好的嵌套命令支持
- 自动生成更漂亮的帮助信息

### Q2: 为什么 CLI 入口是同步函数，但里面调用异步函数？

因为 Click 不直接支持异步函数，所以：
1. CLI 入口必须是同步函数（Click 要求）
2. 使用 `asyncio.run()` 桥接到异步世界
3. 实际业务逻辑在异步函数中执行

### Q3: `str | None` 和 `Optional[str]` 有什么区别？

完全等价！只是语法不同：

```python
# Python 3.10+ 新语法
command: str | None

# Python 3.9- 旧语法
from typing import Optional
command: Optional[str]
```

## 下一步

完成阶段 1 后，你应该能够：

- [x] 运行 `python cli.py --help` 查看帮助
- [x] 理解 Click 装饰器的作用
- [x] 知道为什么使用 asyncio
- [x] 能够添加新的命令行参数

**准备好了吗？让我们进入阶段 2：实现应用层框架！**

## 练习题

### 练习 1：添加新参数

在 `cli.py` 中添加一个 `--model` 参数：

```python
@click.option(
    "--model",
    "-m",
    type=str,
    default="gpt-4",
    help="LLM 模型名称。默认：gpt-4",
)
def my_cli(
    verbose: bool,
    work_dir: Path,
    command: str | None,
    ui: UIMode,
    model: str,  # 新增参数
) -> None:
    asyncio.run(async_main(verbose, work_dir, command, ui, model))
```

测试：
```bash
$ python cli.py --model gpt-3.5-turbo -c "test"
```

### 练习 2：添加新 UI 模式

修改 `UIMode` 类型定义：

```python
UIMode = Literal["print", "shell", "acp"]  # 添加 acp
```

测试：
```bash
$ python cli.py --ui acp -c "test"  # 应该能运行
```

### 练习 3：添加日志输出

在 `async_main` 中添加简单的日志：

```python
import logging

async def async_main(...):
    # 配置日志
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    logger = logging.getLogger(__name__)
    logger.info(f"工作目录: {work_dir}")
    logger.debug(f"命令: {command}")
```

测试：
```bash
$ python cli.py -c "test"                 # 只显示 INFO
$ python cli.py --verbose -c "test"       # 显示 INFO 和 DEBUG
```

---

**完成这些练习后，你就完全掌握阶段 1 的内容了！🎉**
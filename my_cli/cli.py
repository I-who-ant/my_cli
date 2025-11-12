#!/usr/bin/env python3
"""
阶段 1：最简 CLI 入口

学习目标：
1. 使用 Click 框架创建命令行工具
2. 理解 CLI 参数解析
3. 实现一个能运行的最简程序

对应源码：kimi-cli-main/src/kimi_cli/cli.py (266 行)
"""

import asyncio
from pathlib import Path
from typing import Literal

import click

from my_cli import __version__

# 定义 UI 模式类型（目前只实现最简单的）
UIMode = Literal["print", "shell"]


@click.command(context_settings=dict(help_option_names=["-h", "--help"]))
@click.version_option(__version__)
@click.option(
    "--verbose",
    is_flag=True,
    default=False,
    help="打印详细信息。默认：否",
)
@click.option(
    "--work-dir",
    "-w",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    default=Path.cwd(),
    help="工作目录。默认：当前目录",
)
@click.option(
    "--command",
    "-c",
    type=str,
    default=None,
    help="用户查询命令。默认：交互式输入",
)
@click.option(
    "--ui",
    type=click.Choice(["print", "shell"]),
    default="print",
    help="UI 模式。默认：print",
)
def my_cli(
    verbose: bool,
    work_dir: Path,
    command: str | None,
    ui: UIMode,
) -> None:
    """My CLI - 从零开始构建你自己的 AI Agent.

    这是阶段 1 的实现，只包含最基础的 CLI 框架。

    使用示例：

        # 显示帮助信息
        $ python cli.py --help

        # 显示版本
        $ python cli.py --version

        # 运行在 print 模式（默认）
        $ python cli.py -c "Hello World"

        # 指定工作目录
        $ python cli.py -w /tmp -c "Test"

        # 开启详细输出
        $ python cli.py --verbose -c "Debug test"
    """
    # 使用 asyncio.run() 运行异步主函数
    asyncio.run(async_main(verbose, work_dir, command, ui))


async def async_main(
    verbose: bool,
    work_dir: Path,
    command: str | None,
    ui: UIMode,
) -> None:
    """异步主函数 - 实际的业务逻辑在这里执行.

    为什么使用异步？
    - Kimi CLI 大量使用异步 I/O（网络请求、文件读写）
    - 异步可以更好地处理并发任务（UI 渲染 + LLM 请求）
    - asyncio 是现代 Python 的标准异步框架
    """
    # 导入应用层
    from my_cli.app import MyCLI

    if verbose:
        print(f"[CLI 层] My CLI v{__version__}")
        print(f"[CLI 层] 工作目录: {work_dir}")
        print(f"[CLI 层] UI 模式: {ui}")
        print()

    # 创建 MyCLI 应用实例
    app = await MyCLI.create(
        work_dir=work_dir,
        verbose=verbose,
    )

    # 根据 UI 模式路由到不同的 UI 实现
    if ui == "print":
        await app.run_print_mode(command)
    elif ui == "shell":
        await app.run_shell_mode(command)
    else:
        print(f"❌ 错误：不支持的 UI 模式: {ui}")
        print("提示：当前支持的 UI 模式：print, shell")


# 主入口
if __name__ == "__main__":
    my_cli()
#!/usr/bin/env python3
"""
CLI - 命令行入口

学习目标：
1. 使用 Typer 框架创建命令行工具 ⭐ Stage 19.1 切换到 Typer
2. 理解 CLI 参数解析
3. 集成 Session 管理

对应源码：kimi-cli-fork/src/kimi_cli/cli.py

阶段演进：
- Stage 1：最简 CLI 入口 ✅
- Stage 4-5：Soul 引擎集成 ✅
- Stage 18：Session 管理集成 ✅
- Stage 19.1：切换到 Typer 框架 ⭐ 新增
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import Annotated, Literal

import typer

from my_cli import __version__
from my_cli.app import MyCLI, enable_logging
from my_cli.metadata import WorkDirMeta, load_metadata, save_metadata
from my_cli.session import Session
from my_cli.utils.logging import logger

# ============================================================
# Reload 异常 ⭐ Stage 19.2
# ============================================================


class Reload(Exception):
    """Reload configuration."""

    pass


# 创建 Typer 应用 ⭐ Stage 19.1
cli = typer.Typer(
    add_completion=False,
    context_settings={"help_option_names": ["-h", "--help"]},
    help="My CLI, your next CLI agent.",
)

# 定义 UI 模式类型
UIMode = Literal["print", "shell", "acp", "wire"]

# 定义输出格式类型
InputFormat = Literal["text", "stream-json"]
OutputFormat = Literal["text", "stream-json"]


def _version_callback(value: bool) -> None:
    """版本回调函数 ⭐ Stage 19.1 Typer 简化版"""
    if value:
        typer.echo(f"my_cli, version {__version__}")
        raise typer.Exit()


@cli.command()
def my_cli(
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            "-V",
            help="显示版本并退出",
            callback=_version_callback,
            is_eager=True,
        ),
    ] = False,
    verbose: Annotated[
        bool,
        typer.Option("--verbose", help="打印详细信息。默认：否"),
    ] = False,
    debug: Annotated[
        bool,
        typer.Option("--debug", help="打印调试信息。默认：否"),
    ] = False,
    agent_file: Annotated[
        Path | None,
        typer.Option(
            "--agent-file",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="自定义 Agent 规范文件。默认：内置默认 Agent",
        ),
    ] = None,
    model: Annotated[
        str | None,
        typer.Option(
            "--model",
            "-m",
            help="使用的 LLM 模型。默认：配置文件中设置的默认模型",
        ),
    ] = None,
    work_dir: Annotated[
        Path | None,
        typer.Option(
            "--work-dir",
            "-w",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            writable=True,
            help="工作目录。默认：当前目录",
        ),
    ] = None,
    continue_session: Annotated[
        bool,
        typer.Option(
            "--continue",
            "-C",
            help="继续工作目录的上次会话。默认：否",
        ),
    ] = False,
    command: Annotated[
        str | None,
        typer.Option(
            "--command",
            "-c",
            "--query",
            "-q",
            help="用户查询命令。默认：交互式输入",
        ),
    ] = None,
    print_mode: Annotated[
        bool,
        typer.Option(
            "--print",
            help="运行在打印模式（非交互式）。注意：打印模式隐含启用 --yolo",
        ),
    ] = False,
    acp_mode: Annotated[
        bool,
        typer.Option("--acp", help="作为 ACP 服务器运行"),
    ] = False,
    wire_mode: Annotated[
        bool,
        typer.Option("--wire", help="作为 Wire 服务器运行（实验性）"),
    ] = False,
    input_format: Annotated[
        str | None,
        typer.Option(
            "--input-format",
            help="输入格式（必须与 --print 一起使用）。默认：text",
        ),
    ] = None,
    output_format: Annotated[
        str | None,
        typer.Option(
            "--output-format",
            help="输出格式（必须与 --print 一起使用）。默认：text",
        ),
    ] = None,
    mcp_config_file: Annotated[
        list[Path],
        typer.Option(
            "--mcp-config-file",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="加载 MCP 配置文件。可以多次指定以加载多个 MCP 配置。默认：无",
        ),
    ] = [],
    mcp_config: Annotated[
        list[str],
        typer.Option(
            "--mcp-config",
            help="加载 MCP 配置 JSON。可以多次指定以加载多个 MCP 配置。默认：无",
        ),
    ] = [],
    yolo: Annotated[
        bool,
        typer.Option(
            "--yolo",
            "--yes",
            "-y",
            "--auto-approve",
            help="自动批准所有操作。默认：否",
        ),
    ] = False,
    thinking: Annotated[
        str | None,
        typer.Option(
            "--thinking",
            help="启用思考模式（如果支持）。默认：使用上次的设置",
        ),
    ] = None,
) -> None:
    """My CLI - 你的下一个命令行 AI Agent.

    对应源码：kimi-cli-fork/src/kimi_cli/cli.py:197
    """
    # 版本处理在回调函数中完成

    # 验证特殊标志组合
    special_flags = {
        "--print": print_mode,
        "--acp": acp_mode,
        "--wire": wire_mode,
    }
    active_specials = [flag for flag, active in special_flags.items() if active]
    if len(active_specials) > 1:
        typer.echo(f"错误: 不能组合使用 {', '.join(active_specials)}", err=True)
        raise typer.Exit(1)

    # 确定 UI 模式
    ui: UIMode = "shell"
    if print_mode:
        ui = "print"
    elif acp_mode:
        ui = "acp"
    elif wire_mode:
        ui = "wire"

    # 启用日志
    enable_logging(debug)

    # 设置工作目录
    work_dir = (work_dir or Path.cwd()).absolute()

    # 处理会话
    if continue_session:
        session = Session.continue_(work_dir)
        if session is None:
            typer.echo("错误: 工作目录没有找到上次会话", err=True)
            raise typer.Exit(1)
        if verbose:
            typer.echo(f"✓ 继续上次会话: {session.id}")
    else:
        session = Session.create(work_dir)
        if verbose:
            typer.echo(f"✓ 创建新会话: {session.id}")

    if verbose:
        typer.echo(f"✓ 会话历史文件: {session.history_file}")

    # 验证命令
    if command is not None:
        command = command.strip()
        if not command:
            typer.echo("错误: 命令不能为空", err=True)
            raise typer.Exit(1)

    # 验证输入/输出格式
    if input_format is not None and ui != "print":
        typer.echo("错误: 输入格式仅支持打印 UI", err=True)
        raise typer.Exit(1)
    if output_format is not None and ui != "print":
        typer.echo("错误: 输出格式仅支持打印 UI", err=True)
        raise typer.Exit(1)

    # 处理 MCP 配置
    mcp_configs: list[dict] = []
    try:
        # 从文件加载
        for conf_file in mcp_config_file:
            mcp_configs.append(json.loads(conf_file.read_text(encoding="utf-8")))
    except json.JSONDecodeError as e:
        typer.echo(f"错误: 无效的 JSON: {e}", err=True)
        raise typer.Exit(1)

    try:
        # 从命令行参数加载
        for conf in mcp_config:
            mcp_configs.append(json.loads(conf))
    except json.JSONDecodeError as e:
        typer.echo(f"错误: 无效的 JSON: {e}", err=True)
        raise typer.Exit(1)

    async def _run() -> bool:
        """运行主逻辑"""
        # 处理 thinking 模式
        if thinking is None:
            metadata = load_metadata()
            thinking_mode = metadata.thinking
        else:
            # thinking 参数是字符串，需要转换为布尔值
            thinking_mode = thinking.lower() in ("true", "1", "yes", "on")

        # 创建应用实例
        instance = await MyCLI.create(
            session,
            yolo=yolo or (ui == "print"),  # print 模式隐含 yolo
            mcp_configs=mcp_configs,
            model_name=model,
            thinking=thinking_mode,
            agent_file=agent_file,
        )

        # 运行相应的 UI 模式
        match ui:
            case "shell":
                succeeded = await instance.run_shell_mode(command)
            case "print":
                # Stage 18: print 模式暂时使用简化实现
                await instance.run_print_mode(command)
                succeeded = True
            case "acp":
                # TODO: Stage 19+ 实现 ACP 服务器
                typer.echo("ACP 模式尚未实现", err=True)
                succeeded = False
            case "wire":
                # TODO: Stage 19+ 实现 Wire 服务器
                typer.echo("Wire 模式尚未实现", err=True)
                succeeded = False

        # 更新 metadata
        if succeeded:
            metadata = load_metadata()

            # 更新工作目录的会话信息
            work_dir_meta = next(
                (wd for wd in metadata.work_dirs if wd.path == str(session.work_dir)), None
            )

            if work_dir_meta is None:
                logger.warning(
                    "缺少工作目录元数据，正在重新创建: {work_dir}",
                    work_dir=session.work_dir,
                )
                work_dir_meta = WorkDirMeta(path=str(session.work_dir))
                metadata.work_dirs.append(work_dir_meta)

            work_dir_meta.last_session_id = session.id

            # 更新 thinking 模式状态
            metadata.thinking = instance.soul.thinking

            save_metadata(metadata)

        return succeeded

    # 运行主逻辑（支持 Reload 重载）⭐ Stage 19.2
    while True:
        try:
            succeeded = asyncio.run(_run())
            if not succeeded:
                raise typer.Exit(1)
            break  # 正常退出，跳出循环
        except Reload:
            # /setup 或 /reload 触发，重新运行
            continue
        except KeyboardInterrupt:
            typer.echo("\n已取消操作", err=True)
            raise typer.Exit(1)


# 主入口
if __name__ == "__main__":
    cli()

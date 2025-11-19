"""
Shell UI 斜杠命令系统（Meta Command）

职责：
1. 定义斜杠命令注册装饰器
2. 提供命令查询接口
3. 实现命令路由逻辑

对应源码：kimi-cli-fork/src/kimi_cli/ui/shell/metacmd.py (300+行)

为什么单独分离？
1. 斜杠命令是独立的子系统，有自己的注册、查询、执行逻辑
2. 使用装饰器模式，符合开闭原则（OCP）
3. 添加新命令不需要修改核心代码
4. 可以独立测试命令系统

Stage 11 实现：
- 简化版，只支持基础命令注册
- 官方版还包括：
  * 命令参数解析
  * 异步命令支持
  * Kimi Soul 专属命令
  * 复杂的帮助系统
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

from rich.panel import Panel

from my_cli.ui.shell.console import console

if TYPE_CHECKING:
    # 避免循环导入
    from my_cli.ui.shell import ShellApp

# 命令函数类型：接受 ShellApp 和参数列表，返回 None 或 Awaitable
type MetaCmdFunc = Callable[["ShellApp", list[str]], None | Awaitable[None]]


@dataclass(frozen=True, slots=True, kw_only=True)
class MetaCommand:
    """斜杠命令定义"""

    name: str  # 主命令名称（如 "help"）
    description: str  # 命令描述
    func: MetaCmdFunc  # 命令执行函数
    aliases: list[str]  # 别名列表（如 ["h", "?"]）

    def slash_name(self) -> str:
        """/name (aliases)"""
        if self.aliases:
            return f"/{self.name} ({', '.join(self.aliases)})"
        return f"/{self.name}"


# 命令注册表
# 主命令名 -> MetaCommand
_meta_commands: dict[str, MetaCommand] = {}

# 主命令名或别名 -> MetaCommand
_meta_command_aliases: dict[str, MetaCommand] = {}


def get_meta_command(name: str) -> MetaCommand | None:
    """根据命令名或别名查询命令"""
    return _meta_command_aliases.get(name)


def get_meta_commands() -> list[MetaCommand]:
    """获取所有注册的命令（不重复）"""
    return list(_meta_commands.values())


def meta_command(
    func: MetaCmdFunc | None = None,
    *,
    name: str | None = None,
    aliases: list[str] | None = None,
) -> MetaCmdFunc | Callable[[MetaCmdFunc], MetaCmdFunc]:
    """
    装饰器：注册斜杠命令 ⭐ Stage 19.2

    用法：
        @meta_command
        def setup(app, args): ...

        @meta_command(name="config")
        def configure(app, args): ...

        @meta_command(aliases=["h", "?"])
        def help(app, args): ...

    对应源码：kimi-cli-fork/src/kimi_cli/ui/shell/metacmd.py:84-135
    """

    def _register(f: MetaCmdFunc) -> MetaCmdFunc:
        """内部注册函数"""
        primary = name or f.__name__
        alias_list = aliases or []

        cmd = MetaCommand(
            name=primary,
            description=(f.__doc__ or "").strip(),
            func=f,
            aliases=alias_list,
        )

        # 注册主命令
        _meta_commands[primary] = cmd
        _meta_command_aliases[primary] = cmd

        # 注册别名
        for alias in alias_list:
            _meta_command_aliases[alias] = cmd

        return f

    # 支持两种用法：@meta_command 和 @meta_command(...)
    if func is not None:
        return _register(func)
    return _register


def register_meta_command(
    name: str,
    description: str,
    func: MetaCmdFunc,
    aliases: list[str] | None = None,
) -> None:
    """注册斜杠命令"""
    aliases = aliases or []

    cmd = MetaCommand(
        name=name,
        description=description,
        func=func,
        aliases=aliases,
    )

    # 注册主命令
    _meta_commands[name] = cmd
    _meta_command_aliases[name] = cmd

    # 注册别名
    for alias in aliases:
        _meta_command_aliases[alias] = cmd


# ============================================================
# 内置斜杠命令实现
# ============================================================


async def _cmd_help(app: "ShellApp", args: list[str]) -> None:
    """显示帮助信息"""
    help_text = """[bold cyan]📚 可用命令：[/bold cyan]

[bold]基础命令：[/bold]
  exit, quit         退出程序
  Ctrl+D             退出程序
  Ctrl+C             取消当前请求

[bold]斜杠命令：[/bold]
"""

    # 动态列出所有注册的斜杠命令
    for cmd in sorted(get_meta_commands(), key=lambda c: c.name):
        aliases_str = f" ({', '.join(cmd.aliases)})" if cmd.aliases else ""
        help_text += f"  /{cmd.name}{aliases_str:<15} {cmd.description}\n"

    help_text += """
[bold]功能：[/bold]
  - 多轮对话（自动保持 Context）
  - 工具调用（Bash、ReadFile、WriteFile）
  - 命令历史（上下箭头查看历史输入）
  - 流式输出（实时显示 LLM 响应）

[grey50]提示：直接输入问题即可开始对话[/grey50]
"""
    console.print(Panel(help_text, border_style="cyan", padding=(1, 2)))


async def _cmd_clear(app: "ShellApp", args: list[str]) -> None:
    """清空 Context"""
    # TODO: 实现 Context.clear() 方法
    console.print("[yellow]⚠️  /clear 命令暂未实现（需要 Context.clear() 方法）[/yellow]")
    console.print("[grey50]提示：重启程序可清空历史[/grey50]")


# ============================================================
# 注册内置命令
# ============================================================

register_meta_command(
    name="help",
    description="显示此帮助信息",
    func=_cmd_help,
    aliases=["h", "?"],
)

register_meta_command(
    name="clear",
    description="清空对话历史（Context）",
    func=_cmd_clear,
    aliases=["c"],
)

__all__ = [
    "MetaCommand",
    "MetaCmdFunc",
    "get_meta_command",
    "get_meta_commands",
    "register_meta_command",
]

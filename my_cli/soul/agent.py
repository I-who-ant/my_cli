"""
Agent 模块 ⭐ Stage 26 完整实现

学习目标：
1. 理解 Agent 的职责（定义 Agent 的身份和能力）
2. 理解 system_prompt 的作用
3. 理解 load_agent() 的工具加载机制

对应源码：kimi-cli-fork/src/kimi_cli/soul/agent.py
"""

from __future__ import annotations

import importlib
import inspect
import string
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from kosong.tooling import CallableTool, Toolset

from my_cli.agentspec import ResolvedAgentSpec, load_agent_spec
from my_cli.utils.logging import logger

if TYPE_CHECKING:
    from my_cli.config import Config
    from my_cli.session import Session
    from my_cli.soul.approval import Approval
    from my_cli.soul.runtime import BuiltinSystemPromptArgs, Runtime
    from my_cli.soul.toolset import CustomToolset


@dataclass(frozen=True, slots=True, kw_only=True)
class Agent:
    """
    Agent - 定义 AI Agent 的身份和能力 ⭐ Stage 26

    Attributes:
        name: Agent 名称
        system_prompt: 系统提示词
        toolset: 工具集

    对应源码：kimi-cli-fork/src/kimi_cli/soul/agent.py:23-29
    """

    name: str
    system_prompt: str
    toolset: Toolset


async def load_agent(
    agent_file: Path,
    runtime: Runtime,
    *,
    mcp_configs: list[dict[str, Any]] | None = None,
) -> Agent:
    """
    从规范文件加载 Agent ⭐ Stage 26

    Args:
        agent_file: Agent 规范文件路径
        runtime: Runtime 实例
        mcp_configs: MCP 配置列表

    Returns:
        Agent: 加载的 Agent 实例

    Raises:
        FileNotFoundError: Agent 文件不存在
        AgentSpecError: Agent 规范无效

    对应源码：kimi-cli-fork/src/kimi_cli/soul/agent.py:32-80
    """
    logger.info("Loading agent: {agent_file}", agent_file=agent_file)
    agent_spec = load_agent_spec(agent_file)

    # 加载系统提示词
    system_prompt = _load_system_prompt(
        agent_spec.system_prompt_path,
        agent_spec.system_prompt_args,
        runtime.builtin_args,
    )

    # 工具依赖注入映射
    from my_cli.soul.toolset import CustomToolset

    tool_deps: dict[type, Any] = {
        ResolvedAgentSpec: agent_spec,
        Runtime: runtime,
    }

    # 可选依赖（如果 runtime 有这些属性）
    if hasattr(runtime, "config"):
        from my_cli.config import Config

        tool_deps[Config] = runtime.config
    if hasattr(runtime, "builtin_args"):
        from my_cli.soul.runtime import BuiltinSystemPromptArgs

        tool_deps[BuiltinSystemPromptArgs] = runtime.builtin_args
    if hasattr(runtime, "session"):
        from my_cli.session import Session

        tool_deps[Session] = runtime.session
    if hasattr(runtime, "approval"):
        from my_cli.soul.approval import Approval

        tool_deps[Approval] = runtime.approval

    # 处理工具列表
    tools = agent_spec.tools
    if agent_spec.exclude_tools:
        logger.debug("Excluding tools: {tools}", tools=agent_spec.exclude_tools)
        tools = [tool for tool in tools if tool not in agent_spec.exclude_tools]

    # 加载工具
    toolset = CustomToolset()
    bad_tools = _load_tools(toolset, tools, tool_deps)
    if bad_tools:
        logger.warning("Failed to load tools: {bad_tools}", bad_tools=bad_tools)

    # 加载 MCP 工具
    if mcp_configs:
        await _load_mcp_tools(toolset, mcp_configs, runtime)

    return Agent(
        name=agent_spec.name,
        system_prompt=system_prompt,
        toolset=toolset,
    )


def _load_system_prompt(
    path: Path, args: dict[str, str], builtin_args: BuiltinSystemPromptArgs
) -> str:
    """
    加载系统提示词 ⭐ Stage 26

    支持模板变量替换（使用 string.Template）

    Args:
        path: 系统提示词文件路径
        args: Agent 规范中的参数
        builtin_args: 内置参数

    Returns:
        str: 渲染后的系统提示词
    """
    logger.info("Loading system prompt: {path}", path=path)

    if not path.exists():
        logger.warning("System prompt file not found: {path}", path=path)
        return f"You are an AI assistant."

    system_prompt = path.read_text(encoding="utf-8").strip()
    logger.debug(
        "Substituting system prompt with builtin args: {builtin_args}, spec args: {spec_args}",
        builtin_args=builtin_args,
        spec_args=args,
    )

    try:
        return string.Template(system_prompt).substitute(asdict(builtin_args), **args)
    except (KeyError, ValueError) as e:
        logger.warning("Failed to substitute system prompt: {error}", error=e)
        return system_prompt


def _load_tools(
    toolset: CustomToolset,
    tools: list[str],
    deps: dict[type, Any],
) -> list[str]:
    """
    加载工具到 Toolset ⭐ Stage 26

    工具字符串格式：module:ClassName
    例如：my_cli.tools.bash:Bash

    支持依赖注入：根据工具构造函数的类型注解自动注入依赖。

    Args:
        toolset: 目标工具集
        tools: 工具列表
        deps: 依赖注入映射

    Returns:
        list[str]: 加载失败的工具列表

    对应源码：kimi-cli-fork/src/kimi_cli/soul/agent.py:100-149
    """
    bad_tools: list[str] = []

    for tool_str in tools:
        try:
            tool = _load_tool(tool_str, deps)
            if tool is not None:
                toolset.register_tool(tool)
                logger.debug("Loaded tool: {tool}", tool=tool_str)
        except Exception as e:
            logger.warning("Failed to load tool {tool}: {error}", tool=tool_str, error=e)
            bad_tools.append(tool_str)

    return bad_tools


def _load_tool(tool_str: str, deps: dict[type, Any]) -> CallableTool | None:
    """
    加载单个工具

    Args:
        tool_str: 工具字符串（格式：module:ClassName）
        deps: 依赖注入映射

    Returns:
        CallableTool | None: 工具实例，或 None（如果加载失败）
    """
    if ":" not in tool_str:
        raise ValueError(f"Invalid tool format: {tool_str} (expected module:ClassName)")

    module_path, class_name = tool_str.rsplit(":", 1)

    # 导入模块
    try:
        module = importlib.import_module(module_path)
    except ImportError as e:
        raise ImportError(f"Failed to import module {module_path}: {e}") from e

    # 获取工具类
    if not hasattr(module, class_name):
        raise AttributeError(f"Module {module_path} has no attribute {class_name}")

    tool_class = getattr(module, class_name)

    # 检查是否是 CallableTool
    if not (isinstance(tool_class, type) and issubclass(tool_class, CallableTool)):
        raise TypeError(f"{tool_str} is not a CallableTool subclass")

    # 依赖注入
    init_signature = inspect.signature(tool_class.__init__)
    kwargs: dict[str, Any] = {}

    for param_name, param in init_signature.parameters.items():
        if param_name == "self":
            continue
        if param.annotation in deps:
            kwargs[param_name] = deps[param.annotation]
        elif param.default is inspect.Parameter.empty:
            # 必需参数但没有提供依赖
            logger.warning(
                "Tool {tool} requires {param} but no dependency provided",
                tool=tool_str,
                param=param_name,
            )

    # 创建工具实例
    return tool_class(**kwargs)


async def _load_mcp_tools(
    toolset: CustomToolset,
    mcp_configs: list[dict[str, Any]],
    runtime: Runtime,
) -> None:
    """
    加载 MCP 工具 ⭐ Stage 26 完全对齐官方实现

    从 MCP 配置加载外部工具。

    Args:
        toolset: 目标工具集
        mcp_configs: MCP 配置列表
        runtime: Runtime 实例

    Raises:
        ValueError: MCP 配置无效
        RuntimeError: MCP 服务器连接失败

    对应源码：kimi-cli-fork/src/kimi_cli/soul/agent.py:_load_mcp_tools
    """
    import fastmcp

    from my_cli.tools.mcp import MCPTool

    for mcp_config in mcp_configs:
        logger.info("Loading MCP tools from: {mcp_config}", mcp_config=mcp_config)
        client = fastmcp.Client(mcp_config)
        async with client:
            for tool in await client.list_tools():
                toolset += MCPTool(tool, client, runtime=runtime)


__all__ = ["Agent", "load_agent"]

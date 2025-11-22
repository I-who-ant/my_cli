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
from typing import Any

from kosong.tooling import CallableTool, CallableTool2, Toolset

from my_cli.agentspec import ResolvedAgentSpec, load_agent_spec
from my_cli.config import Config
from my_cli.session import Session
from my_cli.soul.approval import Approval
from my_cli.soul.denwarenji import DenwaRenji
from my_cli.soul.runtime import BuiltinSystemPromptArgs, Runtime
from my_cli.soul.toolset import CustomToolset
from my_cli.tools import SkipThisTool
from my_cli.utils.logging import logger


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

    # 工具依赖注入映射（与官方保持一致）
    tool_deps: dict[type, Any] = {
        ResolvedAgentSpec: agent_spec,
        Runtime: runtime,
        Config: runtime.config,
        BuiltinSystemPromptArgs: runtime.builtin_args,
        Session: runtime.session,
        DenwaRenji: runtime.denwa_renji,
        Approval: runtime.approval,
    }

    # 处理工具列表
    tools = agent_spec.tools
    if agent_spec.exclude_tools:
        logger.debug("Excluding tools: {tools}", tools=agent_spec.exclude_tools)
        tools = [tool for tool in tools if tool not in agent_spec.exclude_tools]

    # 加载工具
    toolset = CustomToolset()
    bad_tools = _load_tools(toolset, tools, tool_deps)
    if bad_tools:
        raise ValueError(f"Invalid tools: {bad_tools}")

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


type ToolType = CallableTool | CallableTool2[Any]


def _load_tools(
    toolset: CustomToolset,
    tool_paths: list[str],
    dependencies: dict[type[Any], Any],
) -> list[str]:
    """
    加载工具到 Toolset ⭐ Stage 33 对齐官方

    对应源码：kimi-cli-fork/src/kimi_cli/soul/agent.py:100-119
    """
    bad_tools: list[str] = []
    for tool_path in tool_paths:
        try:
            tool = _load_tool(tool_path, dependencies)
        except SkipThisTool:
            logger.info("Skipping tool: {tool_path}", tool_path=tool_path)
            continue
        if tool:
            toolset += tool
        else:
            bad_tools.append(tool_path)
    logger.info("Loaded tools: {tools}", tools=[tool.name for tool in toolset.tools])
    if bad_tools:
        logger.error("Bad tools: {bad_tools}", bad_tools=bad_tools)
    return bad_tools


def _load_tool(tool_path: str, dependencies: dict[type[Any], Any]) -> ToolType | None:
    """
    加载单个工具（使用位置参数依赖注入）⭐ Stage 33 对齐官方

    对应源码：kimi-cli-fork/src/kimi_cli/soul/agent.py:122-141

    ⚠️ 关键：必须使用 inspect.signature(cls) 而不是 cls.__init__
    原因：在有 from __future__ import annotations 时，
          - signature(cls) 能正确获取类型对象
          - signature(cls.__init__) 会得到字符串形式的注解
    """
    logger.debug("Loading tool: {tool_path}", tool_path=tool_path)
    module_name, class_name = tool_path.rsplit(":", 1)
    try:
        module = importlib.import_module(module_name)
    except ImportError:
        return None
    cls = getattr(module, class_name, None)
    if cls is None:
        return None

    args: list[Any] = []
    for param in inspect.signature(cls).parameters.values():
        if param.kind == inspect.Parameter.KEYWORD_ONLY:
            # 遇到 keyword-only 参数时停止注入依赖
            break
        # 所有位置参数都应该是需要注入的依赖
        if param.annotation not in dependencies:
            raise ValueError(f"Tool dependency not found: {param.annotation}")
        args.append(dependencies[param.annotation])
    return cls(*args)


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

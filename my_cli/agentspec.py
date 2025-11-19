"""
AgentSpec - Agent 规范定义

学习目标：
1. 理解 AgentSpec 的作用（从文件加载 Agent 定义）
2. 理解 Agent 规范文件格式
3. 理解如何从 AgentSpec 创建 Agent

对应源码：kimi-cli-fork/src/kimi_cli/agentspec.py

阶段演进：
- Stage 4-16：使用硬编码的 Agent ✅
- Stage 18：实现 AgentSpec（从文件加载）⭐ 完整实现
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from my_cli.exception import AgentSpecError


def get_agents_dir() -> Path:
    """获取 Agent 配置目录

    Returns:
        Path: Agent 目录路径（当前目录/agents）

    对应源码：kimi-cli-fork/src/kimi_cli/agentspec.py:13-14
    """
    return Path(__file__).parent / "agents"


DEFAULT_AGENT_FILE = get_agents_dir() / "default" / "agent.yaml"
"""默认 Agent 配置文件"""


class AgentSpec(BaseModel):
    """Agent 规范定义 ⭐ Stage 18

    Attributes:
        extend: 要继承的 Agent 文件名（支持 "default" 关键字）
        name: Agent 名称
        system_prompt_path: 系统提示词文件路径
        system_prompt_args: 系统提示词参数（模板变量替换）
        tools: 工具列表
        exclude_tools: 要排除的工具列表
        subagents: 子 Agent 字典

    对应源码：kimi-cli-fork/src/kimi_cli/agentspec.py:20-33
    """

    extend: str | None = Field(default=None, description="Agent file to extend")
    name: str | None = Field(default=None, description="Agent name")
    system_prompt_path: Path | None = Field(
        default=None, description="System prompt path"
    )
    system_prompt_args: dict[str, str] = Field(
        default_factory=dict, description="System prompt arguments"
    )
    tools: list[str] | None = Field(default=None, description="Tools")
    exclude_tools: list[str] | None = Field(default=None, description="Tools to exclude")
    subagents: dict[str, SubagentSpec] | None = Field(default=None, description="Subagents")


class SubagentSpec(BaseModel):
    """子 Agent 规范定义 ⭐ Stage 18

    Attributes:
        path: 子 Agent 文件路径
        description: 子 Agent 描述

    对应源码：kimi-cli-fork/src/kimi_cli/agentspec.py:36-41
    """

    path: Path = Field(description="Subagent file path")
    description: str = Field(description="Subagent description")


@dataclass(frozen=True, slots=True, kw_only=True)
class ResolvedAgentSpec:
    """已解析的 Agent 规范 ⭐ Stage 18

    Attributes:
        name: Agent 名称（必填）
        system_prompt_path: 系统提示词文件路径（必填）
        system_prompt_args: 系统提示词参数
        tools: 工具列表（必填）
        exclude_tools: 要排除的工具列表
        subagents: 子 Agent 字典

    对应源码：kimi-cli-fork/src/kimi_cli/agentspec.py:43-52
    """

    name: str
    system_prompt_path: Path
    system_prompt_args: dict[str, str]
    tools: list[str]
    exclude_tools: list[str]
    subagents: dict[str, SubagentSpec]


def load_agent_spec(agent_file: Path) -> ResolvedAgentSpec:
    """
    从文件加载 Agent 规范 ⭐ Stage 18

    支持 YAML 格式的 Agent 配置文件，包含以下特性：
    - YAML 文件格式
    - 版本检查（当前只支持版本 1）
    - 继承支持（通过 extend 字段）
    - 路径自动解析（相对路径转为绝对路径）

    Args:
        agent_file: Agent 规范文件路径

    Returns:
        ResolvedAgentSpec: 已解析的 Agent 规范对象

    Raises:
        FileNotFoundError: Agent 规范文件不存在
        AgentSpecError: Agent 规范格式错误或缺少必需字段

    对应源码：kimi-cli-fork/src/kimi_cli/agentspec.py:55-78
    """
    agent_spec = _load_agent_spec(agent_file)
    assert agent_spec.extend is None, "agent extension should be recursively resolved"
    if agent_spec.name is None:
        raise AgentSpecError("Agent name is required")
    if agent_spec.system_prompt_path is None:
        raise AgentSpecError("System prompt path is required")
    if agent_spec.tools is None:
        raise AgentSpecError("Tools are required")
    return ResolvedAgentSpec(
        name=agent_spec.name,
        system_prompt_path=agent_spec.system_prompt_path,
        system_prompt_args=agent_spec.system_prompt_args,
        tools=agent_spec.tools,
        exclude_tools=agent_spec.exclude_tools or [],
        subagents=agent_spec.subagents or {},
    )


def _load_agent_spec(agent_file: Path) -> AgentSpec:
    """
    内部：加载并解析 Agent 规范文件

    Args:
        agent_file: Agent 规范文件路径

    Returns:
        AgentSpec: 解析后的 Agent 规范对象

    Raises:
        AgentSpecError: 文件不存在或格式错误

    对应源码：kimi-cli-fork/src/kimi_cli/agentspec.py:81-124
    """
    if not agent_file.exists():
        raise AgentSpecError(f"Agent spec file not found: {agent_file}")
    if not agent_file.is_file():
        raise AgentSpecError(f"Agent spec path is not a file: {agent_file}")
    try:
        with open(agent_file, encoding="utf-8") as f:
            data: dict[str, Any] = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise AgentSpecError(f"Invalid YAML in agent spec file: {e}") from e

    version = data.get("version", 1)
    if version != 1:
        raise AgentSpecError(f"Unsupported agent spec version: {version}")

    agent_spec = AgentSpec(**data.get("agent", {}))
    if agent_spec.system_prompt_path is not None:
        agent_spec.system_prompt_path = (
            agent_file.parent / agent_spec.system_prompt_path
        ).absolute()
    if agent_spec.subagents is not None:
        for v in agent_spec.subagents.values():
            v.path = (agent_file.parent / v.path).absolute()
    if agent_spec.extend:
        if agent_spec.extend == "default":
            base_agent_file = DEFAULT_AGENT_FILE
        else:
            base_agent_file = (agent_file.parent / agent_spec.extend).absolute()
        base_agent_spec = _load_agent_spec(base_agent_file)
        if agent_spec.name is not None:
            base_agent_spec.name = agent_spec.name
        if agent_spec.system_prompt_path is not None:
            base_agent_spec.system_prompt_path = agent_spec.system_prompt_path
        for k, v in agent_spec.system_prompt_args.items():
            # system prompt args should be merged instead of overwritten
            base_agent_spec.system_prompt_args[k] = v
        if agent_spec.tools is not None:
            base_agent_spec.tools = agent_spec.tools
        if agent_spec.exclude_tools is not None:
            base_agent_spec.exclude_tools = agent_spec.exclude_tools
        if agent_spec.subagents is not None:
            base_agent_spec.subagents = agent_spec.subagents
        agent_spec = base_agent_spec
    return agent_spec

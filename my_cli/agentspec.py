"""
AgentSpec - Agent 规范定义

学习目标：
1. 理解 AgentSpec 的作用（从文件加载 Agent 定义）
2. 理解 Agent 规范文件格式
3. 理解如何从 AgentSpec 创建 Agent

对应源码：kimi-cli-fork/src/kimi_cli/agentspec.py

阶段演进：
- Stage 4-16：使用硬编码的 Agent ✅
- Stage 18：实现 AgentSpec（从文件加载）⭐ TODO
"""

from __future__ import annotations

from pathlib import Path

# ============================================================
# TODO: Stage 18+ 完整实现（参考官方）
# ============================================================
# 官方参考：kimi-cli-fork/src/kimi_cli/agentspec.py
#
# Stage 18（AgentSpec）需要：
# 1. 定义 AgentSpec 数据类
# 2. 实现 load_agent_spec() 函数（从文件加载）
# 3. 实现 create_agent_from_spec() 函数
#
# AgentSpec 格式（YAML/JSON）：
# name: "Kimi CLI Assistant"
# description: "A helpful AI assistant"
# system_prompt: |
#   You are a helpful AI assistant.
#   You can use tools to help the user.
# tools:
#   - name: "bash"
#   - name: "read_file"
#   - name: "write_file"
#
# load_agent_spec() 伪代码：
# def load_agent_spec(file_path: Path) -> AgentSpec:
#     with open(file_path) as f:
#         data = yaml.safe_load(f)
#     return AgentSpec(**data)
#
# Stage 4-16 简化版：
# - 使用硬编码的 Agent
# - system_prompt 定义在 Agent 类中
# ============================================================


def load_agent_spec(file_path: Path):
    """
    从文件加载 Agent 规范 ⭐ Stage 18

    Args:
        file_path: Agent 规范文件路径

    Returns:
        AgentSpec: Agent 规范

    对应源码：kimi-cli-fork/src/kimi_cli/agentspec.py
    """
    # TODO: Stage 18 实现
    raise NotImplementedError("AgentSpec not implemented in Stage 4-16")

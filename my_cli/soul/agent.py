"""
阶段 4-5：Agent 类

学习目标：
1. 理解 Agent 的职责（定义 Agent 的身份和能力）
2. 理解 system_prompt 的作用

对应源码：kimi-cli-main/src/kimi_cli/soul/agent.py
"""

from pathlib import Path


class Agent:
    """
    Agent - 定义 AI Agent 的身份和能力

    职责：
    - 定义 Agent 的名称
    - 定义 system_prompt（系统提示词）
    - 管理工具集（Stage 7 实现）

    对应源码：kimi-cli-main/src/kimi_cli/soul/agent.py
    """

    def __init__(
        self,
        name: str,
        work_dir: Path,
        system_prompt: str | None = None,
    ):
        self.name = name
        self.work_dir = work_dir
        self._system_prompt = system_prompt or self._build_default_system_prompt()

    def _build_default_system_prompt(self) -> str:
        """
        构建默认的系统提示词

        Stage 4-5 实现：
        - 简洁的提示词（避免超出 token 限制）
        - 说明当前能力范围

        Stage 7+ 补充：
        - 添加工具使用说明
        - 添加工作目录相关指令
        """
        return f"""你是 {self.name}，一个 AI 助手。

请简洁地回答用户问题。"""

    @property
    def system_prompt(self) -> str:
        """获取系统提示词"""
        return self._system_prompt

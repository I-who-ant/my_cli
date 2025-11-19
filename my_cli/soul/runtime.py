"""
Runtime - 运行时配置和管理

学习目标：
1. 理解 Runtime 的职责（管理运行时配置）
2. 理解异步工厂方法 Runtime.create()
3. 理解内置参数和 Approval 系统

对应源码：kimi-cli-fork/src/kimi_cli/soul/runtime.py

阶段演进：
- Stage 4-16：使用 ChatProvider ✅
- Stage 17：使用 LLM（封装 ChatProvider + max_context_size + capabilities）✅
- Stage 18：完整 Runtime.create() 实现 ⭐
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from my_cli.config import Config
from my_cli.llm import LLM
from my_cli.session import Session
from my_cli.soul.approval import Approval
from my_cli.utils.logging import logger
from my_cli.utils.path import list_directory


@dataclass(frozen=True, slots=True, kw_only=True)
class BuiltinSystemPromptArgs:
    """内置系统提示词参数 ⭐ Stage 19.2: 改为 MY_CLI_ 前缀

    Attributes:
        MY_CLI_NOW: 当前日期时间
        MY_CLI_WORK_DIR: 当前工作目录
        MY_CLI_WORK_DIR_LS: 当前工作目录列表
        MY_CLI_AGENTS_MD: AGENTS.md 文件内容

    对应源码：kimi-cli-fork/src/kimi_cli/soul/runtime.py:18-28
    """

    MY_CLI_NOW: str
    """当前日期时间"""

    MY_CLI_WORK_DIR: Path
    """当前工作目录"""

    MY_CLI_WORK_DIR_LS: str
    """当前工作目录列表"""

    MY_CLI_AGENTS_MD: str
    """AGENTS.md 文件内容"""


def load_agents_md(work_dir: Path) -> str | None:
    """加载工作目录中的 AGENTS.md 文件

    Args:
        work_dir: 工作目录路径

    Returns:
        str | None: AGENTS.md 内容，如果不存在返回 None

    对应源码：kimi-cli-fork/src/kimi_cli/soul/runtime.py:31-41
    """
    paths = [
        work_dir / "AGENTS.md",
        work_dir / "agents.md",
    ]
    for path in paths:
        if path.is_file():
            logger.info("Loaded agents.md: {path}", path=path)
            return path.read_text(encoding="utf-8").strip()
    logger.info("No AGENTS.md found in {work_dir}", work_dir=work_dir)
    return None


@dataclass(frozen=True, slots=True, kw_only=True)
class Runtime:
    """运行时配置和管理 ⭐ Stage 18 完整实现

    职责：
    - 管理配置（Config）
    - 管理 LLM 实例
    - 管理 Session
    - 提供内置参数（BuiltinSystemPromptArgs）
    - 管理电话助理（DenwaRenji）
    - 管理批准系统（Approval）

    对应源码：kimi-cli-fork/src/kimi_cli/soul/runtime.py:44-79
    """

    config: Config
    """配置对象"""

    llm: LLM | None
    """LLM 实例（可能为 None）"""

    session: Session
    """会话对象"""

    builtin_args: BuiltinSystemPromptArgs
    """内置系统提示词参数"""

    denwa_renji: object
    """电话助理（DenwaRenji）"""

    approval: Approval
    """批准系统"""

    @staticmethod
    async def create(
        config: Config,
        llm: LLM | None,
        session: Session,
        yolo: bool,
    ) -> Runtime:
        """
        异步工厂方法 - 创建 Runtime 实例 ⭐ Stage 18 完整实现

        这个工厂方法负责：
        1. 异步加载目录列表（list_directory）
        2. 异步加载 AGENTS.md 文件
        3. 创建内置参数
        4. 创建 DenwaRenji（电话助理）
        5. 创建 Approval（批准系统）
        6. 组装并返回 Runtime 对象

        Args:
            config: 配置对象
            llm: LLM 实例（可能为 None）
            session: Session 实例
            yolo: 是否自动批准所有操作

        Returns:
            Runtime: 运行时实例

        对应源码：kimi-cli-fork/src/kimi_cli/soul/runtime.py:55-79
        """
        # 并行加载目录列表和 AGENTS.md
        ls_output, agents_md = await asyncio.gather(
            asyncio.to_thread(list_directory, session.work_dir),
            asyncio.to_thread(load_agents_md, session.work_dir),
        )

        # 导入 DenwaRenji（延迟导入避免循环依赖）
        from my_cli.soul.denwarenji import DenwaRenji

        # 组装 Runtime ⭐ Stage 19.2: 使用 MY_CLI_ 前缀
        return Runtime(
            config=config,
            llm=llm,
            session=session,
            builtin_args=BuiltinSystemPromptArgs(
                MY_CLI_NOW=datetime.now().astimezone().isoformat(),
                MY_CLI_WORK_DIR=session.work_dir,
                MY_CLI_WORK_DIR_LS=ls_output,
                MY_CLI_AGENTS_MD=agents_md or "",
            ),
            denwa_renji=DenwaRenji(),
            approval=Approval(yolo=yolo),
        )


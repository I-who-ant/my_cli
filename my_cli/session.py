"""
Session - 会话管理

学习目标：
1. 理解 Session 的作用（管理会话历史）
2. 理解会话 ID 生成
3. 理解历史文件路径管理

对应源码：kimi-cli-fork/src/kimi_cli/session.py

阶段演进：
- Stage 4-16：不持久化（简化版）
- Stage 18：实现 Session 管理 ⭐ 完整实现

官方实现要点：
- 使用 @dataclass(frozen=True, slots=True, kw_only=True)
- Session.create() - 创建新会话
- Session.continue_() - 继续上次会话
- 使用 uuid.uuid4() 生成会话 ID
- 依赖 metadata 系统管理 work_dirs
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from pathlib import Path

from my_cli.metadata import WorkDirMeta, load_metadata, save_metadata
from my_cli.utils.logging import logger


@dataclass(frozen=True, slots=True, kw_only=True)
class Session:
    """会话 - 工作目录的会话管理

    Attributes:
        id: 会话 ID（UUID 格式）
        work_dir: 工作目录路径
        history_file: 历史文件路径

    对应源码：kimi-cli-fork/src/kimi_cli/session.py:11-56
    """

    id: str
    """会话 ID"""

    work_dir: Path
    """工作目录"""

    history_file: Path
    """历史文件路径"""

    @staticmethod
    def create(work_dir: Path, _history_file: Path | None = None) -> Session:
        """为工作目录创建新会话

        Args:
            work_dir: 工作目录路径
            _history_file: 可选的历史文件路径（用于测试）

        Returns:
            Session: 新创建的会话对象

        对应源码：kimi-cli-fork/src/kimi_cli/session.py:19-56

        流程：
        1. 加载 metadata
        2. 查找或创建 work_dir_meta
        3. 生成 UUID 格式的会话 ID
        4. 构建历史文件路径
        5. 创建或清空历史文件
        6. 保存 metadata
        7. 返回 Session 对象
        """
        logger.debug("Creating new session for work directory: {work_dir}", work_dir=work_dir)

        # 1. 加载 metadata
        metadata = load_metadata()

        # 2. 查找或创建 work_dir_meta
        work_dir_meta = next(
            (wd for wd in metadata.work_dirs if wd.path == str(work_dir)), None
        )
        if work_dir_meta is None:
            work_dir_meta = WorkDirMeta(path=str(work_dir))
            metadata.work_dirs.append(work_dir_meta)

        # 3. 生成会话 ID（使用 UUID）
        session_id = str(uuid.uuid4())

        # 4. 构建历史文件路径
        if _history_file is None:
            # 使用标准路径：~/.kimi/sessions/<md5_hash>/<session_id>.jsonl
            history_file = work_dir_meta.sessions_dir / f"{session_id}.jsonl"
        else:
            # 使用提供的路径（用于测试）
            logger.warning(
                "Using provided history file: {history_file}", history_file=_history_file
            )
            _history_file.parent.mkdir(parents=True, exist_ok=True)
            if _history_file.exists():
                assert _history_file.is_file()
            history_file = _history_file

        # 5. 创建或清空历史文件
        if history_file.exists():
            # 如果文件已存在，截断它
            logger.warning(
                "History file already exists, truncating: {history_file}",
                history_file=history_file,
            )
            history_file.unlink()
            history_file.touch()

        # 6. 保存 metadata
        save_metadata(metadata)

        # 7. 返回 Session 对象
        return Session(
            id=session_id,
            work_dir=work_dir,
            history_file=history_file,
        )

    @staticmethod
    def continue_(work_dir: Path) -> Session | None:
        """获取工作目录的上次会话

        Args:
            work_dir: 工作目录路径

        Returns:
            Session | None: 如果找到上次会话则返回，否则返回 None

        对应源码：kimi-cli-fork/src/kimi_cli/session.py:58-83

        流程：
        1. 加载 metadata
        2. 查找 work_dir_meta
        3. 检查是否有 last_session_id
        4. 构建历史文件路径
        5. 返回 Session 对象
        """
        logger.debug("Continuing session for work directory: {work_dir}", work_dir=work_dir)

        # 1. 加载 metadata
        metadata = load_metadata()

        # 2. 查找 work_dir_meta
        work_dir_meta = next(
            (wd for wd in metadata.work_dirs if wd.path == str(work_dir)), None
        )
        if work_dir_meta is None:
            logger.debug("Work directory never been used")
            return None

        # 3. 检查是否有 last_session_id
        if work_dir_meta.last_session_id is None:
            logger.debug("Work directory never had a session")
            return None

        # 4. 记录找到的会话 ID
        logger.debug(
            "Found last session for work directory: {session_id}",
            session_id=work_dir_meta.last_session_id,
        )

        session_id = work_dir_meta.last_session_id
        history_file = work_dir_meta.sessions_dir / f"{session_id}.jsonl"

        # 5. 返回 Session 对象
        return Session(
            id=session_id,
            work_dir=work_dir,
            history_file=history_file,
        )

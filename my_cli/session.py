"""
Session 管理 - 会话历史持久化

学习目标：
1. 理解 Session 的作用（管理会话历史）
2. 理解会话 ID 生成
3. 理解历史文件路径管理

对应源码：kimi-cli-fork/src/kimi_cli/session.py

阶段演进：
- Stage 4-16：不持久化（简化版）✅
- Stage 18：实现 Session 管理 ⭐ TODO
"""

from __future__ import annotations

from pathlib import Path

# ============================================================
# TODO: Stage 18+ 完整实现（参考官方）
# ============================================================
# 官方参考：kimi-cli-fork/src/kimi_cli/session.py
#
# Stage 18（Session 管理）需要：
# 1. 实现 Session 类
# 2. 实现会话 ID 生成（时间戳 + 随机数）
# 3. 实现历史文件路径管理
# 4. 实现 create() 和 continue_() 方法
#
# Session 类伪代码：
# class Session:
#     def __init__(self, work_dir: Path, session_id: str):
#         self.work_dir = work_dir
#         self.id = session_id
#         self.history_file = work_dir / ".kimi_history" / f"{session_id}.jsonl"
#
#     @classmethod
#     def create(cls, work_dir: Path) -> Session:
#         """创建新会话"""
#         session_id = generate_session_id()
#         return cls(work_dir, session_id)
#
#     @classmethod
#     def continue_(cls, work_dir: Path) -> Session | None:
#         """继续上次会话"""
#         # 查找最近的会话文件
#         ...
#
# Stage 4-16 简化版：
# - 不持久化历史
# - Context 只存在内存中
# ============================================================


class Session:
    """
    Session - 会话管理 ⭐ Stage 18

    官方实现要点：
    - 管理会话 ID
    - 管理历史文件路径
    - 提供 create() 和 continue_() 工厂方法

    对应源码：kimi-cli-fork/src/kimi_cli/session.py
    """

    def __init__(self, work_dir: Path, session_id: str):
        self.work_dir = work_dir
        self.id = session_id
        # TODO: Stage 18 实现 history_file

    @classmethod
    def create(cls, work_dir: Path):
        """创建新会话 ⭐ Stage 18"""
        # TODO: Stage 18 实现
        raise NotImplementedError("Session not implemented in Stage 4-16")

    @classmethod
    def continue_(cls, work_dir: Path):
        """继续上次会话 ⭐ Stage 18"""
        # TODO: Stage 18 实现
        raise NotImplementedError("Session not implemented in Stage 4-16")

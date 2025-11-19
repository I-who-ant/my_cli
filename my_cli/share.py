"""
Share - 分享功能

学习目标：
1. 理解如何分享会话历史
2. 理解隐私保护（脱敏）
3. 理解共享目录管理

对应源码：kimi-cli-fork/src/kimi_cli/share.py

阶段演进：
- Stage 4-16：不需要 ✅
- Stage 18：共享目录管理 ⭐ 完整实现
- Stage 21：实现分享功能 ⭐ TODO
"""

from __future__ import annotations

from pathlib import Path


def get_share_dir() -> Path:
    """获取共享目录路径

    Returns:
        Path: 共享目录路径 (~/.mc)

    对应源码：kimi-cli-fork/src/kimi_cli/share.py:6-10

    Stage 18 实现：
    - 用于会话管理和元数据存储
    - 所有会话相关文件都存储在 ~/.mc 目录下

    Stage 19.2：⭐ 修改为 .mc 目录
    """
    share_dir = Path.home() / ".mc"
    share_dir.mkdir(parents=True, exist_ok=True)
    return share_dir


# ============================================================
# TODO: Stage 21+ 完整实现（参考官方）
# ============================================================
# 官方参考：kimi-cli-fork/src/kimi_cli/share.py
#
# Stage 21（分享功能）需要：
# 1. 实现历史脱敏（移除敏感信息）
# 2. 实现分享链接生成
# 3. 实现分享内容上传
#
# 分享功能伪代码：
# async def share_session(session: Session) -> str:
#     """
#     分享会话历史
#
#     Returns:
#         str: 分享链接
#     """
#     # 1. 读取历史
#     history = await session.load_history()
#
#     # 2. 脱敏
#     sanitized = sanitize_history(history)
#
#     # 3. 上传
#     share_url = await upload_share(sanitized)
#
#     return share_url
#
# def sanitize_history(history):
#     """移除敏感信息（API Key、路径等）"""
#     ...
# ============================================================


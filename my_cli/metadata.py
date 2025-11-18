"""
Metadata - 元数据管理

学习目标：
1. 理解元数据的���用（版本、构建信息等）
2. 理解如何在运行时获取元数据

对应源码：kimi-cli-fork/src/kimi_cli/metadata.py

阶段演进：
- Stage 4-16：硬编码版本信息 ✅
- Stage 18：从 package metadata 读取 ⭐ TODO
"""

from __future__ import annotations

# ============================================================
# 简化版（Stage 4-16）：硬编码
# ============================================================

VERSION = "0.1.0"
"""版本号"""

BUILD_COMMIT = "unknown"
"""构建 commit"""

BUILD_TIME = "unknown"
"""构建时间"""


# ============================================================
# TODO: Stage 18+ 完整实现（参考官方）
# ============================================================
# 官方参考：kimi-cli-fork/src/kimi_cli/metadata.py
#
# Stage 18（元数据管理）需要：
# 1. 从 importlib.metadata 读取版本
# 2. 从环境变量读取构建信息
#
# 官方实现：
# try:
#     from importlib.metadata import version
#     VERSION = version("kimi_cli")
# except Exception:
#     VERSION = "unknown"
#
# import os
# BUILD_COMMIT = os.getenv("BUILD_COMMIT", "unknown")
# BUILD_TIME = os.getenv("BUILD_TIME", "unknown")
# ============================================================



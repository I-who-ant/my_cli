"""
常量定义 ⭐ Stage 33.6

对应源码：kimi-cli-fork/src/kimi_cli/constant.py

阶段演进：
- Stage 17+: 基础常量（硬编码）✅
- Stage 33.6: 对齐官方（动态生成）⭐
"""

from __future__ import annotations

import importlib.metadata

# 版本信息（动态从包元数据获取）
VERSION = importlib.metadata.version("my-cli")

# User-Agent（动态生成，匹配版本）
USER_AGENT = f"MyCLI/{VERSION}"

# 默认配置文件名
DEFAULT_CONFIG_FILE = ".mycli_config.json"

# 默认工作目录
DEFAULT_WORK_DIR = "."

# ============================================================
# TODO: Stage 33.6+ 更多官方常量（对齐官方）
# ============================================================
# 官方参考：kimi-cli-fork/src/kimi_cli/constant.py
#
# 需要对齐的常量：
# - DEFAULT_AGENT_FILE: 默认 Agent 规范文件路径
# - MAX_CONTEXT_SIZE: 默认最大 Context 大小
# - MAX_STEPS: 默认最大步数
# - etc.
# ============================================================

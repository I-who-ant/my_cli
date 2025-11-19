"""
Context - 对话上下文管理

学习目标：
1. 理解 Context 的职责（管理对话历史、检查点）
2. 理解 kosong.Message 的使用
3. 理解文件后端（JSONL 格式）和文件旋转

对应源码：kimi-cli-fork/src/kimi_cli/soul/context.py

阶段演进：
- Stage 4-16：基础 Context（内存存储）✅
- Stage 18：文件后端 + 检查点支持 ⭐ 完整实现
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path

import aiofiles
import aiofiles.os
from kosong.message import Message

from my_cli.soul.message import system
from my_cli.utils.logging import logger
from my_cli.utils.path import next_available_rotation


class Context:
    """
    Context - 对话上下文管理 ⭐ Stage 18 完整实现

    职责：
    - 管理消息历史（文件后端持久化）
    - 提供格式化的消息列表
    - 支持检查点（checkpoint）和回滚（revert）
    - 追踪 token 使用量
    - 文件旋转（rotation）支持

    对应源码：kimi-cli-fork/src/kimi_cli/soul/context.py:16-22
    """

    def __init__(self, file_backend: Path):
        self._file_backend = file_backend
        self._history: list[Message] = []
        self._token_count: int = 0
        self._next_checkpoint_id: int = 0
        """下一个检查点 ID，从 0 开始，每次检查点后递增"""

    async def restore(self) -> bool:
        """
        从文件后端恢复上下文 ⭐ Stage 18

        从历史文件加载消息历史、token 计数和检查点信息。
        支持特殊角色标记：
        - `_usage`: token 计数记录
        - `_checkpoint`: 检查点记录

        Returns:
            bool: 成功恢复返回 True，无需恢复（文件不存在或为空）返回 False

        Raises:
            RuntimeError: Context 存储已被修改

        对应源码：kimi-cli-fork/src/kimi_cli/soul/context.py:24-50
        """
        logger.debug("Restoring context from file: {file_backend}", file_backend=self._file_backend)
        if self._history:
            logger.error("The context storage is already modified")
            raise RuntimeError("The context storage is already modified")
        if not self._file_backend.exists():
            logger.debug("No context file found, skipping restoration")
            return False
        if self._file_backend.stat().st_size == 0:
            logger.debug("Empty context file, skipping restoration")
            return False

        async with aiofiles.open(self._file_backend, encoding="utf-8") as f:
            async for line in f:
                if not line.strip():
                    continue
                line_json = json.loads(line)
                if line_json["role"] == "_usage":
                    self._token_count = line_json["token_count"]
                    continue
                if line_json["role"] == "_checkpoint":
                    self._next_checkpoint_id = line_json["id"] + 1
                    continue
                message = Message.model_validate(line_json)
                self._history.append(message)

        return True

    @property
    def history(self) -> Sequence[Message]:
        """
        获取消息历史序列

        Returns:
            Sequence[Message]: 只读的消息历史序列

        对应源码：kimi-cli-fork/src/kimi_cli/soul/context.py:52-54
        """
        return self._history

    @property
    def token_count(self) -> int:
        """
        获取当前 token 数量

        Returns:
            int: token 数量

        对应源码：kimi-cli-fork/src/kimi_cli/soul/context.py:56-58
        """
        return self._token_count

    @property
    def n_checkpoints(self) -> int:
        """
        获取检查点数量

        Returns:
            int: 检查点总数（下一个可用的检查点 ID）

        对应源码：kimi-cli-fork/src/kimi_cli/soul/context.py:60-62
        """
        return self._next_checkpoint_id

    async def checkpoint(self, add_user_message: bool):
        """
        创建检查点 ⭐ Stage 18 核心功能

        检查点用于时间旅行功能，可以将对话状态回滚到之前的某个检查点。
        检查点信息以特殊角色 `_checkpoint` 写入文件后端。

        Args:
            add_user_message: 是否添加用户消息（显示检查点 ID）

        对应源码：kimi-cli-fork/src/kimi_cli/soul/context.py:64-74
        """
        checkpoint_id = self._next_checkpoint_id
        self._next_checkpoint_id += 1
        logger.debug("Checkpointing, ID: {id}", id=checkpoint_id)

        async with aiofiles.open(self._file_backend, "a", encoding="utf-8") as f:
            await f.write(json.dumps({"role": "_checkpoint", "id": checkpoint_id}) + "\n")
        if add_user_message:
            await self.append_message(
                Message(role="user", content=[system(f"CHECKPOINT {checkpoint_id}")])
            )

    async def revert_to(self, checkpoint_id: int):
        """
        回滚到指定检查点 ⭐ Stage 18 核心功能

        将对话状态回滚到指定的检查点。回滚过程：
        1. 旋转历史文件（原文件重命名为 backup）
        2. 从备份文件中读取内容，直到目标检查点
        3. 将内容写入新的历史文件
        4. 清空内存中的历史，设置为回滚后的状态

        Args:
            checkpoint_id: 要回滚到的检查点 ID（0 是第一个检查点）

        Raises:
            ValueError: 检查点不存在
            RuntimeError: 没有可用的旋转路径

        对应源码：kimi-cli-fork/src/kimi_cli/soul/context.py:76-128
        """
        logger.debug("Reverting checkpoint, ID: {id}", id=checkpoint_id)
        if checkpoint_id >= self._next_checkpoint_id:
            logger.error("Checkpoint {checkpoint_id} does not exist", checkpoint_id=checkpoint_id)
            raise ValueError(f"Checkpoint {checkpoint_id} does not exist")

        # 旋转历史文件
        rotated_file_path = await next_available_rotation(self._file_backend)
        if rotated_file_path is None:
            logger.error("No available rotation path found")
            raise RuntimeError("No available rotation path found")
        await aiofiles.os.replace(self._file_backend, rotated_file_path)
        logger.debug(
            "Rotated history file: {rotated_file_path}", rotated_file_path=rotated_file_path
        )

        # 恢复上下文直到指定的检查点
        self._history.clear()
        self._token_count = 0
        self._next_checkpoint_id = 0
        async with (
            aiofiles.open(rotated_file_path, encoding="utf-8") as old_file,
            aiofiles.open(self._file_backend, "w", encoding="utf-8") as new_file,
        ):
            async for line in old_file:
                if not line.strip():
                    continue

                line_json = json.loads(line)
                if line_json["role"] == "_checkpoint" and line_json["id"] == checkpoint_id:
                    break

                await new_file.write(line)
                if line_json["role"] == "_usage":
                    self._token_count = line_json["token_count"]
                elif line_json["role"] == "_checkpoint":
                    self._next_checkpoint_id = line_json["id"] + 1
                else:
                    message = Message.model_validate(line_json)
                    self._history.append(message)

    async def append_message(self, message: Message | Sequence[Message]):
        """
        添加消息到上下文 ⭐ Stage 18 文件持久化

        将消息追加到内存历史并写入文件后端。
        支持批量添加消息。

        Args:
            message: 要添加的消息或消息序列

        对应源码：kimi-cli-fork/src/kimi_cli/soul/context.py:130-137
        """
        logger.debug("Appending message(s) to context: {message}", message=message)
        messages = message if isinstance(message, Sequence) else [message]
        self._history.extend(messages)

        async with aiofiles.open(self._file_backend, "a", encoding="utf-8") as f:
            for message in messages:
                await f.write(message.model_dump_json(exclude_none=True) + "\n")

    async def update_token_count(self, token_count: int):
        """
        更新 token 计数 ⭐ Stage 18 文件持久化

        将 token 计数写入文件后端，使用特殊角色 `_usage`。

        Args:
            token_count: 新的 token 计数

        对应源码：kimi-cli-fork/src/kimi_cli/soul/context.py:139-144
        """
        logger.debug("Updating token count in context: {token_count}", token_count=token_count)
        self._token_count = token_count

        async with aiofiles.open(self._file_backend, "a", encoding="utf-8") as f:
            await f.write(json.dumps({"role": "_usage", "token_count": token_count}) + "\n")

    # ============================================================
    # Stage 4-16 兼容性方法（简化版接口）
    # ============================================================

    def get_messages(self) -> list[Message]:
        """
        获取所有消息（兼容 Stage 4-16）

        Returns:
            list[Message]: 消息列表副本

        Note: Stage 18+ 推荐使用 history 属性（只读序列）
        """
        return list(self._history)

    def clear(self) -> None:
        """
        清空上下文（兼容 Stage 4-16）

        Note: Stage 18+ 建议使用 checkpoint/revert 进行状态管理
        """
        self._history.clear()
        self._token_count = 0
        self._next_checkpoint_id = 0

    def __len__(self) -> int:
        """返回消息数量"""
        return len(self._history)


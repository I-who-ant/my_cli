"""
阶段 4-8：KimiSoul 类 - Soul Protocol 的具体实现 + Wire 集成 + 工具调用

学习目标：
1. 理解如何实现 Soul Protocol
2. 理解如何使用 kosong.step() 调用 LLM（支持工具调用）⭐ Stage 8
3. 理解流式响应的处理
4. 理解 Wire 机制和 on_message_part 回调
5. 理解 Agent 循环（多轮工具调用）⭐ Stage 8

对应源码：kimi-cli-fork/src/kimi_cli/soul/kimisoul.py
"""

from __future__ import annotations

import asyncio
from collections.abc import Sequence
from functools import partial
from typing import TYPE_CHECKING

import kosong
import tenacity
from kosong.chat_provider import (
    APIConnectionError,
    APIEmptyResponseError,
    APIStatusError,
    APITimeoutError,
    ThinkingEffort,
)
from kosong.message import Message, TextPart
from kosong.tooling import Toolset
from tenacity import RetryCallState, retry_if_exception, stop_after_attempt, wait_exponential_jitter

from my_cli.soul.agent import Agent
from my_cli.soul.compaction import SimpleCompaction
from my_cli.soul.context import Context
from my_cli.soul.message import check_message, system, tool_result_to_message
from my_cli.soul.runtime import Runtime
from my_cli.utils.logging import logger
from my_cli.wire.message import StepBegin
from my_cli.soul import LLMNotSet, LLMNotSupported
from my_cli.tools.dmail import NAME as SendDMail_NAME  # ⭐ Stage 20

if TYPE_CHECKING:
    from my_cli.soul import wire_send, StatusSnapshot  # 避免循环导入，仅用于类型提示


# 保留的 token 数量（用于压缩阈值计算）
RESERVED_TOKENS = 50_000


class BackToTheFuture(Exception):
    """时间旅行异常 ⭐ Stage 19

    当 D-Mail 被发送时抛出，触发 Context 回滚到指定检查点。
    主 Agent 循环会捕获此异常并处理回滚逻辑。

    Attributes:
        checkpoint_id: 目标检查点 ID
        messages: 要添加到目标检查点的消息列表

    对应源码：kimi-cli-fork/src/kimi_cli/soul/kimisoul.py（在文件内定义）
    """

    def __init__(self, checkpoint_id: int, messages: Sequence[Message]):
        self.checkpoint_id = checkpoint_id
        self.messages = messages


class KimiSoul:
    """
    KimiSoul - Soul Protocol 的具体实现

    这个类实现了 Soul Protocol 定义的接口：
    - name 属性
    - model_name 属性
    - run() 方法

    对应源码：kimi-cli-main/src/kimi_cli/soul/kimisoul.py:48-150
    """

    def __init__(
        self,
        agent: Agent,
        runtime: Runtime,
        *,
        context: Context,
    ):
        """
        初始化 KimiSoul ⭐ Stage 18 修复为官方签名

        Args:
            agent: Agent 实例（定义身份和能力）
            runtime: Runtime 实例（管理 LLM、配置等）
            context: Context 实例（管理对话历史）⭐ 必需的关键字参数

        对应源码：kimi-cli-fork/src/kimi_cli/soul/kimisoul.py:60-74
        """
        self._agent = agent
        self._runtime = runtime
        self._context = context

        # 从 runtime 获取其他组件
        self._denwa_renji = runtime.denwa_renji
        self._approval = runtime.approval
        self._loop_control = runtime.config.loop_control
        self._compaction = SimpleCompaction()  # ⭐ Stage 19: 压缩策略
        self._reserved_tokens = RESERVED_TOKENS

        # 检查 LLM 是否超过保留 token 限制
        if self._runtime.llm is not None:
            assert self._reserved_tokens <= self._runtime.llm.max_context_size

        # 初始化 thinking 模式
        self._thinking_effort: ThinkingEffort = "off"  # ⭐ Stage 18：初始化 thinking 模式

        # ⭐ Stage 20：检查是否有 SendDMail 工具，决定 checkpoint 策略
        self._checkpoint_with_user_message = False
        for tool in agent.toolset.tools:
            if tool.name == SendDMail_NAME:
                self._checkpoint_with_user_message = True
                break

    @property
    def name(self) -> str:
        """实现 Soul Protocol: name 属性"""
        return self._agent.name

    @property
    def model_name(self) -> str:
        """实现 Soul Protocol: model_name 属性"""
        # ⭐ Stage 19.2: 处理 llm 为 None 的情况
        return self._runtime.llm.model_name if self._runtime.llm else ""

    @property
    def runtime(self) -> Runtime:
        """实现 Soul Protocol: runtime 属性 ⭐ Stage 19.1"""
        return self._runtime

    @property
    def thinking(self) -> bool:
        """实现 Soul Protocol: thinking 属性 ⭐ Stage 19.1"""
        return self._thinking_effort != "off"

    @property
    def model_capabilities(self) -> set[str] | None:
        """
        实现 Soul Protocol: model_capabilities 属性 ⭐ Stage 17 更新

        Returns:
            set[str] | None: 能力集合，None 表示未配置 LLM

        官方实现：
        - 从 self._runtime.llm.capabilities 获取
        - LLM 类根据模型配置返回能力集合

        对应源码：kimi-cli-fork/src/kimi_cli/soul/kimisoul.py:102-106
        """
        # ⭐ Stage 19.2: 处理 llm 为 None 的情况
        if self._runtime.llm is None:
            return None
        return self._runtime.llm.capabilities

    @property
    def status(self) -> "StatusSnapshot":
        """
        实现 Soul Protocol: status 属性 ⭐ Stage 16

        Returns:
            StatusSnapshot: 包含 context_usage 等状态信息

        官方实现：
        - return StatusSnapshot(context_usage=self._context_usage)
        - _context_usage 使用 token_count / max_context_size 计算

        简化版实现：
        - 同官方实现，但 token_count 初始为 0
        - 通过 Context.update_token_count() 手动更新

        对应源码：kimi-cli-fork/src/kimi_cli/soul/kimisoul.py:108-110
        """
        from my_cli.soul import StatusSnapshot

        return StatusSnapshot(context_usage=self._context_usage)

    @property
    def _context_usage(self) -> float:
        """
        计算 Context 使用率 ⭐ Stage 16

        Returns:
            float: 使用率（0.0 ~ 1.0）

        官方实现：
        - if self._runtime.llm is not None:
        -     return self._context.token_count / self._runtime.llm.max_context_size
        - return 0.0

        简化版实现：
        - 使用固定的 max_context_size = 32000
        - token_count 从 Context 获取
        - 如果没有 token_count，估算为 message_count * 500

        对应源码：kimi-cli-fork/src/kimi_cli/soul/kimisoul.py:116-120
        """
        # 简化版：使用固定 max_context_size
        max_context_size = 32000

        # 获取 token_count
        token_count = self._context.token_count

        # 如果 token_count 为 0，估算为 message_count * 500
        if token_count == 0:
            message_count = len(self._context.history)  # ⭐ Stage 19.1: 使用 history 属性
            token_count = message_count * 500

        # 计算使用率
        return min(token_count / max_context_size, 1.0)

    @property
    def message_count(self) -> int:
        """
        实现 Soul Protocol: message_count 属性 ⭐ Stage 16

        Returns:
            int: 当前对话轮次数（包括用户和助手消息）
        """
        return len(self._context.history)  # ⭐ Stage 19.1: 使用 history 属性

    def set_thinking(self, enabled: bool) -> None:
        """
        启用/禁用思考模式 ⭐ Stage 18

        Args:
            enabled: True 启用思考模式，False 禁用

        Raises:
            LLMNotSet: 当 LLM 未设置时
            LLMNotSupported: 当 LLM 不支持思考模式时

        对应源码：kimi-cli-fork/src/kimi_cli/soul/kimisoul.py:127-139
        """
        from my_cli.soul import LLMNotSet, LLMNotSupported

        if self._runtime.llm is None:
            raise LLMNotSet()
        if enabled and "thinking" not in self._runtime.llm.capabilities:
            raise LLMNotSupported(self._runtime.llm, ["thinking"])
        self._thinking_effort = "high" if enabled else "off"

    async def run(self, user_input: str) -> None:
        """
        实现 Soul Protocol: run() 方法 ⭐ Stage 16 按官方实现完善

        流程（官方模式）：
        1. 检查 LLM 是否配置（raise LLMNotSet）
        2. 检查消息能力（raise LLMNotSupported）- Stage 16 简化版跳过
        3. 添加用户消息到 Context
        4. 调用 _agent_loop() 进入 Agent 循环 ⭐ 官方模式

        官方实现：
        ```python
        if self._runtime.llm is None:
            raise LLMNotSet()

        user_message = Message(role="user", content=user_input)
        if missing_caps := check_message(user_message, self._runtime.llm.capabilities):
            raise LLMNotSupported(self._runtime.llm, list(missing_caps))

        await self._checkpoint()
        await self._context.append_message(user_message)
        await self._agent_loop()
        ```

        简化版实现：
        - 只检查 ChatProvider 是否存在
        - 跳过 capabilities 检查（简化）
        - 跳过 checkpoint（简化）
        - 调用 _agent_loop()

        Args:
            user_input: 用户输入

        Raises:
            LLMNotSet: 如果 LLM 未配置
            LLMNotSupported: 如果消息包含 LLM 不支持的能力 (简化版不抛出)
            MaxStepsReached: 如果达到最大步数限制

        对应源码：kimi-cli-fork/src/kimi_cli/soul/kimisoul.py:144-155
        """
        # ============================================================
        # Stage 16：官方模式检查 ⭐
        # ============================================================
        # 1. 检查 LLM 是否配置
        from my_cli.soul import LLMNotSet

        if not self._runtime.llm:  # ⭐ Stage 17：改为检查 llm
            raise LLMNotSet()

        # 2. 检查消息能力（简化版跳过）
        # 官方实现：
        # user_message = Message(role="user", content=user_input)
        # if missing_caps := check_message(user_message, self._runtime.llm.capabilities):
        #     raise LLMNotSupported(self._runtime.llm, list(missing_caps))

        # 3. 添加用户消息
        user_msg = Message(role="user", content=user_input)
        await self._context.append_message(user_msg)

        # 4. 调用 _agent_loop() ⭐ 官方模式
        await self._agent_loop()

    async def _agent_loop(self) -> None:
        """
        Agent 循环（主循环）⭐ Stage 20 完整实现（含 D-Mail 支持）

        官方实现要点：
        1. step_no 从 1 开始循环
        2. 每步发送 StepBegin 事件
        3. 每步创建 checkpoint 并更新 DenwaRenji
        4. 调用 _step() 执行一步 ⭐ 官方模式
        5. 捕获 BackToTheFuture 异常，处理时间回滚
        6. _step() 返回 should_stop（True 表示没有工具调用，应该停止）
        7. 如果 should_stop，return（完成）
        8. 如果达到最大步数，raise MaxStepsReached

        对应源码：kimi-cli-fork/src/kimi_cli/soul/kimisoul.py:157-205
        """
        from my_cli.soul import MaxStepsReached, wire_send

        MAX_STEPS = 20
        step_no = 1

        while True:
            # 发送步骤开始事件
            wire_send(StepBegin(n=step_no))

            try:
                # ⭐ Stage 20：每步创建 checkpoint（支持 D-Mail 回滚）
                await self._checkpoint()

                # 调用 _step() 执行一步 ⭐ 官方模式
                should_stop = await self._step()

            except BackToTheFuture as e:
                # ============================================================
                # Stage 20：处理时间回滚 ⭐
                # ============================================================
                # 回滚到目标 checkpoint
                await self._context.revert_to(e.checkpoint_id)

                # 创建新 checkpoint
                await self._checkpoint()

                # 添加 D-Mail 消息
                await self._context.append_message(e.messages)

                # 继续循环（不增加 step_no，相当于重新执行这一步）
                continue

            # 判断是否继续循环
            if should_stop:
                return  # 官方使用 return

            # 继续下一步
            step_no += 1

            # 检查是否达到最大步数
            if step_no > MAX_STEPS:
                raise MaxStepsReached(MAX_STEPS)

    async def _step(self) -> bool:
        """
        执行一个步骤 ⭐ Stage 17 完整实现

        官方实现要点：
        1. 使用 @tenacity.retry 装饰器包装 kosong.step() 调用（重试机制）⭐
        2. 调用 kosong.step() 获取 StepResult
        3. 如果有 usage，更新 token_count 并发送 StatusUpdate
        4. 等待工具执行完成
        5. 调用 _grow_context() 将结果添加到 Context
        6. 返回 should_stop（True = 没有工具调用）

        Returns:
            bool: should_stop（True 表示没有工具调用，应该停止循环）

        对应源码：kimi-cli-fork/src/kimi_cli/soul/kimisoul.py:208-277
        """
        from my_cli.soul import wire_send

        # ⭐ Stage 17：使用 @tenacity.retry 装饰器包装 kosong.step() 调用
        # 官方做法：创建内部函数并用 @tenacity.retry 装饰
        @tenacity.retry(
            retry=retry_if_exception(self._is_retryable_error),
            before_sleep=partial(self._retry_log, "step"),
            wait=wait_exponential_jitter(initial=0.3, max=5, jitter=0.5),
            stop=stop_after_attempt(3),  # 最多重试 3 次（官方使用 self._loop_control.max_retries_per_step）
            reraise=True,
        )
        async def _kosong_step_with_retry() -> "kosong.StepResult":
            # 调用 kosong.step()
            return await kosong.step(
                chat_provider=self._runtime.llm.chat_provider,  # ⭐ Stage 17：使用 llm.chat_provider
                system_prompt=self._agent.system_prompt,
                toolset=self._agent.toolset,  # ⭐ Stage 18：从 agent 获取 toolset
                history=self._context.get_messages(),
                on_message_part=wire_send,
                on_tool_result=wire_send,
            )

        # 执行 kosong.step()（带重试机制）
        result = await _kosong_step_with_retry()

        # ============================================================
        # Stage 16：更新 token_count 并发送 StatusUpdate ⭐
        # ============================================================
        if result.usage is not None:
            # 更新 token_count（使用 LLM API 返回的真实值）
            await self._context.update_token_count(result.usage.input)

            # 发送状态更新事件
            from my_cli.wire.message import StatusUpdate

            wire_send(StatusUpdate(status=self.status))

        # 等待所有工具执行完成
        tool_results = await result.tool_results()

        # 调用 _grow_context() 将结果添加到 Context ⭐ 官方模式
        await self._grow_context(result, tool_results)

        # ============================================================
        # Stage 20：D-Mail 检测和处理 ⭐
        # ============================================================
        # 检查是否有待处理的 D-Mail
        if dmail := self._denwa_renji.fetch_pending_dmail():
            # 验证 checkpoint_id 有效性（DenwaRenji 已经验证过，这里是双重保险）
            assert dmail.checkpoint_id >= 0, "DenwaRenji guarantees checkpoint_id >= 0"
            assert dmail.checkpoint_id < self._context.n_checkpoints, (
                "DenwaRenji guarantees checkpoint_id < n_checkpoints"
            )

            # 抛出 BackToTheFuture 异常，让主循环处理时间回滚
            raise BackToTheFuture(
                dmail.checkpoint_id,
                [Message(role="user", content=dmail.message)],
            )

        # 返回 should_stop
        # 如果 LLM 没有调用工具，说明任务完成
        return not result.tool_calls

    async def _grow_context(
        self, result: "kosong.StepResult", tool_results: list["kosong.tooling.ToolResult"]
    ) -> None:
        """
        将 StepResult 和 ToolResult 添加到 Context ⭐ Stage 17 完整实现

        官方实现要点：
        1. 检查工具消息的能力（raise LLMNotSupported）
        2. 将 assistant 消息添加到 Context
        3. 将 tool 消息添加到 Context
        4. 使用 asyncio.shield 防止中断

        Stage 17 完整实现（与官方一致）：
        ✅ 使用 tool_result_to_message() 批量转换
        ✅ 使用 check_message() 检查 LLM 能力
        ✅ 支持 ImageURLPart 和 ThinkPart
        ✅ 支持多格式输出

        Args:
            result: kosong.step() 的返回结果
            tool_results: 工具执行结果列表

        对应源码：kimi-cli-fork/src/kimi_cli/soul/kimisoul.py:279-300
        """
        # ⭐ Stage 17 完整实现（与官方一致）
        # 1. 将 LLM 响应（assistant 消息）添加到 Context
        await self._context.append_message(result.message)

        # 2. 批量转换工具结果为消息
        if tool_results:
            # 官方实现：使用 tool_result_to_message() 批量转换
            tool_messages = [tool_result_to_message(tr) for tr in tool_results]

            # 3. 检查每个消息并添加到 Context
            for tm in tool_messages:
                # 检查消息内容是否被 LLM 支持
                if missing_caps := check_message(tm, self._runtime.llm.capabilities):
                    # 不支持：抛出 LLMNotSupported 异常
                    raise LLMNotSupported(self._runtime.llm, list(missing_caps))

                # 支持：添加到 Context
                await self._context.append_message(tm)

    # ============================================================
    # Stage 17：重试机制辅助方法 ⭐
    # ============================================================

    @staticmethod
    def _is_retryable_error(exception: BaseException) -> bool:
        """
        检查异常是否可重试 ⭐ Stage 17

        官方实现要点：
        1. 网络相关错误（APIConnectionError, APITimeoutError, APIEmptyResponseError）
        2. API 状态码错误（429, 500, 502, 503）

        Args:
            exception: 捕获的异常

        Returns:
            bool: True 表示可重试，False 表示不可重试

        对应源码：kimi-cli-fork/src/kimi_cli/soul/kimisoul.py:329-337
        """
        # 网络相关错误：连接失败、超时、空响应
        if isinstance(exception, (APIConnectionError, APITimeoutError, APIEmptyResponseError)):
            return True

        # API 状态码错误：429（限流）、500/502/503（服务器错误）
        return isinstance(exception, APIStatusError) and exception.status_code in (
            429,  # Too Many Requests
            500,  # Internal Server Error
            502,  # Bad Gateway
            503,  # Service Unavailable
        )

    @staticmethod
    def _retry_log(name: str, retry_state: RetryCallState):
        """
        记录重试日志 ⭐ Stage 17

        Args:
            name: 重试的操作名称（"step" 或 "compaction"）
            retry_state: tenacity 的 RetryCallState 对象

        对应源码：kimi-cli-fork/src/kimi_cli/soul/kimisoul.py:340-348
        """
        # 简化版：直接打印日志（官方使用 logger.info）
        sleep_time = (
            retry_state.next_action.sleep if retry_state.next_action is not None else "unknown"
        )
        print(
            f"⚠️ Retrying {name} for the {retry_state.attempt_number} time. Waiting {sleep_time} seconds."
        )

    # ============================================================
    # TODO: Stage 17+ 完整方法（参考官方）
    # ============================================================
    # 官方参考：kimi-cli-fork/src/kimi_cli/soul/kimisoul.py
    #
    # Stage 17+（高级特性）需要添加：
    #
    # 1. _checkpoint() 方法（Context 检查点）：
    #    async def _checkpoint(self):
    #        """Create a checkpoint before running the agent loop."""
    #        await self._context.checkpoint()
    #
    # 2. compact_context() 方法（Context 压缩）：
    #    async def compact_context(self) -> None:
    #        """Compact the context to reduce token usage."""
    #        wire_send(CompactionBegin())
    #        summary_messages = await self._compact_with_retry()
    #        await self._context.compact(summary_messages)
    #        wire_send(CompactionEnd())
    #
    # 3. set_thinking() 方法（Thinking 模式切换）：
    #    def set_thinking(self, enabled: bool) -> None:
    #        """Enable or disable thinking mode."""
    #        self._thinking_effort = "high" if enabled else None
    #
    # 4. _is_retryable_error() 静态方法（错误重试判断）：
    #    @staticmethod
    #    def _is_retryable_error(exception: BaseException) -> bool:
    #        """Determine if an error is retryable."""
    #        # 检查 APIError, ConnectionError 等
    #
    # 5. _retry_log() 静态方法（重试日志）：
    #    @staticmethod
    #    def _retry_log(name: str, retry_state: RetryCallState):
    #        """Log retry attempts."""
    #        # 记录重试信息
    #
    # 6. 在 _step() 中使用 @tenacity.retry 装饰器：
    #    @tenacity.retry(
    #        retry=retry_if_exception(self._is_retryable_error),
    #        wait=wait_exponential_jitter(initial=0.3, max=5, jitter=0.5),
    #        stop=stop_after_attempt(max_retries),
    #        reraise=True,
    #    )
    #    async def _kosong_step_with_retry() -> StepResult:
    #        return await kosong.step(...)
    #
    # 7. DenwaRenji 机制（时间旅行 D-Mail）：
    #    - 在 _step() 中处理 BackToTheFuture 异常
    #    - 实现 _denwa_renji.fetch_pending_dmail()
    #
    # 8. ToolRejectedError 处理：
    #    - 在 _step() 中检查 tool_results 是否有被拒绝的工具
    #    - rejected = any(isinstance(result.result, ToolRejectedError) for result in results)
    #
    # 9. asyncio.shield 保护：
    #    - 在 _grow_context() 中使用 shield 防止 Context 操作被中断
    #    - await asyncio.shield(self._grow_context(result, results))
    #
    # 10. Approval 系统集成：
    #     - 在 _agent_loop() 中启动 _pipe_approval_to_wire() 任务
    #     - 处理批准请求（ApprovalRequest）
    # ============================================================

    @property
    def context(self) -> Context:
        """获取 Context（只读）"""
        return self._context

    async def compact_context(self) -> None:
        """压缩 Context（减少 token 使用）⭐ Stage 19

        流程：
        1. 使用 retry 装饰器调用压缩
        2. 回滚到检查点 0
        3. 创建新检查点
        4. 添加压缩后的消息

        Raises:
            LLMNotSet: LLM 未配置
            ChatProviderError: LLM API 错误

        对应源码：kimi-cli-fork/src/kimi_cli/soul/kimisoul.py:302-327
        """

        @tenacity.retry(
            retry=retry_if_exception(self._is_retryable_error),
            before_sleep=partial(self._retry_log, "compaction"),
            wait=wait_exponential_jitter(initial=0.3, max=5, jitter=0.5),
            stop=stop_after_attempt(self._loop_control.max_retries_per_step),
            reraise=True,
        )
        async def _compact_with_retry() -> Sequence[Message]:
            if self._runtime.llm is None:
                raise LLMNotSet()
            return await self._compaction.compact(self._context.history, self._runtime.llm)

        compacted_messages = await _compact_with_retry()
        await self._context.revert_to(0)
        await self._checkpoint()
        await self._context.append_message(compacted_messages)

    async def _checkpoint(self):
        """创建检查点 ⭐ Stage 19/20

        根据是否启用 SendDMail 工具决定 checkpoint 策略：
        - 如果启用 SendDMail：add_user_message=True（在 user 消息后创建 checkpoint）
        - 否则：add_user_message=False（立即创建 checkpoint）

        对应源码：kimi-cli-fork/src/kimi_cli/soul/kimisoul.py（参考上下文功能）
        """
        await self._context.checkpoint(add_user_message=self._checkpoint_with_user_message)
        self._denwa_renji.set_n_checkpoints(self._context.n_checkpoints)

    @staticmethod
    def _is_retryable_error(exception: BaseException) -> bool:
        """判断错误是否可重试 ⭐ Stage 19

        可重试的错误：
        - APIConnectionError: 连接错误
        - APITimeoutError: 超时错误
        - APIEmptyResponseError: 空响应错误
        - APIStatusError: 状态码 429, 500, 502, 503

        对应源码：kimi-cli-fork/src/kimi_cli/soul/kimisoul.py:329-337
        """
        if isinstance(exception, (APIConnectionError, APITimeoutError, APIEmptyResponseError)):
            return True
        return isinstance(exception, APIStatusError) and exception.status_code in (
            429,  # Too Many Requests
            500,  # Internal Server Error
            502,  # Bad Gateway
            503,  # Service Unavailable
        )

    @staticmethod
    def _retry_log(name: str, retry_state: RetryCallState):
        """记录重试日志 ⭐ Stage 19

        对应源码：kimi-cli-fork/src/kimi_cli/soul/kimisoul.py:339-346
        """
        logger.info(
            "Retrying {name} for the {n} time. Waiting {sleep} seconds.",
            name=name,
            n=retry_state.attempt_number,
            sleep=retry_state.next_action.sleep
            if retry_state.next_action is not None
            else "unknown",
        )













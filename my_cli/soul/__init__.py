from __future__ import annotations

import asyncio
import contextlib
from collections.abc import Callable, Coroutine
from contextvars import ContextVar
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from kosong.message import ContentPart

from my_cli.utils.logging import logger
from my_cli.wire import Wire, WireMessage, WireUISide

if TYPE_CHECKING:
    from my_cli.llm import LLM, ModelCapability


class LLMNotSet(Exception):
    """当 LLM 未设置时抛出的异常"""

    pass


class LLMNotSupported(Exception):
    """当 LLM 不支持所需能力时抛出的异常"""

    def __init__(self, llm: LLM, capabilities: list[ModelCapability]):
        self.llm = llm
        self.capabilities = capabilities
        capabilities_str = "capability" if len(capabilities) == 1 else "capabilities"
        super().__init__(
            f"LLM 模型 '{llm.model_name}' 不支持所需 {capabilities_str}: "
            f"{', '.join(capabilities)}."
        )


class MaxStepsReached(Exception):
    """当达到最大步骤数时抛出的异常"""

    n_steps: int
    """已执行的步数"""

    def __init__(self, n_steps: int):
        self.n_steps = n_steps


@dataclass(frozen=True, slots=True)
class StatusSnapshot:
    context_usage: float
    """上下文使用率，单位为百分比"""


@runtime_checkable
class Soul(Protocol):
    """AI Agent 核心协议"""

    @property
    def name(self) -> str:
        """Agent 的名称"""

    @property
    def model_name(self) -> str:
        """Agent 使用的 LLM 模型名称。空字符串表示未配置 LLM"""

    @property
    def model_capabilities(self) -> set[ModelCapability] | None:
        """Agent 使用的 LLM 模型能力。None 表示未配置 LLM"""

    @property
    def status(self) -> StatusSnapshot:
        """Agent 的当前状态。返回值为不可变对象"""

    async def run(self, user_input: str | list[ContentPart]):
        """
        运行 Agent，处理用户输入直到达到最大步骤数或无更多工具调用

        参数:
            user_input (str | list[ContentPart]): 用户的输入

        抛出异常:
            LLMNotSet: 当 LLM 未设置时
            LLMNotSupported: 当 LLM 不支持所需能力时
            ChatProviderError: 当 LLM 提供商返回错误时
            MaxStepsReached: 当达到最大步骤数时
            asyncio.CancelledError: 当用户取消运行时
        """
        ...


type UILoopFn = Callable[[WireUISide], Coroutine[Any, Any, None]]
"""用于可视化 Agent 行为的长时间运行的异步函数"""


class RunCancelled(Exception):
    """当运行被取消事件中止时抛出的异常"""


async def run_soul(
    soul: Soul,
    user_input: str | list[ContentPart],
    ui_loop_fn: UILoopFn,
    cancel_event: asyncio.Event,
) -> None:
    """
    使用给定的用户输入运行 Agent，通过 Wire 连接到 UI 循环

    `cancel_event` 是用于取消运行的外部句柄。当设置事件时，
    运行将优雅地停止并抛出 `RunCancelled` 异常。

    抛出异常:
        LLMNotSet: 当 LLM 未设置时
        LLMNotSupported: 当 LLM 不支持所需能力时
        ChatProviderError: 当 LLM 提供商返回错误时
        MaxStepsReached: 当达到最大步骤数时
        RunCancelled: 当运行被取消事件中止时
    """
    wire = Wire()
    wire_token = _current_wire.set(wire)

    logger.debug("Starting UI loop with function: {ui_loop_fn}", ui_loop_fn=ui_loop_fn)
    ui_task = asyncio.create_task(ui_loop_fn(wire.ui_side))

    logger.debug("Starting soul run")
    soul_task = asyncio.create_task(soul.run(user_input))

    cancel_event_task = asyncio.create_task(cancel_event.wait())
    await asyncio.wait(
        [soul_task, cancel_event_task],
        return_when=asyncio.FIRST_COMPLETED,
    )

    try:
        if cancel_event.is_set():
            logger.debug("Cancelling the run task")
            soul_task.cancel()
            try:
                await soul_task
            except asyncio.CancelledError:
                raise RunCancelled from None
        else:
            assert soul_task.done()  # either stop event is set or the run task is done
            cancel_event_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await cancel_event_task
            soul_task.result()  # this will raise if any exception was raised in the run task
    finally:
        logger.debug("Shutting down the UI loop")
        # shutting down the wire should break the UI loop
        wire.shutdown()
        try:
            await asyncio.wait_for(ui_task, timeout=0.5)
        except asyncio.QueueShutDown:
            logger.debug("UI loop shut down")
            pass
        except TimeoutError:
            logger.warning("UI loop timed out")
        finally:
            _current_wire.reset(wire_token)


_current_wire = ContextVar[Wire | None]("current_wire", default=None)
"""当前 Wire 连接的上下文变量"""


def get_wire_or_none() -> Wire | None:
    """
    获取当前 Wire 或 None

    预期在 Agent 循环中的任何地方调用时都不为 None
    """
    return _current_wire.get()


def wire_send(msg: WireMessage) -> None:
    """
    向当前 Wire 发送消息

    将此视为 Soul 的 `print` 和 `input`
    Soul 应该始终使用此函数发送 Wire 消息
    """
    wire = get_wire_or_none()
    assert wire is not None, "Wire is expected to be set when soul is running"
    wire.soul_side.send(msg)

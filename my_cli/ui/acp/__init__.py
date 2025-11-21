"""
ACP UI 层 - Agent Communication Protocol 服务器 ⭐ Stage 31

实现 ACP 协议，支持 IDE 客户端（如 VSCode Copilot）集成。

对应源码：kimi-cli-fork/src/kimi_cli/ui/acp/__init__.py
"""

from __future__ import annotations

import asyncio
import uuid
from typing import Any

import acp  # pyright: ignore[reportMissingTypeStubs]
import streamingjson  # pyright: ignore[reportMissingTypeStubs]
from kosong.chat_provider import ChatProviderError
from kosong.message import (
    ContentPart,
    TextPart,
    ThinkPart,
    ToolCall,
    ToolCallPart,
)
from kosong.tooling import ToolError, ToolOk, ToolResult

from my_cli.soul import LLMNotSet, MaxStepsReached, RunCancelled, Soul, run_soul
from my_cli.tools import extract_key_argument
from my_cli.utils.logging import logger
from my_cli.wire import WireUISide
from my_cli.wire.message import (
    ApprovalRequest,
    ApprovalResponse,
    CompactionBegin,
    CompactionEnd,
    StatusUpdate,
    StepBegin,
    StepInterrupted,
    SubagentEvent,
)


class _ToolCallState:
    """管理单个工具调用的状态（用于流式更新）"""

    def __init__(self, tool_call: ToolCall):
        # ACP 侧唯一 ID（避免与 LLM 侧 ID 冲突）
        self.acp_tool_call_id = str(uuid.uuid4())
        self.tool_call = tool_call
        self.args = tool_call.function.arguments or ""
        self.lexer = streamingjson.Lexer()
        if tool_call.function.arguments is not None:
            self.lexer.append_string(tool_call.function.arguments)

    def append_args_part(self, args_part: str):
        """追加参数片段"""
        self.args += args_part
        self.lexer.append_string(args_part)

    def get_title(self) -> str:
        """获取工具调用标题（含副标题）"""
        tool_name = self.tool_call.function.name
        subtitle = extract_key_argument(self.lexer, tool_name)
        if subtitle:
            return f"{tool_name}: {subtitle}"
        return tool_name


class _RunState:
    """运行状态"""

    def __init__(self):
        self.tool_calls: dict[str, _ToolCallState] = {}
        self.last_tool_call: _ToolCallState | None = None
        self.cancel_event = asyncio.Event()


class ACPAgent:
    """ACP Agent 协议实现"""

    def __init__(self, soul: Soul, connection: acp.AgentSideConnection):
        self.soul = soul
        self.connection = connection
        self.session_id: str | None = None
        self.run_state: _RunState | None = None

    async def initialize(self, params: acp.InitializeRequest) -> acp.InitializeResponse:
        """处理初始化请求"""
        logger.info(
            "ACP server initialized with protocol version: {version}",
            version=params.protocolVersion,
        )
        return acp.InitializeResponse(
            protocolVersion=params.protocolVersion,
            agentCapabilities=acp.schema.AgentCapabilities(
                loadSession=False,
                promptCapabilities=acp.schema.PromptCapabilities(
                    embeddedContext=False, image=False, audio=False
                ),
            ),
            authMethods=[],
        )

    async def authenticate(self, params: acp.AuthenticateRequest) -> None:
        """处理认证请求"""
        logger.info("Authenticate with method: {method}", method=params.methodId)

    async def newSession(self, params: acp.NewSessionRequest) -> acp.NewSessionResponse:
        """创建新会话"""
        self.session_id = f"sess_{uuid.uuid4().hex[:16]}"
        logger.info("Created session {id} with cwd: {cwd}", id=self.session_id, cwd=params.cwd)
        return acp.NewSessionResponse(sessionId=self.session_id)

    async def loadSession(self, params: acp.LoadSessionRequest) -> None:
        """加载会话"""
        self.session_id = params.sessionId
        logger.info("Loaded session: {id}", id=self.session_id)

    async def setSessionModel(self, params: acp.SetSessionModelRequest) -> None:
        """设置会话模型"""
        logger.warning("Set session model: {model}", model=params.modelId)

    async def setSessionMode(
        self, params: acp.SetSessionModeRequest
    ) -> acp.SetSessionModeResponse | None:
        """设置会话模式"""
        logger.warning("Set session mode: {mode}", mode=params.modeId)
        return None

    async def extMethod(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        """处理扩展方法"""
        logger.warning("Unsupported extension method: {method}", method=method)
        return {}

    async def extNotification(self, method: str, params: dict[str, Any]) -> None:
        """处理扩展通知"""
        logger.warning("Unsupported extension notification: {method}", method=method)

    async def prompt(self, params: acp.PromptRequest) -> acp.PromptResponse:
        """处理 prompt 请求（支持流式输出）"""
        prompt_text = "\n".join(
            block.text for block in params.prompt if isinstance(block, acp.schema.TextContentBlock)
        )

        if not prompt_text:
            raise acp.RequestError.invalid_params({"reason": "No text in prompt"})

        logger.info("Processing prompt: {text}", text=prompt_text[:100])

        self.run_state = _RunState()
        try:
            await run_soul(self.soul, prompt_text, self._stream_events, self.run_state.cancel_event)
            return acp.PromptResponse(stopReason="end_turn")
        except LLMNotSet:
            logger.error("LLM not set")
            raise acp.RequestError.internal_error({"error": "LLM not set"}) from None
        except ChatProviderError as e:
            logger.exception("LLM provider error:")
            raise acp.RequestError.internal_error({"error": f"LLM provider error: {e}"}) from e
        except MaxStepsReached as e:
            logger.warning("Max steps reached: {n}", n=e.n_steps)
            return acp.PromptResponse(stopReason="max_turn_requests")
        except RunCancelled:
            logger.info("Prompt cancelled by user")
            return acp.PromptResponse(stopReason="cancelled")
        except BaseException as e:
            logger.exception("Unknown error:")
            raise acp.RequestError.internal_error({"error": f"Unknown error: {e}"}) from e
        finally:
            self.run_state = None

    async def cancel(self, params: acp.CancelNotification) -> None:
        """处理取消通知"""
        logger.info("Cancel for session: {id}", id=params.sessionId)
        if self.run_state is None:
            logger.warning("No running prompt to cancel")
            return
        if not self.run_state.cancel_event.is_set():
            logger.info("Cancelling running prompt")
            self.run_state.cancel_event.set()

    async def _stream_events(self, wire: WireUISide):
        """流式处理 Wire 事件"""
        while True:
            msg = await wire.receive()
            match msg:
                case StepBegin():
                    pass
                case StepInterrupted():
                    break
                case CompactionBegin():
                    pass
                case CompactionEnd():
                    pass
                case StatusUpdate():
                    pass
                case ThinkPart(think=think):
                    await self._send_thinking(think)
                case TextPart(text=text):
                    await self._send_text(text)
                case ContentPart():
                    logger.warning("Unsupported content part: {part}", part=msg)
                    await self._send_text(f"[{msg.__class__.__name__}]")
                case ToolCall():
                    await self._send_tool_call(msg)
                case ToolCallPart():
                    await self._send_tool_call_part(msg)
                case ToolResult():
                    await self._send_tool_result(msg)
                case SubagentEvent():
                    pass
                case ApprovalRequest():
                    await self._handle_approval_request(msg)

    async def _send_thinking(self, think: str):
        """发送思考内容"""
        if not self.session_id:
            return
        await self.connection.sessionUpdate(
            acp.SessionNotification(
                sessionId=self.session_id,
                update=acp.schema.AgentThoughtChunk(
                    content=acp.schema.TextContentBlock(type="text", text=think),
                    sessionUpdate="agent_thought_chunk",
                ),
            )
        )

    async def _send_text(self, text: str):
        """发送文本块"""
        if not self.session_id:
            return
        await self.connection.sessionUpdate(
            acp.SessionNotification(
                sessionId=self.session_id,
                update=acp.schema.AgentMessageChunk(
                    content=acp.schema.TextContentBlock(type="text", text=text),
                    sessionUpdate="agent_message_chunk",
                ),
            )
        )

    async def _send_tool_call(self, tool_call: ToolCall):
        """发送工具调用"""
        assert self.run_state is not None
        if not self.session_id:
            return

        state = _ToolCallState(tool_call)
        self.run_state.tool_calls[tool_call.id] = state
        self.run_state.last_tool_call = state

        await self.connection.sessionUpdate(
            acp.SessionNotification(
                sessionId=self.session_id,
                update=acp.schema.ToolCallStart(
                    sessionUpdate="tool_call",
                    toolCallId=state.acp_tool_call_id,
                    title=state.get_title(),
                    status="in_progress",
                    content=[
                        acp.schema.ContentToolCallContent(
                            type="content",
                            content=acp.schema.TextContentBlock(type="text", text=state.args),
                        )
                    ],
                ),
            )
        )
        logger.debug("Sent tool call: {name}", name=tool_call.function.name)

    async def _send_tool_call_part(self, part: ToolCallPart):
        """发送工具调用片段（流式参数）"""
        assert self.run_state is not None
        if not self.session_id or not part.arguments_part or self.run_state.last_tool_call is None:
            return

        self.run_state.last_tool_call.append_args_part(part.arguments_part)

        update = acp.schema.ToolCallProgress(
            sessionUpdate="tool_call_update",
            toolCallId=self.run_state.last_tool_call.acp_tool_call_id,
            title=self.run_state.last_tool_call.get_title(),
            status="in_progress",
            content=[
                acp.schema.ContentToolCallContent(
                    type="content",
                    content=acp.schema.TextContentBlock(
                        type="text", text=self.run_state.last_tool_call.args
                    ),
                )
            ],
        )

        await self.connection.sessionUpdate(
            acp.SessionNotification(sessionId=self.session_id, update=update)
        )
        logger.debug("Sent tool call update: {delta}", delta=part.arguments_part[:50])

    async def _send_tool_result(self, result: ToolResult):
        """发送工具结果"""
        assert self.run_state is not None
        if not self.session_id:
            return

        tool_result = result.result
        is_error = isinstance(tool_result, ToolError)

        state = self.run_state.tool_calls.pop(result.tool_call_id, None)
        if state is None:
            logger.warning("Tool call not found: {id}", id=result.tool_call_id)
            return

        update = acp.schema.ToolCallProgress(
            sessionUpdate="tool_call_update",
            toolCallId=state.acp_tool_call_id,
            status="failed" if is_error else "completed",
        )

        if state.tool_call.function.name == "SetTodoList" and not is_error:
            update.content = _tool_result_to_acp_content(tool_result)

        await self.connection.sessionUpdate(
            acp.SessionNotification(sessionId=self.session_id, update=update)
        )
        logger.debug("Sent tool result: {id}", id=result.tool_call_id)

    async def _handle_approval_request(self, request: ApprovalRequest):
        """处理批准请求"""
        assert self.run_state is not None
        if not self.session_id:
            logger.warning("No session ID, auto-rejecting approval request")
            request.resolve(ApprovalResponse.REJECT)
            return

        state = self.run_state.tool_calls.get(request.tool_call_id, None)
        if state is None:
            logger.warning("Tool call not found: {id}", id=request.tool_call_id)
            request.resolve(ApprovalResponse.REJECT)
            return

        permission_request = acp.RequestPermissionRequest(
            sessionId=self.session_id,
            toolCall=acp.schema.ToolCall(
                toolCallId=state.acp_tool_call_id,
                content=[
                    acp.schema.ContentToolCallContent(
                        type="content",
                        content=acp.schema.TextContentBlock(
                            type="text",
                            text=f"Requesting approval to perform: {request.description}",
                        ),
                    ),
                ],
            ),
            options=[
                acp.schema.PermissionOption(
                    optionId="approve",
                    name="Approve",
                    kind="allow_once",
                ),
                acp.schema.PermissionOption(
                    optionId="approve_for_session",
                    name="Approve for this session",
                    kind="allow_always",
                ),
                acp.schema.PermissionOption(
                    optionId="reject",
                    name="Reject",
                    kind="reject_once",
                ),
            ],
        )

        try:
            logger.debug("Requesting permission for action: {action}", action=request.action)
            response = await self.connection.requestPermission(permission_request)
            logger.debug("Received permission response: {response}", response=response)

            if isinstance(response.outcome, acp.schema.AllowedOutcome):
                if response.outcome.optionId == "approve":
                    logger.debug("Permission granted for: {action}", action=request.action)
                    request.resolve(ApprovalResponse.APPROVE)
                elif response.outcome.optionId == "approve_for_session":
                    logger.debug("Permission granted for session: {action}", action=request.action)
                    request.resolve(ApprovalResponse.APPROVE_FOR_SESSION)
                else:
                    logger.debug("Permission denied for: {action}", action=request.action)
                    request.resolve(ApprovalResponse.REJECT)
            else:
                logger.debug("Permission request cancelled for: {action}", action=request.action)
                request.resolve(ApprovalResponse.REJECT)
        except Exception:
            logger.exception("Error handling approval request:")
            request.resolve(ApprovalResponse.REJECT)


def _tool_result_to_acp_content(
    tool_result: ToolOk | ToolError,
) -> list[
    acp.schema.ContentToolCallContent
    | acp.schema.FileEditToolCallContent
    | acp.schema.TerminalToolCallContent
]:
    """将工具结果转换为 ACP 内容"""

    def _to_acp_content(
        part: ContentPart,
    ) -> (
        acp.schema.ContentToolCallContent
        | acp.schema.FileEditToolCallContent
        | acp.schema.TerminalToolCallContent
    ):
        if isinstance(part, TextPart):
            return acp.schema.ContentToolCallContent(
                type="content", content=acp.schema.TextContentBlock(type="text", text=part.text)
            )
        else:
            logger.warning("Unsupported content part in tool result: {part}", part=part)
            return acp.schema.ContentToolCallContent(
                type="content",
                content=acp.schema.TextContentBlock(
                    type="text", text=f"[{part.__class__.__name__}]"
                ),
            )

    content: list[
        (
            acp.schema.ContentToolCallContent
            | acp.schema.FileEditToolCallContent
            | acp.schema.TerminalToolCallContent
        )
    ] = []
    if isinstance(tool_result.output, str):
        content.append(_to_acp_content(TextPart(text=tool_result.output)))
    elif isinstance(tool_result.output, ContentPart):
        content.append(_to_acp_content(tool_result.output))
    elif isinstance(tool_result.output, list):
        content.extend(_to_acp_content(part) for part in tool_result.output)

    return content


class ACPServer:
    """ACP 服务器（基于 stdio）"""

    def __init__(self, soul: Soul):
        self.soul = soul

    async def run(self) -> bool:
        """运行 ACP 服务器"""
        logger.info("Starting ACP server on stdio")

        reader, writer = await acp.stdio_streams()

        _ = acp.AgentSideConnection(
            lambda conn: ACPAgent(self.soul, conn),
            writer,
            reader,
        )

        logger.info("ACP server ready")
        await asyncio.Event().wait()

        return True


__all__ = ["ACPServer", "ACPAgent"]

"""
ACP UI 层 - Agent Communication Protocol 客户端

学习目标：
1. 理解 ACP 协议的 UI 实现
2. 理解如何通过 Wire 接收 Soul 事件
3. 理解流式输出渲染

对应源码：kimi-cli-fork/src/kimi_cli/ui/acp/__init__.py

阶段演进：
- Stage 4-16：使用 Shell UI（CustomPromptSession）✅
- Stage 20：实现 ACP UI（支持 LSP 客户端）⭐ TODO

背景：
ACP (Agent Communication Protocol) 是一个用于 AI Agent 和客户端通信的协议。
类似于 LSP (Language Server Protocol)，但专门为 AI Agent 设计。

ACP UI 的核心功能：
1. 接收 Wire 事件（StepBegin, ContentPart, ToolCall 等）
2. 渲染流式输出（实时显示 LLM 响应）
3. 处理批准请求（ApprovalRequest）
4. 管理工具调用状态（ToolCallState）
"""

from __future__ import annotations

# ============================================================
# TODO: Stage 20+ 完整实现（参考官方）
# ============================================================
# 官方参考：kimi-cli-fork/src/kimi_cli/ui/acp/__init__.py
#
# Stage 20（ACP UI）需要：
# 1. 实现 ACP 服务器（监听客户端连接）
# 2. 实现事件处理（接收 Wire 事件并转换为 ACP 消息）
# 3. 实现流式输出渲染
# 4. 实现批准请求处理
# 5. 实现工具调用状态管理
#
# 核心类：
# - _ToolCallState: 管理单个工具调用的状态
# - ACPApp: ACP 应用主类
#
# _ToolCallState 要点：
# class _ToolCallState:
#     def __init__(self, tool_call: ToolCall):
#         self.acp_tool_call_id = str(uuid.uuid4())  # ACP 侧的唯一 ID
#         self.tool_call = tool_call
#         self.args = tool_call.function.arguments or ""
#         self.lexer = streamingjson.Lexer()  # JSON 流式解析
#
#     def append_args_part(self, args_part: str):
#         """追加参数片段"""
#         self.args += args_part
#         self.lexer.append_string(args_part)
#
#     def get_title(self) -> str:
#         """获取工具调用标题（用于显示）"""
#         tool_name = self.tool_call.function.name
#         subtitle = extract_key_argument(self.lexer, tool_name)
#         return f"{tool_name}: {subtitle}" if subtitle else tool_name
#
# ACPApp 要点：
# class ACPApp:
#     def __init__(self, soul: Soul, cancel_event: asyncio.Event):
#         self.soul = soul
#         self.cancel_event = cancel_event
#         self._tool_call_states: dict[str, _ToolCallState] = {}
#
#     async def run(self, user_input: str | list[ContentPart]):
#         """运行 ACP UI"""
#         # 1. 启动 ACP 服务器
#         # 2. 启动 ui_loop_fn（处理 Wire 事件）
#         # 3. 调用 run_soul()
#         # 4. 处理结果或异常
#
#     async def _ui_loop_fn(self, wire_ui: WireUISide):
#         """UI Loop - 接收 Wire 事件并转换为 ACP 消息"""
#         while True:
#             msg = await wire_ui.receive()
#
#             match msg:
#                 case StepBegin(n):
#                     # 发送步骤开始消息
#                     ...
#                 case TextPart(text):
#                     # 发送文本片段
#                     ...
#                 case ToolCall(...):
#                     # 创建工具调用状态
#                     ...
#                 case ToolCallPart(...):
#                     # 更新工具调用参数
#                     ...
#                 case ToolResult(...):
#                     # 发送工具结果
#                     ...
#                 case ApprovalRequest(...):
#                     # 处理批准请求
#                     ...
#                 case StatusUpdate(...):
#                     # 更新状态
#                     ...
#
# 使用示例：
# async def main():
#     soul = create_soul(work_dir=Path.cwd())
#     cancel_event = asyncio.Event()
#
#     app = ACPApp(soul, cancel_event)
#     await app.run("你好")
#
# ACP 消息格式（JSON-RPC 2.0）：
# {
#     "jsonrpc": "2.0",
#     "method": "textDelta",
#     "params": {
#         "text": "你好"
#     }
# }
#
# {
#     "jsonrpc": "2.0",
#     "method": "toolCallBegin",
#     "params": {
#         "id": "tool_call_123",
#         "name": "Bash",
#         "title": "Bash: ls -la"
#     }
# }
#
# {
#     "jsonrpc": "2.0",
#     "method": "toolCallEnd",
#     "params": {
#         "id": "tool_call_123",
#         "success": true
#     }
# }
#
# Stage 4-16 简化版：
# - 使用 Shell UI（CustomPromptSession）
# - 不需要 ACP 协议
# ============================================================

"""
Soul 消息辅助工具 - 消息格式转换和处理

学习目标：
1. 理解 ToolResult 到 Message 的转换
2. 理解 system() 函数（创建系统消息）
3. 理解 tool_ok_to_message_content() 函数

对应源码：kimi-cli-fork/src/kimi_cli/soul/message.py

阶段演进：
- Stage 8：基础工具系统时已简化实现 ✅
- Stage 17：完整实现 tool_result_to_message() ⭐ TODO
- Stage 18：支持图片输出（ImageURLPart）⭐ TODO
"""

from __future__ import annotations

from collections.abc import Sequence

from kosong.message import ContentPart, Message, TextPart
from kosong.tooling import ToolError, ToolOk, ToolResult
from kosong.tooling.error import ToolRuntimeError


def system(message: str) -> ContentPart:
    """
    创建系统消息 ContentPart

    这个函数用于创建带 <system> 标签的消息片段。
    系统消息通常用于：
    - 工具执行错误提示
    - 工具输出为空提示
    - D-Mail 消息（时间旅行）

    Args:
        message: 系统消息文本

    Returns:
        TextPart: 包含 <system> 标签的文本片段

    对应源码：kimi-cli-fork/src/kimi_cli/soul/message.py:13-14
    """
    return TextPart(text=f"<system>{message}</system>")


def tool_result_to_message(tool_result: ToolResult) -> Message:
    """
    将 ToolResult 转换为 Message ⭐ Stage 17 完整实现

    官方实现要点：
    1. 检查 tool_result.result 类型（ToolError 或 ToolOk）
    2. 如果是 ToolError：
       - 创建 ERROR 系统消息
       - 如果是 ToolRuntimeError，添加额外提示
       - 如果有 output，添加到 content
    3. 如果是 ToolOk：
       - 使用 tool_ok_to_message_content() 转换
    4. 创建 role="tool" 的 Message

    简化版实现（Stage 8-16）：
    - 直接将 result 转换为字符串
    - 不区分 ToolError 和ToolOk

    Args:
        tool_result: 工具执行结果

    Returns:
        Message: 转换后的消息

    对应源码：kimi-cli-fork/src/kimi_cli/soul/message.py:17-34
    """
    # ============================================================
    # TODO: Stage 17 完整实现（参考官方）
    # ============================================================
    # 官方实现：
    #
    # if isinstance(tool_result.result, ToolError):
    #     assert tool_result.result.message, "ToolError should have a message"
    #     message = tool_result.result.message
    #     if isinstance(tool_result.result, ToolRuntimeError):
    #         message += "\nThis is an unexpected error and the tool is probably not working."
    #     content: list[ContentPart] = [system(f"ERROR: {message}")]
    #     if tool_result.result.output:
    #         content.extend(_output_to_content_parts(tool_result.result.output))
    # else:
    #     content = tool_ok_to_message_content(tool_result.result)
    #
    # return Message(
    #     role="tool",
    #     content=content,
    #     tool_call_id=tool_result.tool_call_id,
    # )
    # ============================================================

    # 简化版（Stage 8-16）：直接转换
    if hasattr(tool_result.result, "output"):
        output_str = str(tool_result.result.output)
    else:
        output_str = str(tool_result.result)

    return Message(
        role="tool",
        content=[TextPart(text=output_str)],
        tool_call_id=tool_result.tool_call_id,
    )


def tool_ok_to_message_content(result: ToolOk) -> list[ContentPart]:
    """
    将 ToolOk 转换为消息内容 ⭐ Stage 17 完整实现

    官方实现要点：
    1. 如果有 result.message，添加为系统消息
    2. 使用 _output_to_content_parts() 转换 output
    3. 如果 content 为空，添加 "Tool output is empty." 系统消息

    Args:
        result: ToolOk 结果

    Returns:
        list[ContentPart]: 消息内容片段列表

    对应源码：kimi-cli-fork/src/kimi_cli/soul/message.py:37-45
    """
    # ============================================================
    # TODO: Stage 17 完整实现（参考官方）
    # ============================================================
    # 官方实现：
    #
    # content: list[ContentPart] = []
    # if result.message:
    #     content.append(system(result.message))
    # content.extend(_output_to_content_parts(result.output))
    # if not content:
    #     content.append(system("Tool output is empty."))
    # return content
    # ============================================================

    # 简化版（Stage 8-16）：直接返回
    return [TextPart(text=str(result.output))]


def _output_to_content_parts(
    output: str | ContentPart | Sequence[ContentPart],
) -> list[ContentPart]:
    """
    将工具输出��换为 ContentPart 列表 ⭐ Stage 18 图片支持

    官方实现要点：
    1. 如果 output 是字符串，创建 TextPart
    2. 如果 output 是 ContentPart，直接使用
    3. 如果 output 是 ContentPart 序列，展开

    Args:
        output: 工具输出

    Returns:
        list[ContentPart]: 内容片段列表

    对应源码：kimi-cli-fork/src/kimi_cli/soul/message.py:48-74
    """
    # ============================================================
    # TODO: Stage 18 完整实现（参考官方）
    # ============================================================
    # 官方实现：
    #
    # content: list[ContentPart] = []
    # if isinstance(output, str):
    #     if output.strip():
    #         content.append(TextPart(text=output))
    # elif isinstance(output, ContentPart):
    #     content.append(output)
    # else:
    #     for part in output:
    #         if isinstance(part, TextPart) and not part.text.strip():
    #             continue
    #         content.append(part)
    # return content
    # ============================================================

    # 简化版（Stage 8-16）：只支持字符串
    if isinstance(output, str):
        return [TextPart(text=output)]
    return []


# ============================================================
# TODO: Stage 18+ 完整功能（参考官方）
# ============================================================
# 官方参考：kimi-cli-fork/src/kimi_cli/soul/message.py
#
# Stage 18+（图片支持）需要添加：
#
# from kosong.message import ImageURLPart, ThinkPart
# from kimi_cli.llm import ModelCapability
#
# def check_message(message: Message, capabilities: set[ModelCapability] | None) -> set[ModelCapability]:
#     """检查消息是否包含 LLM 不支持的能力"""
#     if capabilities is None:
#         return set()
#
#     missing_caps: set[ModelCapability] = set()
#     for part in message.content:
#         if isinstance(part, ImageURLPart) and ModelCapability.IMAGE_IN not in capabilities:
#             missing_caps.add(ModelCapability.IMAGE_IN)
#         if isinstance(part, ThinkPart) and ModelCapability.THINKING not in capabilities:
#             missing_caps.add(ModelCapability.THINKING)
#     return missing_caps
# ============================================================

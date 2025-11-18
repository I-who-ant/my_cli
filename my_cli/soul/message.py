"""
Soul 消息辅助工具 - 消息格式转换和处理

学习目标：
1. 理解 ToolResult 到 Message 的转换
2. 理解 system() 函数（创建系统消息）
3. 理解 tool_ok_to_message_content() 函数

对应源码：kimi-cli-fork/src/kimi_cli/soul/message.py

阶段演进：
- Stage 8：基础工具系统时已简化实现 ✅
- Stage 17：完整实现 tool_result_to_message() ⭐ 当前
- Stage 18：支持图片输出（ImageURLPart）⭐ TODO
"""

from __future__ import annotations

from collections.abc import Sequence

from kosong.message import ContentPart, ImageURLPart, Message, TextPart, ThinkPart
from kosong.tooling import ToolError, ToolOk, ToolResult
from kosong.tooling.error import ToolRuntimeError

from my_cli.llm import ModelCapability


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

    Args:
        tool_result: 工具执行结果

    Returns:
        Message: 转换后的消息

    对应源码：kimi-cli-fork/src/kimi_cli/soul/message.py:17-34
    """
    # ⭐ Stage 17 完整实现（官方做法）
    if isinstance(tool_result.result, ToolError):
        # 工具执行出错：创建错误消息
        assert tool_result.result.message, "ToolError should have a message"
        message = tool_result.result.message

        # 如果是运行时错误，添加额外警告
        if isinstance(tool_result.result, ToolRuntimeError):
            message += "\nThis is an unexpected error and the tool is probably not working."

        # 创建系统错误消息
        content: list[ContentPart] = [system(f"ERROR: {message}")]

        # 如果有 output，也添加进去（可能包含错误详情）
        if tool_result.result.output:
            content.extend(_output_to_content_parts(tool_result.result.output))
    else:
        # 工具执行成功：转换为消息内容
        content = tool_ok_to_message_content(tool_result.result)

    return Message(
        role="tool",
        content=content,
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
    # ⭐ Stage 17 完整实现（官方做法）
    content: list[ContentPart] = []

    # 如果有 message，添加为系统消息
    if result.message:
        content.append(system(result.message))

    # 转换 output
    content.extend(_output_to_content_parts(result.output))

    # 如果 content 为空，添加提示
    if not content:
        content.append(system("Tool output is empty."))

    return content


def _output_to_content_parts(
    output: str | ContentPart | Sequence[ContentPart],
) -> list[ContentPart]:
    """
    将工具输出转换为 ContentPart 列表 ⭐ Stage 17 完整实现

    官方实现要点：
    1. 如果 output 是字符串，创建 TextPart
    2. 如果 output 是 ContentPart，直接使用
    3. 如果 output 是 ContentPart 序列，展开
    4. 跳过空文本片段

    Args:
        output: 工具输出

    Returns:
        list[ContentPart]: 内容片段列表

    对应源码：kimi-cli-fork/src/kimi_cli/soul/message.py:48-74
    """
    # ⭐ Stage 17 完整实现（官方做法）
    content: list[ContentPart] = []

    if isinstance(output, str):
        # 字符串：创建 TextPart（跳过空字符串）
        if output.strip():
            content.append(TextPart(text=output))
    elif isinstance(output, ContentPart):
        # 单个 ContentPart：直接添加
        content.append(output)
    else:
        # ContentPart 序列：展开（跳过空文本片段）
        for part in output:
            if isinstance(part, TextPart) and not part.text.strip():
                continue
            content.append(part)

    return content


# ============================================================
# Stage 17 收尾：check_message() 函数实现 ⭐
# ============================================================
# 官方参考：kimi-cli-fork/src/kimi_cli/soul/message.py:63-75
# 对应源码：check_message()


def check_message(
    message: Message, model_capabilities: set[ModelCapability] | None
) -> set[ModelCapability]:
    """
    检查消息内容需要的模型能力 ⭐ Stage 17 完整实现

    这个函数用于在发送消息给 LLM 前检查该消息是否包含 LLM 不支持的内容。
    如果 LLM 不支持某些能力，会抛出 LLMNotSupported 异常。

    官方实现要点：
    1. 遍历消息中的所有 ContentPart
    2. 如果包含 ImageURLPart，需要 "image_in" 能力
    3. 如果包含 ThinkPart，需要 "thinking" 能力
    4. 返回消息需要但 LLM 没有的能力集合

    Args:
        message: 要检查的消息
        model_capabilities: LLM 支持的能力集合（可能为 None）

    Returns:
        set[ModelCapability]: LLM 缺失的能力集合（空集合表示支持）

    对应源码：kimi-cli-fork/src/kimi_cli/soul/message.py:63-75
    """
    # ⭐ Stage 17 完整实现（官方做法）
    # 如果没有能力信息，返回空集合（所有都支持）
    if model_capabilities is None:
        return set()

    # 初始化缺失能力集合
    missing_caps: set[ModelCapability] = set()

    # 遍历消息中的所有内容片段
    if isinstance(message.content, str):
        # 纯文本不需要特殊能力
        return set()

    for part in message.content:
        # 检查是否包含图片内容
        if isinstance(part, ImageURLPart) and ModelCapability("image_in") not in model_capabilities:
            missing_caps.add(ModelCapability("image_in"))

        # 检查是否包含思考内容
        if isinstance(part, ThinkPart) and ModelCapability("thinking") not in model_capabilities:
            missing_caps.add(ModelCapability("thinking"))

    return missing_caps


# ============================================================
# TODO: Stage 18+ 完整功能（参考官方）
# ============================================================
# 官方参考：kimi-cli-fork/src/kimi_cli/soul/message.py
#
# Stage 18+（图片支持）需要添加：
#
# - ImageURLPart 和 ThinkPart 的完整支持（✅ 已完成）
# - ModelCapability 检查机制（✅ 已完成）
# - LLMNotSupported 异常处理（在异常模块中）
# ============================================================

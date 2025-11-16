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

from typing import TYPE_CHECKING

import kosong
from kosong.message import Message, TextPart
from kosong.tooling import Toolset

from my_cli.soul.agent import Agent
from my_cli.soul.context import Context
from my_cli.soul.runtime import Runtime
from my_cli.wire.message import StepBegin

if TYPE_CHECKING:
    from my_cli.soul import wire_send  # 避免循环导入


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
        toolset: Toolset,  # ⭐ Stage 8：新增 toolset 参数
        context: Context | None = None,
    ):
        """
        初始化 KimiSoul

        Args:
            agent: Agent 实例（定义身份和能力）
            runtime: Runtime 实例（管理 ChatProvider）
            toolset: Toolset 实例（工具集）⭐ Stage 8
            context: Context 实例（管理对话历史，可选）
        """
        self._agent = agent
        self._runtime = runtime
        self._toolset = toolset  # ⭐ Stage 8
        self._context = context or Context()

    @property
    def name(self) -> str:
        """实现 Soul Protocol: name 属性"""
        return self._agent.name

    @property
    def model_name(self) -> str:
        """实现 Soul Protocol: model_name 属性"""
        # 从 Runtime 的 ChatProvider 获取模型名称
        return self._runtime.chat_provider.model_name

    async def run(self, user_input: str) -> None:
        """
        实现 Soul Protocol: run() 方法（Stage 8: Agent 循环版本）⭐

        流程：
        1. 添加用户消息到 Context
        2. 进入 Agent 循环：
           - 调用 kosong.step() 生成响应（可能包含工具调用）
           - 执行工具调用（kosong.step() 自动处理）
           - 将结果添加到 Context
           - 如果 LLM 调用了工具，继续循环
           - 如果 LLM 没调用工具，退出循环

        注意：
        - Stage 8 使用 kosong.step() API（支持工具调用）
        - 通过 on_message_part=wire_send 实时发送流式片段
        - 通过 on_tool_result=wire_send 实时发送工具结果
        - Agent 循环最多 20 步（防止无限循环）

        Args:
            user_input: 用户输入

        Raises:
            LLMNotSet: 如果 LLM 未配置
        """
        # 导入 wire_send（避免循环导入，放在函数内）
        from my_cli.soul import wire_send

        # 1. 添加用户消息
        user_msg = Message(role="user", content=user_input)
        await self._context.append_message(user_msg)

        # ============================================================
        # Stage 8: Agent 循环 + kosong.step() ⭐
        # ============================================================
        # 2. Agent 循环（最多 20 步）
        MAX_STEPS = 20
        step_no = 1

        while step_no <= MAX_STEPS:
            # 发送步骤开始事件
            wire_send(StepBegin(n=step_no))

            try:
                # 3. 调用 kosong.step()（一次 LLM 调用 + 工具执行）
                result = await kosong.step(
                    chat_provider=self._runtime.chat_provider,
                    system_prompt=self._agent.system_prompt,
                    toolset=self._toolset,  # ⭐ 传入工具集
                    history=self._context.get_messages(),
                    on_message_part=wire_send,  # ⭐ 实时发送流式片段
                    on_tool_result=wire_send,  # ⭐ 实时发送工具结果
                )

                # 4. 等待所有工具执行完成
                tool_results = await result.tool_results()

                # 5. 将 LLM 响应添加到 Context
                await self._context.append_message(result.message)

                # 6. 将工具结果转换为消息并添加到 Context
                # TODO: Stage 9+ 优化：实现 tool_result_to_message() 函数
                # 官方实现：kimi-cli-fork/src/kimi_cli/soul/message.py:tool_result_to_message()
                # 优化点：
                # - 错误消息格式化（添加 <system>ERROR:</system> 标签）
                # - ToolRuntimeError 特殊处理
                # - 空输出提示
                # Stage 8 简化版：直接创建 tool role 消息
                if tool_results:
                    for tr in tool_results:
                        # 创建 tool 角色消息
                        from kosong.message import TextPart

                        # 简化版：直接用 output 作为内容
                        if hasattr(tr.result, "output"):
                            output_str = str(tr.result.output)
                        else:
                            output_str = str(tr.result)

                        tool_msg = Message(
                            role="tool",
                            content=[TextPart(text=output_str)],
                            tool_call_id=tr.tool_call_id,
                        )
                        await self._context.append_message(tool_msg)

                # 7. 判断是否继续循环
                # 如果 LLM 没有调用工具，说明它认为任务完成了
                if not result.tool_calls:
                    break

                # 继续下一步
                step_no += 1

            except Exception as e:
                # 发生错误时通过 Wire 发送错误消息
                error_text = f"\n\n❌ LLM API 调用失败: {str(e)}\n"
                wire_send(TextPart(text=error_text))
                raise

        # 8. 如果达到最大步数，发送警告
        if step_no > MAX_STEPS:
            warning_text = f"\n\n⚠️ 达到最大步数限制 ({MAX_STEPS})，Agent 循环终止。\n"
            wire_send(TextPart(text=warning_text))

    @property
    def context(self) -> Context:
        """获取 Context（只读）"""
        return self._context

    @property
    def message_count(self) -> int:
        """获取消息数量"""
        return len(self._context)












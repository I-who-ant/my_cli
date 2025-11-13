"""
阶段 4-5：KimiSoul 类 - Soul Protocol 的具体实现

学习目标：
1. 理解如何实现 Soul Protocol
2. 理解如何使用 kosong.generate() 调用 LLM
3. 理解流式响应的处理

对应源码：kimi-cli-main/src/kimi_cli/soul/kimisoul.py
"""

from typing import AsyncIterator

import kosong
from kosong.message import Message

from my_cli.soul.agent import Agent
from my_cli.soul.context import Context
from my_cli.soul.runtime import Runtime


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
        context: Context | None = None,
    ):
        """
        初始化 KimiSoul

        Args:
            agent: Agent 实例（定义身份和能力）
            runtime: Runtime 实例（管理 ChatProvider）
            context: Context 实例（管理对话历史，可选）
        """
        self._agent = agent
        self._runtime = runtime
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

    async def run(self, user_input: str) -> AsyncIterator[str]:
        """
        实现 Soul Protocol: run() 方法

        流程：
        1. 添加用户消息到 Context
        2. 调用 kosong.generate() 生成响应
        3. 输出响应（Stage 4-5: 非流式，一次性返回完整内容）
        4. 保存 AI 响应到 Context

        注意：
        - Stage 4-5 使用非流式输出（简化实现）
        - Stage 6 将实现真正的流式输出（通过 Wire 机制和 on_message_part 回调）

        Args:
            user_input: 用户输入

        Yields:
            str: 响应文本（Stage 4-5 一次性返回完整内容）
        """
        # 1. 添加用户消息
        user_msg = Message(role="user", content=user_input)
        await self._context.append_message(user_msg)

        # ============================================================
        # Stage 4-5: 非流式实现（简化版）✅
        # ============================================================
        # 2. 调用 kosong.generate()
        try:
            result = await kosong.generate(
                chat_provider=self._runtime.chat_provider,
                system_prompt=self._agent.system_prompt,
                tools=[],  # Stage 4-5 暂无工具
                history=self._context.get_messages(),
            )

            # 3. 提取文本内容
            # result.message 已经是完整的消息（kosong.generate 内部已收集所有流式片段）
            message = result.message
            full_content = ""

            # 处理 message.content（可能是 str 或 list[ContentPart]）
            if isinstance(message.content, str):
                full_content = message.content
            elif isinstance(message.content, list):
                # 提取所有 TextPart
                for part in message.content:
                    if hasattr(part, "text") and part.text:
                        full_content += part.text

            # Stage 4-5: 一次性返回完整内容（非流式）
            if full_content:
                yield full_content

            # 4. 保存 AI 响应到 Context
            await self._context.append_message(result.message)

        except Exception as e:
            error_msg = f"\n\n❌ LLM API 调用失败: {str(e)}\n"
            yield error_msg
            raise

        # ============================================================
        # TODO: Stage 6 流式输出升级指南 🚀
        # ============================================================
        # 当前 Stage 4-5 的问题：
        # - kosong.generate() 等待完整响应后才返回
        # - yield 一次性返回全部内容，用户看不到逐字输出效果
        # - 无法实时显示 LLM 思考过程
        #
        # Stage 6 需要改为 Wire 机制：
        # 1. 使用 kosong.generate() 的 on_message_part 回调：
        #    result = await kosong.generate(
        #        chat_provider=self._runtime.chat_provider,
        #        system_prompt=self._agent.system_prompt,
        #        tools=[],
        #        history=self._context.get_messages(),
        #        on_message_part=wire_send,  # ⭐ 实时发送流式片段到 UI
        #    )
        #
        # 2. Wire 机制架构：
        #    - Soul 层通过 wire_send(StreamedMessagePart) 发送消息片段
        #    - Wire 是一个消息队列（asyncio.Queue）
        #    - UI 层通过 wire.ui_side.receive() 接收消息并渲染
        #    - 这样 Soul 和 UI 解耦，支持多种 UI（Shell/Print/TUI）
        #
        # 3. 需要新增的模块（Stage 6）：
        #    - my_cli/wire.py：Wire 类（消息队列）
        #    - my_cli/soul/__init__.py：添加 wire_send() 全局函数
        #    - 修改 run() 方法签名：改为 async def run(user_input: str) -> None
        #      （不再返回 AsyncIterator，改为通过 Wire 发送消息）
        #
        # 4. 官方 kimi-cli 的实现参考：
        #    - /home/seeback/PycharmProjects/Modelrecognize/kimi-cli-fork/src/kimi_cli/soul/kimisoul.py:223-230
        #    - /home/seeback/PycharmProjects/Modelrecognize/kimi-cli-fork/src/kimi_cli/wire/__init__.py
        #
        # 5. Stage 6 的 run() 方法伪代码：
        #    async def run(self, user_input: str) -> None:
        #        # 添加用户消息
        #        user_msg = Message(role="user", content=user_input)
        #        await self._context.append_message(user_msg)
        #
        #        # 调用 kosong.generate() 并通过 Wire 实时发送流式片段
        #        result = await kosong.generate(
        #            chat_provider=self._runtime.chat_provider,
        #            system_prompt=self._agent.system_prompt,
        #            tools=self._agent.toolset.tools,  # Stage 7 添加工具
        #            history=self._context.get_messages(),
        #            on_message_part=wire_send,  # ⭐ 关键：实时发送到 Wire
        #        )
        #
        #        # 保存完整响应到 Context
        #        await self._context.append_message(result.message)
        #
        # 6. UI 层接收流式输出（Shell UI 示例）：
        #    # 在 UI 层循环接收 Wire 消息
        #    while True:
        #        msg = await wire.ui_side.receive()
        #        if isinstance(msg, StreamedMessagePart):
        #            # 实时渲染文本片段（逐字显示效果）
        #            if hasattr(msg, "text") and msg.text:
        #                print(msg.text, end="", flush=True)
        #
        # 7. 参考官方实现文件：
        #    - Wire 定义：kimi-cli-fork/src/kimi_cli/wire/__init__.py
        #    - Soul 使用 Wire：kimi-cli-fork/src/kimi_cli/soul/kimisoul.py:223
        #    - Shell UI 接收 Wire：kimi-cli-fork/src/kimi_cli/ui/shell/__init__.py
        # ============================================================

    @property
    def context(self) -> Context:
        """获取 Context（只读）"""
        return self._context

    @property
    def message_count(self) -> int:
        """获取消息数量"""
        return len(self._context)

"""
SendDMail 工具 - 向过去发送消息

学习目标：
1. 理解如何创建自定义工具（CallableTool2）
2. 理解 SendDMail 工具的实现
3. 理解工具如何与 DenwaRenji 交互

对应源码：kimi-cli-fork/src/kimi_cli/tools/dmail/__init__.py

阶段演进：
- Stage 8-18：不需要 ✅
- Stage 20：实现 SendDMail 工具 ⭐
"""

from pathlib import Path
from typing import Any, override

from kosong.tooling import CallableTool2, ToolError, ToolReturnType

from my_cli.soul.denwarenji import DenwaRenji, DenwaRenjiError, DMail
from my_cli.tools.utils import load_desc

NAME = "SendDMail"


class SendDMail(CallableTool2[DMail]):
    """
    SendDMail 工具 ⭐ Stage 20

    允许 Agent 向过去的 Checkpoint 发送消息。

    工作流程：
    1. Agent 调用这个工具，传入 DMail 参数
    2. 调用 denwa_renji.send_dmail() 发送 D-Mail
    3. 返回 ToolError（因为成功的 SendDMail 永远不会返回）

    注意：
    - 成功的 SendDMail 会触发 BackToTheFuture 异常
    - 这个工具永远返回错误（因为正常情况下不会执行到 return）
    - 如果真的执行到 return，说明 D-Mail 没有成功发送

    对应源码：kimi-cli-fork/src/kimi_cli/tools/dmail/__init__.py
    """

    name: str = NAME
    description: str = load_desc(Path(__file__).parent / "dmail.md")
    params: type[DMail] = DMail

    def __init__(self, denwa_renji: DenwaRenji, **kwargs: Any) -> None:
        """
        初始化 SendDMail 工具

        Args:
            denwa_renji: DenwaRenji 实例（用于发送 D-Mail）
            **kwargs: 传递给父类的其他参数
        """
        super().__init__(**kwargs)
        self._denwa_renji = denwa_renji

    @override
    async def __call__(self, params: DMail) -> ToolReturnType:
        """
        执行 SendDMail 工具

        Args:
            params: DMail 参数（message + checkpoint_id）

        Returns:
            ToolError: 永远返回错误（因为成功会触发异常）

        流程：
        1. 调用 denwa_renji.send_dmail()
        2. 如果抛出 DenwaRenjiError，返回错误
        3. 如果成功（没有异常），返回"未成功发送"错误

        对应源码：kimi-cli-fork/src/kimi_cli/tools/dmail/__init__.py:22-39
        """
        try:
            self._denwa_renji.send_dmail(params)
        except DenwaRenjiError as e:
            return ToolError(
                output="",
                message=f"Failed to send D-Mail. Error: {str(e)}",
                brief="Failed to send D-Mail",
            )

        # 永远返回错误，因为成功的 SendDMail 会触发 BackToTheFuture 异常
        # 如果执行到这里，说明 D-Mail 没有成功发送（可能被其他工具的审批拒绝）
        return ToolError(
            output="",
            message=(
                "If you see this message, the D-Mail was not sent successfully. "
                "This may be because some other tool that needs approval was rejected."
            ),
            brief="D-Mail not sent",
        )

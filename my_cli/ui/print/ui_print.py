"""
阶段 3-5：Print UI 模式 + Soul 引擎集成

学习目标：
1. 实现最简单的 UI 模式（Stage 3）
2. 理解标准输入输出流（Stage 3）
3. 集成 Soul 引擎调用真实 LLM（Stage 4-5）⭐
4. 实现流式响应输出（Stage 4-5）⭐

对应源码：kimi-cli-fork/src/kimi_cli/ui/print/__init__.py (156 行)

阶段演进：
- Stage 3：基础 Print UI ✅
  * 从标准输入/命令参数读取命令
  * 输出到标准输出
  * 处理管道输入

- Stage 4-5：Soul 引擎集成 ✅
  * 调用 create_soul() 创建 Soul 实例
  * 使用 soul.run() 调用真实 LLM
  * 输出响应（Stage 4-5: 非流式）

- Stage 6：Wire 机制 + 真正的流式输出（待实现）
  * 使用 run_soul() 函数连接 Soul 和 UI
  * 使用 Wire 接收流式消息
  * 实时显示 LLM 响应（逐字输出）
  * 支持 input_format (text/stream-json)
  * 支持 output_format (text/stream-json)
  * 处理 SIGINT 信号（Ctrl+C）

- Stage 7：工具调用显示（待实现）
  * 显示工具调用过程
  * 显示工具返回结果

注意：
官方 kimi-cli 没有"模拟模式"！逻辑是：
- 有配置 → 调用真实 LLM
- 无配置 → 抛出 LLMNotSet 异常
"""

import sys
from pathlib import Path


class PrintUI:
    """Print UI - 最简单的用户界面.

    功能：
    1. 从标准输入/命令参数读取用户命令
    2. 输出到标准输出
    3. 适合批处理和脚本集成
    4. 调用 Soul 引擎与真实 LLM 对话 ⭐

    阶段演进：
    - Stage 3：基础输入输出 ✅
    - Stage 4-5：Soul 集成（非流式） ✅
    - Stage 6：Wire 机制（真正的流式输出）
    - Stage 7：工具调用显示

    对应源码：kimi-cli-fork/src/kimi_cli/ui/print/__init__.py:23-156
    """

    def __init__(
        self,
        verbose: bool = False,
        work_dir: Path | None = None,
    ) -> None:
        """初始化 Print UI.

        Args:
            verbose: 是否开启详细输出
            work_dir: 工作目录（调用 Soul 引擎时需要）
        """
        self.verbose = verbose
        self.work_dir = work_dir or Path.cwd()

    async def run(self, command: str | None = None) -> None:
        """运行 Print UI.

        Stage 3-5 实现：
        - 读取命令（从参数或标准输入）
        - 创建 Soul 实例
        - 调用 LLM 并输出响应

        Stage 6 实现：
        - 使用 run_soul() 函数
        - 通过 Wire 接收流式消息
        - 支持 input_format/output_format

        Args:
            command: 用户命令（如果为 None，则从标准输入读取）
        """
        if self.verbose:
            print("[Print UI] 启动 Print UI 模式", file=sys.stderr)

        # ============================================================
        # Stage 3：读取用户命令 ✅
        # ============================================================
        # 如果没有提供命令，尝试从标准输入读取
        if command is None:
            if self.verbose:
                print("[Print UI] 从标准输入读取命令...", file=sys.stderr)

            # 检查是否有管道输入
            if not sys.stdin.isatty():
                # 从管道读取（例如：echo "hello" | python cli.py）
                command = sys.stdin.read().strip()
                if self.verbose:
                    print(f"[Print UI] 从管道读取到命令: {command}", file=sys.stderr)
            else:
                # 没有管道输入，也没有提供 -c 参数
                print("❌ 错误：请使用 -c 参数提供命令，或通过管道输入", file=sys.stderr)
                print("", file=sys.stderr)
                print("示例：", file=sys.stderr)
                print("  python -m my_cli.cli -c \"你的命令\"", file=sys.stderr)
                print("  echo \"你的命令\" | python -m my_cli.cli --ui print", file=sys.stderr)
                return

        # 验证命令
        if not command:
            print("❌ 错误：命令不能为空", file=sys.stderr)
            return

        if self.verbose:
            print(f"[Print UI] 处理命令: {command}", file=sys.stderr)

        # ============================================================
        # Stage 4-5：调用真实 LLM ✅
        # ============================================================
        print("=" * 60)
        print("My CLI - Print UI 模式")
        print("=" * 60)
        print()

        try:
            # 导入 Soul 引擎
            from my_cli.soul import create_soul

            if self.verbose:
                print("[Print UI] 创建 Soul 引擎实例（kosong 框架）", file=sys.stderr)

            # 创建 Soul 实例
            # model_name=None 表示使用配置文件中的 default_model
            # 也可以指定：model_name="kimi-coding" 切换到其他模型
            soul = create_soul(
                work_dir=self.work_dir,
            )

            if self.verbose:
                print("[Print UI] Soul 引擎创建成功", file=sys.stderr)
                print(f"[Print UI] Agent 名称: {soul.name}", file=sys.stderr)
                print(f"[Print UI] 使用模型: {soul.model_name}", file=sys.stderr)

            # 打印用户输入
            print(f"用户命令: {command}")
            print()
            print("AI 响应:")
            print("-" * 60)

            # Stage 4-5：非流式输出（一次性返回完整内容）
            # Stage 6：使用 Wire 机制实现真正的流式输出
            async for chunk in soul.run(command):
                print(chunk, end="", flush=True)

            print()
            print("-" * 60)
            print()
            print("✅ LLM 调用成功！")

            if self.verbose:
                print(f"[Print UI] 消息数量: {soul.message_count}", file=sys.stderr)

        except ImportError as e:
            print()
            print(f"❌ 错误：无法导入依赖库")
            print(f"   详情：{str(e)}")
            print()
            print("请安装依赖：")
            print("  pip install kosong")
            print()

        except ValueError as e:
            # 配置文件错误
            print()
            print(f"❌ 错误：配置文件无效")
            print(f"   详情：{str(e)}")
            print()
            print("请检查配置文件：")
            print("  .mycli_config.json")
            print()
            print("配置模板：")
            print("  {")
            print('    "default_model": "moonshot-k2",')
            print('    "providers": { ... },')
            print('    "models": { ... }')
            print("  }")
            print()

        except Exception as e:
            print()
            print(f"❌ 错误：LLM 调用失败")
            print(f"   详情：{str(e)}")
            print()
            print("可能的原因：")
            print("  1. API Key 未设置或无效")
            print("  2. 网络连接问题")
            print("  3. API 配额不足")
            print("  4. 配置文件不存在或格式错误")
            print()
            print("请检查：")
            print("  - .mycli_config.json 配置文件")
            print("  - 环境变量（KIMI_API_KEY / KIMI_BASE_URL）")
            print("  - 网络连接是否正常")
            print()

        # ============================================================
        # TODO: Stage 6 使用 Wire 机制（参考官方）
        # ============================================================
        # 官方参考：kimi-cli-fork/src/kimi_cli/ui/print/__init__.py:46-156
        #
        # Stage 6 需要改为：
        #
        # async def run(self, command: str | None = None) -> bool:
        #     # 1. 创建 cancel_event（处理 Ctrl+C）
        #     cancel_event = asyncio.Event()
        #
        #     def _handler():
        #         logger.debug("SIGINT received.")
        #         cancel_event.set()
        #
        #     loop = asyncio.get_running_loop()
        #     remove_sigint = install_sigint_handler(loop, _handler)
        #
        #     # 2. 读取命令（支持 stdin 管道）
        #     if command is None and not sys.stdin.isatty():
        #         command = sys.stdin.read().strip()
        #
        #     try:
        #         # 3. 使用 run_soul() 连接 Soul 和 UI
        #         await run_soul(
        #             self.soul,
        #             command,
        #             visualize_fn=self._visualize_text,  # UI 渲染函数
        #             cancel_event=cancel_event,
        #         )
        #     except LLMNotSet:
        #         print("LLM not set")
        #     except ChatProviderError as e:
        #         print(f"LLM provider error: {e}")
        #     except MaxStepsReached as e:
        #         print(f"Max steps reached: {e.n_steps}")
        #     except RunCancelled:
        #         print("Interrupted by user")
        #     finally:
        #         remove_sigint()
        #
        # async def _visualize_text(self, wire: WireUISide):
        #     """从 Wire 接收消息并渲染"""
        #     while True:
        #         msg = await wire.receive()
        #         print(msg)  # 实时显示流式片段
        #         if isinstance(msg, StepInterrupted):
        #             break
        #
        # 完整官方实现：
        # - kimi-cli-fork/src/kimi_cli/ui/print/__init__.py:46-156
        # - 支持 input_format: "text" | "stream-json"
        # - 支持 output_format: "text" | "stream-json"
        # - 支持 context_file（保存对话历史）
        # ============================================================


# ============================================================
# Stage 3-5：示例用法
# ============================================================
async def example_usage():
    """示例：如何使用 PrintUI."""
    ui = PrintUI(verbose=True)

    # 方式 1：直接提供命令
    await ui.run("你好，介绍一下你自己")

    # 方式 2：从标准输入读取
    # await ui.run(None)


if __name__ == "__main__":
    import asyncio

    # 运行示例
    asyncio.run(example_usage())

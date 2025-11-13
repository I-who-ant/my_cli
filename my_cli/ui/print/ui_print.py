"""
阶段 3-5：Print UI 模式 + Soul 引擎集成

学习目标：
1. 实现最简单的 UI 模式（Stage 3）
2. 理解标准输入输出流（Stage 3）
3. 集成 Soul 引擎调用真实 LLM（Stage 4-5）⭐
4. 实现流式响应输出（Stage 4-5）⭐

对应源码：kimi-cli-main/src/kimi_cli/ui/print/__init__.py (154 行)
"""

import sys
from pathlib import Path


class PrintUI:
    """Print UI - 最简单的用户界面.

    功能：
    1. 从标准输入读取用户命令
    2. 输出到标准输出
    3. 适合批处理和脚本集成
    4. 调用 Soul 引擎与真实 LLM 对话（Stage 4-5 新增）⭐

    原项目的 Print UI（PrintApp 类）做了很多事：
    - 支持两种输入格式（text, stream-json）
    - 支持两种输出格式（text, stream-json）
    - 集成 Soul 引擎执行 LLM 调用
    - 处理 SIGINT 信号（Ctrl+C）
    - 实时流式输出 LLM 响应

    阶段演进：
    - Stage 3：接收输入 + 模拟响应
    - Stage 4-5：集成 Soul 引擎 + 真实 LLM 调用 ⭐
    - Stage 7：添加工具调用（Function Calling）
    """

    def __init__(
        self,
        verbose: bool = False,
        work_dir: Path | None = None,
        use_real_llm: bool = False,
    ) -> None:
        """初始化 Print UI.

        Args:
            verbose: 是否开启详细输出
            work_dir: 工作目录（调用 Soul 引擎时需要）
            use_real_llm: 是否使用真实 LLM（False=模拟，True=调用API）
        """
        self.verbose = verbose
        self.work_dir = work_dir or Path.cwd()
        self.use_real_llm = use_real_llm

    async def run(self, command: str | None = None) -> None:
        """运行 Print UI.

        Args:
            command: 用户命令（如果为 None，则从标准输入读取）
        """
        if self.verbose:
            print("[Print UI] 启动 Print UI 模式", file=sys.stderr)

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
                print("  python cli.py -c \"你的命令\"", file=sys.stderr)
                print("  echo \"你的命令\" | python cli.py --ui print", file=sys.stderr)
                return

        # 验证命令
        if not command:
            print("❌ 错误：命令不能为空", file=sys.stderr)
            return

        if self.verbose:
            print(f"[Print UI] 处理命令: {command}", file=sys.stderr)

        # ============================================================
        # 根据配置选择：模拟模式 vs 真实LLM
        # ============================================================
        print("=" * 60)
        print("My CLI - Print UI 模式")
        print("=" * 60)
        print()

        if self.use_real_llm:
            # ============================================================
            # 阶段 4-5：调用真实 LLM ⭐
            # ============================================================
            await self._run_with_real_llm(command)
        else:
            # ============================================================
            # 阶段 3：模拟处理流程（默认）
            # ============================================================
            await self._run_with_mock(command)

    async def _run_with_mock(self, command: str) -> None:
        """
        模拟模式：不调用真实 LLM，只输出模拟响应

        这是 Stage 3 的实现，用于：
        1. 测试 UI 流程
        2. 在没有 API Key 时演示
        3. 开发调试
        """
        print(f"用户命令: {command}")
        print()
        print("AI 响应（模拟）:")
        print("-" * 60)
        print(f"你说：{command}")
        print()
        print("这是一个模拟的 AI 响应。")
        print()
        print("💡 提示：要使用真实 LLM，请：")
        print("  1. 安装 openai 库：pip install openai")
        print("  2. 设置环境变量：")
        print("     export OPENAI_API_KEY='your-api-key'")
        print("     export OPENAI_BASE_URL='https://api.moonshot.cn/v1'  # 可选，使用 Moonshot")
        print("  3. 在 app.py 中设置 use_real_llm=True")
        print()
        print("在后续阶段，还会添加：")
        print("  - 阶段 7：工具系统（Shell/ReadFile/WriteFile）")
        print("  - 阶段 8：Function Calling")
        print("-" * 60)
        print()
        print("✅ Print UI 模拟模式运行成功！")

    async def _run_with_real_llm(self, command: str) -> None:
        """
        真实模式：调用 Soul 引擎和真实 LLM

        这是 Stage 4-5 的实现：
        1. 创建 Soul 实例（使用简化版 kosong 框架）
        2. 流式调用 LLM
        3. 实时输出响应
        """
        try:
            # 导入 Soul 引擎（使用真正的 kosong 框架）
            from my_cli.soul import create_soul

            if self.verbose:
                print("[Print UI] 创建 Soul 引擎实例（kosong 框架）", file=sys.stderr)

            # 创建 Soul 实例（使用便捷工厂函数）
            # Stage 4-5: 使用配置文件系统，model_name 对应配置文件中的 model key
            soul = create_soul(
                work_dir=self.work_dir,
                # model_name=None 表示使用配置文件中的 default_model
                # 也可以指定：model_name="kimi-coding" 切换到 Kimi API
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

            # 流式输出 LLM 响应
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

        except Exception as e:
            print()
            print(f"❌ 错误：LLM 调用失败")
            print(f"   详情：{str(e)}")
            print()
            print("可能的原因：")
            print("  1. API Key 未设置或无效")
            print("  2. 网络连接问题")
            print("  3. API 配额不足")
            print()
            print("请检查：")
            print("  - MOONSHOT_API_KEY 环境变量（或 OPENAI_API_KEY）")
            print("  - 网络连接是否正常")
            print()


# 示例：如何使用这个 PrintUI 类
async def example_usage():
    """示例：如何使用 PrintUI."""
    ui = PrintUI(verbose=True)

    # 方式 1：直接提供命令
    await ui.run("你好，世界！")

    # 方式 2：从标准输入读取
    # await ui.run(None)


if __name__ == "__main__":
    import asyncio

    # 运行示例
    asyncio.run(example_usage())

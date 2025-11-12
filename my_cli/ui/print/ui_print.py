"""
阶段 3：Print UI 模式

学习目标：
1. 实现最简单的 UI 模式
2. 理解标准输入输出流
3. 理解异步消息处理

对应源码：kimi-cli-main/src/kimi_cli/ui/print/__init__.py (154 行)
"""

import sys


class PrintUI:
    """Print UI - 最简单的用户界面.

    功能：
    1. 从标准输入读取用户命令
    2. 输出到标准输出
    3. 适合批处理和脚本集成

    原项目的 Print UI（PrintApp 类）做了很多事：
    - 支持两种输入格式（text, stream-json）
    - 支持两种输出格式（text, stream-json）
    - 集成 Soul 引擎执行 LLM 调用
    - 处理 SIGINT 信号（Ctrl+C）
    - 实时流式输出 LLM 响应

    我们阶段 3 只保留最核心的：
    - 接收用户输入
    - 打印响应（模拟）
    """

    def __init__(self, verbose: bool = False) -> None:
        """初始化 Print UI.

        Args:
            verbose: 是否开启详细输出
        """
        self.verbose = verbose

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
        # 阶段 3：模拟处理流程
        # ============================================================
        # 在后续阶段中，这里会：
        # 1. 创建 Wire 消息队列
        # 2. 启动 Soul 引擎
        # 3. 调用 LLM API
        # 4. 流式输出响应
        #
        # 现在我们只是模拟一个简单的响应
        # ============================================================

        print("=" * 60)
        print("My CLI - Print UI 模式")
        print("=" * 60)
        print()
        print(f"用户命令: {command}")
        print()
        print("AI 响应（模拟）:")
        print("-" * 60)
        print(f"你说：{command}")
        print()
        print("这是一个模拟的 AI 响应。")
        print()
        print("在后续阶段，这里会接入真实的 LLM API：")
        print("  - 阶段 4：实现 Wire 协议层（Soul ↔ UI 通信）")
        print("  - 阶段 5：实现 Soul 核心引擎（LLM 调用）")
        print("  - 阶段 7：实现工具系统（Function Calling）")
        print("-" * 60)
        print()
        print("✅ Print UI 模式运行成功！")


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

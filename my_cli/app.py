"""
阶段 2：应用层框架

学习目标：
1. 创建应用类（MyCLI）
2. 实现配置管理
3. 理解依赖注入模式

对应源码：kimi-cli-main/src/kimi_cli/app.py (265 行)
"""

from pathlib import Path
from typing import Any


class MyCLI:
    """My CLI 应用类 - 管理应用的核心状态和配置.

    这是一个简化版的应用层，负责：
    1. 管理工作目录
    2. 存储用户配置
    3. 提供统一的 UI 入口
    """

    def __init__(
        self,
        work_dir: Path,
        verbose: bool = False,
    ) -> None:
        """初始化 MyCLI 实例.

        Args:
            work_dir: 工作目录
            verbose: 是否开启详细输出
        """
        self.work_dir = work_dir
        self.verbose = verbose

    @staticmethod
    async def create(
        work_dir: Path,
        verbose: bool = False,
    ) -> "MyCLI":
        """异步工厂方法 - 创建 MyCLI 实例.

        为什么使用工厂方法而不是 __init__？
        - __init__ 不能是异步的
        - create 可以执行异步初始化任务（如加载配置、连接 LLM）

        对应源码：kimi-cli-main/src/kimi_cli/app.py:24
        原项目的 create 方法做了很多事：
        - 加载配置文件
        - 创建 LLM 客户端
        - 加载 Agent 规范
        - 初始化 MCP 工具
        - 创建 Soul 引擎

        我们阶段 2 只保留最基础的：
        - 验证工作目录
        - 创建应用实例
        """
        # 验证工作目录是否存在
        if not work_dir.exists():
            raise FileNotFoundError(f"工作目录不存在: {work_dir}")

        # 创建实例
        instance = MyCLI(
            work_dir=work_dir,
            verbose=verbose,
        )

        if verbose:
            print(f"[应用层] MyCLI 实例创建成功")
            print(f"[应用层] 工作目录: {work_dir}")

        return instance

    async def run_print_mode(
        self,
        command: str | None,
    ) -> None:
        """运行 Print UI 模式.

        Print 模式是最简单的 UI：
        - 从标准输入读取命令
        - 输出到标准输出
        - 适合批处理和脚本集成

        对应源码：kimi-cli-main/src/kimi_cli/app.py:167

        Args:
            command: 用户命令（如果为 None，则从标准输入读取）
        """
        # 导入 UI 模块（延迟导入，避免循环依赖）
        from my_cli.ui.print.ui_print import PrintUI

        if self.verbose:
            print("[应用层] 启动 Print UI 模式")

        # 创建 PrintUI 实例
        ui = PrintUI(verbose=self.verbose)

        # 运行 UI
        await ui.run(command)

    async def run_shell_mode(
        self,
        command: str | None,
    ) -> None:
        """运行 Shell UI 模式.

        Shell 模式是交互式 UI：
        - 使用 Rich 库渲染漂亮的终端输出
        - 支持键盘快捷键
        - 实时显示 LLM 响应

        对应源码：kimi-cli-main/src/kimi_cli/app.py:107

        Args:
            command: 初始命令（可选）
        """
        if self.verbose:
            print("[应用层] Shell UI 模式暂未实现")
            print("[应用层] 请使用 Print 模式：--ui print")

        # 阶段 6 再实现 Shell UI
        print("❌ Shell 模式将在阶段 6 实现")
        print("提示：当前请使用 `--ui print` 运行")
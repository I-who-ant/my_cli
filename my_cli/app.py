"""
阶段 2：应用层框架

学习目标：
1. 创建应用类（MyCLI）
2. 实现配置管理
3. 理解依赖注入模式

对应源码：kimi-cli-main/src/kimi_cli/app.py (265 行)

阶段演进：
- Stage 2-3：基础应用框架 ✅
  * MyCLI 类定义
  * 工作目录管理
  * run_print_mode() / run_shell_mode() 入口

- Stage 4-5：Soul 引擎集成 ✅
  * 集成 create_soul() 工厂函数
  * 移除模拟模式（官方没有这个概念）
  * 直接调用真实 LLM API

- Stage 6：完整应用层（待实现）
  * Session 管理（会话持久化）
  * Config 管理（配置加载）
  * 异步 create() 工厂方法
  * 支持多种 UI 模式（shell/print/acp/wire）

- Stage 7+：高级特性（待实现）
  * MCP 工具配置
  * Approval 系统
  * Thinking 模式
"""

from pathlib import Path


class MyCLI:
    """My CLI 应用类 - 管理应用的核心状态和配置.

    这是一个简化版的应用层，负责：
    1. 管理工作目录
    2. 存储用户配置
    3. 提供统一的 UI 入口

    阶段演进：
    - Stage 2-3：基础框架 ✅
    - Stage 4-5：Soul 集成 ✅
    - Stage 6+：完整应用层（Session/Config/多UI模式）
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

        Stage 2-5 实现：
        - 验证工作目录
        - 创建应用实例

        Stage 6+ 补充：
        - 加载配置文件
        - 创建 Session
        - ��建 LLM 客户端
        - 加载 Agent 规范
        - 初始化 MCP 工具
        - 创建 Soul 引擎

        Args:
            work_dir: 工作目录
            verbose: 是否开启详细输出

        Returns:
            MyCLI 实例

        Raises:
            FileNotFoundError: 工作目录不存在
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

        # ============================================================
        # TODO: Stage 6+ 完整实现（参考官方）
        # ============================================================
        # ��方参考：kimi-cli-fork/src/kimi_cli/app.py:26-121
        #
        # @staticmethod
        # async def create(
        #     work_dir: Path,
        #     verbose: bool = False,
        #     session: Session | None = None,  # Stage 6+
        #     config_file: Path | None = None,  # Stage 6+
        #     model_name: str | None = None,    # Stage 6+
        #     yolo: bool = False,               # Stage 8+
        #     thinking: bool = False,           # Stage 8+
        #     mcp_configs: list[dict] | None = None,  # Stage 7+
        #     agent_file: Path | None = None,   # Stage 7+
        # ) -> "MyCLI":
        #     """创建 MyCLI 实例（完整版）"""
        #
        #     # 1. 创建或恢复 Session
        #     if session is None:
        #         session = Session.create(work_dir) or Session.continue_(work_dir)
        #
        #     # 2. 加载配置文件
        #     config = load_config(config_file)
        #
        #     # 3. 创建 Soul 引擎
        #     soul = await create_soul(
        #         work_dir=work_dir,
        #         model_name=model_name,
        #         config_file=config_file,
        #         session=session,
        #         yolo=yolo,
        #         thinking=thinking,
        #         mcp_configs=mcp_configs,
        #     )
        #
        #     # 4. 创建应用实例
        #     instance = MyCLI(
        #         work_dir=work_dir,
        #         verbose=verbose,
        #         soul=soul,
        #         session=session,
        #     )
        #
        #     return instance
        # ============================================================

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

        Stage 2-3 实现：
        - 创建 PrintUI 实例（模拟模式）

        Stage 4-5 实现：✅
        - 创建 PrintUI 实例（真实 LLM）
        - 通过 create_soul() 创建 Soul 引擎
        - 调用 soul.run() 获取 LLM 响应

        Stage 6+ 实现：
        - 使用 PrintApp（官方实现）
        - 集成 Wire 机制
        - 支持 input_format (text/stream-json)
        - 支持 output_format (text/stream-json)

        Args:
            command: 用户命令（如果为 None，则从标准输入读取）
        """
        # 导入 UI 模块（延迟导入，避免循环依赖）
        from my_cli.ui.print.ui_print import PrintUI

        if self.verbose:
            print("[应用层] 启动 Print UI 模式")

        # ============================================================
        # Stage 4-5：直接使用真实 LLM ✅
        # ============================================================
        # 不再需要 use_real_llm 参数！
        # 官方代码逻辑：
        # - 有配置 → 调用真实 LLM
        # - 无配置 → 抛出 LLMNotSet 异常
        ui = PrintUI(
            verbose=self.verbose,
            work_dir=self.work_dir,
        )

        # 运行 UI
        await ui.run(command)

        # ============================================================
        # TODO: Stage 6+ 使用官方 PrintApp
        # ============================================================
        # 官方参考：kimi-cli-fork/src/kimi_cli/ui/print/__init__.py
        #
        # from kimi_cli.ui.print import PrintApp
        #
        # app = PrintApp(
        #     soul=self.soul,
        #     input_format="text",   # or "stream-json"
        #     output_format="text",  # or "stream-json"
        #     context_file=self.session.history_file,
        # )
        #
        # await app.run(command)
        # ============================================================

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

        Stage 2-5：未实现
        Stage 6：实现 Shell UI + Wire 机制
        Stage 7：集成工具调用显示

        Args:
            command: 初始命令（可选）
        """
        if self.verbose:
            print("[应用层] Shell UI 模式暂未实现")
            print("[应用层] 请使用 Print 模式：--ui print")

        # 阶段 6 再实现 Shell UI
        print("❌ Shell 模式将在阶段 6 实现")
        print("提示：当前请使用 `--ui print` 运行")

        # ============================================================
        # TODO: Stage 6 实现 Shell UI
        # ============================================================
        # 官方参考：kimi-cli-fork/src/kimi_cli/ui/shell/__init__.py
        #
        # from kimi_cli.ui.shell import ShellApp
        #
        # app = ShellApp(
        #     soul=self.soul,
        #     work_dir=self.work_dir,
        #     verbose=self.verbose,
        # )
        #
        # await app.run(command)
        # ============================================================

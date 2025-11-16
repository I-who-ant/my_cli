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
        from my_cli.ui.print import PrintUI

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
        """运行 Shell UI 模式 ⭐ Stage 11 模块化架构.

        Shell 模式是交互式 UI：
        - 多轮对话（复用同一个 Soul 实例）
        - Context 自动保持
        - 优雅退出处理（Ctrl+C, Ctrl+D, exit）
        - 实时流式输出

        Stage 11 模块化重构：
        - ✅ console.py    - Console 单例 + 主题配置
        - ✅ metacmd.py    - 斜杠命令系统（装饰器注册）
        - ✅ prompt.py     - CustomPromptSession（输入处理）
        - ✅ visualize.py  - UI Loop 渲染逻辑
        - ✅ __init__.py   - ShellApp 主入口（协调器）

        对应源码：kimi-cli-fork/src/kimi_cli/ui/shell/__init__.py

        阶段演进：
        - Stage 9：Shell 交互模式（基础版）✅
        - Stage 10：UI 美化和增强（enhanced.py.md.backup）✅
        - Stage 11：模块化重构（按官方架构分层）✅

        Args:
            command: 初始命令（可选，如果提供则执行单命令模式）
        """
        # 导入 UI 模块（延迟导入，避免循环依赖）
        # Stage 11：使用模块化 ShellApp ⭐
        try:
            from my_cli.ui.shell import ShellApp

            app = ShellApp(
                verbose=self.verbose,
                work_dir=self.work_dir,
            )
            if self.verbose:
                print("[应用层] 启动 Modular ShellApp (Stage 11)")

            # 运行 ShellApp
            await app.run(command)

        except ImportError as e:
            # 如果模块化架构导入失败，回退到 Stage 10 增强版
            if self.verbose:
                print(f"[应用层] 模块化架构导入失败: {e}")
                print("[应用层] 回退到 Enhanced Shell UI (Stage 10)")

            try:
                from my_cli.ui.shell.enhanced import EnhancedShellUI

                ui = EnhancedShellUI(
                    verbose=self.verbose,
                    work_dir=self.work_dir,
                )
                await ui.run(command)
            except ImportError:
                # 最终回退到基础版 ShellUI
                if self.verbose:
                    print("[应用层] 回退到 Basic Shell UI (Stage 9)")
                # 此处已无法回退，因为 __init__.py 已被重写
                raise

        # ============================================================
        # Stage 11 完成！✅ 已实现官方模块化架构
        # ============================================================
        # 当前实现：
        # - console.py: Console 单例 + 主题配置
        # - metacmd.py: 斜杠命令系统（装饰器注册）
        # - prompt.py: CustomPromptSession（命令历史）
        # - visualize.py: UI Loop 渲染逻辑
        # - __init__.py: ShellApp 主入口
        #
        # TODO Stage 12+：
        # - keyboard.py: 键盘事件监听
        # - debug.py: 调试功能
        # - replay.py: 历史回放
        # - setup.py: 配置向导
        # - update.py: 自动更新
        # - prompt.py 增强：自动补全、状态栏
        # - metacmd.py 增强：@meta_command 装饰器
        # ============================================================

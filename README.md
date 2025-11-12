# My CLI - 从零开始构建你自己的 AI Agent

## 项目简介

这是一个**循序渐进的学习项目**，通过模仿 Kimi CLI 的架构，从基础到高级，一步步构建属于你自己的 AI Agent CLI 工具。

## 为什么需要这个项目？

直接阅读 Kimi CLI 的完整源码太复杂了！这个项目让你：

1. **从最简单的 CLI 入口开始** - 只用 50 行代码就能跑起来
2. **逐步添加功能模块** - 每个阶段都有明确的学习目标
3. **对照原项目理解** - 每个阶段都标注了对应的 `kimi-cli-main/src/kimi_cli` 源码位置
4. **可运行的代码** - 每个阶段都能独立运行，看到效果

## 学习路线图

### 阶段 0：项目初始化（当前阶段）
- [x] 创建基础目录结构
- [x] 了解 7 层架构的目录布局

```
my_cli/
├── cli.py          # CLI 入口层
├── app.py          # 应用层
├── ui/             # UI 层（4 种模式）
├── soul/           # Soul 核心引擎层
├── wire/           # Wire 协议层
├── tools/          # 工具层
├── deps/           # 依赖层（LLM/MCP）
├── prompts/        # Prompt 模板
└── agents/         # Agent 配置
```

### 阶段 1：最简 CLI 入口（~50 行代码）
**学习目标**：
- 使用 Click 框架创建命令行工具
- 理解 CLI 参数解析
- 实现一个能打印 "Hello, My CLI!" 的程序

**对应源码**：`kimi-cli-main/src/kimi_cli/cli.py` (266 行)

**核心概念**：
- `@click.command()` 装饰器
- `@click.option()` 参数定义
- `asyncio.run()` 异步入口

### 阶段 2：应用层框架（~100 行代码）
**学习目标**：
- 创建 MyCLI 应用类
- 实现配置管理
- 添加日志系统

**对应源码**：`kimi-cli-main/src/kimi_cli/app.py` (265 行)

**核心概念**：
- 应用状态管理
- 依赖注入模式
- 异步初始化

### 阶段 3：Print UI 模式（~150 行代码）
**学习目标**：
- 实现最简单的 UI 模式
- 理解输入输出流
- 添加 JSON 格式支持

**对应源码**：`kimi-cli-main/src/kimi_cli/ui/print/ui_print.py` (154 行)

**核心概念**：
- 标准输入输出
- JSON Lines 格式
- 流式数据处理

### 阶段 4：Wire 协议层（~200 行代码）
**学习目标**：
- 理解 Soul ↔ UI 通信机制
- 使用 asyncio.Queue 实现消息队列
- 定义 Wire Message 格式

**对应源码**：`kimi-cli-main/src/kimi_cli/wire/` (多个文件)

**核心概念**：
- 异步消息队列
- 生产者-消费者模式
- Wire Message 协议

### 阶段 5：Soul 核心引擎（~300 行代码）
**学习目标**：
- 实现 Soul 主循环
- 添加工具调用机制
- 集成 LLM API

**对应源码**：`kimi-cli-main/src/kimi_cli/soul/soul.py` (873 行)

**核心概念**：
- 状态机模式
- Function Calling
- 流式响应处理

### 阶段 6：Shell UI 模式（~400 行代码）
**学习目标**：
- 使用 Rich 库创建交互式终端
- 实现 PromptToolkit 输入
- 添加键盘快捷键支持

**对应源码**：`kimi-cli-main/src/kimi_cli/ui/shell/` (多个文件)

**核心概念**：
- Rich 终端渲染
- PromptToolkit 交互
- 异步 UI 更新

### 阶段 7：工具系统（~250 行代码）
**学习目标**：
- 实现工具注册机制
- 添加工具审批流程
- 支持 MCP 工具

**对应源码**：`kimi-cli-main/src/kimi_cli/tools/` (多个文件)

**核心概念**：
- 插件系统
- 审批机制
- MCP 协议

### 阶段 8：ACP 协议（~300 行代码）
**学习目标**：
- 实现 Agent Communication Protocol
- 支持远程 Agent 交互
- 添加审批系统

**对应源码**：`kimi-cli-main/src/kimi_cli/ui/acp/` (多个文件)

**核心概念**：
- JSON-RPC 2.0
- 双向通信
- 审批流程

### 阶段 9：Wire UI 模式（~250 行代码）
**学习目标**：
- 实现 JSON-RPC 服务器
- 支持多客户端连接
- 添加状态同步

**对应源码**：`kimi-cli-main/src/kimi_cli/ui/wire/ui_wire.py` (341 行)

**核心概念**：
- JSON-RPC 服务
- WebSocket 通信
- 状态广播

## 当前进度

- [x] **阶段 0**：项目初始化
- [ ] **阶段 1**：最简 CLI 入口
- [ ] **阶段 2**：应用层框架
- [ ] **阶段 3**：Print UI 模式
- [ ] **阶段 4**：Wire 协议层
- [ ] **阶段 5**：Soul 核心引擎
- [ ] **阶段 6**：Shell UI 模式
- [ ] **阶段 7**：工具系统
- [ ] **阶段 8**：ACP 协议
- [ ] **阶段 9**：Wire UI 模式

## 如何开始？

### 1. 进入项目目录
```bash
cd kimi-cli-main/imitate-src/my_cli
```

### 2. 跟随阶段文档学习
每个阶段都有对应的文档：
- `docs/stage-01-cli-entry.md` - 阶段 1 详细文档
- `docs/stage-02-app-layer.md` - 阶段 2 详细文档
- ... 以此类推

### 3. 对比源码理解
在实现每个阶段时，对照 `kimi-cli-main/src/kimi_cli/` 源码：
- 看看原项目是如何实现的
- 理解为什么要这样设计
- 尝试自己的改进

### 4. 运行测试
每个阶段都能独立运行：
```bash
# 阶段 1
python cli.py --help

# 阶段 3
echo "Hello AI!" | python cli.py --ui print

# 阶段 6
python cli.py --ui shell
```

## 学习建议

1. **不要跳阶段**：每个阶段都有前置依赖，循序渐进最重要
2. **动手实践**：光看不练假把式，必须自己敲代码
3. **理解原理**：不要死记硬背，理解为什么要这样设计
4. **对比源码**：看看 Kimi CLI 的实现，学习最佳实践
5. **做笔记**：记录你的理解和疑问

## 参考文档

- **完整架构文档**：`kimi-cli-main/src/kimi_cli/Kimi_CLI完整架构与数据流总览.md`
- **AI 助手知识库**：`kimi-cli-main/docs/CLAUDE.md`
- **UI 模块详解**：
  - `kimi-cli-learn/阶段4_协议与标准/09_ACP协议/ui_shell模块实现详解.md`
  - `kimi-cli-learn/阶段4_协议与标准/09_ACP协议/ui_print模块实现详解.md`
  - `kimi-cli-learn/阶段4_协议与标准/09_ACP协议/ui_wire模块实现详解.md`

## 技术栈

- **CLI 框架**：Click
- **异步编程**：asyncio
- **终端 UI**：Rich, PromptToolkit
- **JSON-RPC**：自实现 JSON-RPC 2.0
- **LLM API**：OpenAI Compatible API
- **配置管理**：YAML
- **日志**：Python logging

## 常见问题

### Q1: 我需要什么基础？
- Python 基础（至少会写函数和类）
- 了解异步编程（async/await）
- 会用命令行工具

### Q2: 每个阶段需要多长时间？
- 阶段 1-3：每个 2-3 小时
- 阶段 4-6：每个 4-6 小时
- 阶段 7-9：每个 6-8 小时

### Q3: 卡住了怎么办？
1. 查看对应的源码实现
2. 阅读完整架构文档
3. 检查日志输出
4. 问 AI 助手（Claude/ChatGPT）

### Q4: 我可以修改设计吗？
当然可以！这是你自己的项目，鼓励创新和改进！

## 贡献

这是一个学习项目，欢迎：
- 提交你的实现代码
- 分享学习笔记
- 提出改进建议
- 报告问题

## 许可证

MIT License - 自由使用和修改

---

**现在，让我们从阶段 1 开始吧！** 🚀
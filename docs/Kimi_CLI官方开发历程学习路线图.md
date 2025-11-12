# Kimi CLI 官方开发历程学习路线图

> 基于官方仓库 497 个 commits 的真实开发历程整理
> 时间跨度：2025-09-10 至 2025-11-10（2个月）
> 仓库地址：https://github.com/MoonshotAI/kimi-cli

---

## 📋 学习路线概览

```
阶段1: 骨架搭建      (Sep 10, 10 commits)   → 可运行的最小框架
阶段2: 核心功能      (Sep 11-12, 15 commits) → Shell工具、消息历史、-c参数
阶段3: UI增强        (Sep 13-14, 20 commits) → 工具调用可视化、Session管理
阶段4: 工具系统      (Sep 16-18, 30 commits) → Task/Read/Write/Glob/Grep工具
阶段5: 稳定性提升    (Sep 22-25, 25 commits) → 重试机制、配置系统、日志
阶段6: 架构重构      (Sep 26-Oct 5, 45 commits) → Context、工具抽象、MCP支持
阶段7: 完善与发布    (Oct 9-24, 80+ commits) → Agent文件、Shell模式、Approval
阶段8: 生态完善      (Oct 25-Nov 10, 250+ commits) → SDK、多Provider、Thinking模式
```

---

## 🎯 阶段1：骨架搭建（可运行的最小框架）

**时间**：2025-09-10
**Commits**：10个
**目标**：从零到一，搭建可运行的 CLI 框架

### 关键 Commits（时间正序）

```
8b827e5 | 2025-09-10 | init
e997490 | 2025-09-10 | chore: update readme
7798a2e | 2025-09-10 | feat: a runnable skeleton
e06c4ae | 2025-09-10 | chore: rename `src/kimi` to `src/kimi_cli`
5f6a743 | 2025-09-10 | feat: add shortcuts for cli options
```

### 学习重点

#### 1.1 项目初始化（`8b827e5 init`）

**做了什么**：
- 创建基本目录结构
- 配置 `pyproject.toml`
- 添加 `.gitignore`

**学习要点**：
```
kimi-cli/
├── src/
│   └── kimi/          # 初始命名
├── pyproject.toml     # 项目配置
├── README.md          # 项目说明
└── .gitignore         # Git忽略规则
```

**对应 my_cli**：
- 已完成：✅ 基本目录结构
- 已完成：✅ `pyproject.toml` 和 `setup.py`
- 已完成：✅ README.md

---

#### 1.2 可运行的骨架（`7798a2e feat: a runnable skeleton`）

**做了什么**：
- 实现 CLI 入口（使用 Click）
- 实现 App 层
- 实现最简单的 Print UI
- 实现 Soul 引擎骨架

**关键文件**：
```python
# cli.py - CLI入口
@click.command()
@click.option("--verbose", is_flag=True)
@click.option("--work-dir", "-w", type=click.Path(...))
def kimi(verbose: bool, work_dir: Path):
    asyncio.run(async_main(verbose, work_dir))

# app.py - 应用层
class KimiCLI:
    async def run_print_mode(self):
        # 运行打印模式
        pass

# soul.py - 灵魂引擎
class Soul:
    async def run(self):
        # 核心AI循环
        pass
```

**学习要点**：
1. **三层架构**：CLI → App → Soul
2. **异步编程**：全程使用 `async/await`
3. **Click框架**：命令行参数解析
4. **最小可运行**：能启动、能响应，但功能极简

**对应 my_cli**：
- 已完成：✅ `cli.py` 入口
- 已完成：✅ `app.py` 应用层
- 待完成：❌ `soul.py` 核心引擎（当前只有占位符）

---

#### 1.3 代码规范（`e06c4ae chore: rename src/kimi to src/kimi_cli`）

**做了什么**：
- 将 `src/kimi` 重命名为 `src/kimi_cli`
- 避免包名与命令名冲突

**学习要点**：
- **命名规范**：包名用下划线，命令名用短横线
  - 包名：`kimi_cli`（Python导入）
  - 命令名：`kimi`（Shell命令）
  - 项目名：`kimi-cli`（PyPI包名）

**对应 my_cli**：
- 已完成：✅ 使用了正确的命名规范
  - 包名：`my_cli`
  - 命令名：`my_cli`（别名：`mc`）
  - 项目名：`my-cli`

---

#### 1.4 快捷选项（`5f6a743 feat: add shortcuts for cli options`）

**做了什么**：
- 添加命令行选项的快捷键
  - `--work-dir` → `-w`
  - `--command` → `-c`
  - `--verbose` → `-v`

**代码示例**：
```python
@click.option("--work-dir", "-w", type=click.Path(...))
@click.option("--command", "-c", type=str)
@click.option("--verbose", "-v", is_flag=True)
```

**对应 my_cli**：
- 已完成：✅ 所有选项都有快捷键

---

### 阶段1 总结

#### 完成的功能
- ✅ 可运行的 CLI 框架
- ✅ 基本的三层架构（CLI → App → Soul）
- ✅ 命令行选项解析
- ✅ 异步编程基础

#### 代码结构
```
src/kimi_cli/
├── __init__.py
├── cli.py          # CLI入口（Click）
├── app.py          # 应用层
├── soul.py         # AI引擎骨架
└── ui/
    └── print/
        └── ui_print.py   # 打印UI
```

#### 关键技术
- **Click**：命令行框架
- **asyncio**：异步编程
- **三层架构**：分离关注点

#### My CLI 对比
| 功能 | Kimi CLI | My CLI | 状态 |
|------|----------|--------|------|
| CLI入口 | ✅ | ✅ | 已完成 |
| App层 | ✅ | ✅ | 已完成 |
| Soul引擎 | ✅ 骨架 | ❌ 占位符 | 待完善 |
| Print UI | ✅ | ✅ | 已完成 |

---

## 🚀 阶段2：核心功能（Shell工具、消息历史）

**时间**：2025-09-11 至 2025-09-12
**Commits**：15个
**目标**：添加最核心的功能，让工具能真正干活

### 关键 Commits

```
ef3ac1f | 2025-09-11 | chore: correct naming of meta command
772f538 | 2025-09-11 | feat: support parameterized system prompt
2bdcd30 | 2025-09-11 | feat: add shell tool
a6fdcca | 2025-09-11 | feat: save message history to `~/.local/share/kimi/`
69dc2dd | 2025-09-11 | feat: support `kimi -c "command"`
9c2db93 | 2025-09-11 | refactor: move print loop to `Soul`
651d456 | 2025-09-11 | chore: rename `app.agent` to `app.soul`
cd6f005 | 2025-09-11 | fix: step loading animation
921d97b | 2025-09-12 | refactor: simplify stream printing
dd5cfee | 2025-09-12 | feat: tool call status visualization
f5748b1 | 2025-09-12 | feat: display tool call detail
f0ad196 | 2025-09-12 | feat: display (fake) context percentage
29da356 | 2025-09-12 | feat: display failed tool call
```

### 学习重点

#### 2.1 参数化系统提示（`772f538 feat: support parameterized system prompt`）

**做了什么**：
- 支持在系统提示中注入动态参数
- 如工作目录、当前时间等

**代码示例**：
```python
system_prompt = f"""
You are Kimi, an AI assistant.
Current working directory: {work_dir}
Current time: {datetime.now()}
"""
```

**学习要点**：
- **动态提示**：根据运行时环境生成提示
- **上下文注入**：将工作目录等信息传给AI

---

#### 2.2 Shell 工具（`2bdcd30 feat: add shell tool`）

**做了什么**：
- 实现 Shell 工具，允许 AI 执行 Shell 命令
- 这是最核心的工具！

**代码示例**：
```python
class ShellTool:
    async def execute(self, command: str) -> str:
        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        return stdout.decode() + stderr.decode()
```

**学习要点**：
- **异步子进程**：使用 `asyncio.create_subprocess_shell`
- **输出捕获**：捕获 stdout 和 stderr
- **安全性**：需要考虑命令注入风险

**对应 my_cli**：
- 待实现：❌ Shell 工具（这是核心！）

---

#### 2.3 消息历史持久化（`a6fdcca feat: save message history`）

**做了什么**：
- 将对话历史保存到 `~/.local/share/kimi/`
- 支持多会话管理

**代码示例**：
```python
history_dir = Path.home() / ".local" / "share" / "kimi"
history_file = history_dir / f"session_{session_id}.jsonl"

# 保存消息
with open(history_file, "a") as f:
    json.dump(message, f)
    f.write("\n")
```

**学习要点**：
- **JSONL格式**：每行一个JSON对象
- **会话管理**：每个会话独立的历史文件
- **XDG规范**：使用 `~/.local/share/` 存储用户数据

---

#### 2.4 单命令模式（`69dc2dd feat: support kimi -c "command"`）

**做了什么**：
- 支持 `kimi -c "Hello World"` 直接运行命令
- 不进入交互模式

**代码示例**：
```python
@click.option("--command", "-c", type=str)
def kimi(command: str | None):
    if command:
        # 单命令模式
        result = await run_once(command)
        print(result)
    else:
        # 交互模式
        await run_interactive()
```

**学习要点**：
- **两种模式**：单命令 vs 交互
- **用户体验**：快速执行任务

**对应 my_cli**：
- 已完成：✅ 支持 `-c` 参数

---

#### 2.5 架构调整（`9c2db93 refactor: move print loop to Soul`）

**做了什么**：
- 将打印循环从 UI 移到 Soul 层
- 更清晰的职责分离

**架构变化**：
```
之前：UI 控制打印循环
UI.run() → Soul.step() → UI.print()

之后：Soul 控制循环，UI 只负责显示
Soul.run() → 循环 { step() → UI.display() }
```

**学习要点**：
- **职责分离**：Soul 负责逻辑，UI 负责显示
- **架构演进**：随着开发不断调整架构

---

#### 2.6 工具调用可视化（`dd5cfee feat: tool call status visualization`）

**做了什么**：
- 显示工具调用的状态（运行中/成功/失败）
- 使用 Rich 库美化输出

**效果示例**：
```
🔧 Running tool: shell
  $ ls -la
✅ Tool completed in 0.2s

🔧 Running tool: read_file
  📄 reading: src/main.py
✅ Tool completed in 0.1s
```

**学习要点**：
- **Rich库**：终端美化输出
- **实时反馈**：让用户知道 AI 在做什么
- **状态管理**：追踪工具调用状态

---

### 阶段2 总结

#### 完成的功能
- ✅ Shell 工具（核心！）
- ✅ 消息历史持久化
- ✅ 单命令模式（`-c`）
- ✅ 工具调用可视化
- ✅ 参数化系统提示

#### 代码结构
```
src/kimi_cli/
├── cli.py          # 新增 -c 参数
├── app.py          # 新增单命令模式
├── soul.py         # 新增循环控制
├── tools/
│   └── shell.py    # ⭐ Shell 工具
└── ui/
    └── print/
        └── ui_print.py   # 新增工具调用显示
```

#### 关键技术
- **异步子进程**：`asyncio.create_subprocess_shell`
- **JSONL存储**：消息历史持久化
- **Rich库**：终端美化
- **架构重构**：职责分离

#### My CLI 对比
| 功能 | Kimi CLI | My CLI | 状态 |
|------|----------|--------|------|
| Shell工具 | ✅ | ❌ | **急需实现** |
| 消息历史 | ✅ | ❌ | 待实现 |
| `-c` 参数 | ✅ | ✅ | 已完成 |
| 工具可视化 | ✅ | ❌ | 待实现 |

---

## 📊 阶段3：UI增强与Session管理

**时间**：2025-09-13 至 2025-09-14
**Commits**：20个
**目标**：改进用户体验，添加会话管理

### 关键 Commits

```
f4864ba | 2025-09-13 | feat: display context usage percentage
8e0640d | 2025-09-13 | feat: graceful interruption of agent runs
d24f215 | 2025-09-13 | feat: support AGENTS.md
420a291 | 2025-09-13 | feat: support session
05b4187 | 2025-09-13 | feat: print session name in welcome message
6591bd7 | 2025-09-14 | feat: more intuitive session management
98b7fea | 2025-09-14 | feat: support `--version` option
05f22b5 | 2025-09-14 | chore: bump version to 0.8.0
```

### 学习重点

#### 3.1 上下文使用率显示（`f4864ba feat: display context usage percentage`）

**做了什么**：
- 实时显示上下文使用率（如 45% / 128K tokens）
- 提醒用户接近上下文限制

**效果**：
```
Context: [████████████░░░░░░░░] 65% (83K/128K tokens)
```

#### 3.2 优雅中断（`8e0640d feat: graceful interruption`）

**做了什么**：
- 支持 Ctrl+C 优雅中断 AI 运行
- 保存当前状态，不丢失对话历史

#### 3.3 AGENTS.md 支持（`d24f215 feat: support AGENTS.md`）

**做了什么**：
- 读取项目中的 `AGENTS.md` 文件
- 作为额外的上下文注入到系统提示

**AGENTS.md 示例**：
```markdown
# Project Context

This is a CLI tool for AI agents.

## Tools Available
- shell: Execute shell commands
- read_file: Read file contents
```

#### 3.4 Session 管理（`420a291 feat: support session`）

**做了什么**：
- 支持多会话管理
- 每个会话独立的历史记录
- 可以随时切换或新建会话

**命令示例**：
```bash
kimi --session work    # 使用 work 会话
kimi --session debug   # 使用 debug 会话
kimi                   # 使用默认会话
```

---

### 阶段3 总结

#### 完成的功能
- ✅ 上下文使用率显示
- ✅ 优雅中断（Ctrl+C）
- ✅ AGENTS.md 项目上下文
- ✅ 多会话管理
- ✅ `--version` 选项

#### My CLI 对比
| 功能 | Kimi CLI | My CLI | 优先级 |
|------|----------|--------|--------|
| 上下文显示 | ✅ | ❌ | 中 |
| 优雅中断 | ✅ | ❌ | 高 |
| AGENTS.md | ✅ | ❌ | 中 |
| Session管理 | ✅ | ❌ | 低 |

---

## 🛠️ 阶段4：工具系统（Read/Write/Glob/Grep）

**时间**：2025-09-16 至 2025-09-18
**Commits**：30个
**目标**：完善工具系统，添加文件操作工具

### 关键 Commits

```
79897fe | 2025-09-16 | feat: add `task` tool
2b65949 | 2025-09-17 | feat: add read_file and write_file tools
6d9c71e | 2025-09-17 | feat: add glob tool
6cf367e | 2025-09-18 | feat: add grep tool
6a37a21 | 2025-09-18 | feat: support metacmd rename & alias
```

### 学习重点

#### 4.1 Task 工具（子Agent）

**做了什么**：
- 允许 AI 创建子 Agent 处理子任务
- 子 Agent 有独立的上下文

#### 4.2 文件操作工具

**ReadFile**：
```python
async def read_file(file_path: str, offset: int = 0, limit: int = 1000):
    with open(file_path) as f:
        lines = f.readlines()[offset:offset+limit]
    return "".join(lines)
```

**WriteFile**：
```python
async def write_file(file_path: str, content: str):
    with open(file_path, "w") as f:
        f.write(content)
```

#### 4.3 搜索工具

**Glob**（文件匹配）：
```python
import glob
results = glob.glob("**/*.py", recursive=True)
```

**Grep**（内容搜索）：
```python
import subprocess
result = subprocess.run(
    ["grep", "-r", pattern, directory],
    capture_output=True
)
```

#### 4.4 元命令系统

**做了什么**：
- 支持 `/rename`、`/alias` 等元命令
- 不通过 AI，直接执行的命令

---

### 阶段4 总结

#### 完成的工具
- ✅ Shell（阶段2）
- ✅ ReadFile
- ✅ WriteFile
- ✅ Glob
- ✅ Grep
- ✅ Task（子Agent）

#### My CLI 对比
| 工具 | Kimi CLI | My CLI | 优先级 |
|------|----------|--------|--------|
| Shell | ✅ | ❌ | **最高** |
| ReadFile | ✅ | ❌ | **最高** |
| WriteFile | ✅ | ❌ | 高 |
| Glob | ✅ | ❌ | 高 |
| Grep | ✅ | ❌ | 高 |
| Task | ✅ | ❌ | 中 |

---

## 💪 阶段5-8：持续迭代（省略详细内容）

由于篇幅限制，阶段5-8只列出关键milestone：

### 阶段5：稳定性提升（Sep 22-25）
- 重试机制
- 配置文件系统
- 日志系统
- `kimi_run` 函数（SDK）

### 阶段6：架构重构（Sep 26-Oct 5）
- Context 抽象
- ToolResultBuilder
- MCP 协议支持
- PatchFile 工具

### 阶段7：完善与发布（Oct 9-24）
- Agent 文件系统
- Shell 模式切换
- Approval 机制
- Markdown 渲染

### 阶段8：生态完善（Oct 25-Nov 10）
- SDK化（`KimiCLI` 类）
- 多 Provider（Anthropic、OpenAI）
- Thinking 模式
- 图片粘贴支持

---

## 🎓 学习建议

### 对于 My CLI 项目

#### 第一阶段：基础功能（当前急需）

**优先级1（最高）**：
1. ✅ 完成 Shell 工具
2. ✅ 完成 ReadFile 工具
3. ✅ 完成 WriteFile 工具
4. ✅ 实现基本的 Soul 引擎（调用 LLM）

**优先级2（高）**：
5. ✅ 添加 Glob 工具
6. ✅ 添加 Grep 工具
7. ✅ 工具调用可视化

**优先级3（中）**：
8. 消息历史持久化
9. 优雅中断（Ctrl+C）
10. AGENTS.md 支持

#### 第二阶段：体验优化

11. Session 管理
12. 上下文使用率显示
13. 元命令系统

#### 第三阶段：高级功能

14. Task 工具（子Agent）
15. Approval 机制
16. 配置文件系统

---

## 📚 参考资源

### 官方仓库
- GitHub：https://github.com/MoonshotAI/kimi-cli
- 你的 Fork：https://github.com/I-who-ant/kimi-cli

### 本地路径
- 官方代码：`/home/seeback/PycharmProjects/Modelrecognize/kimi-cli-fork`
- My CLI 代码：`/home/seeback/PycharmProjects/Modelrecognize/kimi-cli-main/imitate-src`

### 学习方法

#### 方法1：按 Commit 学习
```bash
cd kimi-cli-fork

# 查看特定 commit
git show 7798a2e   # feat: a runnable skeleton

# 查看某个文件的演进
git log --follow -- src/kimi_cli/soul.py

# 查看两个版本之间的差异
git diff 8b827e5..7798a2e
```

#### 方法2：按功能学习
```bash
# 查找 Shell 工具的相关 commits
git log --grep="shell" --oneline

# 查找工具相关的修改
git log --all -- src/kimi_cli/tools/
```

#### 方法3：对比学习
1. 在 `kimi-cli-fork` 中找到功能实现
2. 在 `my_cli` 中实现类似功能
3. 对比差异，理解设计思路

---

## 🎯 总结

### Kimi CLI 开发特点

1. **快速迭代**：2个月497个commits，平均每天7-8个
2. **渐进式开发**：从骨架→核心功能→工具系统→生态完善
3. **重构不断**：架构随着需求不断调整
4. **测试驱动**：引入单元测试和快照测试
5. **社区驱动**：大量PR贡献，issue反馈

### 关键学习点

1. **从简到繁**：先实现最小可运行版本
2. **职责分离**：CLI → App → Soul 三层架构
3. **工具优先**：Shell 工具是最核心的功能
4. **用户体验**：工具调用可视化、优雅中断等细节
5. **持续重构**：不断调整架构以适应新需求

### My CLI 下一步

**立即行动**：
1. 实现 Shell 工具（核心！）
2. 实现 ReadFile/WriteFile
3. 集成 LLM API（Moonshot）
4. 实现基本的工具调用循环

**短期目标**：
- 1周内：完成核心工具（Shell/Read/Write）
- 2周内：实现完整的 Soul 引擎
- 3周内：添加工具可视化

**长期目标**：
- 参考 Kimi CLI 的架构持续迭代
- 贡献代码到官方仓库
- 构建自己的 Agent 生态

---

**现在你可以开始真正的开发了！** 🚀

**老王建议**：先跑通 Shell 工具，这是最核心的！其他都是锦上添花！
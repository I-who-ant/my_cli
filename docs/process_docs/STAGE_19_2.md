# Stage 19.2: 配置目录与命名统一

**完成日期**: 2025-01-19
**目标**: 将项目从 `kimi-cli` 命名体系完全迁移到 `my_cli` 命名体系

---

## 一、问题背景

### 1.1 发现的问题

在 Stage 19.1 完成后，测试 `my_cli` 命令时发现以下问题：

1. **配置目录混乱**: 代码中使用 `~/.kimi/` 目录，与项目名 `my_cli` 不一致
2. **环境变量命名不统一**: 使用 `KIMI_BASE_URL`、`KIMI_API_KEY` 等，应该用 `MY_CLI_` 前缀
3. **模板变量命名不统一**: System Prompt 中使用 `${KIMI_NOW}` 等变量
4. **Agent配置位置错误**: 尝试在运行时动态生成配置，而官方是打包在源码中
5. **LLM未配置时崩溃**: 当没有配置API Key时，访问 `model_name` 和 `model_capabilities` 属性崩溃

### 1.2 用户需求

用户提出：
> "为什么我调用my_cli时AI说'我无法直接访问文件系统'，明明装了ReadFile工具？"

**根本原因**: Agent配置文件中的工具路径是 `kimi_cli.tools.*`，而实际应该是 `my_cli.tools.*`

---

## 二、架构对齐研究

### 2.1 官方 kimi-cli 架构

通过研究官方源码 `kimi-cli-fork/src/kimi_cli/`，发现：

**源码打包配置** (在源码包内):
```
src/kimi_cli/agents/default/
  ├── agent.yaml      # Agent配置（工具列表、System Prompt路径）
  └── system.md       # System Prompt模板（包含 ${KIMI_*} 变量）
```

**运行时数据** (用户目录):
```
~/.kimi/
  ├── config.json     # 用户的LLM配置（可选）
  ├── sessions/       # 会话历史
  └── logs/           # 日志文件
```

**关键发现**:
1. `share.py` 只有 11 行，只做一件事：返回 `~/.kimi` 目录
2. Agent配置不是运行时生成的，而是随pip包一起分发
3. `agentspec.py` 中定义 `get_agents_dir()` 返回源码目录

### 2.2 命名规范分析

| 类型 | 官方kimi-cli | 应该改为(my_cli) |
|------|-------------|-----------------|
| 配置目录 | `~/.kimi/` | `~/.mc/` |
| 环境变量 | `KIMI_BASE_URL` | `MY_CLI_BASE_URL` |
| 环境变量 | `KIMI_API_KEY` | `MY_CLI_API_KEY` |
| 模板变量 | `${KIMI_NOW}` | `${MY_CLI_NOW}` |
| 模板变量 | `${KIMI_WORK_DIR}` | `${MY_CLI_WORK_DIR}` |

---

## 三、具体修改步骤

### 3.1 修改配置目录 (share.py)

**文件**: `my_cli/share.py`
**修改行**: 第 36 行

**修改前**:
```python
share_dir = Path.home() / ".kimi"
```

**修改后**:
```python
share_dir = Path.home() / ".mc"
```

**原因**:
- 保持简洁，学习官方只有一个函数
- 删除了多余的 `init_share_dir()` 函数（147行）

---

### 3.2 修改模板变量 (runtime.py)

**文件**: `my_cli/soul/runtime.py`

#### 3.2.1 修改类定义（第32-55行）

**修改前**:
```python
@dataclass(frozen=True, slots=True, kw_only=True)
class BuiltinSystemPromptArgs:
    """内置系统提示词参数"""

    KIMI_NOW: str
    KIMI_WORK_DIR: Path
    KIMI_WORK_DIR_LS: str
    KIMI_AGENTS_MD: str
```

**修改后**:
```python
@dataclass(frozen=True, slots=True, kw_only=True)
class BuiltinSystemPromptArgs:
    """内置系统提示词参数 ⭐ Stage 19.2: 改为 MY_CLI_ 前缀"""

    MY_CLI_NOW: str
    MY_CLI_WORK_DIR: Path
    MY_CLI_WORK_DIR_LS: str
    MY_CLI_AGENTS_MD: str
```

#### 3.2.2 修改实例化（第157-162行）

**修改前**:
```python
builtin_args=BuiltinSystemPromptArgs(
    KIMI_NOW=datetime.now().astimezone().isoformat(),
    KIMI_WORK_DIR=session.work_dir,
    KIMI_WORK_DIR_LS=ls_output,
    KIMI_AGENTS_MD=agents_md or "",
)
```

**修改后**:
```python
builtin_args=BuiltinSystemPromptArgs(
    MY_CLI_NOW=datetime.now().astimezone().isoformat(),
    MY_CLI_WORK_DIR=session.work_dir,
    MY_CLI_WORK_DIR_LS=ls_output,
    MY_CLI_AGENTS_MD=agents_md or "",
)
```

---

### 3.3 修改环境变量 (llm.py)

**文件**: `my_cli/llm.py`
**函数**: `augment_provider_with_env_vars()`
**修改行**: 第 269-287 行

**修改前**:
```python
match provider.type:
    case "kimi":
        if base_url := os.getenv("KIMI_BASE_URL"):
            provider.base_url = base_url
            applied["KIMI_BASE_URL"] = base_url
        if api_key := os.getenv("KIMI_API_KEY"):
            provider.api_key = SecretStr(api_key)
            applied["KIMI_API_KEY"] = "******"
        if model_name := os.getenv("KIMI_MODEL_NAME"):
            model.model = model_name
            applied["KIMI_MODEL_NAME"] = model_name
        # ... 其他环境变量
```

**修改后**:
```python
match provider.type:
    case "kimi":
        # ⭐ Stage 19.2: 使用 MY_CLI_ 前缀的环境变量
        if base_url := os.getenv("MY_CLI_BASE_URL"):
            provider.base_url = base_url
            applied["MY_CLI_BASE_URL"] = base_url
        if api_key := os.getenv("MY_CLI_API_KEY"):
            provider.api_key = SecretStr(api_key)
            applied["MY_CLI_API_KEY"] = "******"
        if model_name := os.getenv("MY_CLI_MODEL_NAME"):
            model.model = model_name
            applied["MY_CLI_MODEL_NAME"] = model_name
        # ... 其他环境变量
```

**完整环境变量列表**:
- `MY_CLI_BASE_URL` - API基础URL
- `MY_CLI_API_KEY` - API密钥
- `MY_CLI_MODEL_NAME` - 模型名称
- `MY_CLI_MODEL_MAX_CONTEXT_SIZE` - 最大上下文大小
- `MY_CLI_MODEL_CAPABILITIES` - 模型能力

---

### 3.4 创建Agent配置文件

#### 3.4.1 创建目录

```bash
mkdir -p /home/seeback/PycharmProjects/Modelrecognize/kimi-cli-main/imitate-src/my_cli/agents/default
```

#### 3.4.2 创建 agent.yaml

**文件**: `my_cli/agents/default/agent.yaml`

```yaml
version: 1
agent:
  name: "MyCLI Assistant"
  system_prompt_path: ./system.md
  system_prompt_args:
    ROLE_ADDITIONAL: ""
  tools:
    # ⭐ Stage 7-8 已实现的工具
    - "my_cli.tools.bash:Bash"
    - "my_cli.tools.file:ReadFile"
    - "my_cli.tools.file:WriteFile"
    # TODO: Stage 9+ 待实现的工具
    # - "my_cli.tools.task:Task"
    # - "my_cli.tools.think:Think"
    # - "my_cli.tools.todo:SetTodoList"
    # - "my_cli.tools.file:Glob"
    # - "my_cli.tools.file:Grep"
    # - "my_cli.tools.file:StrReplaceFile"
    # - "my_cli.tools.file:PatchFile"
    # - "my_cli.tools.web:SearchWeb"
    # - "my_cli.tools.web:FetchURL"
```

**关键点**:
- 工具路径使用 `my_cli.tools.*` 而不是 `kimi_cli.tools.*`
- 只列出已实现的工具（Bash, ReadFile, WriteFile）
- 未实现的工具注释掉

#### 3.4.3 创建 system.md

**文件**: `my_cli/agents/default/system.md`

```markdown
You are MyCLI Assistant, an AI assistant specializing in software engineering tasks.

${ROLE_ADDITIONAL}

# Tool Use

When handling user requests, you can call available tools to accomplish tasks.
Use tools when appropriate - you have Bash, ReadFile, and WriteFile available.

When calling tools:
- Do not provide explanations, tool calls should be self-explanatory
- Follow the description of each tool and its parameters
- Make parallel tool calls when possible to improve efficiency

Tool call results will be returned in a `tool` message.
Decide your next action based on results:
1. Continue working on the task
2. Inform the user that the task is completed or failed
3. Ask the user for more information

# Response Language

ALWAYS use the SAME language as the user, unless explicitly instructed otherwise.

# Coding Guidelines

- Keep it simple. Do not overcomplicate things.
- Make MINIMAL changes to achieve the goal.
- Follow the coding style of existing code in the project.

# Working Environment

## Operating System

The operating environment is NOT sandboxed. Any action will immediately affect the user's system.
Be EXTREMELY cautious. Unless explicitly instructed, never access files outside the working directory.

## Working Directory

The current working directory is `${MY_CLI_WORK_DIR}`.
This should be considered as the project root if instructed to perform tasks on the project.

Directory listing:
```
${MY_CLI_WORK_DIR_LS}
```

## Date and Time

Current date/time in ISO format: `${MY_CLI_NOW}`.
For exact time, use Bash tool with proper command.
```

**关键点**:
- 使用 `${MY_CLI_NOW}` 替代 `${KIMI_NOW}`
- 使用 `${MY_CLI_WORK_DIR}` 替代 `${KIMI_WORK_DIR}`
- 使用 `${MY_CLI_WORK_DIR_LS}` 替代 `${KIMI_WORK_DIR_LS}`

---

### 3.5 修复LLM为None的崩溃 (kimisoul.py)

**文件**: `my_cli/soul/kimisoul.py`

#### 3.5.1 修复 model_name 属性（第87-91行）

**问题**: `AttributeError: 'NoneType' object has no attribute 'model_name'`

**修改前**:
```python
@property
def model_name(self) -> str:
    """实现 Soul Protocol: model_name 属性"""
    # ⭐ Stage 17：从 Runtime 的 LLM 获取模型名称
    return self._runtime.llm.model_name
```

**修改后**:
```python
@property
def model_name(self) -> str:
    """实现 Soul Protocol: model_name 属性"""
    # ⭐ Stage 19.2: 处理 llm 为 None 的情况
    return self._runtime.llm.model_name if self._runtime.llm else ""
```

#### 3.5.2 修复 model_capabilities 属性（第103-120行）

**问题**: `AttributeError: 'NoneType' object has no attribute 'capabilities'`

**修改前**:
```python
@property
def model_capabilities(self) -> set[str] | None:
    """实现 Soul Protocol: model_capabilities 属性"""
    # ⭐ Stage 17：从 Runtime 的 LLM 获取 capabilities
    return self._runtime.llm.capabilities
```

**修改后**:
```python
@property
def model_capabilities(self) -> set[str] | None:
    """实现 Soul Protocol: model_capabilities 属性"""
    # ⭐ Stage 19.2: 处理 llm 为 None 的情况
    if self._runtime.llm is None:
        return None
    return self._runtime.llm.capabilities
```

**原理**: 学习官方 `kimi-cli-fork/src/kimi_cli/soul/kimisoul.py:100` 的处理方式

---

## 四、测试验证

### 4.1 测试无配置启动

```bash
$ mc
╭──────────────────────────────╮
│                              │
│  欢迎使用 MyCLI Assistant!   │
│                              │
│  模型:                       │  # ✅ 空白，不崩溃
│  输入 /help 查看可用命令     │
│  输入 exit 或按 Ctrl+D 退出  │
│  按 Ctrl+C 可以取消当前请求  │
│                              │
╰──────────────────────────────╯
```

**结果**: ✅ 成功启动，不再崩溃

### 4.2 测试配置目录

```bash
$ ls ~/.mc/
sessions  logs

$ ls ~/.mc/sessions/
00e9d7ab73be08ad18e1c1d13580f470/
```

**结果**: ✅ 配置目录从 `~/.kimi` 改为 `~/.mc`

### 4.3 测试环境变量

```bash
$ export MY_CLI_BASE_URL="https://api.moonshot.cn/v1"
$ export MY_CLI_API_KEY="sk-test-key-123"
$ export MY_CLI_MODEL_NAME="moonshot-v1-8k"
$ mc -c "你好"

❌ LLM API 错误: Error code: 401 - {'error': {'message': 'Invalid Authentication'...
```

**结果**: ✅ 环境变量生效（401错误说明API Key被读取并使用，只是假密钥所以认证失败）

### 4.4 测试Agent配置

```bash
$ ls my_cli/agents/default/
agent.yaml  system.md
```

**结果**: ✅ Agent配置打包在源码中

---

## 五、配置方法说明

### 5.1 方式1: 环境变量配置（推荐用于开发）

**临时配置** (当前终端会话):
```bash
export MY_CLI_BASE_URL="https://api.moonshot.cn/v1"
export MY_CLI_API_KEY="sk-xxxxxx"
export MY_CLI_MODEL_NAME="moonshot-v1-8k"
mc
```

**永久配置** (~/.bashrc 或 ~/.zshrc):
```bash
echo 'export MY_CLI_BASE_URL="https://api.moonshot.cn/v1"' >> ~/.bashrc
echo 'export MY_CLI_API_KEY="sk-xxxxxx"' >> ~/.bashrc
echo 'export MY_CLI_MODEL_NAME="moonshot-v1-8k"' >> ~/.bashrc
source ~/.bashrc
```

### 5.2 方式2: 配置文件（推荐用于生产）

**文件路径**: `~/.mc/config.json`

**示例内容**:
```json
{
  "default_model": "moonshot",
  "models": {
    "moonshot": {
      "provider": "kimi_provider",
      "model": "moonshot-v1-8k",
      "max_context_size": 8000,
      "capabilities": ["image_in"]
    }
  },
  "providers": {
    "kimi_provider": {
      "type": "kimi",
      "base_url": "https://api.moonshot.cn/v1",
      "api_key": "sk-xxxxxx",
      "custom_headers": {}
    }
  },
  "loop_control": {
    "max_steps_per_run": 100,
    "max_retries_per_step": 3
  }
}
```

**优先级**: 环境变量 > config.json

---

## 六、修改文件清单

| 文件 | 变更类型 | 变更行数 | 说明 |
|------|---------|---------|------|
| `my_cli/share.py` | 修改 | 1行 | 配置目录 `.kimi` → `.mc` |
| `my_cli/share.py` | 删除 | -147行 | 删除 `init_share_dir()` 函数 |
| `my_cli/soul/runtime.py` | 修改 | 9行 | 模板变量 `KIMI_*` → `MY_CLI_*` |
| `my_cli/llm.py` | 修改 | 18行 | 环境变量 `KIMI_*` → `MY_CLI_*` |
| `my_cli/soul/kimisoul.py` | 修改 | 6行 | 处理 LLM 为 None 的情况 |
| `my_cli/agents/default/agent.yaml` | 新建 | +22行 | Agent 配置文件 |
| `my_cli/agents/default/system.md` | 新建 | +51行 | System Prompt 模板 |

**总计**: 修改 5 个文件，新建 2 个文件

---

## 七、架构对比

### 7.1 官方 kimi-cli 架构

```
kimi-cli-fork/
├── src/kimi_cli/
│   ├── agents/default/
│   │   ├── agent.yaml          # 源码打包
│   │   └── system.md            # 源码打包
│   ├── share.py                 # get_share_dir() → ~/.kimi
│   ├── agentspec.py             # get_agents_dir() → src/kimi_cli/agents
│   └── ...

~/.kimi/                         # 运行时数据
├── config.json                  # 可选，用户配置
├── sessions/                    # 会话历史
└── logs/                        # 日志文件

环境变量:
  KIMI_BASE_URL
  KIMI_API_KEY
  KIMI_MODEL_NAME
```

### 7.2 my_cli 架构（Stage 19.2后）

```
kimi-cli-main/imitate-src/
├── my_cli/
│   ├── agents/default/
│   │   ├── agent.yaml          # ✅ 源码打包
│   │   └── system.md            # ✅ 源码打包
│   ├── share.py                 # ✅ get_share_dir() → ~/.mc
│   ├── agentspec.py             # ✅ get_agents_dir() → src/my_cli/agents
│   └── ...

~/.mc/                           # ✅ 运行时数据
├── config.json                  # 可选，用户配置
├── sessions/                    # 会话历史
└── logs/                        # 日志文件

环境变量:                        # ✅ 统一前缀
  MY_CLI_BASE_URL
  MY_CLI_API_KEY
  MY_CLI_MODEL_NAME
```

**结论**: 完全对齐官方架构！

---

## 八、关键学习点

### 8.1 配置打包策略

**错误做法** (之前的尝试):
```python
def init_share_dir():
    """运行时动态生成配置"""
    agent_file = share_dir / "agents" / "my-agent.yaml"
    if not agent_file.exists():
        agent_file.write_text(agent_config)  # ❌ 复杂、易出错
```

**正确做法** (学习官方):
```
# Agent配置直接放在源码里
my_cli/agents/default/agent.yaml    # ✅ 随 pip 包分发
my_cli/agents/default/system.md     # ✅ 随 pip 包分发
```

**优势**:
- 简单：配置和代码一起版本管理
- 可靠：pip install 后立即可用
- 一致：所有用户使用相同的默认配置

### 8.2 命名统一原则

**原则**: 所有与项目相关的命名都用统一前缀

| 类型 | 前缀 | 示例 |
|------|------|------|
| 配置目录 | `.项目简称` | `~/.mc/` |
| 环境变量 | `项目名_` | `MY_CLI_BASE_URL` |
| 模板变量 | `${项目名_*}` | `${MY_CLI_NOW}` |
| Python包 | `项目名.` | `my_cli.tools.bash` |

### 8.3 优雅降级处理

**原则**: 功能可选时，未配置不应崩溃

**示例**:
```python
# ❌ 不好的做法：直接访问可能为 None 的属性
@property
def model_name(self) -> str:
    return self._runtime.llm.model_name  # 崩溃！

# ✅ 好的做法：检查并返回默认值
@property
def model_name(self) -> str:
    return self._runtime.llm.model_name if self._runtime.llm else ""
```

### 8.4 简洁即王道

**原则**: 不做不必要的抽象和封装

**官方 share.py** (11行):
```python
from pathlib import Path

def get_share_dir() -> Path:
    share_dir = Path.home() / ".kimi"
    share_dir.mkdir(parents=True, exist_ok=True)
    return share_dir
```

**之前的错误做法** (150行):
- 添加 `init_share_dir()` 函数
- 尝试动态生成配置文件
- 过度封装导致复杂度暴增

**教训**: 遇到问题时，先看官方怎么做，不要自己瞎设计！

---

## 九、后续改进建议

### 9.1 添加 setup 命令（TODO: Stage 20）

参考官方可能有的 setup 流程：

```python
# cli.py
@cli.command()
def setup():
    """交互式配置向导"""
    print("🚀 欢迎使用 MyCLI! 让我们开始配置...")

    # 1. 选择 API Provider
    provider_type = prompt("选择 API Provider (kimi/openai): ")

    # 2. 输入 API Key
    api_key = prompt("输入 API Key: ", is_password=True)

    # 3. 输入 Base URL
    base_url = prompt("输入 Base URL (默认: https://api.moonshot.cn/v1): ")

    # 4. 选择默认模型
    model_name = prompt("选择默认模型 (moonshot-v1-8k): ")

    # 5. 生成配置文件
    config = Config(...)
    config_file = get_share_dir() / "config.json"
    config_file.write_text(config.model_dump_json(indent=2))

    print("✅ 配置完成！现在可以运行 `mc` 开始使用了！")
```

### 9.2 改进日志命名（TODO: Stage 20）

```python
# app.py: enable_logging()
logger.add(
    get_share_dir() / "logs" / "my_cli.log",  # 从 "kimi.log" 改名
    level="TRACE" if debug else "INFO",
    rotation="06:00",
    retention="10 days",
)
```

### 9.3 添加环境变量检查（TODO: Stage 20）

```python
# app.py: MyCLI.create()
if not provider.base_url or not model.model:
    logger.warning("⚠️  LLM 未配置！")
    logger.warning("请设置环境变量:")
    logger.warning("  export MY_CLI_BASE_URL='...'")
    logger.warning("  export MY_CLI_API_KEY='...'")
    logger.warning("  export MY_CLI_MODEL_NAME='...'")
    logger.warning("或运行 `mc setup` 进行配置")
    llm = None
```

---

## 十、总结

### 10.1 Stage 19.2 成果

✅ **配置目录统一**: `~/.kimi/` → `~/.mc/`
✅ **环境变量统一**: `KIMI_*` → `MY_CLI_*`
✅ **模板变量统一**: `${KIMI_*}` → `${MY_CLI_*}`
✅ **Agent配置打包**: 学习官方，放在源码中
✅ **优雅降级处理**: LLM未配置时不崩溃
✅ **架构完全对齐**: 与官方 kimi-cli 架构一致

### 10.2 命名体系对照表

| 概念 | 官方 kimi-cli | my_cli (Stage 19.2后) |
|------|--------------|----------------------|
| 配置目录 | `~/.kimi/` | `~/.mc/` ✅ |
| 环境变量 | `KIMI_BASE_URL` | `MY_CLI_BASE_URL` ✅ |
| 环境变量 | `KIMI_API_KEY` | `MY_CLI_API_KEY` ✅ |
| 模板变量 | `${KIMI_NOW}` | `${MY_CLI_NOW}` ✅ |
| 模板变量 | `${KIMI_WORK_DIR}` | `${MY_CLI_WORK_DIR}` ✅ |
| Agent配置路径 | `kimi_cli.tools.*` | `my_cli.tools.*` ✅ |
| Agent配置位置 | `src/kimi_cli/agents/` | `src/my_cli/agents/` ✅ |
| 日志文件 | `kimi.log` | `kimi.log` (TODO) |

### 10.3 核心经验

1. **遇到问题先看官方**: 不要自己瞎设计，官方已经给出了最佳实践
2. **简洁即王道**: 能 11 行解决的不要写 150 行
3. **命名要统一**: 所有相关命名用统一前缀，避免混乱
4. **配置要打包**: 默认配置随源码分发，不要运行时生成
5. **优雅要降级**: 可选功能未配置时不应崩溃

---

**Stage 19.2 完成标志**: ✅ 命名体系完全统一，配置架构对齐官方，无配置时优雅降级！

**下一步**: Stage 20 - 实现 setup 命令，提供交互式配置向导

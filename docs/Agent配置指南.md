# Agent 配置指南

## 概述

MyCLI 使用 Agent 配置文件来定义 AI 助手的行为、可用工具和系统提示词。

---

## 配置文件位置

默认 Agent 配置**随包一起安装**，位于：
```
<python_package_dir>/my_cli/agents/default/
├── agent.yaml       # Agent 配置
└── system.md        # 系统提示词
```

**开发模式**（`pip install -e .`）：
```
/path/to/project/my_cli/agents/default/
```

**安装模式**（`pip install my-cli`）：
```
~/.conda/envs/my_cli/lib/python3.13/site-packages/my_cli/agents/default/
# 或
/usr/local/lib/python3.13/site-packages/my_cli/agents/default/
```

> **注意**：agents 配置是包的一部分，安装时会自动包含。无需手动复制到 `~/.mc/` 或其他位置。

---

## agent.yaml 配置结构

```yaml
version: 1
agent:
  name: "MyCLI Assistant"
  system_prompt_path: ./system.md
  system_prompt_args:
    ROLE_ADDITIONAL: ""
  tools:
    # 文件操作工具
    - "my_cli.tools.file:ReadFile"
    - "my_cli.tools.file:WriteFile"
    - "my_cli.tools.file:Glob"
    - "my_cli.tools.file:Grep"
    - "my_cli.tools.file:StrReplaceFile"
    - "my_cli.tools.file:PatchFile"
    # 命令行工具
    - "my_cli.tools.bash:Bash"
    # 网络工具
    - "my_cli.tools.web:SearchWeb"
    - "my_cli.tools.web:FetchURL"
    # 高级工具
    - "my_cli.tools.task:Task"
    - "my_cli.tools.todo:SetTodoList"
    - "my_cli.tools.think:Think"
```

### 配置项说明

| 字段 | 说明 |
|------|------|
| `version` | 配置文件版本（当前为 1） |
| `agent.name` | Agent 名称 |
| `agent.system_prompt_path` | 系统提示词文件路径（相对于 agent.yaml） |
| `agent.system_prompt_args` | 系统提示词模板变量 |
| `agent.tools` | 可用工具列表 |

---

## 工具配置

### 工具格式

```yaml
tools:
  - "模块路径:工具类名"
```

### 可用工具列表

#### 文件操作工具

| 工具 | 路径 | 功能 |
|------|------|------|
| ReadFile | `my_cli.tools.file:ReadFile` | 读取文件内容 |
| WriteFile | `my_cli.tools.file:WriteFile` | 写入文件 |
| Glob | `my_cli.tools.file:Glob` | 文件模式匹配（如 `*.py`） |
| Grep | `my_cli.tools.file:Grep` | 内容搜索（正则） |
| StrReplaceFile | `my_cli.tools.file:StrReplaceFile` | 字符串替换 |
| PatchFile | `my_cli.tools.file:PatchFile` | 补丁式编辑 |

#### 命令行工具

| 工具 | 路径 | 功能 |
|------|------|------|
| Bash | `my_cli.tools.bash:Bash` | 执行 bash 命令 |

#### 网络工具

| 工具 | 路径 | 功能 |
|------|------|------|
| SearchWeb | `my_cli.tools.web:SearchWeb` | 网络搜索 |
| FetchURL | `my_cli.tools.web:FetchURL` | 获取网页内容 |

#### 高级工具

| 工具 | 路径 | 功能 |
|------|------|------|
| Task | `my_cli.tools.task:Task` | 创建子任务 |
| SetTodoList | `my_cli.tools.todo:SetTodoList` | 管理待办列表 |
| Think | `my_cli.tools.think:Think` | 思考工具 |

---

## system.md 提示词配置

系统提示词定义 Agent 的行为和规则。

### 模板变量

系统提示词支持模板变量（使用 `${变量名}` 语法）：

| 变量 | 说明 | 示例 |
|------|------|------|
| `${ROLE_ADDITIONAL}` | 额外角色说明 | 在 `agent.yaml` 中定义 |
| `${MY_CLI_WORK_DIR}` | 当前工作目录 | `/home/user/project` |
| `${MY_CLI_WORK_DIR_LS}` | 工作目录列表 | `ls -la` 输出 |
| `${MY_CLI_NOW}` | 当前时间 | `2025-11-21T16:00:00+08:00` |

### 提示词结构

```markdown
You are MyCLI Assistant, an interactive CLI agent...

${ROLE_ADDITIONAL}

# Prompt and Tool Use
...

# General Coding Guidelines
...

# Working Environment
...
```

---

## 自定义 Agent

### 1. 创建自定义 Agent 目录

```bash
mkdir -p my_cli/agents/my_custom_agent
cd my_cli/agents/my_custom_agent
```

### 2. 创建配置文件

**agent.yaml:**
```yaml
version: 1
agent:
  name: "My Custom Agent"
  system_prompt_path: ./system.md
  system_prompt_args:
    ROLE_ADDITIONAL: "You are specialized in Python development."
  tools:
    - "my_cli.tools.file:ReadFile"
    - "my_cli.tools.file:WriteFile"
    - "my_cli.tools.bash:Bash"
```

**system.md:**
```markdown
You are ${name}, a Python development assistant.

${ROLE_ADDITIONAL}

# Your specific instructions here...
```

### 3. 使用自定义 Agent

```bash
my_cli --agent-file my_cli/agents/my_custom_agent/agent.yaml
```

---

## 排除工具

如果需要排除某些默认工具：

```yaml
agent:
  tools:
    - "my_cli.tools.bash:Bash"
    - "my_cli.tools.file:ReadFile"
  exclude_tools:
    - "my_cli.tools.web:SearchWeb"  # 排除网络搜索
```

---

## 故障排查

### 工具不调用

**问题**：AI 一直解释但不调用工具

**解决**：
1. 检查 `kosong` 版本：`pip show kosong`（应为 0.25.1+）
2. 检查工具是否正确配置在 `agent.yaml` 中
3. 检查 system.md 是否包含工具使用说明

### 工具加载失败

**问题**：启动时报错 `Invalid tools`

**解决**：
1. 检查工具路径格式：`模块:类名`
2. 确认工具类已实现
3. 查看日志：`my_cli --debug`

---

## 最佳实践

1. **最小化工具集**：只启用需要的工具，提高性能
2. **清晰的提示词**：在 system.md 中明确说明 Agent 的职责
3. **模板变量**：充分利用内置变量（如工作目录、时间）
4. **并行调用**：提示词中强调"并行调用工具"以提高效率

---

## 示例配置

### Python 开发专用 Agent

```yaml
version: 1
agent:
  name: "Python Dev Assistant"
  system_prompt_path: ./system.md
  system_prompt_args:
    ROLE_ADDITIONAL: |
      You are specialized in Python development.
      Always follow PEP 8 style guide.
  tools:
    - "my_cli.tools.file:ReadFile"
    - "my_cli.tools.file:WriteFile"
    - "my_cli.tools.file:Grep"
    - "my_cli.tools.bash:Bash"
    - "my_cli.tools.task:Task"
```

### 只读分析 Agent

```yaml
version: 1
agent:
  name: "Code Analyzer"
  system_prompt_path: ./system.md
  system_prompt_args:
    ROLE_ADDITIONAL: "You can only read files, never modify them."
  tools:
    - "my_cli.tools.file:ReadFile"
    - "my_cli.tools.file:Glob"
    - "my_cli.tools.file:Grep"
    - "my_cli.tools.bash:Bash"
  exclude_tools:
    - "my_cli.tools.file:WriteFile"
    - "my_cli.tools.file:StrReplaceFile"
```

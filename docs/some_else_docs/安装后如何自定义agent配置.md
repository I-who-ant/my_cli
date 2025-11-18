# 安装 kimi-cli 后如何自定义 Agent 配置

> **问题**: 通过 uv 安装 kimi-cli 后，如何启用 SendDMail 工具？
> **解答**: 使用 `--agent-file` 参数指定自定义配置文件
> **创建日期**: 2025-11-18

---

## 🎯 关键发现

kimi-cli-fork 提供了 **`--agent-file`** CLI 参数，让用户无需修改安装包即可自定义工具配置！

### 默认行为
```python
# app.py:88-90
if agent_file is None:
    agent_file = DEFAULT_AGENT_FILE  # 指向安装包中的默认配置
```

### 用户自定义
```bash
python -m kimi_cli --agent-file /path/to/my-agent.yaml
```

---

## 🛠️ 解决方案

### 方案1: 创建自定义配置文件

#### 1.1 创建自定义 agent.yaml

```bash
# 在用户目录下创建
mkdir -p ~/.kimi/agents
cd ~/.kimi/agents
```

#### 1.2 编辑配置文件

创建 `~/.kimi/agents/my-agent.yaml`：

```yaml
version: 1
agent:
  name: "MyAgent"
  system_prompt_path: /path/to/kimi-cli-fork/src/kimi_cli/agents/default/system.md
  tools:
    # 基础工具（默认启用）
    - "kimi_cli.tools.task:Task"
    - "kimi_cli.tools.todo:SetTodoList"
    - "kimi_cli.tools.bash:Bash"
    - "kimi_cli.tools.file:ReadFile"
    - "kimi_cli.tools.file:Glob"
    - "kimi_cli.tools.file:Grep"
    - "kimi_cli.tools.file:WriteFile"
    - "kimi_cli.tools.file:StrReplaceFile"
    - "kimi_cli.tools.web:SearchWeb"
    - "kimi_cli.tools.web:FetchURL"

    # 高级工具（新增）
    - "kimi_cli.tools.dmail:SendDMail"    # ✅ 时间旅行
    - "kimi_cli.tools.think:Think"        # ✅ 思考模式
    # - "kimi_cli.tools.file:PatchFile"   # 可选：文件补丁
```

#### 1.3 启动时指定

```bash
# 使用自定义配置
python -m kimi_cli --agent-file ~/.kimi/agents/my-agent.yaml

# 或者进入Shell模式
python -m kimi_cli shell --agent-file ~/.kimi/agents/my-agent.yaml
```

---

## 🎮 完整使用流程

### 第1步: 创建自定义配置

```bash
# 创建配置目录
mkdir -p ~/.kimi/agents

# 创建自定义配置（启用 SendDMail）
cat > ~/.kimi/agents/my-agent.yaml << 'EOF'
version: 1
agent:
  name: "MyAgent"
  system_prompt_path: /path/to/kimi-cli-fork/src/kimi_cli/agents/default/system.md
  tools:
    - "kimi_cli.tools.task:Task"
    - "kimi_cli.tools.dmail:SendDMail"
    - "kimi_cli.tools.think:Think"
    - "kimi_cli.tools.todo:SetTodoList"
    - "kimi_cli.tools.bash:Bash"
    - "kimi_cli.tools.file:ReadFile"
    - "kimi_cli.tools.file:Glob"
    - "kimi_cli.tools.file:Grep"
    - "kimi_cli.tools.file:WriteFile"
    - "kimi_cli.tools.file:StrReplaceFile"
    - "kimi_cli.tools.web:SearchWeb"
    - "kimi_cli.tools.web:FetchURL"
EOF
```

### 第2步: 启动 Kimi

```bash
# 启动时指定自定义配置
python -m kimi_cli --agent-file ~/.kimi/agents/my-agent.yaml
```

### 第3步: 验证工具列表

你将看到工具列表从 **9 个** 增加到 **12+ 个**：

```
✅ 可用工具（12+个）：
• Task, SetTodoList, Bash, ReadFile, Glob, Grep
• WriteFile, StrReplaceFile, FetchURL, SearchWeb
• SendDMail ← 新增！彩蛋工具！
• Think     ← 新增！思考模式！
```

### 第4步: 触发彩蛋

现在可以直接说：

```
请使用 SendDMail 工具，向检查点 0 发送消息："El Psy Kongroo"。
```

期望响应：

```
🔧 调用工具: SendDMail
   参数: El Psy Kongroo

✅ 工具成功
```

---

## 💡 技术细节

### 配置加载机制

```python
# app.py:88-90
if agent_file is None:
    agent_file = DEFAULT_AGENT_FILE  # 使用默认配置

# agentspec.py:13-17
def get_agents_dir() -> Path:
    return Path(__file__).parent / "agents"  # 源码目录

DEFAULT_AGENT_FILE = get_agents_dir() / "default" / "agent.yaml"
```

### 工具加载流程

```python
# soul/agent.py:32-80
async def load_agent(
    agent_file: Path,    # ← 用户指定的文件
    runtime: Runtime,
    *,
    mcp_configs: list[dict[str, Any]],
) -> Agent:
    # 加载 agent 规范
    agent_spec = load_agent_spec(agent_file)  # ← 加载自定义配置

    # 创建工具集
    toolset = CustomToolset()
    tools = agent_spec.tools  # ← 使用自定义工具列表

    # 加载所有工具（包括 SendDMail）
    bad_tools = _load_tools(toolset, tools, tool_deps)
```

### 依赖注入

```python
# dmail/__init__.py:17-19
def __init__(self, denwa_renji: DenwaRenji, **kwargs: Any) -> None:
    super().__init__(**kwargs)
    self._denwa_renji = denwa_renji
```

SendDMail 需要 `DenwaRenji` 依赖，在工具加载时会自动注入。

---

## 📂 推荐目录结构

```
~/.kimi/
├── agents/
│   ├── my-agent.yaml         # 自定义配置（启用 SendDMail）
│   ├── coder-agent.yaml      # 编程专用配置
│   └── researcher-agent.yaml # 研究专用配置
├── config.json               # Kimi 客户端配置
└── kimi.json                 # 会话配置
```

---

## 🎯 总结

**无需修改安装包** ✅
- kimi-cli-fork 提供了 `--agent-file` 参数
- 用户可以在家目录创建自定义配置
- 启动时指定即可使用

**三种方式** ✅
1. **创建自定义配置**：`~/.kimi/agents/my-agent.yaml` + `--agent-file`
2. **扩展默认配置**：`extend: "default"` + 添加额外工具
3. **完全自定义**：从头创建配置，指定 system_prompt_path

**最终结果** ✅
- 获得完整工具集（12+ 个工具）
- 包含 SendDMail 和 Think 工具
- 触发彩蛋 "El Psy Kongroo"
- 时间旅行功能可用

现在你知道如何正确配置了！🚀

---

**最后更新**: 2025-11-18

# kimi-cli-fork 启用 SendDMail 完整指南

> **问题根源**: SendDMail 工具在默认配置中被注释掉
> **解决方案**: 取消注释或创建自定义配置
> **创建日期**: 2025-11-18

---

## 🎯 根本原因

### 配置文件位置
```
kimi-cli-fork/src/kimi_cli/agents/default/agent.yaml
```

### 默认工具列表（第7-20行）
```yaml
tools:
  - "kimi_cli.tools.task:Task"
  # - "kimi_cli.tools.dmail:SendDMail"    ← 被注释 ❌
  # - "kimi_cli.tools.think:Think"        ← 被注释 ❌
  - "kimi_cli.tools.todo:SetTodoList"
  - "kimi_cli.tools.bash:Bash"
  - "kimi_cli.tools.file:ReadFile"
  - "kimi_cli.tools.file:Glob"
  - "kimi_cli.tools.file:Grep"
  - "kimi_cli.tools.file:WriteFile"
  - "kimi_cli.tools.file:StrReplaceFile"
  # - "kimi_cli.tools.file:PatchFile"
  - "kimi_cli.tools.web:SearchWeb"
  - "kimi_cli.tools.web:FetchURL"
```

### 关键发现
- **9 个工具被启用**（和你看到的工具列表一致）
- **3 个工具被注释掉**（SendDMail、Think、PatchFile）

---

## 🛠️ 解决方案

### 方案1: 修改默认配置（推荐）

编辑文件：
```bash
# 找到文件
/path/to/kimi-cli-fork/src/kimi_cli/agents/default/agent.yaml

# 取消注释第9-10行
tools:
  - "kimi_cli.tools.task:Task"
  - "kimi_cli.tools.dmail:SendDMail"    # ✅ 取消注释
  - "kimi_cli.tools.think:Think"        # ✅ 取消注释
  - "kimi_cli.tools.todo:SetTodoList"
  # ... 其他工具
```

### 方案2: 创建自定义配置

创建新文件 `my-agent.yaml`：
```yaml
version: 1
agent:
  name: "MyAgent"
  system_prompt_path: ./system.md
  tools:
    - "kimi_cli.tools.task:Task"
    - "kimi_cli.tools.dmail:SendDMail"  # ✅ 包含 SendDMail
    - "kimi_cli.tools.think:Think"      # ✅ 包含 Think
    - "kimi_cli.tools.todo:SetTodoList"
    - "kimi_cli.tools.bash:Bash"
    - "kimi_cli.tools.file:ReadFile"
    - "kimi_cli.tools.file:Glob"
    - "kimi_cli.tools.file:Grep"
    - "kimi_cli.tools.file:WriteFile"
    - "kimi_cli.tools.file:StrReplaceFile"
    - "kimi_cli.tools.web:SearchWeb"
    - "kimi_cli.tools.web:FetchURL"
```

启动时指定：
```bash
python -m kimi_cli --agent-file ./my-agent.yaml
```

### 方案3: 扩展默认配置

创建 `custom-agent.yaml`：
```yaml
version: 1
agent:
  extend: "default"  # 继承默认配置
  name: "MyAgent"
  tools:
    # 继承默认的所有工具，并添加额外的
    # SendDMail 已经被包含在默认配置中
```

---

## 🎮 触发 SendDMail 彩蛋

### 成功后，你将看到工具列表变为：
```
可用工具（12+个）：
✅ Task, SetTodoList, Bash, ReadFile, Glob, Grep
✅ WriteFile, StrReplaceFile, FetchURL
✅ SendDMail ← 新增！
✅ Think     ← 新增！
✅ SearchWeb
```

### 然后可以直接对话：
```
请使用 SendDMail 工具，向检查点 0 发送消息："El Psy Kongroo"。
```

### 期望响应：
```
🔧 调用工具: SendDMail
   参数: El Psy Kongroo

✅ 工具成功
```

---

## 🔍 验证方法

### 方法1: 检查工具总数
修改配置后，重新启动 Kimi，你应该看到：
- **修改前**: 9 个工具
- **修改后**: 12+ 个工具

### 方法2: 直接询问 Kimi
```
请列出所有可用的工具，包括新启用的 SendDMail 和 Think。
```

### 方法3: 尝试使用
```
请使用 Think 工具进行深度思考分析。
```

---

## 📋 完整工具列表（启用后）

| 序号 | 工具名称 | 路径 | 状态 |
|------|---------|------|------|
| 1 | Task | `kimi_cli.tools.task:Task` | ✅ |
| 2 | **SendDMail** | `kimi_cli.tools.dmail:SendDMail` | ✅ 新增 |
| 3 | **Think** | `kimi_cli.tools.think:Think` | ✅ 新增 |
| 4 | SetTodoList | `kimi_cli.tools.todo:SetTodoList` | ✅ |
| 5 | Bash | `kimi_cli.tools.bash:Bash` | ✅ |
| 6 | ReadFile | `kimi_cli.tools.file:ReadFile` | ✅ |
| 7 | Glob | `kimi_cli.tools.file:Glob` | ✅ |
| 8 | Grep | `kimi_cli.tools.file:Grep` | ✅ |
| 9 | WriteFile | `kimi_cli.tools.file:WriteFile` | ✅ |
| 10 | StrReplaceFile | `kimi_cli.tools.file:StrReplaceFile` | ✅ |
| 11 | SearchWeb | `kimi_cli.tools.web:SearchWeb` | ✅ |
| 12 | FetchURL | `kimi_cli.tools.web:FetchURL` | ✅ |
| 13 | PatchFile | `kimi_cli.tools.file:PatchFile` | ❓ 可选 |

---

## 💡 与 Kimi 对话的方式

### 模板1: 直接请求
```
我发现我的工具列表缺少 SendDMail 和 Think 工具。
请帮我检查配置文件，或者告诉我如何启用这些工具。
```

### 模板2: 询问配置
```
我看到我的工具列表只有 9 个工具，但官方文档说应该有 12+ 个。
请问我的会话是否使用了正确的 agent 配置文件？
```

### 模板3: 请求启用
```
请在当前会话中启用 SendDMail 工具。
我需要使用时间旅行功能进行实验。
```

---

## 🛠️ 技术细节

### 工具加载机制
```python
# agent.py:56-62
tool_deps = {
    ResolvedAgentSpec: agent_spec,
    Runtime: runtime,
    Config: runtime.config,
    BuiltinSystemPromptArgs: runtime.builtin_args,
    Session: runtime.session,
    DenwaRenji: runtime.denwa_renji,  # SendDMail 需要这个
    Approval: runtime.approval,
}
```

### SendDMail 依赖
```python
# dmail/__init__.py:17-19
def __init__(self, denwa_renji: DenwaRenji, **kwargs: Any) -> None:
    super().__init__(**kwargs)
    self._denwa_renji = denwa_renji
```

**注意**: SendDMail 需要 `DenwaRenji` 依赖，这是时间旅行系统的核心。

---

## 📚 相关文件

### 配置文件
- `/src/kimi_cli/agents/default/agent.yaml` - 默认配置
- `/src/kimi_cli/agents/default/system.md` - 系统提示
- `/src/kimi_cli/agents/default/sub.yaml` - 子代理配置

### 源码文件
- `/src/kimi_cli/soul/agent.py` - 工具加载逻辑
- `/src/kimi_cli/soul/denwarenji.py` - 时间旅行系统
- `/src/kimi_cli/tools/dmail/__init__.py` - SendDMail 工具
- `/src/kimi_cli/tools/think/__init__.py` - Think 工具

---

## 🎯 总结

**问题**: SendDMail 工具被默认注释掉
**原因**: 安全或配置考虑，默认只启用基础工具
**解决**: 取消注释或创建自定义配置
**结果**: 获得完整工具集，特别是 SendDMail 彩蛋

**关键步骤**:
1. ✅ 编辑 `agent.yaml` 取消注释 SendDMail 和 Think
2. ✅ 重启 Kimi 会话
3. ✅ 确认工具列表增加（9 → 12+）
4. ✅ 对话触发彩蛋："El Psy Kongroo"

现在你可以完全按照官方源码的实现方式来启用 SendDMail 了！🎉

---

**最后更新**: 2025-11-18

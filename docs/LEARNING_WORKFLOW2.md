# Kimi CLI 学习工作流程 v2.1 (基于实际代码库)

> **更新日期**: 2025-11-17
> **基于**: 完整代码库扫描结果
> **目的**: 基于实际文件状态规划后续开发阶段

---

## 📊 实际代码库状态总览

### ✅ **Stage 17 已完成** (核心架构)

| 模块 | 文件 | 行数 | 状态 | 说明 |
|------|------|------|------|------|
| **LLM抽象层** | `my_cli/llm.py` | 299 | ✅ 完整 | LLM类、create_llm()工厂、重试机制 |
| **消息转换** | `my_cli/soul/message.py` | 192 | ✅ 完整 | ToolResult→Message转换 |
| **工具集** | `my_cli/soul/toolset.py` | 126 | ✅ 完整 | CustomToolset上下文管理 |
| **Soul引擎** | `my_cli/soul/kimisoul.py` | 504 | ✅ 完整 | @tenacity.retry重试机制 |
| **参数提取** | `my_cli/tools/__init__.py` | 177 | ✅ 完整 | extract_key_argument() |
| **UI Shell** | `my_cli/ui/shell/visualize.py` | 252 | ✅ 完整 | ToolCallPart流式支持 |
| **UI Print** | `my_cli/ui/print/__init__.py` | 319 | ✅ 完整 | ToolCallPart流式支持 |
| **运行时** | `my_cli/soul/runtime.py` | 56 | ✅ 完整 | 使用LLM替代ChatProvider |
| **工厂函数** | `my_cli/soul/__init__.py` | 597 | ✅ 完整 | create_soul()使用create_llm() |

**已实现的核心文件总计**: ~2,500 行高质量代码

---

### 🔲 **Stage 18 准备就绪** (会话与规范)

| 模块 | 文件 | 行数 | 状态 | 说明 |
|------|------|------|------|------|
| **会话管理** | `my_cli/session.py` | 83 | 🔲 框架 | 有TODO，需要完整实现 |
| **Agent规范** | `my_cli/agentspec.py` | 66 | 🔲 框架 | 有TODO，需要完整实现 |
| **上下文** | `my_cli/soul/context.py` | 93 | 🔲 框架 | 有基础实现，需完善 |
| **元数据** | `my_cli/metadata.py` | 52 | 🔲 简化版 | 硬编码版本，需改进 |

---

### 🔲 **Stage 19-21 框架已创建** (高级特性)

| 模块 | 文件 | 行数 | 状态 | 说明 |
|------|------|------|------|------|
| **时间旅行** | `my_cli/soul/denwarenji.py` | 197 | 🔲 框架 | DMail类定义，需实现逻辑 |
| **压缩** | `my_cli/soul/compaction.py` | 124 | 🔲 框架 | 有常量定义，需实现函数 |
| **批准** | `my_cli/soul/approval.py` | 234 | 🔲 部分 | 有部分实现，需完善 |
| **分享** | `my_cli/share.py` | 49 | 🔲 框架 | 有TODO注释 |
| **异常** | `my_cli/exception.py` | 38 | 🔲 基础 | 需添加BackToTheFuture |

---

### ✅ **基础模块已完善**

| 模块 | 文件 | 行数 | 状态 | 说明 |
|------|------|------|------|------|
| **CLI入口** | `my_cli/cli.py` | 125 | ✅ 完整 | Click命令行框架 |
| **应用层** | `my_cli/app.py` | 315 | ✅ 完整 | MyCLI应用类 |
| **配置管理** | `my_cli/config.py` | 417 | ✅ 完整 | Pydantic配置系统 |
| **常量** | `my_cli/constant.py` | 27 | ✅ 完整 | 系统常量定义 |
| **工具utils** | `my_cli/tools/utils.py` | 323 | ✅ 完整 | ToolResultBuilder等 |
| **工具集** | `my_cli/tools/toolset.py` | 137 | ✅ 完整 | SimpleToolset |
| **Bash工具** | `my_cli/tools/bash/__init__.py` | N/A | ✅ 完整 | Bash工具 |
| **File工具** | `my_cli/tools/file/__init__.py` | N/A | ✅ 完整 | ReadFile/WriteFile |
| **Shell UI** | `my_cli/ui/shell/*.py` | ~600 | ✅ 完整 | 完整Shell界面 |
| **Wire机制** | `my_cli/wire/*.py` | N/A | ✅ 完整 | 消息传递机制 |
| **ACP框架** | `my_cli/ui/acp/__init__.py` | 144 | 🔲 框架 | LSP风格客户端 |

**基础模块总计**: ~2,000 行代码

---

## 🎯 后续阶段完整规划

### ⭐ **Stage 18: 会话管理 + Agent规范** (立即可开始)

**优先级**: 🔥🔥🔥🔥🔥 (最高)

**完成条件**: 实现4个关键文件，让CLI支持会话持久化和Agent规范加载

#### 📁 1. my_cli/session.py (83→200行)
**当前状态**: TODO注释 + 框架类定义

**需要实现**:
```python
class Session:
    def __init__(self, work_dir: Path, session_id: str):
        # TODO: 实现 history_file 属性
        self.history_file = work_dir / ".kimi_history" / f"{session_id}.jsonl"

    @classmethod
    async def create(cls, work_dir: Path, agent_name: str = "default") -> Session:
        # TODO: 生成会话ID（时间戳+随机数）
        # TODO: 创建历史文件目录
        # TODO: 保存Session元数据

    @classmethod
    async def continue_(cls, work_dir: Path, session_id: str) -> Session | None:
        # TODO: 从历史文件恢复会话
        # TODO: 验证会话完整性

    async def save_message(self, message: Message) -> None:
        # TODO: 将Message保存为JSONL格式

    async def load_history(self) -> list[Message]:
        # TODO: 从JSONL文件加载历史
```

**测试用例**:
```python
# 测试创建会话
session = await Session.create(work_dir)
assert session.id.startswith("session_")
assert session.history_file.exists()

# 测试保存消息
await session.save_message(user_msg)
await session.save_message(ai_msg)

# 测试加载历史
history = await session.load_history()
assert len(history) == 2
```

#### 📁 2. my_cli/agentspec.py (66→150行)
**当前状态**: TODO注释 + load_agent_spec()框架

**需要实现**:
```python
from pydantic import BaseModel
from typing import list

class AgentSpec(BaseModel):
    name: str
    description: str
    system_prompt: str
    tools: list[str]
    capabilities: set[str] = set()

async def load_agent_spec(file_path: Path) -> AgentSpec:
    # TODO: 支持YAML和JSON格式
    # TODO: 验证AgentSpec完整性
    # TODO: 返回AgentSpec实例

async def create_agent_from_spec(spec: AgentSpec) -> Agent:
    # TODO: 根据规范创建Agent实例
    # TODO: 加载指定工具
    # TODO: 设置system_prompt
```

**AgentSpec示例文件**:
```yaml
# agents/coding-assistant.yaml
name: "Coding Assistant"
description: "专业代码助手"
system_prompt: |
  你是一个专业的代码助手...
tools:
  - Bash
  - ReadFile
  - WriteFile
  - Glob
  - Grep
capabilities:
  - coding
  - file_ops
```

#### 📁 3. my_cli/soul/context.py (93→150行)
**当前状态**: 基础Context类，有token_count TODO

**需要实现**:
```python
class Context:
    def __init__(self):
        self.messages: list[Message] = []
        self.n_checkpoints = 0
        # TODO: 实现 token_count 动态计算
        self.token_count = 0

    async def restore(self, history_file: Path) -> None:
        # TODO: 从JSONL文件恢复Context
        # TODO: 解析Message并加载
        # TODO: 计算token_count

    async def save(self, history_file: Path) -> None:
        # TODO: 保存Context到JSONL文件
        # TODO: 批量写入优化

    async def compact(self, summary_messages: list[Message]) -> None:
        # TODO: Stage 19实现：压缩Context
        pass
```

#### 📁 4. my_cli/metadata.py (52→80行)
**当前状态**: 硬编码版本信息

**需要实现**:
```python
try:
    from importlib.metadata import version
    VERSION = version("kimi_cli")
except Exception:
    VERSION = "0.1.0"  # fallback

import os
BUILD_COMMIT = os.getenv("BUILD_COMMIT", "unknown")
BUILD_TIME = os.getenv("BUILD_TIME", "unknown")

def get_version_info() -> dict:
    # TODO: 返回版本信息字典
    return {
        "version": VERSION,
        "commit": BUILD_COMMIT,
        "build_time": BUILD_TIME,
    }
```

**Stage 18实施计划**:
- **第1周**: session.py 完整实现 + 测试
- **第2周**: agentspec.py 完整实现 + 示例文件
- **第3周**: context.py 完善 + metadata.py 改进
- **第4周**: 集成测试 + CLI参数支持 `--session` `--agent`

---

### ⭐ **Stage 19: 时间旅行 + Context压缩**

**优先级**: 🔥🔥🔥🔥 (高)

**完成条件**: 实现CheckPoint/D-Mail机制，自动Context压缩

#### 📁 1. my_cli/soul/denwarenji.py (197→300行)
**当前状态**: DMail类定义 + TODO注释

**需要实现**:
```python
class DenwaRenji:
    def __init__(self):
        self._n_checkpoints = 0
        self._pending_dmails: list[DMail] = []

    def set_n_checkpoints(self, n: int) -> None:
        # TODO: 更新检查点数量
        self._n_checkpoints = n

    def send_dmail(self, checkpoint_id: int, content: str) -> None:
        # TODO: 发送D-Mail到指定检查点
        # TODO: 验证checkpoint_id有效性
        dmail = DMail(checkpoint_id=checkpoint_id, content=content)
        self._pending_dmails.append(dmail)

    def fetch_pending_dmail(self) -> DMail | None:
        # TODO: 获取待处理的D-Mail
        # TODO: 检查是否应该触发时间旅行
        if self._pending_dmails:
            return self._pending_dmails.pop(0)
        return None
```

#### 📁 2. my_cli/soul/compaction.py (124→200行)
**当前状态**: 常量定义 + compact_messages() TODO

**需要实现**:
```python
async def compact_messages(
    messages: list[Message],
    target_count: int = 10,
) -> list[Message]:
    """
    压缩消息列表（保留重要消息，生成摘要）
    """
    # TODO: Stage 19 实现压缩算法
    # 1. 保留最近10条消息
    # 2. 将中间旧消息压缩为摘要
    # 3. 保留工具调用的关键信息
    # 4. 使用LLM生成摘要
    pass

def should_compact(context: Context) -> bool:
    # TODO: 判断是否需要压缩
    # 基于token_count和max_context_size
    usage = context.token_count / context.max_context_size
    return usage > COMPACTION_THRESHOLD
```

#### 📁 3. my_cli/soul/kimisoul.py 增强
**当前状态**: 504行，Stage 17已完成

**需要添加**:
```python
# 在KimiSoul类中添加
async def _checkpoint(self) -> None:
    """保存检查点"""
    # TODO: 保存Context快照
    self._context.n_checkpoints += 1
    # TODO: 更新DenwaRenji检查点数量

async def compact_context(self) -> None:
    """压缩Context（超过阈值时自动调用）"""
    # TODO: 调用compaction.compact_messages()
    # TODO: 替换旧消息为摘要
    # TODO: 重新计算token_count

async def _step(self, ...) -> None:
    # 在每个step中
    # TODO: 检查并处理D-Mail
    # TODO: 检查是否需要压缩
    # TODO: 定期保存检查点
```

#### 📁 4. my_cli/exception.py (38→60行)
**需要添加**:
```python
class BackToTheFuture(Exception):
    """时间旅行异常 - 触发回滚到检查点"""

    def __init__(self, checkpoint_id: int, messages: list[Message]):
        self.checkpoint_id = checkpoint_id
        self.messages = messages
        super().__init__(f"Time travel to checkpoint {checkpoint_id}")

# 在kimisoul.py中使用
if dmail := self._denwa_renji.fetch_pending_dmail():
    raise BackToTheFuture(dmail.checkpoint_id, [...])
```

---

### ⭐ **Stage 20: Approval系统完善**

**优先级**: 🔥🔥🔥 (中)

**当前状态**: approval.py (234行) 有部分实现

**需要完善**:
```python
class Approval:
    def __init__(self, yolo: bool = False):
        self._request_queue: asyncio.Queue = asyncio.Queue()
        self._yolo = yolo
        self._auto_approve_actions: set[str] = set()

    async def request(
        self,
        sender: str,
        action: str,
        description: str,
    ) -> bool:
        # TODO: 如果是YOLO模式，直接批准
        # TODO: 如果在auto_approve_actions中，直接批准
        # TODO: 否则，放入请求队列等待用户响应

    async def fetch_request(self) -> ApprovalRequest | None:
        # TODO: 从队列获取请求
        # TODO: 返回给Soul通过Wire发送到UI
```

**UI层支持**:
- Shell UI: 显示批准提示，等待用户输入
- Print UI: 暂停等待用户输入
- ACP UI: 发送JSON-RPC批准请求

---

### ⭐ **Stage 21: 分享功能 + MCP集成**

**优先级**: 🔥🔥 (低)

#### 📁 1. my_cli/share.py (49→150行)
```python
async def share_session(
    session: Session,
    anonymize: bool = True,
) -> str:
    """
    分享会话历史
    """
    # TODO: 读取历史
    history = await session.load_history()

    # TODO: 脱敏处理
    if anonymize:
        history = sanitize_history(history)

    # TODO: 上传到分享服务
    share_url = await upload_share(history)

    return share_url

def sanitize_history(history: list[Message]) -> list[Message]:
    """移除敏感信息"""
    # TODO: 移除API Key
    # TODO: 替换真实路径为占位符
    # TODO: 脱敏个人信息
    pass
```

#### 📁 2. Tools模块扩展
**需要实现的工具**:
- `my_cli/tools/file/glob.py` - 文件模式匹配
- `my_cli/tools/file/grep.py` - 内容搜索
- `my_cli/tools/web/search.py` - 网页搜索
- `my_cli/tools/web/fetch.py` - 获取网页
- `my_cli/tools/dmail/send.py` - 发送D-Mail
- `my_cli/tools/think.py` - 思考模式
- `my_cli/tools/todo.py` - TODO列表

---

## 📊 文件依赖关系图 (已更新)

```
my_cli/
├─ ✅ llm.py (Stage 17)
│  └─ 被 Runtime 使用
│
├─ 🔲 session.py (Stage 18) ⭐ NEXT
│  └─ 被 KimiSoul 使用
│
├─ 🔲 agentspec.py (Stage 18) ⭐ NEXT
│  └─ 被 CLI 使用 (--agent 参数)
│
├─ ✅ config.py
│  └─ 被 create_soul() 使用
│
├─ ✅ app.py
│  ├─ run_print_mode() ✅
│  ├─ run_shell_mode() ✅
│  └─ Stage 18: 添加 --session, --agent 参数
│
├─ 🔲 context.py (Stage 18-19)
│  ├─ Stage 18: restore/save (历史持久化)
│  └─ Stage 19: compact (Context压缩)
│
├─ 🔲 denwarenji.py (Stage 19)
│  └─ 被 KimiSoul 使用 (时间旅行)
│
├─ 🔲 compaction.py (Stage 19)
│  └─ 被 KimiSoul.compact_context() 使用
│
├─ 🔲 approval.py (Stage 20)
│  ├─ 被 Runtime 创建
│  └─ 被危险工具使用 (request 批准)
│
└─ 🔲 share.py (Stage 21)
   └─ 被 CLI 使用 (--share 参数)
```

---

## 🧪 测试策略 (已更新)

### Stage 18 测试矩阵

| 测试类型 | 测试内容 | 命令 |
|---------|---------|------|
| **单元测试** | Session.create() | `pytest tests/test_session.py::test_create` |
| **单元测试** | Session保存/加载 | `pytest tests/test_session.py::test_save_load` |
| **单元测试** | AgentSpec加载 | `pytest tests/test_agentspec.py::test_load_yaml` |
| **集成测试** | 完整会话流程 | `pytest tests/test_session.py::test_full_session` |
| **集成测试** | CLI参数支持 | `pytest tests/test_cli.py::test_session_args` |
| **E2E测试** | 历史持久化 | `python cli.py -c "test" --session s1 && python cli.py --continue s1` |

### Stage 19 测试矩阵

| 测试类型 | 测试内容 | 命令 |
|---------|---------|------|
| **单元测试** | Checkpoint保存 | `pytest tests/test_denwarenji.py::test_checkpoint` |
| **单元测试** | D-Mail发送 | `pytest tests/test_denwarenji.py::test_send_dmail` |
| **单元测试** | Context压缩 | `pytest tests/test_compaction.py::test_compact_messages` |
| **集成测试** | 自动压缩 | `pytest tests/test_kimisoul.py::test_auto_compact` |
| **集成测试** | 时间旅行回滚 | `pytest tests/test_denwarenji.py::test_time_travel` |

---

## 💡 开发建议 (已优化)

### 1. 优先完成 Stage 18 ⭐
**理由**:
- ✅ 文件已存在，只有TODO注释，实现成本低
- ✅ Session是后续所有功能的基础
- ✅ AgentSpec提供灵活性和可配置性
- ✅ 用户体验提升明显（历史持久化）

### 2. 渐进式开发策略
```bash
# 每次只实现一个功能块
git add my_cli/session.py
git commit -m "feat(session): 实现Session类和create()方法"

# 立即测试
pytest tests/test_session.py -v

# 然后实现下一个功能
git add my_cli/session.py
git commit -m "feat(session): 实现continue_()方法"
```

### 3. 及时更新TODO
```python
# 在TODO实现后立即更新状态
# ❌ BEFORE:
# TODO: Stage 18 实现

# ✅ AFTER:
# ✅ Stage 18 实现 (PR #123)
```

### 4. 文档同步更新
每个功能完成后，同步更新：
- `docs/STAGE_18_*.md` - 实现文档
- `README.md` - 使用示例
- `tests/` - 测试覆盖

---

## 🚀 快速开始 (已更新)

### Stage 18 第一天行动清单

**上午** (2小时):
- [ ] 阅读官方代码 `kimi-cli-fork/src/kimi_cli/session.py`
- [ ] 在 `my_cli/session.py` 中删除TODO注释
- [ ] 实现 `Session.__init__()` 和 `create()` 方法

**下午** (3小时):
- [ ] 编写单元测试 `tests/test_session.py`
- [ ] 运行测试验证 `pytest tests/test_session.py -v`
- [ ] 实现 `continue_()` 方法

**第二天** (5小时):
- [ ] 实现 `save_message()` 和 `load_history()`
- [ ] 编写集成测试
- [ ] 更新CLI参数支持 `--session`

**预计**: 2天完成Stage 18的核心功能

---

## 📚 学习资源 (已补充)

### 官方参考代码路径
```bash
# 克隆官方仓库
git clone https://github.com/Lcoderfit/kimi-cli-fork.git
cd kimi-cli-fork/src/kimi_cli

# 重点查看文件
cat session.py           # Session管理
cat agentspec.py         # Agent规范
cat soul/context.py      # 上下文持久化
cat soul/denwarenji.py   # 时间旅行
cat soul/compaction.py   # 压缩
cat soul/approval.py     # 批准
```

### 关键依赖库文档
- **Pydantic**: https://docs.pydantic.dev/
- **PyYAML**: https://pyyaml.org/
- **asyncio.Queue**: https://docs.python.org/3/library/asyncio-queue.html
- **contextvar**: https://docs.python.org/3/library/contextvars.html

---

## ✅ 总结 (已完善)

这个学习工作流程v2.1基于实际代码库扫描，为后续开发提供：

### 📋 清晰的状态报告
- **已实现**: 2,500行核心代码（Stage 17）
- **框架就绪**: 1,000行TODO注释文件（Stage 18-21）
- **基础完善**: 2,000行基础设施代码

### 🎯 精确的下一步行动
- **Stage 18**: 4个文件，4周完成
- **Stage 19**: 4个文件，3周完成
- **Stage 20**: 1个文件，2周完成
- **Stage 21**: 2个文件，2周完成

### 🔧 实用的开发指南
- 具体到每天的开发任务
- 单元测试+集成测试+E2E测试
- 官方代码对照和最佳实践
- Git提交规范和文档更新

### 📊 成功指标
- **Stage 18**: CLI支持 `--session` 和 `--agent` 参数
- **Stage 19**: 自动Context压缩，时间旅行D-Mail
- **Stage 20**: 危险操作需要用户批准
- **Stage 21**: 会话历史分享功能

**立即行动**: 开始Stage 18，优先实现 `my_cli/session.py`！

---

**Created by**: 老王 (暴躁但专业)
**Version**: 2.1 (基于实际代码库)
**Last Updated**: 2025-11-17
**Status**: 🟢 Stage 18 Ready to Start
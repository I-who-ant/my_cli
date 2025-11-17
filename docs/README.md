# Kimi CLI 学习文档

本目录包含 Kimi CLI 从零开始的实现文档，按阶段组织。

## 📚 文档目录

### 阶段性学习文档

| 文档 | 阶段 | 说明 |
|------|------|------|
| [stage-04-05-soul-engine.md](./stage-04-05-soul-engine.md) | Stage 4-5 | Soul 引擎实现，集成 kosong 框架和 LLM |
| [stage-06-wire-mechanism.md](./stage-06-wire-mechanism.md) | Stage 6 | Wire 消息队列机制，实现流式输出 |
| [STAGE_06_SUMMARY.md](./STAGE_06_SUMMARY.md) | Stage 6 总结 | ⭐ Stage 6 完成总结（包含验收测试）|
| [STAGE_07_SUMMARY.md](./STAGE_07_SUMMARY.md) | Stage 7 总结 | ⭐ Stage 7 工具系统基础架构总结 |

### 架构设计文档

| 文档 | 类型 | 说明 |
|------|------|------|
| [wire-architecture-design.md](./wire-architecture-design.md) | 架构设计 | Wire 机制的深度架构设计和原理解析 |
| [some_else_docs/streaming-output-implementation.md](./some_else_docs/streaming-output-implementation.md) | 流式输出 | 流式输出完整实现详解（SSE → Terminal）|
| [STAGE_07_vs_OFFICIAL.md](./STAGE_07_vs_OFFICIAL.md) | 对比分析 | ⭐ Stage 7 vs 官方工具系统对比 |

### 流程分析文档

| 文档 | 说明 |
|------|------|
| [some_process_docs.md](./some_process_docs.md) | 原始流程分析文档 |

## 🎯 学习路径

### 推荐阅读顺序

1. **Stage 4-5**：Soul 引擎基础
   - 阅读 [stage-04-05-soul-engine.md](./stage-04-05-soul-engine.md)
   - 理解 kosong 框架集成
   - 理解配置管理系统

2. **Stage 6**：Wire 机制
   - 阅读 [stage-06-wire-mechanism.md](./stage-06-wire-mechanism.md)
   - 理解异步消息队列
   - 理解流式输出原理

3. **深入架构**：Wire 设计思想
   - 阅读 [wire-architecture-design.md](./wire-architecture-design.md)
   - 理解 ContextVar 机制
   - 理解任务调度和并发管理

## 📖 核心概念速查

### Wire 机制

- **Wire**：Soul 和 UI 之间的消息队列
- **WireSoulSide**：Soul 层发送接口（生产者）
- **WireUISide**：UI 层接收接口（消费者）
- **ContextVar**：线程安全的全局状态管理
- **run_soul()**：Soul 和 UI 的调度器
- **wire_send()**：发送消息到 Wire 的全局函数

### Soul 引擎

- **Soul Protocol**：AI Agent 引擎的接口定义
- **KimiSoul**：Soul Protocol 的具体实现
- **Agent**：定义 AI 的身份和能力
- **Runtime**：管理 ChatProvider 和执行配置
- **Context**：管理对话历史

### 配置系统

- **Config**：主配置类
- **LLMProvider**：LLM 提供商配置
- **LLMModel**：LLM 模型配置
- **环境变量覆盖**：支持 `KIMI_API_KEY` 等环境变量

## 🔧 代码位置索引

### Stage 6 核心代码

| 模块 | 文件 | 说明 |
|------|------|------|
| Wire 队列 | `my_cli/wire/__init__.py` | Wire、WireSoulSide、WireUISide |
| Wire 消息 | `my_cli/wire/message.py` | 消息类型定义 |
| Soul 集成 | `my_cli/soul/__init__.py` | wire_send、run_soul |
| KimiSoul | `my_cli/soul/kimisoul.py` | on_message_part 回调 |
| Print UI | `my_cli/ui/print/__init__.py` | UI Loop 实现 |

### Stage 4-5 核心代码

| 模块 | 文件 | 说明 |
|------|------|------|
| 配置管理 | `my_cli/config.py` | Config、Provider、Model |
| Soul 协议 | `my_cli/soul/__init__.py` | Soul Protocol、create_soul |
| KimiSoul | `my_cli/soul/kimisoul.py` | KimiSoul 实现 |
| Agent | `my_cli/soul/agent.py` | Agent 实现 |
| Runtime | `my_cli/soul/runtime.py` | Runtime 实现 |
| Context | `my_cli/soul/context.py` | Context 实现 |

## 🎓 常见问题

### Q1：Wire 和直接调用有什么区别？

**直接调用**（Stage 4-5）：
```python
async for chunk in soul.run(command):
    print(chunk)
```

**Wire 机制**（Stage 6）：
```python
await run_soul(soul, command, ui_loop, cancel_event)

async def ui_loop(wire_ui):
    while True:
        msg = await wire_ui.receive()
        print(msg)
```

**优势**：
- ✅ Soul 和 UI 完全解耦
- ✅ 真正的流式输出
- ✅ 支持用户中断
- ✅ 支持多种 UI

### Q2：ContextVar 和全局变量有什么区别？

- **全局变量**：所有任务共享，并发不安全
- **ContextVar**：每个任务独立的上下文，并发安全

### Q3：如何扩展新的消息类型？

1. 在 `wire/message.py` 定义新消息类
2. 更新 `Event` 类型联合
3. UI Loop 添加处理逻辑

## 📝 文档编写规范

### 文档结构

每个阶段文档应包含：

1. **学习目标**：本阶段要学习什么
2. **核心概念**：关键概念详解
3. **代码实现**：具体实现和代码示例
4. **架构演进**：从上一阶段到本阶段的变化
5. **测试验证**：如何验证实现正确性
6. **参考资料**：官方源码位置

### 代码示例规范

```python
# ✅ 好的示例：有注释、清晰
def wire_send(msg: WireMessage) -> None:
    """发送消息到 Wire"""
    wire = _current_wire.get()  # 获取当前 Wire
    wire.soul_side.send(msg)    # 发送消息

# ❌ 坏的示例：无注释、混乱
def f(m):
    w=g()
    w.s.s(m)
```

## 🚀 下一步

- **Stage 7**：工具系统（Toolset + kosong.step）
- **Stage 8**：高级特性（Compaction + Approval）
- **Stage 9**：Shell UI（交互式界面）

---

**最后更新**：2025-01-15
**维护者**：老王

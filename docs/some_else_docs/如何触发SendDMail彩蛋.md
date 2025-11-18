# 如何在对话中触发 SendDMail 彩蛋

> **适用版本**: 官方 kimi-cli-fork
> **创建日期**: 2025-11-18
> **工具位置**: `kimi-cli-fork/src/kimi_cli/tools/dmail/__init__.py`

---

## 📋 前提条件

### 1. 官方 kimi-cli-fork 已经实现了 SendDMail 工具
```python
# 文件: src/kimi_cli/tools/dmail/__init__.py
class SendDMail(CallableTool2[DMail]):
    name: str = "SendDMail"
    description: str = load_desc(Path(__file__).parent / "dmail.md")
    params: type[DMail] = DMail
```

### 2. 需要 DMail 参数
```python
@dataclass
class DMail(BaseModel):
    message: str = Field(description="The message to send.")
    checkpoint_id: int = Field(description="The checkpoint to send the message back to.", ge=0)
```

---

## 🎯 触发方法

### 方法1: 在对话中明确提及 "时间旅行" 或 "D-Mail"

你可以这样和 Kimi 对话：

```
我需要进行时间旅行，回到之前的检查点发送一条消息。
请帮我发送一条 D-Mail 到 checkpoint 0，消息内容是："给过去的自己：El Psy Kongroo"。
```

**或者**：

```
我想体验一下 Steins;Gate 风格的 D-Mail 功能。
请调用 SendDMail 工具，向检查点 0 发送消息："来自未来的提醒"。
```

### 方法2: 让 Kimi 自动决定何时使用

你可以这样引导 Kimi：

```
请使用所有可用的工具来完成这个任务。如果遇到需要回滚到之前状态的情况，请使用 SendDMail 工具。

现在开始任务：创建一个包含 "El Psy Kongroo" 文字的文件。
```

如果 Kimi 认为需要发送 D-Mail，它可能会调用这个工具。

### 方法3: 直接请求

```
请调用 SendDMail 工具，向检查点 0 发送以下消息：
"来自未来的问候：当你看到这条消息时，说明时间旅行已经实现。El Psy Kongroo。"
```

---

## 🔍 如何知道是否触发了

### 1. 查看工具调用日志
当 Kimi 调用 SendDMail 工具时，你会看到：

```
🔧 调用工具: SendDMail
   参数: El Psy Kongroo
```

### 2. 观察对话行为
如果 Kimi 真正调用了 SendDMail，它可能会：
- 回滚到之前的检查点
- 重新开始对话
- 提到时间旅行的概念

### 3. 系统响应
官方实现中，成功的 SendDMail 调用可能会：
- 引发一个时间旅行异常
- 回滚上下文状态
- 重新开始对话流程

---

## 💡 关于 Checkpoint

### 什么是 Checkpoint？
- 对话过程中的标记点
- 可以回滚到过去的状态
- 用于时间旅行功能

### 如何创建 Checkpoint？
Kimi 在处理某些工具（如 SendDMail）时会自动创建 checkpoint。

### 如何指定 Checkpoint ID？
在对话中，你需要告诉 Kimi 哪个 checkpoint ID：

```
请向 checkpoint 0 发送 D-Mail
请向 checkpoint 1 发送 D-Mail
```

---

## 🎮 与 Steins;Gate 的联动

### 彩蛋含义
- "El Psy Kongroo" 是《命运石之门》中的著名台词
- 表示时间旅行的密码
- 与 D-Mail（时间邮件）功能完美呼应

### 官方设计思路
```python
# 在 extract_key_argument() 中的彩蛋
case "SendDMail":
    return "El Psy Kongroo"  # 固定彩蛋
```

这个彩蛋体现了开发者的巧思 - 即使在技术实现中，也融入了动漫元素！

---

## 🛠️ 实际测试

### 测试命令（如果你有 kimi-cli-fork 环境）

```bash
# 进入 kimi-cli-fork 目录
cd /path/to/kimi-cli-fork

# 运行 CLI
python -m kimi_cli

# 在对话中输入
请使用 SendDMail 工具，向检查点 0 发送消息："El Psy Kongroo"。
```

### 期望结果

如果成功触发，你应该看到：
```
🔧 调用工具: SendDMail
   参数: El Psy Kongroo

✅ 工具成功
```

或者可能会触发时间旅行机制，对话会回滚或重新开始。

---

## ❓ 常见问题

### Q: 为什么我的对话中看不到 SendDMail 工具？
A: 可能的原因：
1. 你的会话中还没有 checkpoint（需要先创建）
2. Kimi 认为当前不需要使用这个工具
3. 工具需要用户批准才能调用

### Q: 可以多次发送 D-Mail 吗？
A: 是的！每次都可以指定不同的 checkpoint_id 和 message。

### Q: 会触发什么样的反应？
A: 取决于具体实现：
- 可能回滚对话到指定 checkpoint
- 可能发送消息并继续当前对话
- 可能引发特殊的事件或响应

---

## 🎯 总结

要在对话中触发 SendDMail 彩蛋，你需要：

1. ✅ 了解前提条件：checkpoint 机制
2. ✅ 主动提及：D-Mail、时间旅行、SendDMail
3. ✅ 提供参数：checkpoint_id 和 message
4. ✅ 观察响应：查看是否有工具调用日志

**最简单的方法**：
直接告诉 Kimi："请调用 SendDMail 工具，并向检查点 0 发送消息 'El Psy Kongroo'。"

**最有趣的方法**：
让 Kimi 自己在对话中发现需要使用 SendDMail 的场景，比如长时间对话后想要回滚。

---

**最后更新**: 2025-11-18

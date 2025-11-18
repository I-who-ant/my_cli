# Kimi 工具集完整配置指南

> **问题**: Kimi 只显示 9 个工具，缺少 SendDMail、Think、SearchWeb 等
> **分析**: 可能使用了简化版工具集配置
> **解决方案**: 启用完整工具集或通过配置启用缺失的工具
> **创建日期**: 2025-11-18

---

## 📊 问题现状

### Kimi 当前显示的工具（9个）
- ✅ Task
- ✅ SetTodoList
- ✅ Bash
- ✅ ReadFile
- ✅ Glob
- ✅ Grep
- ✅ WriteFile
- ✅ StrReplaceFile
- ✅ FetchURL

### 官方完整工具集（20+个）
- ❌ SendDMail（时间旅行）
- ❌ Think（思考模式）
- ❌ SearchWeb（网页搜索）
- ❌ CMD（Windows 命令行）
- ❌ BrowseUrl（浏览 URL）
- ❓ 等等...

---

## 🔍 原因分析

### 1. 工具集分层设计
```
kimi-cli-fork 工具集
├── 基础工具（9个）- 始终可用
│   ├── 文件操作：ReadFile, WriteFile, Glob, Grep
│   ├── 命令执行：Bash
│   ├── 网络：FetchURL
│   └── 任务管理：Task, SetTodoList
│
└── 高级工具（需要配置）
    ├── 时间旅行：SendDMail
    ├── 搜索：SearchWeb, BrowseUrl
    ├── 思考：Think
    └── 系统：CMD
```

### 2. 可能的原因
- **简化版工具集**：为了性能或安全考虑，只加载基础工具
- **配置缺失**：某些工具需要配置文件或环境变量
- **权限限制**：某些工具需要管理员批准
- **模式限制**：可能需要特定启动模式

---

## 🛠️ 解决方案

### 方案1: 检查配置文件

#### 查找配置文件
```bash
# 常见配置文件位置
find ~ -name "*.json" -o -name "*.yaml" -o -name "*.yml" | grep -i kimi

# 查找 kimi-cli 相关配置
find ~ -type d -name "*kimi*" 2>/dev/null

# 查看当前目录配置
ls -la | grep -i kimi
```

#### 检查 kimi-cli-fork 源码中的配置
```bash
# 查看工具注册逻辑
grep -r "SimpleToolset\|create_toolset" /path/to/kimi-cli-fork/src/
```

### 方案2: 通过 Kimi 对话启用

#### 方式1: 请求启用完整工具集
```
请启用所有可用的工具，包括 SendDMail、Think、SearchWeb 等。
或者告诉我如何配置才能访问完整工具集。
```

#### 方式2: 检查可用工具
```
请列出所有可能的工具列表，包括那些我可能还没有启用的。
如果有哪些工具是可选的，请告诉我如何启用它们。
```

#### 方式3: 检查权限
```
我需要使用 SendDMail 工具进行时间旅行功能。
请告诉我如何申请该工具的使用权限，或者如何配置会话以获得完整工具访问权限。
```

### 方案3: 检查会话启动参数

#### 查看启动方式
你可能是通过以下方式启动的：
```bash
# 方式1: 简化启动
python -m kimi_cli

# 方式2: 带参数启动
python -m kimi_cli --simple-tools  # 可能只加载基础工具

# 方式3: 完整启动
python -m kimi_cli --full-tools    # 加载所有工具
python -m kimi_cli --all-tools     # 加载所有工具
```

### 方案4: 通过 Web 界面启用

如果你使用的是 Web 界面：
1. 查看设置/配置页面
2. 寻找"工具"或"工具集"选项
3. 启用"完整工具集"或"高级工具"
4. 重启对话

---

## 🎯 针对性的对话模板

### 模板1: 直接请求
```
你好，我注意到我的可用工具列表不完整。
请问如何才能启用所有工具，包括：
- SendDMail（时间旅行功能）
- Think（思考模式）
- SearchWeb（网页搜索）
- CMD（Windows 命令行）

或者，你是否知道当前的工具集有什么限制条件？
```

### 模板2: 询问配置
```
我想使用 SendDMail 工具进行时间旅行实验。
但是我的工具列表中没有这个工具。
请问：
1. 是否需要特定配置才能使用？
2. 是否需要升级到完整版本？
3. 是否有替代方案？
```

### 模板3: 检查权限
```
我在尝试调用 SendDMail 工具时，收到错误说工具不存在。
请问这是什么原因？是否需要申请权限？
我的用户ID是 [你的ID]，想使用时间旅行功能。
```

---

## 📝 问题反馈

如果以上方案都不行，可能的原因：

### 1. **版本限制**
- 你使用的可能是简化版或社区版
- 完整工具集可能只在付费版提供
- 需要升级到最新版本

### 2. **地区限制**
- 某些地区可能没有开放所有功能
- 需要通过特殊渠道申请

### 3. **服务端限制**
- Kimi 的 API 可能对某些工具有特殊限制
- 需要使用特定模型或服务

---

## 🚀 快速测试

### 测试1: 检查工具总数
```
请告诉我当前可用的工具总数，以及完整的工具列表。
如果工具数量少于15个，可能工具集不完整。
```

### 测试2: 尝试使用缺失工具
```
请使用 SearchWeb 工具搜索 "El Psy Kongroo"。
如果成功，说明工具存在；如果失败，查看错误信息。
```

### 测试3: 检查模式
```
我看到我有 Task 工具，请确认：
1. 我的工具集是否处于"完整模式"？
2. 如果不是，如何切换到完整模式？
3. 当前工具集有哪些限制？
```

---

## 💡 官方建议

根据 kimi-cli-fork 源码，SendDMail 工具需要：

1. **DenwaRenji 系统**：
   ```python
   # 工具初始化需要 DenwaRenji 实例
   def __init__(self, denwa_renji: DenwaRenji):
       self._denwa_renji = denwa_renji
   ```

2. **Checkpoint 机制**：
   ```python
   # 需要检查点支持
   for tool in agent.toolset.tools:
       if tool.name == "SendDMail":
           self._checkpoint_with_user_message = True
   ```

3. **完整工具集**：
   ```python
   # 完整工具集应该包含
   all_tools = [
       Bash(), ReadFile(), WriteFile(),
       # ...
       SendDMail(denwa_renji),  # 重点
       Think(), SearchWeb(),
       # ...
   ]
   ```

---

## 📊 成功标志

如果你成功启用了完整工具集，你应该能看到：
```
可用工具（20+个）：
• Task
• SetTodoList
• Bash
• ReadFile
• Glob
• Grep
• WriteFile
• StrReplaceFile
• FetchURL
• SendDMail  ← 看到它！
• Think
• SearchWeb
• CMD
• ...
```

然后就可以这样触发彩蛋了：
```
请使用 SendDMail 工具，向检查点 0 发送消息："El Psy Kongroo"。
```

---

## 📞 后续支持

如果仍然无法解决问题，建议：

1. **联系 Kimi 官方**：
   - 询问工具集限制原因
   - 申请完整工具集访问权限
   - 了解付费/免费版本区别

2. **查看文档**：
   - Kimi 官方文档关于工具集的说明
   - kimi-cli-fork 的使用指南

3. **社区求助**：
   - GitHub Issues
   - 官方论坛
   - 技术交流群

---

## 🎯 总结

**当前状况**：
- Kimi 只有 9 个基础工具
- 缺少 11+ 个高级工具（包括 SendDMail）

**可能原因**：
- 使用了简化版工具集
- 配置中未启用完整工具集
- 需要特殊权限或模式

**解决方案**：
1. 检查配置和启动参数
2. 通过对话请求启用完整工具集
3. 检查权限和模式设置
4. 联系官方获取支持

**目标**：获得 20+ 个工具的完整工具集，特别是 SendDMail！

---

**最后更新**: 2025-11-18

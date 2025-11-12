# 分阶段学习工作流指南

## 🎯 学习目标

让你能够：
1. **一轮一轮地学习**：每个阶段都有清晰的检查点
2. **Git 标签管理**：用标签标记每个阶段的完成
3. **GitHub 查看历史**：在 GitHub 上查看每个阶段的提交记录
4. **规范的提交信息**：使用 Conventional Commits 和 emoji

## 📋 学习阶段规划

### 已完成阶段

- [x] **Stage 0**: 项目初始化
- [x] **Stage 1**: 最简 CLI 入口
- [x] **Stage 2**: 应用层框架
- [x] **Stage 3**: Print UI 模式

### 待学习阶段

- [ ] **Stage 4**: Wire 协议层（Soul ↔ UI 通信）
- [ ] **Stage 5**: Soul 核心引擎（LLM 调用）
- [ ] **Stage 6**: Shell UI 模式（交互式终端）
- [ ] **Stage 7**: 工具系统（Function Calling）
- [ ] **Stage 8**: ACP 协议（远程 Agent）
- [ ] **Stage 9**: Wire UI 模式（JSON-RPC 服务）

## 🔖 Git 标签策略

### 标签命名规范

```
stage-{阶段号}-{简短描述}

例如：
- stage-1-cli-entry
- stage-2-app-layer
- stage-3-print-ui
- stage-4-wire-protocol
```

### 创建标签

```bash
# 为当前提交打标签
git tag -a stage-1-cli-entry -m "阶段 1: 最简 CLI 入口完成"

# 推送标签到远程
git push origin stage-1-cli-entry

# 或推送所有标签
git push origin --tags
```

### 查看标签

```bash
# 列出所有标签
git tag

# 查看标签详情
git show stage-1-cli-entry

# 在 GitHub 查看
# https://github.com/I-who-ant/my_cli/tags
```

## 📝 提交信息规范

### Conventional Commits + Emoji

参考你的 `/zcf:git-commit` 命令风格：

```
<emoji> <type>(<scope>): <subject>

<body>

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

### 提交类型对照表

| Emoji | Type | 说明 | 示例 |
|-------|------|------|------|
| 🎉 | init | 初始化项目 | `🎉 init: 项目初始化` |
| ✨ | feat | 新增功能 | `✨ feat(stage4): 实现 Wire 协议层` |
| 🐛 | fix | 修复 Bug | `🐛 fix(cli): 修复参数解析错误` |
| 📝 | docs | 文档更新 | `📝 docs: 添加阶段 4 学习文档` |
| ♻️ | refactor | 代码重构 | `♻️ refactor(app): 优化应用层架构` |
| ✅ | test | 添加测试 | `✅ test(cli): 添加 CLI 单元测试` |
| 🎨 | style | 代码格式 | `🎨 style: 格式化代码` |
| ⚡️ | perf | 性能优化 | `⚡️ perf(soul): 优化 LLM 调用` |
| 🔧 | chore | 构建/配置 | `🔧 chore: 更新依赖` |

## 🚀 完整工作流示例

### 阶段 1-3（已完成）回顾

```bash
# 1. 创建初始提交（已完成）
git add .
git commit -m "🎉 init: My CLI 基础框架 - 阶段 1-3 完整实现"
git push

# 2. 为阶段打标签
git tag -a stage-1-3-foundation -m "阶段 1-3: CLI 入口、应用层、Print UI 完成"
git push origin stage-1-3-foundation
```

### 阶段 4 学习流程（示例）

```bash
# ========================================
# 第 1 步：阅读文档，理解需求
# ========================================
cat docs/stage-04-wire-protocol.md  # 假设有这个文档

# ========================================
# 第 2 步：创建新分支（可选，但推荐）
# ========================================
git checkout -b feature/stage-4-wire-protocol

# ========================================
# 第 3 步：实现 Wire 协议层
# ========================================

# 3.1 创建目录结构
mkdir -p my_cli/wire

# 3.2 创建文件
touch my_cli/wire/__init__.py
touch my_cli/wire/message.py
touch my_cli/wire/queue.py

# 3.3 实现代码（边写边测试）
# ... 编写代码 ...

# 3.4 测试功能
my_cli --verbose -c "测试 Wire 协议"

# ========================================
# 第 4 步：提交代码
# ========================================

# 4.1 查看改动
git status
git diff

# 4.2 添加文件
git add my_cli/wire/

# 4.3 提交（使用 emoji 风格）
git commit -m "$(cat <<'EOF'
✨ feat(stage4): 实现 Wire 协议层

## 新增功能
- Wire Message 数据结构
- asyncio.Queue 消息队列
- Soul ↔ UI 通信机制

## 技术细节
- WireMessage 类定义（message.py）
- MessageQueue 实现（queue.py）
- 支持双向异步通信

## 测试
- 手动测试通过
- Wire 消息正常收发

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"

# ========================================
# 第 5 步：打标签
# ========================================
git tag -a stage-4-wire-protocol -m "阶段 4: Wire 协议层完成"

# ========================================
# 第 6 步：推送到远程
# ========================================
# 如果用了分支
git push origin feature/stage-4-wire-protocol
git push origin stage-4-wire-protocol

# 如果直接在 main 分支
git push origin main
git push origin stage-4-wire-protocol

# ========================================
# 第 7 步：在 GitHub 查看
# ========================================
# 打开浏览器：
# - 提交历史：https://github.com/I-who-ant/my_cli/commits/main
# - 标签列表：https://github.com/I-who-ant/my_cli/tags
# - 具体提交：点击 commit hash 查看详情
```

## 🏷️ 为已完成阶段补打标签

```bash
# 查看当前提交历史
git log --oneline

# 为现有的提交打标签
git tag -a stage-1-3-foundation -m "阶段 1-3: CLI 入口、应用层、Print UI 完成" e5c0887

# 推送标签
git push origin stage-1-3-foundation

# 在 GitHub 查看
# https://github.com/I-who-ant/my_cli/releases
```

## 📊 在 GitHub 查看提交历史

### 方法 1：Commits 页面

```
https://github.com/I-who-ant/my_cli/commits/main
```

可以看到：
- 所有提交的列表
- 每个提交的 emoji 图标
- 提交信息和文件改动
- 提交时间和作者

### 方法 2：Tags 页面

```
https://github.com/I-who-ant/my_cli/tags
```

可以看到：
- 所有标签列表
- 每个标签的说明
- 对应的提交记录
- 下载源码的链接

### 方法 3：Releases 页面

```
https://github.com/I-who-ant/my_cli/releases
```

**可选**：为每个阶段创建 Release

```bash
# 在 GitHub 网页操作：
# 1. 进入 Releases 页面
# 2. 点击 "Create a new release"
# 3. 选择标签 stage-4-wire-protocol
# 4. 填写发布说明
# 5. 点击 "Publish release"
```

### 方法 4：单个提交详情

```
https://github.com/I-who-ant/my_cli/commit/<commit-hash>
```

可以看到：
- 完整的提交信息
- 文件改动的 diff
- 添加的行数和删除的行数

## 🔍 本地查看提交历史

### 图形化日志

```bash
# 漂亮的提交历史
git log --graph --pretty=format:'%Cred%h%Creset -%C(yellow)%d%Creset %s %Cgreen(%cr) %C(bold blue)<%an>%Creset' --abbrev-commit

# 或使用别名
git config --global alias.lg "log --graph --pretty=format:'%Cred%h%Creset -%C(yellow)%d%Creset %s %Cgreen(%cr) %C(bold blue)<%an>%Creset' --abbrev-commit"

# 然后就可以用
git lg
```

### 查看某个标签的代码

```bash
# 切换到某个标签
git checkout stage-1-3-foundation

# 查看当时的代码
ls -la

# 运行当时的版本
my_cli --version

# 返回最新代码
git checkout main
```

### 对比两个阶段的差异

```bash
# 对比阶段 3 和阶段 4 的差异
git diff stage-1-3-foundation..stage-4-wire-protocol

# 只看文件列表
git diff --name-only stage-1-3-foundation..stage-4-wire-protocol

# 查看统计信息
git diff --stat stage-1-3-foundation..stage-4-wire-protocol
```

## 📚 学习建议

### 每个阶段的流程

1. **阅读文档**：`docs/stage-XX-*.md`
2. **理解原理**：查看对应的 Kimi CLI 源码
3. **实现代码**：边写边测试
4. **本地测试**：`my_cli -c "测试"`
5. **规范提交**：使用 emoji + conventional commits
6. **打标签**：标记阶段完成
7. **推送远程**：`git push origin main --tags`
8. **GitHub 查看**：验证提交和标签

### Git 工作流建议

**简单流程**（适合个人学习）：
```bash
main 分支
  ↓
  实现功能
  ↓
  提交 + 打标签
  ↓
  推送
```

**分支流程**（推荐）：
```bash
main 分支
  ↓
feature/stage-4 分支
  ↓
  实现功能
  ↓
  提交
  ↓
  合并到 main
  ↓
  打标签
  ↓
  推送
```

## 🎯 检查清单

每完成一个阶段，确保：

- [ ] 代码能正常运行（`my_cli -c "test"`）
- [ ] 添加了相应的文档（`docs/stage-XX-*.md`）
- [ ] 提交信息规范（emoji + type + scope）
- [ ] 打了 Git 标签（`stage-XX-描述`）
- [ ] 推送到远程（`git push origin main --tags`）
- [ ] 在 GitHub 验证（查看 commits 和 tags）

## 🛠️ 快捷命令

创建一些 Git 别名，方便使用：

```bash
# 配置别名
git config --global alias.st "status"
git config --global alias.co "checkout"
git config --global alias.br "branch"
git config --global alias.ci "commit"
git config --global alias.lg "log --graph --pretty=format:'%Cred%h%Creset -%C(yellow)%d%Creset %s %Cgreen(%cr) %C(bold blue)<%an>%Creset' --abbrev-commit"

# 使用
git st          # = git status
git co main     # = git checkout main
git br          # = git branch
git ci -m "..."  # = git commit -m "..."
git lg          # = 漂亮的日志
```

## 🎉 总结

1. **学习流程**：阅读文档 → 实现代码 → 测试 → 提交 → 打标签 → 推送
2. **提交规范**：emoji + conventional commits
3. **标签管理**：每个阶段一个标签
4. **GitHub 查看**：commits / tags / releases 页面
5. **本地测试**：`pip install -e .` + `my_cli` 命令

---

**现在开始你的学习之旅吧！** 🚀

下一步：
1. 运行 `pip install -e .` 安装 my_cli 命令
2. 为阶段 1-3 补打标签
3. 开始学习阶段 4

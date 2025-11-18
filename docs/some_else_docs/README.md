# 技术文档索引

> **目录**: `docs/some_else_docs/`
> **用途**: 记录各种技术细节和实现经验

---

## 📚 文档列表

### 1. extract_key_argument 与 streamingjson 实现详解
**文件名**: `extract_key_argument_streamingjson.md`

**内容概要**:
- ❓ 问题背景：为什么不支持 streamingjson.Lexer？
- 🔍 官方实现分析：kimi-cli-fork 源码解读
- 🛠️ 解决方案：从依赖安装到完整实现
- 🔬 技术要点：Lexer原理、类型注解、可选依赖、模式匹配、彩蛋设计
- ✅ 测试验证：完整测试套件和CLI验证
- 🎯 最佳实践：函数设计、类型注解、文档字符串规范
- 📚 相关资源：官方文档、源码参考

**关键收获**:
- ✅ Stage 17 就可以实现完整功能
- ✅ 不需要等到后面阶段
- ✅ 和官方完全一致（已验证 v0.52 最新代码）
- 🔄 官方新增了 `shorten_middle()` 缩短显示（可选优化）

---

## 🔍 如何使用这些文档

### 查找特定技术问题
```bash
# 搜索关键词
grep -r "streamingjson" docs/some_else_docs/

# 查看文档
cat docs/some_else_docs/extract_key_argument_streamingjson.md
```

### 学习技术实现
```bash
# 1. 阅读问题背景
# 2. 查看官方实现
# 3. 对比我们的解决方案
# 4. 运行测试验证
```

### 贡献新文档
```bash
# 1. 在 docs/some_else_docs/ 目录下创建新文档
# 2. 使用 Markdown 格式
# 3. 包含技术细节、代码示例、最佳实践
# 4. 更新本索引文件
```

---

## 📝 文档规范

### 文件命名
- 使用英文小写和下划线
- 以 `.md` 结尾
- 描述性名称（体现文档内容）

### 文档结构
```markdown
# 标题

> 元信息（创建日期、文档类型、相关模块）

---

## 📋 问题背景

## 🔍 官方实现分析

## 🛠️ 解决方案

## 🔬 技术要点深度解析

## ✅ 测试验证

## 🎯 最佳实践

## 📚 相关资源

## 💡 总结
```

### 内容要求
- **详细**: 包含足够的技术细节
- **实用**: 提供可运行的代码示例
- **准确**: 与官方实现保持一致
- **清晰**: 使用代码块、表格、列表等格式化

---

## 🚀 快速导航

### 当前已收录文档
- [extract_key_argument 与 streamingjson 实现详解](./extract_key_argument_streamingjson.md) ⭐ 已验证 v0.52
- [如何在对话中触发 SendDMail 彩蛋](./如何触发SendDMail彩蛋.md)
- [Kimi 工具集完整配置指南](./Kimi工具集完整配置指南.md)
- [kimi-cli-fork 启用 SendDMail 完整指南](./kimi-cli-fork启用SendDMail完整指南.md) ⭐ 已验证 v0.52
- [安装后如何自定义 agent 配置](./安装后如何自定义agent配置.md)
- [message.py 调用关系分析](./message.py调用关系分析.md) ⭐ Stage 17 完整分析
- [工具结果到消息转换完整流程](./工具结果到消息转换完整流程.md) ⭐ 数据流详解
- [Stage 17 收尾完成报告](./Stage17收尾完成报告.md) ⭐ Stage 17 完整实现报告

### 待收录文档（建议）
- [ ] LLM 抽象层设计模式
- [ ] ToolCallPart 流式传输机制
- [ ] ChatProvider 与 LLM 适配器
- [ ] @tenacity.retry 重试机制实现
- [ ] Context 压缩算法
- [ ] 时间旅行（DMail）系统设计
- [ ] Approval 批准系统架构
- [ ] KimiSoul 引擎源码分析

---

## 💬 反馈与贡献

如果发现文档错误或有改进建议，欢迎：
1. 创建 Issue 反馈
2. 提交 PR 修改
3. 补充新文档

---

**最后更新**: 2025-11-18

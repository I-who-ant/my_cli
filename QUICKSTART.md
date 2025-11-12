# My CLI - 快速开始

## 🎯 推荐方式：conda + uv

结合 conda 的环境管理和 uv 的快速依赖管理！

---

## 🚀 快速开始（5 步）

### 1. 创建 conda 环境

```bash
# -n是指  定环境名
conda create -n my_cli python=3.13
```

### 2. 激活环境

```bash
conda activate my_cli
(my_cli) $  # ← 提示符显示环境名
```


### 3. 安装 uv

```bash
(my_cli) $ pip install uv
```

### 4. 进入项目并安装

```bash
(my_cli) $ cd /path/to/kimi-cli-main/imitate-src
(my_cli) $ make prepare
```

### 5. 测试运行

```bash
(my_cli) $ my_cli --version
(my_cli) $ my_cli -c "Hello World"
```

---

## 📖 详细说明

### 为什么用 conda？
- ✅ 环境有名字，提示符清晰：`(my_cli) $`
- ✅ 统一管理：`conda env list` 查看所有环境
- ✅ 切换方便：`conda activate 环境名`

### 为什么用 uv？
- ⚡ **速度快**：比 pip 快 10-100 倍
- 🔒 **依赖锁定**：`uv.lock` 确保版本一致
- 🎯 **对标 Kimi CLI**：专业工作流

### Makefile 自动检测

`make prepare` 会自动检测你的环境：

```bash
# 在 conda 环境中
(my_cli) $ make prepare
检测到 conda 环境: my_cli
在当前环境中安装依赖...
✅ 依赖已安装到 conda 环境: my_cli

# 不在任何环境中
$ make prepare
未检测到 conda 环境，创建 .venv/ 虚拟环境...
✅ 虚拟环境创建完成！
```

---

## 🔄 日常使用

### 每次使用前

```bash
# 激活 conda 环境
conda activate my_cli
(my_cli) $

# 直接使用
(my_cli) $ my_cli --help
```

### 使用完毕

```bash
# 退出环境
(my_cli) $ conda deactivate
$
```

### 查看所有环境

```bash
conda env list

# 输出示例：
# base                  *  /home/user/anaconda3
# DeepLearning             /home/user/.conda/envs/DeepLearning
# my_cli                   /home/user/.conda/envs/my_cli
```

---

## 📚 学习路线

项目分为 9 个阶段：

- [x] **阶段 1-3**：基础框架（CLI + App + Print UI）
- [ ] **阶段 4**：Wire 协议层
- [ ] **阶段 5**：Soul 核心引擎
- [ ] **阶段 6**：Shell UI 模式
- [ ] **阶段 7**：工具系统
- [ ] **阶段 8**：ACP 协议
- [ ] **阶段 9**：Wire UI 模式

详见：[README.md](README.md)

---

## 🛠️ 常用命令

```bash
# 安装依赖
make prepare

# 测试命令
make test

# 清理缓存
make clean

# 查看帮助
make help
```

---

## 🆚 其他安装方式

### 不用 conda（纯 uv）

```bash
cd imitate-src
uv sync
source .venv/bin/activate
(.venv) $ my_cli --help
```

**缺点**：提示符只显示 `(.venv)`，看不出是哪个项目。

### 不用 uv（纯 pip）

```bash
conda create -n my_cli python=3.10
conda activate my_cli
(my_cli) $ pip install -e .
```

**缺点**：安装慢，没有依赖锁定。

---

## 📄 更多文档

- [INSTALL.md](INSTALL.md) - 详细安装指南
- [README.md](README.md) - 完整学习路线
- [docs/LEARNING_WORKFLOW.md](docs/LEARNING_WORKFLOW.md) - 学习工作流

---

**开始你的学习之旅！** 🚀

```bash
conda activate my_cli
(my_cli) $ my_cli -c "Let's start learning!"
```

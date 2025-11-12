# My CLI - 安装指南

## 🎯 推荐方式：conda + uv 混合

结合 conda 的环境管理和 uv 的依赖管理，最佳实践！

### 为什么用 conda？
- ✅ 环境有名字，提示符清晰 `(my_cli) $`
- ✅ 统一管理：`conda env list` 查看所有环境
- ✅ 你熟悉的工作流

### 为什么用 uv？
- ✅ 依赖管理快（比 pip 快 10-100 倍）
- ✅ 锁定版本（`uv.lock` 确保一致性）
- ✅ 对标 Kimi CLI 的专业工作流

---

## 🚀 快速开始

### 步骤 1：创建 conda 环境

```bash
# 创建专门的环境
conda create -n my_cli python=3.10

# 激活环境
conda activate my_cli

# 提示符变成：
(my_cli) [seeback@seeback ~]$
```

### 步骤 2：安装 uv

```bash
# 在 my_cli 环境中安装 uv
(my_cli) $ pip install uv

# 验证安装
(my_cli) $ uv --version
```

### 步骤 3：安装项目

```bash
# 进入项目目录
(my_cli) $ cd /path/to/kimi-cli-main/imitate-src

# 使用 uv 安装依赖
(my_cli) $ uv sync

# 或使用 Makefile
(my_cli) $ make prepare
```

### 步骤 4：验证安装

```bash
# 查看命令位置
(my_cli) $ which my_cli
/home/seeback/.conda/envs/my_cli/bin/my_cli

# 测试命令
(my_cli) $ my_cli --version
my_cli, version 0.1.0

# 运行测试
(my_cli) $ my_cli -c "Hello World"
```

---

## 📂 环境结构

```
conda 环境位置：
~/.conda/envs/my_cli/
├── bin/
│   ├── python
│   ├── pip
│   ├── uv
│   └── my_cli          # ← 命令安装在这里
├── lib/
└── ...

项目目录（代码）：
/path/to/kimi-cli-main/imitate-src/
├── my_cli/             # 源代码
├── pyproject.toml      # 项目配置
├── uv.lock             # 依赖锁定文件（uv 生成）
└── Makefile
```

**关键点**：
- 环境在 `~/.conda/envs/my_cli/`（conda 管理）
- 代码在项目目录（方便编辑）
- uv.lock 记录精确的依赖版本

---

## 🔄 日常使用

### 激活环境

```bash
# 每次新终端都需要激活
conda activate my_cli
(my_cli) $

# 现在可以直接用
(my_cli) $ my_cli --help
```

### 退出环境

```bash
(my_cli) $ conda deactivate
$
```

### 切换项目

```bash
# 在 my_cli 环境中
(my_cli) $ cd ~/other-project

# 环境还是 my_cli
(my_cli) $ # 如果想用其他环境
(my_cli) $ conda deactivate
$ conda activate other_env
```

---

## 🎓 与纯 uv 方式对比

### 纯 uv 方式（Kimi CLI 原版）

```bash
# 1. 在项目目录创建 .venv/
cd project
uv sync

# 2. 激活（每次）
source .venv/bin/activate

# 提示符：
(.venv) $  # ← 看不出是哪个项目
```

### conda + uv 方式（推荐）

```bash
# 1. 创建 conda 环境（一次）
conda create -n my_cli python=3.10

# 2. 激活
conda activate my_cli

# 提示符：
(my_cli) $  # ← 清楚地知道在 my_cli 环境
```

**对比**：

| 特性 | 纯 uv (.venv) | conda + uv |
|------|--------------|-----------|
| 提示符 | `(.venv) $` | `(my_cli) $` |
| 环境位置 | 项目目录 | `~/.conda/envs/` |
| 查看环境 | 无 | `conda env list` |
| 识别度 | 低 | 高 |

---

## 🛠️ Makefile 命令

```bash
# 安装依赖（自动检测 uv）
make prepare

# 测试命令
make test

# 清理缓存
make clean

# 查看帮助
make help
```

**注意**：Makefile 会自动检测是否在 conda 环境中，不会创建 `.venv/`！

---

## ❓ 常见问题

### Q1: 我必须用 uv 吗？

**不是！你也可以只用 conda：**

```bash
conda create -n my_cli python=3.10
conda activate my_cli
(my_cli) $ cd imitate-src
(my_cli) $ pip install -e .  # 不用 uv
```

但 uv 更快，推荐尝试！

### Q2: 如果我不想用 conda 呢？

**可以！纯 uv 方式：**

```bash
cd imitate-src
uv sync
source .venv/bin/activate
```

但提示符只显示 `(.venv)`，不如 conda 清晰。

### Q3: uv.lock 是什么？

**依赖锁定文件**，记录精确版本：

```toml
# uv.lock 示例
[[package]]
name = "click"
version = "8.1.7"
source = { registry = "https://pypi.org/simple" }
```

作用：
- 团队协作：所有人版本一致
- 可重现：随时恢复相同环境

### Q4: 为什么提示符很重要？

```bash
# 场景：你有多个项目
(DeepLearning) $ cd project1  # 搞不清是哪个项目
(DeepLearning) $ cd project2

# vs

(my_cli) $ cd other-project  # 清楚知道在 my_cli 环境
(other_env) $ cd another      # 切换了环境，提示符变化
```

### Q5: conda 环境会占用很多空间吗？

```bash
# 查看环境大小
du -sh ~/.conda/envs/my_cli
# 大约 200-500 MB（取决于依赖）

# 删除环境
conda env remove -n my_cli
```

---

## 📝 总结

### 推荐方案：conda + uv

1. **创建**：`conda create -n my_cli python=3.10`
2. **激活**：`conda activate my_cli`
3. **安装 uv**：`pip install uv`
4. **安装项目**：`uv sync`
5. **使用**：`my_cli --help`

**优势**：
- ✅ 环境有清晰名字
- ✅ conda 统一管理
- ✅ uv 快速依赖管理
- ✅ 两者优势结合

---

**选择你喜欢的方式，开始学习吧！** 🎉

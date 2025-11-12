# 安装指南 - 两种方式任选

## 🎯 选择安装方式

My CLI 支持两种安装方式，根据你的需求选择：

| 方式 | 适合场景 | 优势 | 劣势 |
|------|---------|------|------|
| **方案1：pip** | 快速上手、已有虚拟环境 | 简单快速 | 可能与其他项目冲突 |
| **方案2：uv（推荐）** | 独立学习、多项目并存 | 完全隔离、速度快 | 需要额外激活 |

---

## 🚀 方案1：使用 pip（复用现有虚拟环境）

### 适用场景
- 你已经在一个虚拟环境中（如 `DeepLearning`）
- 想快速开始学习
- 不担心依赖冲突

### 安装步骤

```bash
# 1. 确认在虚拟环境中
(DeepLearning) $ echo $CONDA_DEFAULT_ENV
DeepLearning

# 2. 进入项目目录
cd kimi-cli-main/imitate-src

# 3. 安装
pip install -e .

# 或使用 Makefile
make install
```

### 验证安装

```bash
# 查看命令位置
which my_cli
# 输出：/home/seeback/.conda/envs/DeepLearning/bin/my_cli

# 运行测试
my_cli --version
my_cli -c "Hello World"
```

### 卸载

```bash
pip uninstall my-cli

# 或使用 Makefile
make uninstall
```

---

## 🌟 方案2：使用 uv（推荐 - 独立虚拟环境）

### 适用场景
- 你有多个项目在 `DeepLearning` 环境
- 想要完全隔离的学习环境
- 追求更快的安装速度

### 安装步骤

```bash
# 1. 进入项目目录（可以在任何环境中）
cd kimi-cli-main/imitate-src

# 2. 使用 uv 创建虚拟环境并安装
make prepare

# 等价于手动执行：
# pip install uv              # 如果没有 uv
# uv sync                     # 创建 .venv/ 并安装

# 3. 激活虚拟环境
source .venv/bin/activate

# 4. 验证安装
which my_cli
# 输出：/path/to/imitate-src/.venv/bin/my_cli

my_cli --version
```

### 项目结构

```
kimi-cli-main/imitate-src/
├── .venv/                    # uv 创建的虚拟环境
│   ├── bin/
│   │   └── my_cli            # my_cli 命令在这里
│   ├── lib/
│   └── ...
├── my_cli/                   # 源代码
├── pyproject.toml            # 项目配置（uv 使用）
├── setup.py                  # 项目配置（pip 使用）
└── Makefile                  # 便捷命令
```

### 日常使用

```bash
# 激活虚拟环境
source .venv/bin/activate

# 现在可以使用 my_cli
my_cli -c "Hello World"

# 退出虚拟环境
deactivate
```

### 卸载

```bash
# 删除虚拟环境
make clean-venv

# 或手动删除
rm -rf .venv
```

---

## 📊 两种方式的对比

### 安装速度

```bash
# pip 方式
pip install -e .                # 10-30 秒

# uv 方式
uv sync                         # 2-5 秒（快 5-10 倍！）
```

### 虚拟环境位置

**pip 方式**：
```
/home/seeback/.conda/envs/DeepLearning/
├── bin/
│   └── my_cli                  # 与 DeepLearning 其他工具共存
├── lib/
└── ...
```

**uv 方式**：
```
kimi-cli-main/imitate-src/.venv/
├── bin/
│   └── my_cli                  # 完全独立
├── lib/
└── ...
```

### 激活方式

**pip 方式**：
```bash
# 已经在 DeepLearning 环境中
(DeepLearning) $ my_cli --help
```

**uv 方式**：
```bash
# 需要激活项目虚拟环境
$ source .venv/bin/activate
(.venv) $ my_cli --help

# 退出
(.venv) $ deactivate
```

---

## 🤔 如何选择？

### 选择 pip（方案1），如果：
- ✅ 你只学习这一个项目
- ✅ 你想快速开始
- ✅ 你不在意 DeepLearning 环境变"重"

### 选择 uv（方案2），如果：
- ✅ 你有多个项目在 DeepLearning 环境
- ✅ 你想要干净的隔离环境
- ✅ 你想体验 Kimi CLI 的安装方式
- ✅ 你追求更快的安装速度

**老王推荐**：方案2（uv）！就像 Kimi CLI 一样，独立环境更专业！

---

## 🔧 常见问题

### Q1: 我可以同时使用两种方式吗？

**可以！但不推荐。**

```bash
# 会导致两个 my_cli 命令
/home/seeback/.conda/envs/DeepLearning/bin/my_cli  # pip 安装
/path/to/imitate-src/.venv/bin/my_cli              # uv 安装

# 激活哪个环境就用哪个
```

### Q2: uv 比 pip 快在哪里？

**uv 的优势**：
1. **Rust 实现**：比 Python 写的 pip 快 10-100 倍
2. **并行下载**：同时下载多个包
3. **智能缓存**：已下载的包不重复下载
4. **锁定依赖**：uv.lock 精确记录版本

```bash
# pip 安装（串行）
下载 click → 安装 click → 完成
    ↓ 约 10 秒

# uv 安装（并行）
下载 click → 完成
    ↓ 约 2 秒
```

### Q3: pyproject.toml vs setup.py 有什么区别？

**pyproject.toml**（现代方式）：
```toml
[project]
name = "my-cli"
version = "0.1.0"
dependencies = ["click>=8.1.0"]

[project.scripts]
my_cli = "my_cli.cli:my_cli"
```

**setup.py**（传统方式）：
```python
setup(
    name="my-cli",
    version="0.1.0",
    install_requires=["click>=8.1.0"],
    entry_points={
        "console_scripts": [
            "my_cli=my_cli.cli:my_cli",
        ],
    },
)
```

**两者功能相同！** uv 和 pip 都能读取 pyproject.toml。

### Q4: 我用了 uv，还能用 pip 吗？

**完全可以！**

```bash
# 激活 uv 创建的虚拟环境
source .venv/bin/activate

# 里面也有 pip
pip list
pip install some-package

# uv 和 pip 可以混用
```

### Q5: 如何切换环境？

```bash
# 当前在 DeepLearning 环境
(DeepLearning) $ which my_cli
/home/seeback/.conda/envs/DeepLearning/bin/my_cli

# 切换到 uv 环境
(DeepLearning) $ conda deactivate
$ cd kimi-cli-main/imitate-src
$ source .venv/bin/activate

# 现在在 uv 环境
(.venv) $ which my_cli
/path/to/imitate-src/.venv/bin/my_cli
```

---

## 📝 Makefile 命令速查

### 方案1（pip）
```bash
make install      # 安装
make uninstall    # 卸载
```

### 方案2（uv）
```bash
make prepare      # 创建 .venv/ 并安装
make activate     # 显示激活命令
make clean-venv   # 删除 .venv/
```

### 通用命令
```bash
make help         # 显示帮助
make test         # 测试命令
make clean        # 清理缓存
```

---

## 🎓 学习建议

**初学者**：
1. 先用**方案1（pip）**快速上手
2. 理解基本概念后
3. 再切换到**方案2（uv）**体验专业工作流

**有经验者**：
直接用**方案2（uv）**，体验现代 Python 开发！

---

## 🚀 快速开始

### 方案1（pip - 最快）
```bash
cd kimi-cli-main/imitate-src
make install
my_cli -c "Hello World"
```

### 方案2（uv - 推荐）
```bash
cd kimi-cli-main/imitate-src
make prepare
source .venv/bin/activate
my_cli -c "Hello World"
```

---

**选择你喜欢的方式，开始学习吧！** 🎉

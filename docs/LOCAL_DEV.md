# 本地学习环境配置指南

## 🎯 目标

在你的虚拟环境中安装 `my_cli` 命令，就像使用 `kimi` 命令一样！

## 📋 前提条件

你已经在虚拟环境中：
```bash
(DeepLearning) [seeback@seeback Modelrecognize]$
```

## 🚀 安装步骤

### 方法 1：开发模式安装（推荐）

```bash
# 进入项目目录
cd kimi-cli-main/imitate-src

# 以开发模式安装（-e 代表 editable）
pip install -e .

# 验证安装
which my_cli
# 输出：/path/to/venv/bin/my_cli

# 直接运行！
my_cli --help
my_cli --version
my_cli -c "Hello World"
```

**开发模式的优势**：
- ✅ 修改代码后**立即生效**，无需重新安装
- ✅ 可以直接用 `my_cli` 命令
- ✅ 代码还在原位置，方便编辑

### 方法 2：普通安装（不推荐学习时使用）

```bash
# 普通安装
pip install .

# 问题：每次修改代码都要重新安装
pip install --upgrade .
```

## 🔍 Magic 详解

### 安装前后对比

**安装前**：
```bash
# 只能这样运行（太长了！）
python -m my_cli.cli -c "Hello World"
```

**安装后**：
```bash
# 可以直接运行（简洁！）
my_cli -c "Hello World"
```

### 发生了什么？

1. **`pip install -e .` 执行时**：
   ```
   读取 setup.py
   ↓
   发现 entry_points 中定义了 "my_cli=my_cli.cli:my_cli"
   ↓
   在虚拟环境的 bin/ 目录创建可执行文件 "my_cli"
   ↓
   该文件是一个包装器脚本
   ```

2. **虚拟环境的 bin/ 目录**：
   ```bash
   # 查看你的虚拟环境 bin 目录
   ls $(python -c "import sys; print(sys.prefix)")/bin/my_cli

   # 输出类似：
   # /home/seeback/.conda/envs/DeepLearning/bin/my_cli
   ```

3. **包装器脚本内容**：
   ```bash
   # 查看自动生成的 my_cli 脚本
   cat $(which my_cli)
   ```

   输出类似：
   ```python
   #!/home/seeback/.conda/envs/DeepLearning/bin/python
   # -*- coding: utf-8 -*-
   import re
   import sys
   from my_cli.cli import my_cli
   if __name__ == '__main__':
       sys.argv[0] = re.sub(r'(-script\.pyw|\.exe)?$', '', sys.argv[0])
       sys.exit(my_cli())
   ```

4. **调用流程**：
   ```
   你输入：my_cli -c "Hello"
   ↓
   Shell 在 PATH 中找到：/path/to/venv/bin/my_cli
   ↓
   执行该脚本
   ↓
   脚本导入：from my_cli.cli import my_cli
   ↓
   调用：my_cli() 函数
   ↓
   Click 解析参数 ['-c', 'Hello']
   ↓
   运行你的代码！
   ```

## 📝 完整演示

```bash
# 1. 进入项目目录
cd /home/seeback/PycharmProjects/Modelrecognize/kimi-cli-main/imitate-src

# 2. 确认在虚拟环境中
echo $CONDA_DEFAULT_ENV
# 输出：DeepLearning

# 3. 安装（开发模式）
pip install -e .

# 预期输出：
# Obtaining file:///home/seeback/PycharmProjects/Modelrecognize/kimi-cli-main/imitate-src
# Installing collected packages: my-cli
#   Running setup.py develop for my-cli
# Successfully installed my-cli-0.1.0

# 4. 验证安装
which my_cli
# 输出：/home/seeback/.conda/envs/DeepLearning/bin/my_cli

# 5. 测试命令
my_cli --version
# 输出：my_cli, version 0.1.0

my_cli --help
# 输出：帮助信息

my_cli -c "Hello World"
# 输出：模拟 AI 响应

# 6. 开启详细输出
my_cli --verbose -c "测试"
# 输出：带详细日志的响应

# 7. 从管道输入
echo "Hello from pipe" | my_cli
# 输出：处理管道输入的结果
```

## 🎓 学习工作流

### 阶段 1-3（当前）

```bash
# 1. 安装
pip install -e .

# 2. 测试基础功能
my_cli --help
my_cli -c "Hello"

# 3. 修改代码
# 编辑 my_cli/cli.py 或其他文件

# 4. 立即测试（无需重新安装）
my_cli -c "测试修改"

# 5. 满意后提交
git add .
git commit -m "阶段1-3: 完成基础框架"
git push
```

### 后续阶段（4-9）

每完成一个阶段：

```bash
# 1. 实现新功能
# 例如：阶段 4 实现 Wire 协议

# 2. 更新依赖（如果需要）
pip install -e ".[stage4]"

# 3. 测试新功能
my_cli --ui print -c "测试 Wire 协议"

# 4. 提交代码（使用 emoji 提交）
git add .
# 手动提交或使用工具
git commit -m "✨ feat(stage4): 实现 Wire 协议层"
git push

# 5. 在 GitHub 查看提交历史
# https://github.com/I-who-ant/my_cli/commits/main
```

## 🔧 常见问题

### Q1: 安装后命令找不到？

```bash
# 检查 my_cli 是否在 PATH 中
which my_cli

# 如果找不到，检查虚拟环境
echo $PATH | grep DeepLearning

# 重新激活虚拟环境
conda deactivate
conda activate DeepLearning
```

### Q2: 修改代码后不生效？

```bash
# 开发模式（-e）应该立即生效
# 如果不生效，可能是缓存问题

# 清理 Python 缓存
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# 重新安装
pip install -e . --force-reinstall --no-deps
```

### Q3: 如何卸载？

```bash
# 卸载 my_cli 命令
pip uninstall my-cli

# 验证卸载
which my_cli
# 输出：（空）
```

### Q4: 如何查看安装的文件位置？

```bash
# 查看包安装信息
pip show my-cli

# 输出：
# Name: my-cli
# Version: 0.1.0
# Location: /home/seeback/PycharmProjects/Modelrecognize/kimi-cli-main/imitate-src
# Editable project location: /home/seeback/PycharmProjects/Modelrecognize/kimi-cli-main/imitate-src
```

### Q5: 虚拟环境中的 bin/ 在哪里？

```bash
# 获取虚拟环境路径
python -c "import sys; print(sys.prefix)"
# 输出：/home/seeback/.conda/envs/DeepLearning

# bin/ 目录就在：
# /home/seeback/.conda/envs/DeepLearning/bin/

# 查看所有可执行命令
ls $(python -c "import sys; print(sys.prefix)")/bin/ | grep my_cli
```

## 📚 与 Kimi CLI 对比

### Kimi CLI 的安装

```bash
# Kimi CLI 也是用同样的方式
pip install kimi-cli

# 然后可以直接用
kimi --help
```

### My CLI 的安装（学习版）

```bash
# 你的学习版
pip install -e .

# 然后可以直接用
my_cli --help
```

**区别**：
- Kimi CLI：从 PyPI 安装（`pip install kimi-cli`）
- My CLI：从本地安装（`pip install -e .`）

**相同点**：
- 都使用 `entry_points` 定义命令
- 都会在虚拟环境 bin/ 创建可执行文件
- 都可以直接运行

## 🎯 总结

1. **`setup.py`**：定义了包的安装配置和命令入口
2. **`pip install -e .`**：以开发模式安装，修改代码立即生效
3. **虚拟环境 bin/**：只在当前虚拟环境有效，不会污染系统
4. **`my_cli` 命令**：就像 `kimi` 命令一样方便使用

**下一步**：
- [x] 运行 `pip install -e .`
- [ ] 测试 `my_cli --help`
- [ ] 开始学习后续阶段
- [ ] 每个阶段完成后提交到 Git

---

**准备好了吗？运行 `pip install -e .` 开始吧！** 🚀

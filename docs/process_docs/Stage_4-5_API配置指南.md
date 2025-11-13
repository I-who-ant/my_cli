# Stage 4-5：API 配置指南

> 本文档介绍如何配置 Moonshot API Key，让 Soul 引擎能够调用真实的 LLM。

---

## 📋 目录

1. [为什么需要 API Key](#为什么需要-api-key)
2. [申请 Moonshot API Key](#申请-moonshot-api-key)
3. [配置 API Key](#配置-api-key)
4. [启用真实 LLM 模式](#启用真实-llm-模式)
5. [测试验证](#测试验证)
6. [常见问题](#常见问题)

---

## 为什么需要 API Key

**我们的 Soul 引擎使用 Moonshot Kimi 模型**：

```python
# my_cli/soul/__init__.py
from kosong.chat_provider.kimi import Kimi

chat_provider = Kimi(
    base_url="https://api.moonshot.cn/v1",
    api_key=api_key,  # ⭐ 需要 API Key
    model="moonshot-v1-8k",
)
```

**为什么选择 Moonshot？**
1. ✅ 官方 Kimi CLI 就是用的 Moonshot
2. ✅ 支持中文对话效果好
3. ✅ 有免费额度（15元体验金）
4. ✅ kosong 框架原生支持

---

## 申请 Moonshot API Key

### 步骤 1：注册账号

访问 Moonshot 官网：
- 🔗 **https://platform.moonshot.cn/**

点击右上角"登录/注册"，使用手机号注册。

### 步骤 2：实名认证（可选）

**新用户有 15 元体验金**，无需实名即可使用：
- 免费额度可以支持数千次对话
- 足够完成我们的学习项目

如果需要更多额度，可以：
1. 进入"个人中心"
2. 完成实名认证
3. 充值（按需）

### 步骤 3：创建 API Key

1. 登录后，进入 **"API Keys"** 页面：
   - 🔗 https://platform.moonshot.cn/console/api-keys

2. 点击 **"创建新的 API Key"**

3. 输入 Key 名称（例如：`my_cli_dev`）

4. 点击 **"创建"**

5. **⚠️ 重要**：立即复制并保存 API Key！
   ```
   sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```

   ⚠️ **这个 Key 只会显示一次！** 一旦关闭窗口就无法再查看，只能重新创建。

### 步骤 4：查看额度

在控制台首页可以看到：
- 💰 当前余额
- 📊 使用量统计
- 📈 调用历史

---

## 配置 API Key

### 方式 1：环境变量（推荐）✅

**为什么推荐环境变量？**
- ✅ 不会把 API Key 提交到 Git
- ✅ 跨项目共享配置
- ✅ 安全性高

#### Linux / macOS

**临时设置**（当前终端有效）：
```bash
export MOONSHOT_API_KEY='sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
```

**永久设置**（推荐）：

1. 编辑配置文件：
   ```bash
   # 如果使用 bash
   nano ~/.bashrc

   # 如果使用 zsh
   nano ~/.zshrc
   ```

2. 在文件末尾添加：
   ```bash
   # Moonshot API Key
   export MOONSHOT_API_KEY='sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
   ```

3. 保存并生效：
   ```bash
   # bash
   source ~/.bashrc

   # zsh
   source ~/.zshrc
   ```

4. 验证配置：
   ```bash
   echo $MOONSHOT_API_KEY
   # 应该输出你的 API Key
   ```

#### Windows

**临时设置**（当前 CMD 有效）：
```cmd
set MOONSHOT_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**临时设置**（当前 PowerShell 有效）：
```powershell
$env:MOONSHOT_API_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

**永久设置**（推荐）：

1. 打开"环境变量"设置：
   - 右键"此电脑" → "属性"
   - 点击"高级系统设置"
   - 点击"环境变量"

2. 在"用户变量"中点击"新建"：
   - 变量名：`MOONSHOT_API_KEY`
   - 变量值：`sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

3. 点击"确定"保存

4. **重启终端**验证：
   ```cmd
   echo %MOONSHOT_API_KEY%
   ```

---

### 方式 2：代码中硬编码（不推荐）❌

**⚠️ 警告**：这种方式会把 API Key 暴露在代码中，容易泄露！

如果只是临时测试，可以修改 `my_cli/soul/__init__.py`：

```python
def create_soul(
    work_dir: Path,
    agent_name: str = "MyCLI Assistant",
    model: str = "moonshot-v1-8k",
    api_key: str | None = None,  # ⭐ 可以传入 API Key
    base_url: str = "https://api.moonshot.cn/v1",
) -> KimiSoul:
    # ...
    chat_provider = Kimi(
        base_url=base_url,
        api_key=api_key or "sk-xxxxxx",  # ❌ 不推荐硬编码
        model=model,
    )
```

**❌ 千万不要提交这种代码到 Git！**

---

### 方式 3：配置文件（可选）

**创建 `.env` 文件**（不要提交到 Git）：

```bash
# .env
MOONSHOT_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**在 `.gitignore` 中添加**：
```gitignore
.env
```

**使用 `python-dotenv` 加载**：
```bash
pip install python-dotenv
```

```python
# 在 app.py 中
from dotenv import load_dotenv
load_dotenv()  # 自动加载 .env 文件
```

---

## 启用真实 LLM 模式

### 当前代码的模式切换

**默认：模拟模式**（不需要 API Key）
```python
# my_cli/app.py
ui = PrintUI(
    verbose=self.verbose,
    work_dir=self.work_dir,
    use_real_llm=False  # ⭐ 默认是模拟模式
)
```

**启用：真实 LLM 模式**
```python
# my_cli/app.py
ui = PrintUI(
    verbose=self.verbose,
    work_dir=self.work_dir,
    use_real_llm=True  # ⭐ 改为 True
)
```

### 修改步骤

1. **打开文件**：`my_cli/app.py`

2. **找到 `run_print_mode()` 方法**（大约在第 50 行）：
   ```python
   async def run_print_mode(
       self,
       command: str | None,
   ) -> None:
       from my_cli.ui.print.ui_print import PrintUI

       ui = PrintUI(
           verbose=self.verbose,
           work_dir=self.work_dir,
           use_real_llm=False,  # ⭐ 找到这一行
       )

       await ui.run(command)
   ```

3. **修改为**：
   ```python
   use_real_llm=True,  # ⭐ 改为 True
   ```

4. **保存文件**

---

## 测试验证

### 测试 1：检查环境变量

```bash
# Linux/macOS
echo $MOONSHOT_API_KEY

# Windows CMD
echo %MOONSHOT_API_KEY%

# Windows PowerShell
echo $env:MOONSHOT_API_KEY
```

**预期输出**：
```
sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

如果输出为空，说明环境变量没有设置成功。

---

### 测试 2：模拟模式（不需要 API Key）

```bash
cd kimi-cli-main/imitate-src
python -m my_cli.cli -c "你好" --verbose
```

**预期输出**：
```
[CLI 层] My CLI v0.1.0
[CLI 层] 工作目录: /current/path
...
AI 响应（模拟）:
------------------------------------------------------------
你说：你好

这是一个模拟的 AI 响应。

💡 提示：要使用真实 LLM，请：
  1. 安装 openai 库：pip install openai
  2. 设置环境变量：
     export MOONSHOT_API_KEY='your-api-key'
...
✅ Print UI 模拟模式运行成功！
```

---

### 测试 3：真实 LLM 模式（需要 API Key）

**前提**：
1. ✅ 已设置 `MOONSHOT_API_KEY` 环境变量
2. ✅ 已安装 kosong：`pip install -e kosong-main/`
3. ✅ 已修改 `app.py` 的 `use_real_llm=True`

**运行**：
```bash
python -m my_cli.cli -c "你好，介绍一下你自己" --verbose
```

**预期输出**：
```
[CLI 层] My CLI v0.1.0
[Print UI] 启动 Print UI 模式
[Print UI] 创建 Soul 引擎实例（kosong 框架）
[Print UI] Soul 引擎创建成功
[Print UI] 工作目录: /current/path
[Print UI] ChatProvider: Kimi (Moonshot)
============================================================
My CLI - Print UI 模式
============================================================

用户命令: 你好，介绍一下你自己

AI 响应:
------------------------------------------------------------
你好！我是 Kimi，一个由月之暗面科技开发的 AI 助手。我擅长...
（流式输出，逐字显示）
------------------------------------------------------------

✅ LLM 调用成功！
[Print UI] 消息数量: 2
```

---

## 常见问题

### Q1: 提示 "API Key 未设置或无效"

**原因**：
- 环境变量没有设置
- 环境变量名称错误
- API Key 已过期或被删除

**解决**：
1. 检查环境变量：
   ```bash
   echo $MOONSHOT_API_KEY
   ```

2. 重新设置环境变量

3. 重启终端

4. 在 Moonshot 控制台检查 API Key 是否有效

---

### Q2: 提示 "余额不足"

**原因**：
- 免费额度用完了
- 没有充值

**解决**：
1. 登录 Moonshot 控制台查看余额
2. 充值或等待免费额度恢复

---

### Q3: 提示 "网络连接问题"

**原因**：
- 网络不稳定
- 无法访问 api.moonshot.cn

**解决**：
1. 检查网络连接
2. 尝试使用代理（如果需要）
3. 检查防火墙设置

---

### Q4: kosong 导入失败

**错误信息**：
```
ImportError: No module named 'kosong'
```

**解决**：
```bash
# 安装 kosong 框架
cd kimi-cli-main/imitate-src
pip install -e kosong-main/
```

---

### Q5: 我可以用其他模型吗？

**可以！** kosong 支持多种 ChatProvider：

#### 使用 OpenAI

1. 设置环境变量：
   ```bash
   export OPENAI_API_KEY='sk-xxxxxx'
   ```

2. 修改 `my_cli/soul/__init__.py`：
   ```python
   from kosong.chat_provider.openai import OpenAI

   chat_provider = OpenAI(
       api_key=api_key,
       model="gpt-3.5-turbo",
   )
   ```

#### 使用 Anthropic Claude

1. 设置环境变量：
   ```bash
   export ANTHROPIC_API_KEY='sk-ant-xxxxxx'
   ```

2. 修改代码：
   ```python
   from kosong.chat_provider.anthropic import Anthropic

   chat_provider = Anthropic(
       api_key=api_key,
       model="claude-3-5-sonnet-20241022",
   )
   ```

---

## 配置检查清单

在运行真实 LLM 模式前，请确认：

- [ ] 已在 Moonshot 官网注册账号
- [ ] 已创建 API Key 并保存
- [ ] 已设置环境变量 `MOONSHOT_API_KEY`
- [ ] 环境变量设置正确（`echo $MOONSHOT_API_KEY` 有输出）
- [ ] 已安装 kosong：`pip install -e kosong-main/`
- [ ] 已修改 `app.py` 的 `use_real_llm=True`
- [ ] 已重启终端（如果刚设置环境变量）
- [ ] 余额充足（至少有几元）

**全部勾选？恭喜！你可以开始使用真实 LLM 了！** 🎉

---

## 安全建议

### ⚠️ 保护你的 API Key

1. **永远不要**把 API Key 提交到 Git
2. **永远不要**在公开场合分享 API Key
3. **定期轮换** API Key（建议每月更换）
4. **使用环境变量**而不是硬编码

### .gitignore 配置

确保你的 `.gitignore` 包含：
```gitignore
# 环境变量文件
.env
.env.local

# API Key 配置
*_api_key.txt
secrets.yaml
```

### API Key 泄露怎么办？

1. **立即**登录 Moonshot 控制台
2. **删除**泄露的 API Key
3. **创建**新的 API Key
4. **检查**余额是否异常
5. **联系**客服（如果有盗用）

---

## 总结

### 推荐配置流程

1. **注册 Moonshot** → 获得 15 元体验金
2. **创建 API Key** → 保存到安全的地方
3. **设置环境变量** → `export MOONSHOT_API_KEY='sk-xxx'`
4. **修改 app.py** → `use_real_llm=True`
5. **测试验证** → `python -m my_cli.cli -c "你好"`

### 后续阶段

当前 Stage 4-5 只实现了基础对话，后续还会添加：

- **Stage 6**：Wire 消息队列（Soul 和 UI 解耦）
- **Stage 7**：工具系统（Shell/ReadFile/WriteFile）
- **Stage 8**：Function Calling（LLM 自动调用工具）

---

**老王的建议**：
- 🔐 保护好你的 API Key，别泄露！
- 💰 注意监控余额，避免意外扣费
- 📊 查看调用记录，了解使用情况
- 🧪 先用模拟模式测试，再切换真实模式

**现在你可以开始和你的 AI 助手对话了！** 🚀

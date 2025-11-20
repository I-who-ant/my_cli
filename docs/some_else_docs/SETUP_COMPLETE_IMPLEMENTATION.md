# Setup 完整实现与 Reload 异常修复

**记录日期**: 2025-01-20
**相关提交**:
- `416013b` - feat(setup): 完全对齐官方 setup 实现
- `d97ac74` - fix(shell): 修复 Reload 异常被错误捕获的问题

---

## 📋 问题背景

### 1. Setup 实现不完整

**初版实现**（简化版）：
```
1. 选择平台
2. 输入 API Key
3. ❌ 手动输入模型名称
4. ❌ 手动输入 max_context_size
5. 保存配置
```

**用户反馈**：
> "官方的 setup.py 输入 API Key 后的选择不一样，无需什么输入模型名称之类的，修改为官方那种"

**官方完整实现**：
```
1. 选择平台
2. 输入 API Key
3. ✅ 自动调用 API 拉取模型列表
4. ✅ 从列表中选择模型
5. ✅ 自动读取 context_length
6. 保存配置
```

### 2. Reload 异常被错误捕获

**用户遇到的错误**：
```
✓ MyCLI 配置完成！正在重新加载...
❌ 命令执行失败:
✨ You:
```

**问题原因**：
- `_run_meta_command()` 捕获了所有异常（`except Exception as e`）
- `Reload` 异常被当作普通错误处理
- 导致 CLI 没有重新加载配置

---

## 🔧 解决方案

### 1. Setup 完整实现

**文件**: `my_cli/ui/shell/setup.py`

#### 1.1 更新 _SetupResult 结构

```python
# ❌ 之前的结构
class _SetupResult(NamedTuple):
    api_key: SecretStr
    model_name: str
    base_url: str
    provider_name: str
    max_context_size: int

# ✅ 对齐官方的结构
class _SetupResult(NamedTuple):
    platform: _Platform  # 直接使用 platform 对象
    api_key: SecretStr
    model_id: str
    max_context_size: int
```

**优势**：
- 更简洁的数据结构
- 避免重复存储 base_url 和 provider_name
- 便于访问 platform 的其他属性（如 search_url）

#### 1.2 重写 _setup() 核心逻辑

```python
async def _setup() -> _SetupResult | None:
    """
    交互式配置流程 ⭐ 完全对齐官方实现

    流程：
    1. 选择平台
    2. 输入 API Key
    3. 调用 API 拉取模型列表 ⭐ 关键改进
    4. 从列表中选择模型 ⭐ 关键改进
    5. 返回配置结果（包含 context_length）⭐ 关键改进
    """
    # 1. 选择平台
    platform_name = await _prompt_choice(
        header="Select the API platform",
        choices=[platform.name for platform in _PLATFORMS],
    )
    if not platform_name:
        console.print("[red]未选择平台[/red]")
        return None

    platform = next(p for p in _PLATFORMS if p.name == platform_name)

    # 2. 输入 API Key
    api_key = await _prompt_text("Enter your API key", is_password=True)
    if not api_key:
        return None

    # 3. 调用 API 拉取模型列表 ⭐ 关键改进
    models_url = f"{platform.base_url}/models"
    try:
        async with (
            new_client_session() as session,
            session.get(
                models_url,
                headers={
                    "Authorization": f"Bearer {api_key}",
                },
                raise_for_status=True,
            ) as response,
        ):
            resp_json = await response.json()
    except aiohttp.ClientError as e:
        console.print(f"[red]获取模型列表失败: {e}[/red]")
        return None

    model_dict = {model["id"]: model for model in resp_json["data"]}

    # 4. 过滤模型（根据 allowed_prefixes）
    model_ids: list[str] = [model["id"] for model in resp_json["data"]]
    if platform.allowed_prefixes is not None:
        model_ids = [
            model_id
            for model_id in model_ids
            if model_id.startswith(tuple(platform.allowed_prefixes))
        ]

    if not model_ids:
        console.print("[red]该平台没有可用模型[/red]")
        return None

    # 5. 选择模型 ⭐ 关键改进
    model_id = await _prompt_choice(
        header="Select the model",
        choices=model_ids,
    )
    if not model_id:
        console.print("[red]未选择模型[/red]")
        return None

    model = model_dict[model_id]

    # 6. 返回配置结果（自动读取 context_length）⭐ 关键改进
    return _SetupResult(
        platform=platform,
        api_key=SecretStr(api_key),
        model_id=model_id,
        max_context_size=model["context_length"],  # ⭐ 从 API 响应中读取
    )
```

#### 1.3 添加必要的依赖

```python
import aiohttp
from my_cli.utils.aiohttp import new_client_session
```

#### 1.4 更新 setup() 主函数

```python
@meta_command
async def setup(app: "ShellApp", args: list[str]):
    """交互式配置 MyCLI ⭐ 完全对齐官方实现"""
    console.print("\n[bold cyan]MyCLI 配置向导[/bold cyan]\n")

    result = await _setup()
    if not result:
        return  # 用户取消或错误

    config = load_config()

    # 添加 Provider
    config.providers[result.platform.id] = LLMProvider(
        type="kimi",
        base_url=result.platform.base_url,
        api_key=result.api_key,
    )

    # 添加 Model
    config.models[result.model_id] = LLMModel(
        provider=result.platform.id,
        model=result.model_id,
        max_context_size=result.max_context_size,  # ⭐ 自动获取
    )

    config.default_model = result.model_id

    # ⭐ 自动配置 moonshot_search
    if result.platform.search_url:
        config.services.moonshot_search = MoonshotSearchConfig(
            base_url=result.platform.search_url,
            api_key=result.api_key,
        )

    save_config(config)

    console.print("\n[green]✓[/green] MyCLI 配置完成！正在重新加载...\n")
    await asyncio.sleep(1)
    console.clear()

    from my_cli.cli import Reload
    raise Reload
```

### 2. 修复 Reload 异常处理

**文件**: `my_cli/ui/shell/__init__.py`

#### 2.1 问题代码

```python
# ❌ 之前的代码（捕获所有异常）
async def _run_meta_command(self, command_name: str) -> None:
    try:
        result = cmd.func(self, cmd_args)
        if asyncio.iscoroutine(result):
            await result
    except Exception as e:
        console.print(f"[red]❌ 命令执行失败: {e}[/red]")
        import traceback
        traceback.print_exc()
```

**问题分析**：
1. `Reload` 继承自 `Exception`
2. `except Exception as e` 会捕获 `Reload` 异常
3. 导致 `Reload` 无法向上传播到 `cli.py`
4. CLI 不会重新加载配置

#### 2.2 修复代码

```python
# ✅ 修复后的代码（特殊处理 Reload）
async def _run_meta_command(self, command_name: str) -> None:
    try:
        result = cmd.func(self, cmd_args)
        if asyncio.iscoroutine(result):
            await result
    except Exception as e:
        # ⭐ 特殊处理：Reload 异常需要向上传播
        from my_cli.cli import Reload
        if isinstance(e, Reload):
            raise  # 向上传播，由 cli.py 的 while 循环捕获

        console.print(f"[red]❌ 命令执行失败: {e}[/red]")
        import traceback
        traceback.print_exc()
```

#### 2.3 官方实现参考

**文件**: `kimi-cli-fork/src/kimi_cli/ui/shell/__init__.py:163-165`

```python
try:
    ret = command.func(self, command_args)
    if isinstance(ret, Awaitable):
        await ret
except LLMNotSet:
    logger.error("LLM not set")
    console.print("[red]LLM not set, send /setup to configure[/red]")
except ChatProviderError as e:
    logger.exception("LLM provider error:")
    console.print(f"[red]LLM provider error: {e}[/red]")
except asyncio.CancelledError:
    logger.info("Interrupted by user")
    console.print("[red]Interrupted by user[/red]")
except Reload:
    # just propagate
    raise  # ⭐ 关键：重新抛出 Reload 异常
except BaseException as e:
    logger.exception("Unknown error:")
    console.print(f"[red]Unknown error: {e}[/red]")
    raise
```

---

## 🎯 改进效果

### 1. Setup 用户体验提升

**之前（手动输入）**：
```
Select the API platform
> Moonshot AI 开放平台 (moonshot.cn)

Enter your API key: ****

模型名称 (默认: moonshot-v1-8k): kimi-k2-thinking-turbo
Max Context Size (默认: 128000): 262144
```

**现在（自动获取）**：
```
Select the API platform
> Moonshot AI 开放平台 (moonshot.cn)

Enter your API key: ****

Select the model
  1. kimi-k2-pro
  2. kimi-k2-thinking-turbo
> 3. kimi-k2-latest
```

**优势**：
- ✅ 无需记忆模型名称
- ✅ 无需查询 context_length
- ✅ 实时显示可用模型
- ✅ 防止输入错误的模型名称

### 2. Reload 正常工作

**之前**：
```
✓ MyCLI 配置完成！正在重新加载...
❌ 命令执行失败:
✨ You:
```

**现在**：
```
✓ MyCLI 配置完成！正在重新加载...
[清屏]
╭──────────────────────────────────────────────────────────────────╮
│                      Welcome to MyCLI Assistant!                  │
│  Directory: ~/project                                            │
│  Session: xxx-xxx-xxx                                            │
│  Model: kimi-k2-thinking-turbo                                   │
╰──────────────────────────────────────────────────────────────────╯

✨ You:
```

**优势**：
- ✅ 配置立即生效
- ✅ 无需手动重启 CLI
- ✅ 用户体验流畅

---

## 📊 技术细节

### 1. API 调用示例

**请求**：
```http
GET https://api.moonshot.cn/v1/models
Authorization: Bearer sk-xxx
```

**响应**：
```json
{
  "data": [
    {
      "id": "kimi-k2-pro",
      "context_length": 262144,
      "created": 1234567890,
      "object": "model"
    },
    {
      "id": "kimi-k2-thinking-turbo",
      "context_length": 262144,
      "created": 1234567890,
      "object": "model"
    }
  ]
}
```

### 2. allowed_prefixes 过滤

**平台定义**：
```python
_Platform(
    id="moonshot-cn",
    name="Moonshot AI 开放平台 (moonshot.cn)",
    base_url="https://api.moonshot.cn/v1",
    allowed_prefixes=["kimi-k2-"],  # ⭐ 只允许 kimi-k2-* 模型
)
```

**过滤逻辑**：
```python
if platform.allowed_prefixes is not None:
    model_ids = [
        model_id
        for model_id in model_ids
        if model_id.startswith(tuple(platform.allowed_prefixes))
    ]
```

**结果**：
- ✅ `kimi-k2-pro` - 显示
- ✅ `kimi-k2-thinking-turbo` - 显示
- ❌ `moonshot-v1-8k` - 过滤掉（不符合前缀）

### 3. Reload 异常传播路径

```
setup.py:142 (raise Reload)
    ↓
shell/__init__.py:251 (检测到 Reload，重新抛出)
    ↓
shell/__init__.py:289 (app.run 向上传播)
    ↓
app.py:289 (run_shell_mode 向上传播)
    ↓
cli.py:354 (while True 循环捕获)
    ↓
cli.py:355 (continue - 重新运行 _run())
```

---

## 🔍 对比总结

| 方面 | 初版实现 | 完整实现 | 改进 |
|------|---------|---------|------|
| **模型选择** | 手动输入 | API 拉取列表 | ✅ 用户体验 |
| **context_length** | 手动输入 | 自动读取 | ✅ 准确性 |
| **allowed_prefixes** | ❌ 不支持 | ✅ 支持 | ✅ 模型过滤 |
| **search 自动配置** | ✅ 支持 | ✅ 支持 | - |
| **Reload 处理** | ❌ 被错误捕获 | ✅ 正确传播 | ✅ 功能修复 |
| **错误处理** | 基础 | 完善 | ✅ 用户友好 |

---

## 📚 相关文档

- **官方实现**: `kimi-cli-fork/src/kimi_cli/ui/shell/setup.py:94-159`
- **Reload 处理**: `kimi-cli-fork/src/kimi_cli/ui/shell/__init__.py:163-165`
- **Stage 21 文档**: `docs/STAGE_21_TOOLS_EXTENSION.md`

---

## ✅ 测试验证

### 1. Setup 完整流程测试

```bash
# 1. 启动 CLI
python -m my_cli.cli

# 2. 执行 setup
/setup

# 3. 选择平台
> Moonshot AI 开放平台 (moonshot.cn)

# 4. 输入 API Key
sk-xxx

# 5. 选择模型（从列表中）
> kimi-k2-thinking-turbo

# 6. 验证配置生效
# CLI 自动重新加载，显示新模型
```

### 2. Reload 异常测试

```bash
# 1. 运行 /setup
/setup
# ... 完成配置 ...

# 预期结果：
# - 显示 "✓ MyCLI 配置完成！正在重新加载..."
# - CLI 清屏
# - 显示新的欢迎界面（使用新配置）
# - 无 "❌ 命令执行失败" 错误
```

### 3. 配置文件验证

```python
from my_cli.config import load_config

config = load_config()
assert config.default_model == "kimi-k2-thinking-turbo"
assert "kimi-k2-thinking-turbo" in config.models
assert config.models["kimi-k2-thinking-turbo"].max_context_size == 262144
assert config.services.moonshot_search is not None
```

---

## 🎓 经验总结

### 1. 异常处理最佳实践

**原则**：
- 不要捕获不应该处理的异常
- 特殊异常（如 Reload）需要向上传播
- 使用 `isinstance()` 检测特定异常类型

**示例**：
```python
try:
    await some_function()
except SpecialException:
    raise  # 重新抛出特殊异常
except Exception as e:
    # 处理普通异常
    logger.error(f"Error: {e}")
```

### 2. API 集成模式

**步骤**：
1. 输入认证信息（API Key）
2. 调用 API 拉取数据
3. 处理响应（过滤、转换）
4. 用户选择（从数据中）
5. 使用选择的数据配置

**优势**：
- 数据实时准确
- 用户体验友好
- 减少手动输入错误

### 3. 配置管理模式

**关键点**：
- 使用 Pydantic 验证
- 支持环境变量覆盖
- 提供默认值
- 自动配置相关服务（如 search）

---

**生成时间**: 2025-01-20
**作者**: Claude（老王编程助手）
**版本**: v1.0

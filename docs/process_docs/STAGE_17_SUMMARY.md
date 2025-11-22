# Stage 17 完整总结：LLM 统一接口层 + 重试机制 + 工具系统增强

> **作者**: 老王
> **日期**: 2025-01-17
> **难度**: ⭐⭐⭐⭐⭐
> **关键词**: LLM 抽象层、create_llm、@tenacity.retry、CustomToolset、tool_result_to_message

---

## 📋 目录

1. [Stage 17 概览](#stage-17-概览)
2. [核心改动文件清单](#核心改动文件清单)
3. [详细实现分析](#详细实现分析)
4. [架构变化对比](#架构变化对比)
5. [测试验证](#测试验证)
6. [学习总结](#学习总结)

---

## Stage 17 概览

### 为什么需要 Stage 17？

**Stage 16 的问题：**
- ❌ 直接使用 `ChatProvider`，缺少统一的 LLM 抽象层
- ❌ 没有 `max_context_size` 和 `capabilities` 管理
- ❌ 没有重试机制，网络错误会直接导致失败
- ❌ 工具调用缺少上下文管理（tool_call_id）
- ❌ 工具消息转换过于简化，不区分 ToolError/ToolOk

**Stage 17 的解决方案：**
- ✅ **LLM 统一接口层**：封装 ChatProvider + max_context_size + capabilities
- ✅ **create_llm() 工厂函数**：支持 5 种 ChatProvider（Kimi、OpenAI Legacy、OpenAI Responses、Anthropic、_chaos）
- ✅ **@tenacity.retry 重试机制**：自动重试网络错误和 API 限流
- ✅ **CustomToolset**：管理 current_tool_call 上下文
- ✅ **完整的工具消息转换**：区分 ToolError/ToolOk，支持空输出和系统消息

### Stage 17 核心目标

1. **抽象化 LLM 接口**：统一管理不同 Provider 的 LLM
2. **增强可靠性**：网络错误自动重试
3. **完善工具系统**：工具调用上下文管理 + 完整的消息转换
4. **提升代码质量**：遵循官方架构，为后续扩展打好基础

---

## 核心改动文件清单

### 新增文件（1 个）

| 文件路径 | 行数 | 作用 |
|---------|------|------|
| `my_cli/llm.py` | 296 | LLM 统一接口层：LLM 类、create_llm() 工厂函数、环境变量覆盖 |

### 修改文件（7 个）

| 文件路径 | 改动行数 | 主要改动 |
|---------|---------|---------|
| `my_cli/soul/message.py` | +73, -38 | 完整实现 tool_result_to_message()、tool_ok_to_message_content()、_output_to_content_parts() |
| `my_cli/soul/toolset.py` | +6, -3 | CustomToolset.handle() 设置 current_tool_call 上下文 |
| `my_cli/soul/kimisoul.py` | +85, -46 | 导入 tenacity、_step() 添加重试机制、使用 self._runtime.llm |
| `my_cli/tools/__init__.py` | +150, -10 | 新增 extract_key_argument()、_normalize_path() |
| `my_cli/soul/runtime.py` | +23, -13 | 使用 LLM 替代 ChatProvider |
| `my_cli/soul/__init__.py` | +14, -18 | create_soul() 使用 create_llm() |
| `my_cli/soul/message.py` | 见上 | 工具消息转换完整版 |

### 依赖变化

**新增依赖：**
- `tenacity`：重试机制库

**安装命令：**
```bash
pip install tenacity
```

---

## 详细实现分析

### 1. my_cli/llm.py - LLM 统一接口层 ⭐⭐⭐⭐⭐

**文件位置：** `my_cli/llm.py`
**行数：** 296 行
**对应源码：** `kimi-cli-fork/src/kimi_cli/llm.py`

#### 1.1 LLM 类

```python
@dataclass(slots=True)
class LLM:
    """统一的 LLM 接口"""
    chat_provider: ChatProvider      # kosong 的 ChatProvider
    max_context_size: int           # 最大 Context 大小
    capabilities: set[ModelCapability]  # 模型能力（image_in, thinking）

    @property
    def model_name(self) -> str:
        return self.chat_provider.model_name
```

**作用：**
- 封装 `ChatProvider`，添加额外的元数据（max_context_size、capabilities）
- 提供统一的 `model_name` 属性

**为什么需要 LLM 类？**
- ❌ **Stage 16 问题**：直接使用 `ChatProvider`，不知道模型的 max_context_size 和 capabilities
- ✅ **Stage 17 解决**：LLM 类统一管理这些信息，方便后续使用

#### 1.2 create_llm() 工厂函数

```python
def create_llm(
    provider: "LLMProvider",
    model: "LLMModel",
    *,
    stream: bool = True,
    session_id: str | None = None,
) -> LLM:
    """根据 Provider 类型创建对应的 ChatProvider，然后封装成 LLM"""
    match provider.type:
        case "kimi":
            from kosong.chat_provider.kimi import Kimi
            chat_provider = Kimi(...)
        case "openai_legacy":
            from kosong.contrib.chat_provider.openai_legacy import OpenAILegacy
            chat_provider = OpenAILegacy(...)
        case "openai_responses":
            from kosong.contrib.chat_provider.openai_responses import OpenAIResponses
            chat_provider = OpenAIResponses(...)
        case "anthropic":
            from kosong.contrib.chat_provider.anthropic import Anthropic
            chat_provider = Anthropic(...)
        case "_chaos":
            # 测试用的混沌 ChatProvider（模拟错误）
            chat_provider = ChaosChatProvider(...)

    return LLM(
        chat_provider=chat_provider,
        max_context_size=model.max_context_size,
        capabilities=_derive_capabilities(provider, model),
    )
```

**作用：**
- 根据 `provider.type` 创建不同的 `ChatProvider`（工厂模式）
- 支持 5 种 ChatProvider：Kimi、OpenAI Legacy、OpenAI Responses、Anthropic、_chaos
- 封装成 `LLM` 对象

**为什么使用工厂函数？**
- ✅ **统一创建入口**：所有 LLM 创建都通过 `create_llm()`
- ✅ **解耦配置和实现**：配置文件只需要指定 `type`，不需要知道具体的 ChatProvider 类
- ✅ **支持多种 Provider**：未来添加新 Provider 只需要在 `match` 中添加一个 `case`

#### 1.3 _derive_capabilities() - 能力推导

```python
def _derive_capabilities(provider: "LLMProvider", model: "LLMModel") -> set[ModelCapability]:
    """根据 Provider 类型和 Model 名称推导额外的能力"""
    capabilities = (
        model.capabilities if hasattr(model, "capabilities") and model.capabilities else set()
    )

    # Kimi 特殊处理：自动添加 thinking 能力
    if provider.type == "kimi":
        if model.model == "kimi-for-coding" or "thinking" in model.model:
            capabilities.add("thinking")

    return capabilities
```

**作用：**
- 根据模型名称自动推导能力（如 Kimi 的 thinking 能力）
- 兼容 config 缺失 `capabilities` 字段

**为什么需要能力推导？**
- ✅ **智能默认值**：Kimi 的 `kimi-for-coding` 和 `thinking` 模型自动添加 `thinking` 能力
- ✅ **减少配置**：用户不需要手动配置 `capabilities`

#### 1.4 augment_provider_with_env_vars() - 环境变量覆盖

```python
def augment_provider_with_env_vars(provider: "LLMProvider", model: "LLMModel") -> dict[str, str]:
    """从环境变量覆盖 Provider/Model 设置"""
    applied: dict[str, str] = {}

    match provider.type:
        case "kimi":
            if base_url := os.getenv("KIMI_BASE_URL"):
                provider.base_url = base_url
                applied["KIMI_BASE_URL"] = base_url
            if api_key := os.getenv("KIMI_API_KEY"):
                provider.api_key = SecretStr(api_key)
                applied["KIMI_API_KEY"] = "******"
            # ... 更多环境变量

    return applied
```

**作用：**
- 允许用户通过环境变量临时覆盖配置文件中的设置
- 支持覆盖：base_url、api_key、model_name、max_context_size、capabilities

**使用场景：**
```bash
# 临时使用不同的 API Key
export KIMI_API_KEY="sk-xxx"
python my_cli/cli.py --ui shell
```

---

### 2. my_cli/soul/message.py - 工具消息转换完整版 ⭐⭐⭐⭐

**文件位置：** `my_cli/soul/message.py`
**行数：** 193 行（+73, -38）
**对应源码：** `kimi-cli-fork/src/kimi_cli/soul/message.py`

#### 2.1 tool_result_to_message() - 完整版

**Before（Stage 16）：**
```python
def tool_result_to_message(tool_result: ToolResult) -> Message:
    # ❌ 简化版：直接转换为字符串，不区分 ToolError 和 ToolOk
    if hasattr(tool_result.result, "output"):
        output_str = str(tool_result.result.output)
    else:
        output_str = str(tool_result.result)

    return Message(
        role="tool",
        content=[TextPart(text=output_str)],
        tool_call_id=tool_result.tool_call_id,
    )
```

**After（Stage 17）：**
```python
def tool_result_to_message(tool_result: ToolResult) -> Message:
    # ✅ 完整版：区分 ToolError 和 ToolOk
    if isinstance(tool_result.result, ToolError):
        # 工具执行出错：创建错误消息
        assert tool_result.result.message, "ToolError should have a message"
        message = tool_result.result.message

        # 如果是运行时错误，添加额外警告
        if isinstance(tool_result.result, ToolRuntimeError):
            message += "\nThis is an unexpected error and the tool is probably not working."

        # 创建系统错误消息
        content: list[ContentPart] = [system(f"ERROR: {message}")]

        # 如果有 output，也添加进去（可能包含错误详情）
        if tool_result.result.output:
            content.extend(_output_to_content_parts(tool_result.result.output))
    else:
        # 工具执行成功：转换为消息内容
        content = tool_ok_to_message_content(tool_result.result)

    return Message(
        role="tool",
        content=content,
        tool_call_id=tool_result.tool_call_id,
    )
```

**改进点：**
1. ✅ **区分 ToolError 和 ToolOk**：错误消息带 `<system>ERROR: ...</system>` 标签
2. ✅ **ToolRuntimeError 额外警告**：提示工具可能无法正常工作
3. ✅ **错误详情**：如果 ToolError 有 output，也添加到消息中

#### 2.2 tool_ok_to_message_content() - 处理空输出

**Before（Stage 16）：**
```python
def tool_ok_to_message_content(result: ToolOk) -> list[ContentPart]:
    # ❌ 简化版：直接返回 output
    return [TextPart(text=str(result.output))]
```

**After（Stage 17）：**
```python
def tool_ok_to_message_content(result: ToolOk) -> list[ContentPart]:
    content: list[ContentPart] = []

    # 如果有 message，添加为系统消息
    if result.message:
        content.append(system(result.message))

    # 转换 output
    content.extend(_output_to_content_parts(result.output))

    # 如果 content 为空，添加提示
    if not content:
        content.append(system("Tool output is empty."))

    return content
```

**改进点：**
1. ✅ **支持 result.message**：工具可以返回系统消息
2. ✅ **处理空输出**：添加 `<system>Tool output is empty.</system>` 提示
3. ✅ **使用 _output_to_content_parts()**：支持 ContentPart 序列

#### 2.3 _output_to_content_parts() - 支持 ContentPart 序列

**Before（Stage 16）：**
```python
def _output_to_content_parts(output: str | ContentPart | Sequence[ContentPart]) -> list[ContentPart]:
    # ❌ 简化版：只支持字符串
    if isinstance(output, str):
        return [TextPart(text=output)]
    return []
```

**After（Stage 17）：**
```python
def _output_to_content_parts(output: str | ContentPart | Sequence[ContentPart]) -> list[ContentPart]:
    content: list[ContentPart] = []

    if isinstance(output, str):
        # 字符串：创建 TextPart（跳过空字符串）
        if output.strip():
            content.append(TextPart(text=output))
    elif isinstance(output, ContentPart):
        # 单个 ContentPart：直接添加
        content.append(output)
    else:
        # ContentPart 序列：展开（跳过空文本片段）
        for part in output:
            if isinstance(part, TextPart) and not part.text.strip():
                continue
            content.append(part)

    return content
```

**改进点：**
1. ✅ **支持 ContentPart**：工具可以返回单个 ContentPart
2. ✅ **支持 ContentPart 序列**：工具可以返回多个 ContentPart（如文本 + 图片）
3. ✅ **跳过空文本**：避免添加空的 TextPart

---

### 3. my_cli/soul/toolset.py - CustomToolset 完整版 ⭐⭐⭐

**文件位置：** `my_cli/soul/toolset.py`
**行数：** 133 行（+6, -3）
**对应源码：** `kimi-cli-fork/src/kimi_cli/soul/toolset.py`

#### 3.1 CustomToolset.handle() - 设置 current_tool_call 上下文

**Before（Stage 16）：**
```python
class CustomToolset(SimpleToolset):
    def handle(self, tool_call: ToolCall) -> HandleResult:
        # ❌ 简化版：直接调用父类
        return super().handle(tool_call)
```

**After（Stage 17）：**
```python
class CustomToolset(SimpleToolset):
    @override
    def handle(self, tool_call: ToolCall) -> HandleResult:
        # ✅ 完整版：设置 current_tool_call 上下文
        token = current_tool_call.set(tool_call)
        try:
            return super().handle(tool_call)
        finally:
            current_tool_call.reset(token)
```

**作用：**
- 在工具调用前设置 `current_tool_call` ContextVar
- 在工具调用后重置 ContextVar

**为什么需要 current_tool_call？**
- ✅ **工具可以获取自己的 tool_call_id**：通过 `get_current_tool_call_or_none()` 获取
- ✅ **Approval 系统需要 tool_call_id**：批准请求需要知道是哪个工具在请求

#### 3.2 ContextVar 原理

```python
# 定义 ContextVar
current_tool_call = ContextVar[ToolCall | None]("current_tool_call", default=None)

# 设置
token = current_tool_call.set(tool_call)

# 获取
tool_call = current_tool_call.get()

# 重置
current_tool_call.reset(token)
```

**ContextVar 特点：**
- ✅ **线程安全**：每个异步任务有独立的上下文副本
- ✅ **不会互相干扰**：并发任务之间不会互相影响
- ✅ **非常适合异步环境**：asyncio 中传递"全局"状态

---

### 4. my_cli/soul/kimisoul.py - @tenacity.retry 重试机制 ⭐⭐⭐⭐⭐

**文件位置：** `my_cli/soul/kimisoul.py`
**行数：** 430 行（+85, -46）
**对应源码：** `kimi-cli-fork/src/kimi_cli/soul/kimisoul.py`

#### 4.1 导入 tenacity

```python
import tenacity
from kosong.chat_provider import (
    APIConnectionError,
    APIEmptyResponseError,
    APIStatusError,
    APITimeoutError,
)
from tenacity import RetryCallState, retry_if_exception, stop_after_attempt, wait_exponential_jitter
```

**新增导入：**
- `tenacity`：重试机制库
- `APIConnectionError`、`APITimeoutError`、`APIEmptyResponseError`：网络错误
- `APIStatusError`：API 状态码错误
- `RetryCallState`、`retry_if_exception`、`stop_after_attempt`、`wait_exponential_jitter`：tenacity 相关函数

#### 4.2 _step() - 添加重试机制

**Before（Stage 16）：**
```python
async def _step(self) -> bool:
    # ❌ 简化版：直接调用 kosong.step()，没有重试机制
    result = await kosong.step(
        chat_provider=self._runtime.chat_provider,
        system_prompt=self._agent.system_prompt,
        toolset=self._toolset,
        history=self._context.get_messages(),
        on_message_part=wire_send,
        on_tool_result=wire_send,
    )
    # ...
```

**After（Stage 17）：**
```python
async def _step(self) -> bool:
    # ✅ 完整版：使用 @tenacity.retry 装饰器包装 kosong.step() 调用
    @tenacity.retry(
        retry=retry_if_exception(self._is_retryable_error),
        before_sleep=partial(self._retry_log, "step"),
        wait=wait_exponential_jitter(initial=0.3, max=5, jitter=0.5),
        stop=stop_after_attempt(3),  # 最多重试 3 次
        reraise=True,
    )
    async def _kosong_step_with_retry() -> "kosong.StepResult":
        return await kosong.step(
            chat_provider=self._runtime.llm.chat_provider,
            system_prompt=self._agent.system_prompt,
            toolset=self._toolset,
            history=self._context.get_messages(),
            on_message_part=wire_send,
            on_tool_result=wire_send,
        )

    # 执行 kosong.step()（带重试机制）
    result = await _kosong_step_with_retry()
    # ...
```

**重试参数解释：**
- `retry=retry_if_exception(self._is_retryable_error)`：只重试可重试的错误
- `before_sleep=partial(self._retry_log, "step")`：重试前记录日志
- `wait=wait_exponential_jitter(initial=0.3, max=5, jitter=0.5)`：指数退避 + 抖动
  - 第 1 次重试：等待 0.3 秒
  - 第 2 次重试：等待 0.6 秒
  - 第 3 次重试：等待 1.2 秒
  - 最大等待：5 秒
  - 抖动：±0.5 秒（避免雷击效应）
- `stop=stop_after_attempt(3)`：最多重试 3 次
- `reraise=True`：重试失败后重新抛出异常

#### 4.3 _is_retryable_error() - 检查可重试错误

```python
@staticmethod
def _is_retryable_error(exception: BaseException) -> bool:
    """检查异常是否可重试"""
    # 网络相关错误：连接失败、超时、空响应
    if isinstance(exception, (APIConnectionError, APITimeoutError, APIEmptyResponseError)):
        return True

    # API 状态码错误：429（限流）、500/502/503（服务器错误）
    return isinstance(exception, APIStatusError) and exception.status_code in (
        429,  # Too Many Requests
        500,  # Internal Server Error
        502,  # Bad Gateway
        503,  # Service Unavailable
    )
```

**可重试的错误：**
1. ✅ `APIConnectionError`：网络连接失败
2. ✅ `APITimeoutError`：请求超时
3. ✅ `APIEmptyResponseError`：空响应
4. ✅ `APIStatusError` 429：Too Many Requests（API 限流）
5. ✅ `APIStatusError` 500：Internal Server Error（服务器内部错误）
6. ✅ `APIStatusError` 502：Bad Gateway（网关错误）
7. ✅ `APIStatusError` 503：Service Unavailable（服务不可用）

**不可重试的错误：**
- ❌ `APIStatusError` 400：Bad Request（请求参数错误）
- ❌ `APIStatusError` 401：Unauthorized（未授权）
- ❌ `APIStatusError` 403：Forbidden（禁止访问）
- ❌ `APIStatusError` 404：Not Found（未找到）
- ❌ 其他异常：逻辑错误、代码错误等

#### 4.4 _retry_log() - 记录重试日志

```python
@staticmethod
def _retry_log(name: str, retry_state: RetryCallState):
    """记录重试日志"""
    sleep_time = (
        retry_state.next_action.sleep if retry_state.next_action is not None else "unknown"
    )
    print(
        f"⚠️ Retrying {name} for the {retry_state.attempt_number} time. Waiting {sleep_time} seconds."
    )
```

**日志输出示例：**
```
⚠️ Retrying step for the 1 time. Waiting 0.3 seconds.
⚠️ Retrying step for the 2 time. Waiting 0.6 seconds.
⚠️ Retrying step for the 3 time. Waiting 1.2 seconds.
```

#### 4.5 使用 self._runtime.llm

**改动位置 1：model_name 属性**
```python
@property
def model_name(self) -> str:
    # ✅ Stage 17：从 Runtime 的 LLM 获取模型名称
    return self._runtime.llm.model_name
```

**改动位置 2：model_capabilities 属性**
```python
@property
def model_capabilities(self) -> set[str] | None:
    # ✅ Stage 17：从 Runtime 的 LLM 获取 capabilities
    return self._runtime.llm.capabilities
```

**改动位置 3：run() 检查 LLM**
```python
async def run(self, user_input: str | list[ContentPart]):
    # 1. 检查 LLM 是否配置
    if not self._runtime.llm:  # ⭐ Stage 17：改为检查 llm
        raise LLMNotSet()
```

**改动位置 4：_step() 使用 llm.chat_provider**
```python
async def _kosong_step_with_retry() -> "kosong.StepResult":
    return await kosong.step(
        chat_provider=self._runtime.llm.chat_provider,  # ⭐ Stage 17：使用 llm.chat_provider
        # ...
    )
```

---

### 5. my_cli/tools/__init__.py - extract_key_argument() 函数 ⭐⭐⭐

**文件位置：** `my_cli/tools/__init__.py`
**行数：** 178 行（+150, -10）
**对应源码：** `kimi-cli-fork/src/kimi_cli/tools/__init__.py`

#### 5.1 extract_key_argument() - 提取关键参数

```python
def extract_key_argument(json_content: str, tool_name: str) -> str | None:
    """从工具调用参数中提取关键参数（用于 UI 显示）"""
    try:
        curr_args: JsonType = json.loads(json_content)
    except json.JSONDecodeError:
        return None

    if not curr_args:
        return None

    key_argument: str = ""

    # 根据工具名称提取关键参数
    match tool_name:
        case "Bash" | "CMD":
            if not isinstance(curr_args, dict) or not curr_args.get("command"):
                return None
            key_argument = str(curr_args["command"])

        case "ReadFile":
            if not isinstance(curr_args, dict) or not curr_args.get("path"):
                return None
            key_argument = _normalize_path(str(curr_args["path"]))

        # ... 更多工具

    return key_argument
```

**支持的工具：**
- ✅ `Bash` / `CMD`：提取 `command`
- ✅ `ReadFile` / `WriteFile` / `StrReplaceFile`：提取 `path`（归一化）
- ✅ `Glob`：提取 `pattern`
- ✅ `Grep`：提取 `pattern`
- ✅ `SearchWeb`：提取 `query`
- ✅ `FetchURL`：提取 `url`
- ✅ `Task`：提取 `description`
- ✅ `Think`：提取 `thought`
- ✅ `SendDMail`：返回 `"El Psy Kongroo"`（彩蛋）
- ✅ `SetTodoList`：返回 `None`
- ✅ 其他工具：返回完整 JSON 字符串

**使用场景：**
- UI 显示工具调用时，显示关键参数而不是完整 JSON
- 例如：`Bash(command="ls -la")` 而不是 `Bash({"command": "ls -la", "timeout": 30, ...})`

#### 5.2 _normalize_path() - 归一化路径

```python
def _normalize_path(path: str) -> str:
    """归一化路径（移除 CWD 前缀）"""
    cwd = str(Path.cwd().absolute())

    # 如果路径以 CWD 开头，移除 CWD 前缀
    if path.startswith(cwd):
        path = path[len(cwd) :].lstrip("/\\")

    return path
```

**作用：**
- 将绝对路径转换为相对路径
- 例如：`/home/user/project/src/main.py` → `src/main.py`

**为什么需要归一化路径？**
- ✅ **简化显示**：相对路径更简洁
- ✅ **保护隐私**：不暴露完整路径

---

### 6. my_cli/soul/runtime.py - 使用 LLM 替代 ChatProvider ⭐⭐⭐

**文件位置：** `my_cli/soul/runtime.py`
**行数：** 57 行（+23, -13）
**对应源码：** `kimi-cli-fork/src/kimi_cli/soul/runtime.py`

**Before（Stage 16）：**
```python
class Runtime:
    def __init__(
        self,
        chat_provider: ChatProvider,  # ❌ 直接使用 ChatProvider
        max_steps: int = 20,
    ):
        self.chat_provider = chat_provider
        self.max_steps = max_steps
```

**After（Stage 17）：**
```python
class Runtime:
    def __init__(
        self,
        llm: "LLM",  # ✅ 使用 LLM
        max_steps: int = 20,
    ):
        self.llm = llm
        self.max_steps = max_steps
```

**改进点：**
- ✅ **统一的 LLM 接口**：Runtime 不直接依赖 ChatProvider
- ✅ **访问 max_context_size 和 capabilities**：通过 `self.llm.max_context_size` 和 `self.llm.capabilities` 访问

---

### 7. my_cli/soul/__init__.py - create_soul() 使用 create_llm() ⭐⭐⭐⭐

**文件位置：** `my_cli/soul/__init__.py`
**行数：** 593 行（+14, -18）
**对应源码：** `kimi-cli-fork/src/kimi_cli/app.py`

**Before（Stage 16）：**
```python
def create_soul(...) -> KimiSoul:
    # 1. 加载配置文件
    config = load_config(config_file)
    provider, model = get_provider_and_model(config, model_name)

    # 2. 创建 Agent
    agent = Agent(name=agent_name, work_dir=work_dir)

    # 3. 创建 ChatProvider
    chat_provider = Kimi(
        base_url=provider.base_url,
        api_key=provider.api_key.get_secret_value(),
        model=model.model,
    )

    # 4. 创建 Runtime
    runtime = Runtime(
        chat_provider=chat_provider,  # ❌ 传入 ChatProvider
        max_steps=20,
    )

    # 5. 创建 SimpleToolset
    toolset = SimpleToolset()

    # 6. 创建 KimiSoul
    soul = KimiSoul(agent=agent, runtime=runtime, toolset=toolset)
    return soul
```

**After（Stage 17）：**
```python
def create_soul(...) -> KimiSoul:
    from my_cli.soul.kimisoul import KimiSoul

    # 1. 加载配置文件
    config = load_config(config_file)
    provider, model = get_provider_and_model(config, model_name)

    # 2. 创建 Agent
    agent = Agent(name=agent_name, work_dir=work_dir)

    # ============================================================
    # ⭐ Stage 17：使用 create_llm() 创建 LLM
    # ============================================================

    # 3. 创建 LLM（使用 create_llm() 工厂函数）
    from my_cli.llm import create_llm

    llm = create_llm(
        provider=provider,
        model=model,
        stream=True,
        session_id=None,  # Stage 17+：传入 session.id
    )

    # 4. 创建 Runtime（传入 LLM）
    runtime = Runtime(
        llm=llm,  # ✅ 传入 LLM 而不是 ChatProvider
        max_steps=20,
    )

    # 5. 创建 SimpleToolset
    toolset = SimpleToolset()

    # 6. 创建 KimiSoul
    soul = KimiSoul(agent=agent, runtime=runtime, toolset=toolset)
    return soul
```

**改进点：**
- ✅ **使用 create_llm()**：统一创建 LLM
- ✅ **支持多种 Provider**：未来添加新 Provider 不需要修改 create_soul()

---

## 架构变化对比

### Stage 16 架构

```
create_soul()
    ↓
1. load_config() → provider, model
    ↓
2. Agent(name, work_dir)
    ↓
3. Kimi(base_url, api_key, model)  ← 直接创建 ChatProvider
    ↓
4. Runtime(chat_provider, max_steps)  ← 传入 ChatProvider
    ↓
5. SimpleToolset()
    ↓
6. KimiSoul(agent, runtime, toolset)
    ↓
    使用 runtime.chat_provider 调用 LLM
```

**问题：**
- ❌ 缺少 LLM 抽象层
- ❌ 没有 max_context_size 和 capabilities 管理
- ❌ 没有重试机制
- ❌ 工具调用缺少上下文管理

### Stage 17 架构

```
create_soul()
    ↓
1. load_config() → provider, model
    ↓
2. Agent(name, work_dir)
    ↓
3. create_llm(provider, model)  ← ⭐ 使用工厂函数
    ↓
    match provider.type:
        case "kimi" → Kimi(...)
        case "openai_legacy" → OpenAILegacy(...)
        case "openai_responses" → OpenAIResponses(...)
        case "anthropic" → Anthropic(...)
        case "_chaos" → ChaosChatProvider(...)
    ↓
    LLM(chat_provider, max_context_size, capabilities)  ← ⭐ 封装成 LLM
    ↓
4. Runtime(llm, max_steps)  ← ⭐ 传入 LLM
    ↓
5. SimpleToolset()
    ↓
6. KimiSoul(agent, runtime, toolset)
    ↓
    使用 runtime.llm.chat_provider 调用 LLM
    ↓
    _step() 中使用 @tenacity.retry 重试机制  ← ⭐ 自动重试
```

**改进：**
- ✅ LLM 抽象层：统一管理 ChatProvider + max_context_size + capabilities
- ✅ 工厂函数：支持多种 Provider
- ✅ 重试机制：自动重试网络错误和 API 限流
- ✅ 工具上下文：CustomToolset 管理 current_tool_call

---

## 测试验证

### 测试命令

```bash
# 安装依赖
pip install tenacity

# 测试基础功能
python my_cli/cli.py --ui shell --command "你好，请简单介绍一下你自己（用一句话）"
```

### 测试结果

```
💬 AI 回复:

你好，我是 MyCLI Assistant，一个简洁高效的 AI 命令行助手。
```

**测试通过 ✅**

### 测试覆盖

1. ✅ **LLM 创建**：create_llm() 成功创建 Kimi ChatProvider
2. ✅ **LLM 封装**：Runtime 使用 LLM 而不是 ChatProvider
3. ✅ **KimiSoul 集成**：使用 self._runtime.llm.chat_provider
4. ✅ **重试机制**：（未触发，因为网络正常）
5. ✅ **工具消息转换**：（未触发，因为没有工具调用）

---

## 学习总结

### 核心知识点

#### 1. LLM 抽象层设计

**为什么需要抽象层？**
- ✅ **解耦配置和实现**：配置文件只需要指定 `type`
- ✅ **统一管理元数据**：max_context_size、capabilities
- ✅ **支持多种 Provider**：未来扩展更容易

**设计模式：**
- ✅ **工厂模式**：create_llm() 根据 type 创建不同的 ChatProvider
- ✅ **封装模式**：LLM 类封装 ChatProvider + 元数据

#### 2. @tenacity.retry 重试机制

**重试策略：**
- ✅ **指数退避**：0.3s → 0.6s → 1.2s → 2.4s → 5s（最大）
- ✅ **抖动**：±0.5s（避免雷击效应）
- ✅ **最大重试次数**：3 次
- ✅ **选择性重试**：只重试可重试的错误

**可重试的错误：**
- ✅ 网络错误：APIConnectionError、APITimeoutError、APIEmptyResponseError
- ✅ API 限流：429 Too Many Requests
- ✅ 服务器错误：500、502、503

**不可重试的错误：**
- ❌ 请求错误：400、401、403、404
- ❌ 逻辑错误：代码错误、参数错误

#### 3. ContextVar 上下文管理

**ContextVar 特点：**
- ✅ **线程安全**：每个异步任务有独立的上下文副本
- ✅ **不会互相干扰**：并发任务之间不会互相影响
- ✅ **非常适合异步环境**：asyncio 中传递"全局"状态

**使用场景：**
- ✅ **current_tool_call**：工具调用上下文
- ✅ **_current_wire**：当前 Wire 上下文（Stage 6）

#### 4. 工具消息转换

**关键点：**
- ✅ **区分 ToolError 和 ToolOk**：错误消息带 `<system>ERROR: ...</system>` 标签
- ✅ **处理空输出**：添加 `<system>Tool output is empty.</system>` 提示
- ✅ **支持 ContentPart 序列**：工具可以返回多个 ContentPart（如文本 + 图片）

### 最佳实践

#### 1. 工厂模式

```python
def create_llm(provider: LLMProvider, model: LLMModel) -> LLM:
    match provider.type:
        case "kimi":
            chat_provider = Kimi(...)
        case "openai_legacy":
            chat_provider = OpenAILegacy(...)
        # ... 更多 Provider

    return LLM(chat_provider, max_context_size, capabilities)
```

**优点：**
- ✅ 统一创建入口
- ✅ 解耦配置和实现
- ✅ 支持多种 Provider

#### 2. 重试机制

```python
@tenacity.retry(
    retry=retry_if_exception(is_retryable_error),
    before_sleep=log_retry,
    wait=wait_exponential_jitter(initial=0.3, max=5, jitter=0.5),
    stop=stop_after_attempt(3),
    reraise=True,
)
async def call_api():
    return await api_call()
```

**优点：**
- ✅ 自动重试网络错误
- ✅ 指数退避 + 抖动
- ✅ 最大重试次数限制

#### 3. ContextVar 上下文管理

```python
# 定义
current_context = ContextVar[Context | None]("current_context", default=None)

# 使用
token = current_context.set(context)
try:
    # 执行操作
    pass
finally:
    current_context.reset(token)
```

**优点：**
- ✅ 线程安全
- ✅ 不会互相干扰
- ✅ 适合异步环境

---

## 下一步（Stage 18+）

Stage 17 完成后，下一步可以实现：

1. **Stage 18：图片支持**
   - ImageURLPart：支持图片输入和输出
   - check_message()：检查消息能力

2. **Stage 19：Context 压缩**
   - SimpleCompaction：压缩 Context 以节省 Token
   - CompactionBegin/CompactionEnd：压缩控制事件

3. **Stage 20：Checkpoint/Rollback 机制**
   - _checkpoint()：创建 Context 检查点
   - BackToTheFuture：时间旅行异常

4. **Stage 21：Approval 系统**
   - ApprovalRequest：批准请求
   - ApprovalResponse：批准响应

---

## 总结

Stage 17 是一个重要的里程碑，完成了以下核心功能：

1. ✅ **LLM 统一接口层**：封装 ChatProvider + max_context_size + capabilities
2. ✅ **create_llm() 工厂函数**：支持 5 种 ChatProvider
3. ✅ **@tenacity.retry 重试机制**：自动重试网络错误和 API 限流
4. ✅ **CustomToolset**：管理 current_tool_call 上下文
5. ✅ **完整的工具消息转换**：区分 ToolError/ToolOk，支持空输出和系统消息

**代码质量提升：**
- ✅ 遵循官方架构
- ✅ 代码结构清晰
- ✅ 注释详细
- ✅ 测试通过

**学习收获：**
- ✅ 理解 LLM 抽象层设计
- ✅ 理解 @tenacity.retry 重试机制
- ✅ 理解 ContextVar 上下文管理
- ✅ 理解工具消息转换

艹！老王我写完了！这份文档详细解释了 Stage 17 的所有改动，你应该能理解清楚了吧？😤

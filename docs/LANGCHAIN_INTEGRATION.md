# LangChain 集成文档

## 概述

本项目已经集成了 LangChain，使用 DeepSeek-V3.2 模型进行智能错误分析。

## 架构设计

### 懒加载单例模式

`langchain_analyzer.py` 实现了懒加载的单例模式，避免重复初始化：

```python
_ERROR_ANALYSIS_CHAIN: Optional['Runnable'] = None

def get_error_analysis_chain():
    global _ERROR_ANALYSIS_CHAIN
    if _ERROR_ANALYSIS_CHAIN is None:
        _ERROR_ANALYSIS_CHAIN = _build_error_analysis_chain()
    return _ERROR_ANALYSIS_CHAIN
```

### 核心组件

1. **PromptTemplate**: 结构化错误分析的提示词
2. **ChatOpenAI**: 封装 DeepSeek-V3.2 API 调用
3. **Runnable Pipeline**: 使用 LangChain Expression Language (LCEL) 构建链式处理流程

## 使用方式

### 在 failure_inspector.py 中调用

```python
from langchain_analyzer import analyze_error_with_langchain

analysis = analyze_error_with_langchain(command, error_output, minecontext_summary)
```

### 错误处理

如果 LangChain 未安装，会优雅降级并提供安装提示：

```python
try:
    from langchain_analyzer import analyze_error_with_langchain
    analysis = analyze_error_with_langchain(cmd, output, minecontext_result)
    engine_info = "langchain_deepseek_v3"
except ImportError as e:
    analysis = f"LangChain 分析器导入失败: {e}\n建议: pip install langchain langchain-openai python-dotenv"
    engine_info = "error_no_langchain"
```

## 配置

### 环境变量

在项目根目录创建 `.env` 文件：

```bash
SILICONFLOW_API_KEY=sk-your-api-key-here
SILICONFLOW_BASE_URL=https://api.siliconflow.cn/v1
MODEL_NAME=deepseek-ai/DeepSeek-V3.2
```

### 环境变量说明

- `SILICONFLOW_API_KEY`: SiliconFlow 平台的 API 密钥
- `SILICONFLOW_BASE_URL`: API 基础地址（默认: https://api.siliconflow.cn/v1）
- `MODEL_NAME`: 使用的模型名称（默认: deepseek-ai/DeepSeek-V3.2）

## 安装依赖

```bash
pip install langchain langchain-openai python-dotenv
```

或者在项目根目录运行：

```bash
pip install -r requirements.txt
```

如果 requirements.txt 包含以下内容：

```
langchain>=0.1.0
langchain-openai>=0.0.5
python-dotenv>=1.0.0
```

## 测试

### 测试 LangChain 分析器

```bash
./.venv/Scripts/python.exe langchain_analyzer.py
```

### 测试完整流程

```bash
./.venv/Scripts/python.exe failure_inspector.py "python some_broken_script.py"
```

## 输出格式

在 `trajectory_{timestamp}.json` 中，LLM 分析步骤会包含引擎信息：

```json
{
  "type": "llm_analysis",
  "engine": "langchain_deepseek_v3",
  "result": "... LLM 生成的分析结果 ..."
}
```

可能的 engine 值：
- `langchain_deepseek_v3`: 成功使用 LangChain 和 DeepSeek-V3.2
- `error_no_langchain`: LangChain 模块导入失败
- `error_analysis_failed`: 分析过程中出现异常

## 性能优化

### 懒加载

链只在第一次调用时构建，后续调用复用已初始化的链，减少 API 连接和模型加载的延迟。

### 上下文长度控制

- MineContext JSON 摘要最多 3000 字符
- 错误输出最多 2000 字符
- 防止 prompt 过大导致 API 调用失败

## 与原始实现的对比

### 之前（llm_client.py）

```python
def call_llm(prompt: str) -> str:
    # 直接使用 requests 调用 API
    # 每次调用都重新初始化连接
    # 需要手动处理重试、错误处理、响应解析
```

### 现在（langchain_analyzer.py）

```python
def analyze_error_with_langchain(...) -> str:
    # 使用 LangChain 的抽象层
    # 链式调用，支持复杂的工作流
    # 自动处理序列化、错误重试
    # 支持流式输出（未来扩展）
```

## Future Enhancements

1. **流式输出**: 启用 `streaming=True` 实现实时响应
2. **记忆功能**: 集成 ConversationBufferMemory 保持对话上下文
3. **工具调用**: 添加自定义工具让 LLM 能调用项目内的函数
4. **多种模型**: 支持根据不同错误类型切换模型（e.g., 简单错误用轻量模型）

## Troubleshooting

### 问题：ImportError: No module named 'langchain'

**解决方案**：
```bash
pip install langchain langchain-openai python-dotenv
```

### 问题：API 密钥错误

**解决方案**：
检查 `.env` 文件中的 `SILICONFLOW_API_KEY` 是否设置正确。

### 问题：分析结果为空或不相关

**解决方案**：
- 检查 MineContext 摘要是否包含有效信息
- 调整 `MODEL_NAME` 参数，尝试不同模型
- 检查 API 调用限制和配额

## 参考文档

- [LangChain 官方文档](https://python.langchain.com/docs/)
- [LangChain Expression Language](https://python.langchain.com/docs/expression_language/)
- [SiliconFlow API 文档](https://docs.siliconflow.cn/)

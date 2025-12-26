# MineContext Integration Project

一个用于集成 MineContext 的模块化 Python 项目，提供完整的 API 包装、CLI 工具和 MCP 支持。

## 项目结构

```
minecontext_integration/
├── src/mcagent/               # 核心库
│   ├── context_wrapper.py        # MineContext API 包装器
│   ├── llm_client.py             # LLM 客户端
│   ├── langchain_analyzer.py     # LangChain 分析器
│   ├── inspector.py              # 失败检查器核心
│   ├── trajectory.py             # 轨迹记录功能
│   └── __init__.py
├── cli/                       # CLI 工具
│   ├── failure_inspector.py      # 失败检查器
│   ├── get_contexts_simple.py    # 上下文获取工具
│   ├── run_test.py               # 测试运行器
│   ├── setup_examples.py         # 示例设置脚本
│   └── some_broken_script.py     # 测试用脚本
├── mcp/                       # MCP 服务器
│   └── minecontext_mcp_server.py
├── tests/                     # 测试文件
│   ├── test_success_report.py
│   └── test_wrapper_service.py
├── docs/                      # 文档
├── examples/                  # 示例文件
├── samples/                   # 数据样本
└── README.md
```

## 快速开始

### 1. 安装依赖

```bash
pip install requests langchain mcp fastapi
```

## 核心 API

### 获取 MineContext 摘要

```python
import sys
from pathlib import Path

# 添加 src 到 Python 路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from mcagent.context_wrapper import get_minecontext_summary

# 获取最新摘要
summary = get_minecontext_summary(
    task_type="debug_error",
    detail_level="medium"
)
print(summary)
```

### 数据压缩

```python
from mcagent.context_wrapper import compress_home_context

# 压缩上下文数据
compressed = compress_home_context(raw_data)
print(compressed["user_intent_summary"])
```

## CLI 工具

### 1. 失败检查器

检查命令执行失败并自动获取上下文：

```bash
python cli/failure_inspector.py "pytest tests/"
```

### 2. 上下文获取

获取 MineContext 所有类型的上下文：

```bash
python cli/get_contexts_simple.py
```

### 3. 运行测试示例

```bash
python cli/setup_examples.py
```

## 运行测试

```bash
# 运行核心功能测试
python tests/test_success_report.py

# 测试 MCP 服务器连接
python tests/test_wrapper_service.py
```

## MCP 服务器

项目提供 MCP (Model Context Protocol) 服务器支持，可与支持 MCP 的应用集成：

```bash
python mcp/minecontext_mcp_server.py
```

服务器提供 `minecontext_screen_context` 工具，返回当前上下文的压缩摘要。

## 依赖

- **requests** - HTTP 请求库
- **langchain** - LLM 分析框架
- **mcp** - FastMCP 协议支持
- **fastapi** - API 服务框架

安装完整依赖：
```bash
pip install -r requirements.txt
```

## 支持的 API 端点

项目调用以下 MineContext API：
- `/api/debug/reports` - 获取报告数据
- `/api/debug/todos` - 获取待办事项
- `/api/debug/activities` - 获取活动记录
- `/api/debug/tips` - 获取提示信息

## 输出结构

压缩后的上下文摘要包含：
- `status` - 执行状态
- `timestamp` - 时间戳
- `user_intent_summary` - 用户意图总结
  - `natural_language` - 自然语言描述
  - `top_todos` - 高优先级任务列表
  - `confidence` - 置信度
- `recent_activity` - 最近活动
  - `title` - 活动标题
  - `summary` - 活动摘要
  - `time_range` - 时间范围
  - `focus_areas` - 关注领域
  - `key_entities` - 关键实体
- `tips_summary` - 提示汇总

## 测试状态

✅ 所有核心功能测试通过：
- ✅ `compress_home_context()` 函数正常工作
- ✅ 数据压缩和摘要生成功能正常
- ✅ 输出数据结构完整且符合规范
- ✅ 用户意图总结正确生成
- ✅ 最近活动正确提取
- ✅ 提示汇总正确生成
- ✅ 项目可以返回最新的 minecontext 记录

## 项目结构说明

### 核心库 (src/mcagent/)
所有核心功能模块，提供统一的 API 接口。其他模块通过 `mcagent.*` 导入。

### CLI 工具 (cli/)
封装了常用操作脚本，适用于命令行环境。

### MCP 服务器 (mcp/)
通过 FastMCP 暴露 `minecontext_screen_context` 工具，支持与 MCP 兼容的 AI 代理集成。

### 测试文件 (tests/)
包含完整的功能测试和连接测试。

## 许可证

MIT License

# MineContext Integration Project

## 项目结构

```
minecontext_integration/
├── src/                        # 核心源代码
│   └── mcagent/               # MineContext Agent 核心库
│       ├── __init__.py
│       ├── context_wrapper.py    # 原 minecontext_wrapper.py 的逻辑
│       ├── llm_client.py         # LLM 客户端
│       ├── langchain_analyzer.py # LangChain 分析器
│       ├── inspector.py          # 失败检查器核心逻辑
│       └── trajectory.py         # 轨迹结构 & 保存函数
├── cli/                       # CLI 脚本和工具
│   ├── failure_inspector.py     # 失败检查器 CLI（薄薄一层）
│   ├── get_contexts_simple.py   # 获取上下文的脚本
│   ├── run_test.py              # 测试运行器
│   ├── setup_examples.py        # 设置示例脚本
│   └── some_broken_script.py    # 用于测试的破坏性脚本
├── mcp/                       # MCP (Model Context Protocol) 服务器
│   └── minecontext_mcp_server.py
├── tests/                     # 测试文件
│   ├── test_success_report.py  # 成功测试报告脚本
│   └── samples/               # 测试样本
├── samples/                   # 数据样本
├── examples/                  # 示例文件
├── docs/                      # 文档目录
└── README.md
```

## 主要功能

### 1. context_wrapper.py - 上下文包装器
- 从 MineContext API 获取并压缩上下文数据
- 支持获取 reports、todos、activities、tips 四类数据
- 生成用户意图总结、最近活动、提示汇总

### 2. inspector.py - 失败检查器
- 检查命令执行结果
- 集成 MineContext 上下文获取
- 支持 LLM 错误分析
- 生成 trajectory 数据记录

### 3. minecontext_mcp_server.py - MCP 服务器
- 提供 `minecontext_screen_context` 工具
- 通过 FastMCP 暴露 API
- 返回压缩的上下文摘要 JSON

## 使用方法

### 获取 MineContext 摘要
```python
from mcagent.context_wrapper import get_minecontext_summary

# 获取最新摘要
summary = get_minecontext_summary(task_type="debug_error", detail_level="medium")
print(summary)
```

### 运行 CLI 工具
```bash
# 获取上下文摘要
cd cli
python get_contexts_simple.py

# 检查命令失败
python failure_inspector.py "pytest"

# 运行测试
python setup_examples.py
```

### 使用 MCP 服务器
```bash
cd mcp
python minecontext_mcp_server.py
```

## 运行测试

```bash
cd tests
python test_success_report.py
```

## API 端点

项目调用以下 MineContext API：
- `/api/debug/reports` - 获取报告数据
- `/api/debug/todos` - 获取待办事项
- `/api/debug/activities` - 获取活动记录
- `/api/debug/tips` - 获取提示信息

## 依赖

- requests - HTTP 请求库
- langchain - LLM 分析框架
- mcp - FastMCP 协议支持

安装依赖：
```bash
pip install requests langchain mcp
```

## 测试状态

✅ 所有核心功能测试通过：
- compress_home_context 函数正常工作
- 数据压缩和摘要生成功能正常
- 输出数据结构完整
- 用户意图总结正确生成
- 最近活动正确提取
- 提示汇总正确生成
- 项目可以返回最新的 minecontext 记录

## 许可证

MIT License

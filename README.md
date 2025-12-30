# MineContext Integration Project

一个用于集成 MineContext 的模块化 Python 项目，提供完整的 API 包装、CLI 工具和 MCP 支持。

## 项目结构

```
minecontext_integration/
├── src/mcagent/               # 核心库
│   ├── context_wrapper.py        # MineContext API 包装器（新增行为挖掘功能）
│   ├── behavior_miner.py         # 行为挖掘引擎（NEW!）
│   ├── llm_client.py             # LLM 客户端
│   ├── langchain_analyzer.py     # LangChain 分析器
│   ├── inspector.py              # 失败检查器核心
│   ├── trajectory.py             # 轨迹记录功能
│   └── __init__.py
├── cli/                       # CLI 工具
│   ├── mine_behaviors.py         # 行为挖掘 CLI（NEW!）
│   ├── failure_inspector.py      # 失败检查器
│   ├── get_contexts_simple.py    # 上下文获取工具
│   ├── run_test.py               # 测试运行器
│   ├── setup_examples.py         # 示例设置脚本
│   └── some_broken_script.py     # 测试用脚本
├── mcp/                       # MCP 服务器
│   └── minecontext_mcp_server.py
├── tests/                     # 测试文件
│   ├── test_behavior_miner.py    # 行为挖掘测试（NEW!）
│   ├── test_success_report.py
│   └── test_wrapper_service.py
├── data/                      # 缓存目录（自动生成）
├── docs/                      # 文档
├── examples/                  # 示例文件
├── samples/                   # 数据样本
│   └── sample_activities.json    # 示例活动数据
└── README.md
```

## 新增功能：行为挖掘 🚀

### 功能概述

**行为挖掘 (Behavior Mining)** 自动分析 MineContext 活动数据，识别用户的行为模式，生成 Top N 候选 clusters。

### 核心特性

- ✅ **智能聚类**：基于标题和关键词相似度自动聚类
- ✅ **时间分析**：自动计算时间范围和持续天数
- ✅ **本地缓存**：`data/cache_activities_{date}.json` 避免重复请求
- ✅ **稳定接口**：`get_activities(days=N)` 支持分页和错误处理
- ✅ **CLI 工具**：命令行一键分析

### 快速开始

#### 1. 行为挖掘（推荐）

**使用 CLI 工具：**

```bash
# 分析最近7天的数据，返回 Top 5 行为模式
python cli/mine_behaviors.py --days 7 --top-n 5

# 分析最近3天的数据，不使用缓存
python cli/mine_behaviors.py --days 3 --no-cache

# 清除所有缓存
python cli/mine_behaviors.py --clear-cache

# 调整相似度阈值（更严格的聚类）
python cli/mine_behaviors.py --similarity-threshold 0.8

# 输出到 JSON 文件
python cli/mine_behaviors.py --output results.json --verbose
```

**使用 Python API：**

```python
import sys
from pathlib import Path

# 添加 src 到 Python 路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from mcagent.behavior_miner import mine_behaviors

# 挖掘最近7天的行为模式
clusters = mine_behaviors(days=7, top_n=5)

# 输出结果
for cluster in clusters:
    print(f"{cluster['title']}: {cluster['freq']} 次")
    print(f"  时间: {cluster['time_range']['start']} ~ {cluster['time_range']['end']}")
    print(f"  样本: {cluster['sample_activity_ids']}")
```

**示例输出：**

```
【Top 1】开发 MineContext 集成
  候选 ID: candidate_0
  频率: 4 次
  时间范围: 2025-12-25T09:00:00 ~ 2025-12-29T12:00:00
  持续天数: 5 天
  样本 IDs: act_010, act_006

【Top 2】优化 MineContext 错误处理
  候选 ID: candidate_2
  频率: 2 次
  时间范围: 2025-12-26T10:00:00 ~ 2025-12-28T12:00:00
  持续天数: 3 天
  样本 IDs: act_008, act_003
```

#### 2. 演示脚本

```bash
# 离线演示（使用示例数据，无需 MineContext 服务）
python demo_mine_behaviors.py
```

#### 3. 运行测试

```bash
# 测试行为挖掘功能
python tests/test_behavior_miner.py
```

### 输出结构

每个候选 cluster 包含以下字段：

```json
{
  "candidate_id": "candidate_0",
  "title": "开发 MineContext 集成",
  "freq": 4,
  "time_range": {
    "start": "2025-12-25T09:00:00",
    "end": "2025-12-29T12:00:00",
    "duration_days": 5
  },
  "sample_activity_ids": ["act_010", "act_006"]
}
```

### 技术细节

**聚类算法：**
- 基于标题相似度（子串匹配）
- 基于关键词提取（URL、应用名、大写词）
- 可配置的相似度阈值（默认 0.6）

**缓存机制：**
- 自动创建 `data/` 目录
- 缓存文件：`cache_activities_YYYYMMDD.json`
- 缓存有效期：基于文件修改时间
- API 失败时自动回退到缓存

**关键词提取：**
- 从 URL 提取域名（如 `github.com` → `github`）
- 识别常见应用名（如 `Claude`, `VSCode`, `Chrome`）
- 提取大写词（项目名、模块名）

## 原有功能

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

### 1. 行为挖掘 CLI（NEW!）

```bash
# 挖掘行为模式
python cli/mine_behaviors.py --days 7 --top-n 5
```

### 2. 失败检查器

检查命令执行失败并自动获取上下文：

```bash
python cli/failure_inspector.py "pytest tests/"
```

### 3. 上下文获取

获取 MineContext 所有类型的上下文：

```bash
python cli/get_contexts_simple.py
```

### 4. 运行测试示例

```bash
python cli/setup_examples.py
```

## 安装依赖

```bash
pip install requests langchain mcp fastapi
```

安装完整依赖：
```bash
pip install -r requirements.txt
```

## 支持的 API 端点

项目调用以下 MineContext API：
- `/api/debug/reports` - 获取报告数据
- `/api/debug/todos` - 获取待办事项
- `/api/debug/activities` - 获取活动记录（新增行为挖掘）
- `/api/debug/tips` - 获取提示信息

## 输出结构

### 压缩后的上下文摘要

包含：
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

### 行为挖掘结果

新增行为挖掘输出结构：
- `candidate_id` - 候选行为 ID
- `title` - 行为标题
- `freq` - 出现频率
- `time_range` - 时间范围（含持续时间）
- `sample_activity_ids` - 示例活动 ID

## 测试状态

✅ 所有核心功能测试通过：
- ✅ `compress_home_context()` 函数正常工作
- ✅ 数据压缩和摘要生成功能正常
- ✅ 输出数据结构完整且符合规范
- ✅ 用户意图总结正确生成
- ✅ 最近活动正确提取
- ✅ 提示汇总正确生成
- ✅ 项目可以返回最新的 minecontext 记录
- ✅ **新增：行为挖掘功能正常工作**
- ✅ **新增：聚类算法正确识别行为模式**
- ✅ **新增：CLI 工具稳定输出 Top 5 clusters**

## 项目结构说明

### 核心库 (src/mcagent/)

所有核心功能模块，提供统一的 API 接口。其他模块通过 `mcagent.*` 导入。

**新增模块：**
- `behavior_miner.py` - 行为挖掘引擎，提供聚类分析和模式识别
- `context_wrapper.py` - 增强版 API 包装器，新增 `get_activities()` 和缓存机制

### CLI 工具 (cli/)

封装了常用操作脚本，适用于命令行环境。

**新增工具：**
- `mine_behaviors.py` - 行为挖掘 CLI，支持参数化配置

### MCP 服务器 (mcp/)

通过 FastMCP 暴露 `minecontext_screen_context` 工具，支持与 MCP 兼容的 AI 代理集成。

### 测试文件 (tests/)

包含完整的功能测试和连接测试。

**新增测试：**
- `test_behavior_miner.py` - 行为挖掘功能测试

### 数据文件

- `samples/sample_activities.json` - 示例活动数据
- `data/cache_activities_YYYYMMDD.json` - 自动生成的缓存文件

## 许可证

MIT License

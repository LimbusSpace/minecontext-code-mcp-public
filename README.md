


# MineContext Integration

MineContext 上下文数据获取与压缩工具，用于从 MineContext 服务中获取用户工作上下文并生成智能摘要。

## 项目简介

本项目提供了一套完整的工具链，用于：
- 从 MineContext 本地服务获取用户工作上下文数据（待办事项、活动记录、提示等）
- 智能压缩原始数据，提取关键信息
- 生成结构化的上下文摘要，供上层应用（如 AI Agent）使用
- 在命令执行失败时自动捕获错误并记录上下文，结合 LLM 进行智能分析
- 压缩比约为 **22.7%**，能将数万字符的原始数据压缩为数千字节的精炼摘要

核心功能包括上下文获取与压缩、故障检测与诊断、LLM 智能分析以及轨迹记录与回放。

## 功能特性

### 核心功能

1. **多源数据获取**
   - 支持获取 reports（报告）、todos（待办事项）、activities（活动）、tips（提示）
   - 同时提供两种调用方式：/contexts 端点（主要）和各独立端点（测试用）
   - 自动处理 API 响应和错误，支持超时配置
   - 支持数据持久化保存（自动导出 JSON）

2. **智能压缩与摘要生成**
   - 提取最高优先级的待办任务（按紧急程度和截止时间排序，支持可配置数量）
   - 识别最近的工作活动并提取关键信息（摘要、时间范围、焦点领域、关键实体、截图路径）
   - 生成自然语言的用户意图摘要
   - 收集最新的提示信息（tips）
   - 压缩比约 22.7%，显著降低 Token 消耗

3. **全面的错误处理机制**
   - **服务不可用检测**：连接失败、超时、HTTP 错误自动捕获
   - **数据解析验证**：JSON 格式验证，确保返回数据完整性
   - **优雅降级**：错误情况下返回统一格式而非抛出异常
   - **错误分类**：MineContextUnavailable、Timeout、HttpError、InvalidJSON、CompressionError
   - **友好提示**：每类错误都包含解决建议（hint）

4. **故障诊断与轨迹记录（Failure Inspector）**
   - **自动捕获**：命令执行失败时（exit_code != 0）自动触发
   - **上下文获取**：立即调用 MineContext 获取当前用户工作状态
   - **LLM 智能分析**：调用 SiliconFlow API 的 DeepSeek-V3 模型分析错误原因
   - **结构化记录**：生成 trajectory_YYYYMMDD_HHMMSS.json 文件
   - **完整回放**：包含命令输出、退出码、MineContext 上下文、LLM 分析结果

5. **LLM 集成能力**
   - 支持 SiliconFlow API（deepseek-ai/DeepSeek-V3.2 模型）
   - **LangChain 集成**：使用 PromptTemplate + ChatOpenAI 构建结构化分析链
   - **懒加载单例模式**：避免重复初始化，提升性能
   - 自动重试机制（指数退避策略）
   - 完整错误处理（API 密钥无效、频率限制、超时等）
   - 可配置温度、最大 Token 数、TopP 等参数
   - 提供稳定的客户端封装（llm_client.py）和 LangChain 分析器（langchain_analyzer.py）

6. **API 设计**
   - 单一入口函数 `get_minecontext_summary()`，简单易用
   - 统一的返回数据结构（成功/错误状态字段一致）
   - 可选参数扩展（task_type、detail_level）预留
   - 清晰的类型注解和文档字符串


## 项目结构与模块职责

本仓库实现了 MineContext 与 LLM/Trae 之间的中间层，按照「5 层架构」划分为：

1. **外部感知层（MineContext，独立项目）**
   - 通过本地 HTTP API 暴露 `/contexts` 等接口，负责采集屏幕、活动、OCR 等原始上下文。

2. **数据处理层（本仓库）**
   - `minecontext_wrapper.py`  
     - 调用 MineContext `/contexts` 接口，获取原始 JSON；
     - 提取 `reports / todos / activities / tips` 等多源数据；
     - 压缩为统一的结构化摘要 JSON：  
       `status / user_intent_summary / recent_activity / tips_summary / meta`；
     - 提供入口函数 `get_minecontext_summary(task_type, detail_level)`，并实现优雅降级。
   - `get_contexts_simple.py`  
     - 调试脚本，用于直接导出 `/contexts` 的原始数据快照；
   - `samples/` & `minecontext_contexts_*.json`  
     - 存放原始上下文样本以及压缩示例，便于离线调试压缩策略。

3. **Agent 接口层（Trae / MCP，位于 Trae 仓库）**
   - `minecontext_mcp_server.py`（在 Trae 侧）  
     - 通过 MCP 协议暴露 `minecontext_screen_context` 工具；
     - 内部调用本仓库的 `get_minecontext_summary()`；
   - TRAE IDE 智能体「故障诊断师」  
     - 挂载 MCP 工具 `minecontext_screen_context`，在对话中可主动获取屏幕上下文摘要。

4. **决策层（mini-Agent & TRAE 智能体）**
   - `failure_inspector.py`
     - 运行指定命令（如 `python some_broken_script.py` / `pytest`）；
     - 捕获失败输出与退出码；
     - 调用 `get_minecontext_summary()` 获取 MineContext 摘要；
     - **调用 `langchain_analyzer.py`（LangChain + DeepSeek-V3）进行结构化错误分析**；
     - 将三步结果统一写入 `trajectory_*.json`。
   - `llm_client.py`
     - 封装 SiliconFlow DeepSeek-V3 模型调用，提供 `call_llm(prompt) -> str` 接口。
   - `langchain_analyzer.py`
     - 基于 LangChain 的智能错误分析器，使用 PromptTemplate + ChatOpenAI 构建分析链；
     - 实现**懒加载单例模式**，避免重复初始化；
     - 自动截断上下文，防止 prompt 过大。
   - `run_test.py` / `some_broken_script.py` / `tests/`
     - 构造不同错误场景，驱动 `failure_inspector` 进行端到端验证。

5. **轨迹记录与可解释性层**
   - `trajectory_*.json`  
     - 记录单次诊断的完整轨迹：
       1）失败命令及输出；  
       2）MineContext 屏幕上下文摘要；  
       3）LLM 生成的中文分析与建议。
   - `examples/trajectory_file_not_found.json`  
     - 文件不存在（FileNotFoundError）场景的完整闭环示例。
   - `examples/trajectory_pytest_failure.json`  
     - Pytest 用例失败场景的闭环示例。
   - `examples/README.md`  
     - 对轨迹结构的说明，指导如何解读每一步的含义。

通过上述拆分，本项目实现了：

- **生态协同**：  
  通过 `minecontext_wrapper` + MCP server + TRAE 智能体，将 MineContext 的屏幕上下文能力接入到 Trae/LLM 生态中；

- **人机对齐与可解释性**：  
  在失败诊断场景中，将 MineContext 提供的 `user_intent_summary`、`recent_activity` 等上下文注入 LLM 推理链路，并在 `trajectory_*.json` 中完整记录，方便事后回溯「Agent 为什么这样判断」。

- **Token 效率优化**：  
  通过压缩策略，仅保留错误分析所需的高价值字段，将原始 MineContext JSON 体积削减到约 20%–25%，降低了工具调用的 Token 开销。

## 项目结构

```
minecontext_integration/
├── minecontext_wrapper.py           # 核心封装模块（压缩 + API 调用）
├── get_contexts_simple.py           # 数据获取测试脚本
├── failure_inspector.py             # 故障检测器（捕获错误 + 生成轨迹 + LangChain 集成）
├── llm_client.py                    # LLM API 客户端（SiliconFlow / DeepSeek-V3.2）
├── langchain_analyzer.py            # LangChain 错误分析器（懒加载单例模式）
├── run_test.py                      # 测试运行脚本
├── setup_examples.py                # 示例生成脚本
├── some_broken_script.py            # 用于测试的错误示例
├── minecontext_contexts_*.json      # 原始数据备份（自动导出）
├── trajectory_*.json                # 轨迹文件（自动导出）
├── samples/                         # 示例数据目录
│   └── compressed_home_example.json # 压缩示例
├── examples/                        # 轨迹示例目录
│   ├── README.md                    # 示例说明
│   ├── trajectory_file_not_found.json    # 文件未找到错误示例
│   └── trajectory_pytest_failure.json    # Pytest 失败示例
├── docs/                            # 文档目录
│   └── LANGCHAIN_INTEGRATION.md     # LangChain 集成文档
├── tests/                           # 测试目录
│   ├── test_broken.py              # 故意失败的测试用例
│   └── test_xxx.py                 # 其他测试文件
├── requirements.txt                 # 项目依赖（LangChain、python-dotenv 等）
├── .env                             # 环境变量配置文件（API 密钥等）
└── README.md                        # 本文档
```

## 安装要求

- Python 3.7+
- requests 库
- LangChain 及其相关依赖（可选，用于智能错误分析）

### 基础依赖
```bash
pip install requests
```

### LLM 分析功能（推荐）
```bash
pip install langchain langchain-openai python-dotenv
```

或使用 requirements.txt 一键安装：
```bash
pip install -r requirements.txt
```

MineContext 服务要求：
- MineContext 已安装并运行在本地
- 服务监听地址：`http://127.0.0.1:1733`

**注意**：该项目已与 SiliconFlow LLM API 集成（使用 deepseek-ai/DeepSeek-V3.2 模型），请在项目根目录创建 `.env` 文件并配置 API 密钥：

```bash
# .env 文件内容
SILICONFLOW_API_KEY=sk-your-api-key-here
SILICONFLOW_BASE_URL=https://api.siliconflow.cn/v1
MODEL_NAME=deepseek-ai/DeepSeek-V3.2
```

## 快速开始

### 前提条件

1. **启动 MineContext 服务**（如果未启动）
2. 确保 MineContext 监听在 `http://127.0.0.1:1733`

### 方式一：使用封装好的主函数（推荐）

这是最常用的方式，直接在 Python 代码中调用 API 获取用户上下文摘要。

**基本示例：**

```python

from minecontext_wrapper import get_minecontext_summary

# 获取最新的上下文摘要
summary = get_minecontext_summary()

# 检查是否成功
if summary["status"] == "ok":
    print("✓ 成功获取上下文摘要")
    print("\n--- 用户意图 ---")
    print(summary["user_intent_summary"]["natural_language"])
    print("\n--- 高优先级待办事项 ---")
    for todo in summary["user_intent_summary"]["top_todos"]:
        print(f"  • {todo['content']} (截至: {todo['end_time']})")
    print("\n--- 最近活动 ---")
    print(f"  标题: {summary['recent_activity']['title']}")
    print(f"  摘要: {summary['recent_activity']['summary'][:100]}...")
else:
    print("✗ 获取失败")
    print(f"  错误类型: {summary['error']['type']}")
    print(f"  错误消息: {summary['error']['message']}")
    print(f"  解决建议: {summary['error']['hint']}")
```

**运行方式：** 将上述代码保存为 `.py` 文件并执行，或在 Python 交互环境中运行。

**预期输出（成功时）：**

```
✓ 成功获取上下文摘要

--- 用户意图 ---
当前最高优先级任务包括：完善 MineContext 集成项目的 README 文档、修复 API 调用错误...

--- 高优先级待办事项 ---
  • 完善 MineContext 集成项目的 README 文档 (截至: 2025-12-14 18:00:00)
  • 测试 failure_inspector 功能 (截至: 2025-12-15 10:00:00)
```

**预期输出（MineContext 未运行时）：**

```
✗ 获取失败
  错误类型: MineContextUnavailable
  错误消息: 无法连接 MineContext 本地服务: HTTPConnectionPool(host='127.0.0.1', port=1733)
  解决建议: 请确认 MineContext 已启动，并监听在 http://localhost:1733。
```

#### 返回结构

成功时（status: "ok"）：
```json
{
  "status": "ok",
  "source": "MineContext",
  "timestamp": "2025-12-09T10:30:00",
  "user_intent_summary": {
    "natural_language": "当前最高优先级任务包括：...",
    "top_todos": [
      {
        "id": 1,
        "content": "任务内容",
        "end_time": "2025-12-09 18:00:00",
        "urgency": 2,
        "status": "pending"
      }
    ],
    "evidence": ["从 todos 中识别出 3 个高优先级任务。"],
    "confidence": 0.85
  },
  "recent_activity": {
    "title": "活动标题",
    "summary": "活动摘要...",
    "time_range": {"start": "...", "end": "..."},
    "focus_areas": ["领域1", "领域2"],
    "key_entities": ["实体1"],
    "screenshot_paths": ["path/to/screenshot.png"]
  },
  "tips_summary": [
    {
      "created_at": "2025-12-09",
      "summary": "提示内容..."
    }
  ],
  "meta": {
    "task_type": null,
    "detail_level": "medium"
  }
}
```

失败时（status: "error"）：
```json
{
  "status": "error",
  "source": "MineContext",
  "timestamp": "2025-12-09T10:30:00",
  "error": {
    "type": "MineContextUnavailable",
    "message": "无法连接 MineContext 本地服务: ...",
    "hint": "请确认 MineContext 已启动，并监听在 http://localhost:1733。"
  },
  "user_intent_summary": null,
  "recent_activity": null,
  "tips_summary": null
}
```

### 方式二：手动获取并压缩数据

如果你需要对数据处理有更多控制，可以分开调用获取和压缩函数。

**使用场景：**
- 需要对原始数据进行预处理
- 分批处理大量历史数据
- 集成到自定义的数据处理流程中

**示例代码：**

```python
from minecontext_wrapper import fetch_latest_context, compress_home_context
import json

# 1. 获取原始数据
raw_data = fetch_latest_context(limit=1)
print(f"原始数据大小: {len(str(raw_data))} 字符")

# 2. 压缩数据
summary = compress_home_context(raw_data)
print(f"压缩后大小: {len(str(summary))} 字符")

# 3. 使用结果（格式化为 JSON 输出）
print(json.dumps(summary, ensure_ascii=False, indent=2))
```

**运行方式：**
```bash
python -c "
from minecontext_wrapper import fetch_latest_context, compress_home_context
import json
raw = fetch_latest_context(limit=1)
print(json.dumps(compress_home_context(raw), ensure_ascii=False, indent=2))
"
```

### 方式三：使用测试脚本获取多类型数据

**脚本路径：** `get_contexts_simple.py`

此脚本演示如何分别获取不同类型的上下文数据（reports、todos、activities、tips）。

**使用场景：**
- 测试 MineContext 各端点是否正常工作
- 获取完整的历史数据（不限于最新一条）
- 调试数据格式和字段问题

**运行命令：**
```bash
python get_contexts_simple.py
```

**功能特点：**
- 调用 MineContext 的独立端点（`/api/debug/reports`, `/api/debug/todos`, `/api/debug/activities`, `/api/debug/tips`）
- 显示详细的获取进度和汇总信息
- 自动保存数据到 `minecontext_contexts_YYYYMMDD_HHMMSS.json`
- 预览每条数据的前几条记录

**输出示例：**
```
============================================================
MineContext 上下文数据获取工具
============================================================

[API] 正在获取 reports 数据...
  [OK] 成功获取 5 条记录
[API] 正在获取 todos 数据...
  [OK] 成功获取 10 条记录

数据获取汇总
============================================================
获取时间: 2025-12-14T14:30:00
成功类型: 4/4
总记录数: 35
```

**注意：** 此脚本主要用于测试和调试，实际应用推荐使用方式一（`get_minecontext_summary`）。

### 方式四：故障检测与轨迹记录（Failure Inspector）

**脚本路径：** `failure_inspector.py` 和 `run_test.py`

**核心功能：**
自动监控命令执行，失败时捕获上下文并生成分析报告。

**使用场景：**
- CI/CD 流水线中自动记录失败构建的上下文
- 用户环境问题时收集上下文信息
- 生产环境监控和错误分析
- 自动化测试失败分析

**基本使用：**

```bash
# 执行指定命令并监控其状态
python failure_inspector.py "your_command_here"

# 示例：运行一个会失败的脚本
python failure_inspector.py "python some_broken_script.py"

# 示例：运行 pytest 测试
python failure_inspector.py "pytest tests/test_broken.py -v"

# 不指定命令时，使用默认命令（pytest）
python failure_inspector.py
```

**使用测试脚本（推荐）：**

`run_test.py` 会自动设置 API 密钥并运行 failure_inspector：

```bash
python run_test.py "python some_broken_script.py"
```

**工作原理：**
1. 执行指定的 shell 命令
2. 监控退出码（exit_code）
3. 如果命令失败（exit_code != 0）：
   - 获取 MineContext 上下文摘要
   - **调用 LangChain 分析器进行智能错误分析**（`engine: "langchain_deepseek_v3"`）
   - 生成结构化轨迹文件（trajectory_YYYYMMDD_HHMMSS.json）
4. 如果命令成功：仅记录执行信息

**LangChain 集成：**
- 使用 PromptTemplate 构建结构化分析 prompt
- 通过 ChatOpenAI 连接 SiliconFlow DeepSeek-V3.2
- 实现懒加载单例模式，避免重复初始化
- 自动截断 MineContext 摘要（最大 3000 字符）和错误输出（最大 2000 字符）

**轨迹文件示例：**

失败的命令会生成 `trajectory.json`（示例见 [examples/README.md](examples/README.md)）：

```json
{
  "timestamp": "2025-12-12T16:40:02",
  "command": "python some_broken_script.py",
  "steps": [
    {
      "type": "bash",
      "command": "python some_broken_script.py",
      "exit_code": 1,
      "output_excerpt": "Traceback (most recent call last):\n  FileNotFoundError: [Errno 2]..."
    },
    {
      "type": "minecontext_context",
      "result": {
        "status": "error",
        "timestamp": "2025-12-12T16:40:03.073078",
        "user_intent_summary": {...},
        "recent_activity": {...},
        "tips_summary": [...],
        "error": {
          "type": "MineContextUnavailable",
          "message": "无法连接 MineContext 本地服务...",
          "hint": "请确认 MineContext 已启动，并监听在 http://localhost:1733。"
        }
      }
    },
    {
      "type": "llm_analysis",
      "result": "根据错误信息和上下文分析，问题可能是..."
    }
  ]
}
```

**轨迹记录的优势：**
- **无侵入式监控**：自动捕获命令失败，无需修改被测代码
- **完整的错误上下文**：包含命令输出、用户工作状态、环境信息
- **智能分析**：结合 LLM 提供可能的错误原因和修复建议
- **便于排查**：结构化数据可用于日志分析、监控系统集成

**使用建议：**
- 集成到 CI/CD 流水线中，自动记录失败构建
- 开发过程中用于调试工具
- 生产环境监控失败命令的模式和根因

## 命令行工具参考

### 快速测试脚本

以下脚本可以快速体验各个功能：

| 脚本 | 功能 | 使用示例 |
|------|------|----------|
| `get_contexts_simple.py` | 获取并显示所有类型数据 | `python get_contexts_simple.py` |
| `failure_inspector.py` | 监控命令失败并生成轨迹 | `python failure_inspector.py "python some_broken_script.py"` |
| `run_test.py` | 自动设置 API 密钥并运行 failure_inspector | `python run_test.py "python some_broken_script.py"` |
| `some_broken_script.py` | 用于测试的错误示例脚本 | `python some_broken_script.py` |

### 完整示例流程

**场景：开发过程中测试错误捕获功能**

步骤 1：查看当前 MineContext 数据
```bash
python get_contexts_simple.py
```

步骤 2：运行一个会失败的脚本，观察轨迹生成
```bash
python run_test.py "python some_broken_script.py"
```

步骤 3：检查生成的 trajectory.json 文件
```bash
type trajectory.json
```

## API 参考

### 主函数

#### `get_minecontext_summary(task_type=None, detail_level="medium")`

获取并压缩 MineContext 上下文摘要。这是对外暴露的主入口函数，自动完成数据获取、压缩和错误处理。

**参数：**
- `task_type` (str, optional): 任务类型（预留扩展，暂未使用）
- `detail_level` (str, default="medium"): 详细程度（预留扩展，暂未使用）

**返回：**
- Dict[str, Any]: 统一结构的结果字典，包含 `status`、`user_intent_summary`、`recent_activity`、`tips_summary` 等字段

**使用示例：**
```python
from minecontext_wrapper import get_minecontext_summary
import json

# 基础用法
result = get_minecontext_summary()
print(json.dumps(result, ensure_ascii=False, indent=2))

# 高级用法（预留参数）
result = get_minecontext_summary(task_type="coding", detail_level="high")
```

**错误处理：**
```python
result = get_minecontext_summary()

if result["status"] == "ok":
    summary = result["user_intent_summary"]
    print(f"识别到 {len(summary['top_todos'])} 个高优先级任务")
else:
    error = result["error"]
    print(f"错误类型: {error['type']}")
    print(f"错误消息: {error['message']}")
    print(f"解决建议: {error['hint']}")
```

### 数据获取函数

#### `fetch_latest_context(limit=1, timeout=5.0)`

调用 MineContext /contexts 端点获取原始数据。这是底层的 API 调用函数。

**参数：**
- `limit` (int, default=1): 返回的记录数
- `timeout` (float, default=5.0): 请求超时时间（秒）

**返回：**
- Dict[str, Any]: 原始上下文数据，包含 `timestamp` 和 `data` 字段

**异常：**
- `requests.exceptions.RequestException`: HTTP 请求异常（连接失败、超时等）
- `ValueError`: JSON 解析失败

**使用示例：**
```python
from minecontext_wrapper import fetch_latest_context

# 获取最新的上下文数据
try:
    raw_data = fetch_latest_context(limit=1, timeout=5.0)
    print(f"数据时间戳: {raw_data.get('timestamp')}")
    print(f"待办事项数: {len(raw_data.get('data', {}).get('todos', {}).get('records', []))}")
except requests.exceptions.ConnectionError:
    print("无法连接到 MineContext 服务")
except Exception as e:
    print(f"获取数据失败: {e}")
```

### 数据压缩函数

#### `compress_home_context(raw)`

压缩原始上下文数据为摘要。该函数处理数据解析、过滤和摘要生成。

**参数：**
- `raw` (Dict[str, Any]): 原始数据（来自 MineContext 的 /contexts 响应）

**返回：**
- Dict[str, Any]: 压缩后的摘要，结构包含 `user_intent_summary`、`recent_activity`、`tips_summary`

**压缩逻辑：**
- **待办事项**：按紧急程度降序、截止时间升序排序，取前 3 条（可配置）
- **最近活动**：按结束时间排序，取最新一条，提取摘要、焦点领域、关键实体、截图路径
- **提示信息**：按创建时间排序，取最新的 2 条（可配置）

**使用示例：**
```python
from minecontext_wrapper import compress_home_context
import json
import pathlib

# 从文件加载原始数据
raw_data = json.loads(pathlib.Path("samples/latest.json").read_text(encoding="utf-8"))

# 压缩数据
summary = compress_home_context(raw_data)

# 输出结果
print(json.dumps(summary, ensure_ascii=False, indent=2))
```

### 实用工具函数

#### `_build_top_todos(raw, max_items=3)`

从原始数据中提取最高优先级的待办任务列表。

**排序规则：**
1. 紧急程度（urgency）降序
2. 截止时间（end_time）升序

**返回字段：**
- id: 任务 ID
- content: 任务内容
- end_time: 截止时间
- urgency: 紧急程度
- status: 状态（"pending" 或 "done"）

#### `_build_recent_activity(raw)`

从原始数据中提取最近的活动记录。

**返回字段：**
- title: 活动标题
- summary: 活动摘要（截断至 220 字符）
- time_range: 时间范围（start, end）
- focus_areas: 焦点领域列表
- key_entities: 关键实体列表
- screenshot_paths: 截图路径列表

#### `_build_tips_summary(raw, max_items=2)`

从原始数据中提取最新的提示信息。

**返回字段：**
- created_at: 创建时间
- summary: 提示摘要（截断至 200 字符）

## 错误处理

本模块设计了完整的错误处理机制，确保在 MineContext 服务不可用时，上层应用仍能正常运行。

### 错误类型与场景

| 错误类型 | 常见场景 | HTTP 状态码 | 可能原因 | 解决建议 |
|---------|---------|------------|---------|---------|
| **MineContextUnavailable** | 连接错误 | - | 服务未启动、端口错误、防火墙 | 确认服务状态、检查网络 |
| **Timeout** | 请求超时 | - | 服务响应慢、网络延迟 | 增加超时时间、检查网络 |
| **HttpError** | HTTP 错误 | 4xx/5xx | 服务端错误、认证失败 | 检查服务端日志 |
| **InvalidJSON** | 解析失败 | 200 | 返回数据格式错误 | 检查 MineContext 版本 |
| **CompressionError** | 压缩逻辑错误 | - | 数据缺失、字段不匹配 | 检查数据结构 |

### 错误处理最佳实践

```python
import logging
from minecontext_wrapper import get_minecontext_summary

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_context_with_fallback():
    """获取上下文，失败时使用默认值"""
    result = get_minecontext_summary()

    if result["status"] == "error":
        error = result["error"]

        # 记录详细错误日志
        logger.error(f"[MineContext] {error['type']}: {error['message']}")
        logger.warning(f"[MineContext] Hint: {error['hint']}")
        logger.info("[MineContext] 使用默认值继续执行")

        # 返回默认上下文
        return {
            "user_intent_summary": {
                "natural_language": "无法获取 MineContext 数据，使用默认配置",
                "top_todos": [],
                "evidence": [],
                "confidence": 0.0
            },
            "recent_activity": None,
            "tips_summary": [],
            "meta": {
                "using_default": True,
                "error_type": error['type']
            }
        }

    # 成功情况
    logger.info("[MineContext] 成功获取上下文数据")
    return result

# 使用示例
context = get_context_with_fallback()
process_user_intent(context["user_intent_summary"])
```

### 重试策略

对于网络不稳定场景，可以实现重试机制：

```python
import time
from minecontext_wrapper import get_minecontext_summary

def get_context_with_retry(max_attempts=3, delay=2):
    """带重试机制的上下文获取"""
    for attempt in range(max_attempts):
        result = get_minecontext_summary()

        if result["status"] == "ok":
            return result

        # 如果是可重试错误
        error_type = result["error"]["type"]
        if error_type in ["MineContextUnavailable", "Timeout"]:
            if attempt < max_attempts - 1:
                time.sleep(delay * (attempt + 1))
                continue

        # 不可重试错误或达到最大尝试次数
        return result

    return result
```

## 数据格式

### 原始数据结构

MineContext 返回的原始数据格式：

```json
{
  "timestamp": "2025-12-09T10:30:00",
  "data": {
    "todos": {
      "count": 5,
      "records": [
        {
          "id": 1,
          "content": "任务内容",
          "status": 0,
          "urgency": 2,
          "end_time": "2025-12-09 18:00:00"
        }
      ]
    },
    "activities": { "records": [...] },
    "tips": { "records": [...] },
    "reports": { "records": [...] }
  }
}
```

### 压缩后的数据结构

见上文 [返回结构](#返回结构) 部分。

### 轨迹数据结构（Trajectory）

命令执行失败时生成的结构化数据：

```json
{
  "timestamp": "2025-12-11T18:49:47",
  "command": "pytest",
  "steps": [
    {
      "type": "bash",
      "command": "pytest",
      "exit_code": 1,
      "output_excerpt": "错误输出..."
    },
    {
      "type": "minecontext_context",
      "result": {
        "status": "error",
        "source": "MineContext",
        "error": {
          "type": "MineContextUnavailable",
          "message": "..."
        },
        "user_intent_summary": null
      }
    }
  ]
}
```

**字段说明：**
- `timestamp`: 错误发生时间
- `command`: 执行的命令
- `steps`: 执行步骤数组
  - `type`: 步骤类型（bash, minecontext_context）
  - 其他字段根据类型变化

## 压缩算法说明

### 待办事项压缩
- 筛选：按紧急程度降序、截止时间升序排序
- 数量：默认最多 3 条
- 字段：id、content、end_time、urgency、status

### 活动记录压缩
- 筛选：取最近的一条活动
- 内容：摘要截断至 220 字符
- 元数据：提取 focus_areas 和 key_entities
- 资源：收集截图路径

### 提示压缩
- 筛选：按创建时间排序，取最新的 2 条
- 内容：摘要截断至 200 字符

## 开发说明

### 添加新功能

如果要支持不同的压缩策略，可以扩展 `get_minecontext_summary` 的参数：

```python
def get_minecontext_summary(
    task_type: Optional[str] = None,
    detail_level: str = "medium",
    max_todos: int = 3,
    max_tips: int = 2
) -> Dict[str, Any]:
    # 根据参数调整压缩逻辑
    if detail_level == "high":
        max_todos = 5
        max_tips = 3
    # ...
```

### 测试

```bash
# 测试压缩功能
python test_compress.py

# 手动获取最新数据并查看
python -c "from minecontext_wrapper import get_minecontext_summary; import json; print(json.dumps(get_minecontext_summary(), ensure_ascii=False, indent=2))"
```

## 许可证

MIT License

## 联系方式

如有问题或建议，请提交 Issue 或联系项目维护者。

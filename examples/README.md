# Failure Inspector 示例轨迹文件

此目录包含 failure_inspector.py 生成的轨迹文件示例，展示系统在捕获命令失败时如何记录上下文和生成分析。

## 示例文件

### 1. trajectory_file_not_found.json
**场景**: 运行包含文件读取错误的 Python 脚本

**命令**:
```bash
python some_broken_script.py
```

**错误类型**:
- FileNotFoundError: 尝试读取不存在的文件 `/nonexistent/file.txt`

**轨迹结构**:
- `timestamp`: 命令执行时间
- `command`: 执行的命令
- `steps`: 包含以下步骤
  - `bash`: 命令执行结果（退出码 1 和错误输出）
  - `minecontext_context`: MineContext 提供的上下文摘要
    - 包含用户意图、最近活动和提示信息
  - `llm_analysis`: LLM 对错误和上下文的分析结果

### 2. trajectory_pytest_failure.json
**场景**: 运行 pytest 测试套件失败

**命令**:
```bash
pytest tests/test_xxx.py
```

**错误类型**:
- 命令未找到：pytest 不是内部或外部命令

**轨迹结构**: 同上，包含完整的错误分析流程

## 使用方法

运行 failure_inspector.py 来生成轨迹文件：

```bash
python failure_inspector.py "你的命令"
```

轨迹文件将自动生成，文件名格式为：`trajectory_YYYYMMDD_HHMMSS.json`

如果命令执行失败（退出码 != 0），轨迹文件将包含：
1. 命令输出和退出码
2. MineContext 上下文摘要
3. LLM 分析结果

## 数据结构说明

### 顶层字段
- `status`: "ok" 或 "error"
- `source`: "MineContext"
- `timestamp`: ISO 格式时间戳
- `user_intent_summary`: 用户意图摘要（可能为 null）
- `recent_activity`: 最近活动记录（可能为 null）
- `tips_summary`: 提示信息摘要（可能为 null）
- `meta`: 元数据（包含 task_type 和 detail_level）

### 错误情况
如果 MineContext 服务不可用，返回结构包含：
- `error`: 错误详细信息
  - `type`: 错误类型
  - `message`: 错误消息
  - `hint`: 解决建议
  - 所有数据字段为 null

## 相关文件

- `../failure_inspector.py`: 主执行脚本
- `../minecontext_wrapper.py`: MineContext API 封装
- `../tests/test_broken.py`: 用于测试的故意失败用例

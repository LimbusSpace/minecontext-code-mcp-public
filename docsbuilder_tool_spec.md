3.1 工具基本信息
text

工具名称：minecontext_screen_context
调用方式：HTTP POST

URL: http://127.0.0.1:18080/minecontext_summary
方法: POST
Content-Type: application/json
3.2 请求参数 Schema
jsonc

{
  "task_type": "debug_error | implement_feature | refactor | unknown (可选，默认 unknown)",
  "detail_level": "low | medium | high (可选，默认 medium)"
}
示例：

JSON

{
  "task_type": "debug_error",
  "detail_level": "medium"
}
3.3 响应示例（截断版）
从你刚才 test_wrapper_service.py 的输出里，复制一小段贴进去，比如：

jsonc

{
  "status": "ok",
  "source": "MineContext",
  "timestamp": "2025-12-14T15:30:12.123456",
  "user_intent_summary": {
    "natural_language": "当前最高优先级任务包括：抓取 MineContext 项目的 JSON 样本数据，用于后续开发使用；完成 MineContext 和 Trae 的 demo 搭建；...",
    "top_todos": [...],
    "evidence": [...],
    "confidence": 0.85
  },
  "recent_activity": {...},
  "tips_summary": [...],
  "meta": {
    "task_type": "debug_error",
    "detail_level": "medium"
  }
}
最后加一句说明：

在智能体 Builder 中，可以把此 HTTP 工具配置为：

失败诊断阶段使用的 Tool；
由 Agent 在 Bash / 测试失败时调用，并将返回的 JSON 注入到下一轮 prompt 中。

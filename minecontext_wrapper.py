# minecontext_wrapper.py
import json
import requests
from typing import Any, Dict, List, Optional
from datetime import datetime

# MineContext API 配置
MINECONTEXT_BASE_URL = "http://127.0.0.1:1733"
CONTEXTS_ENDPOINT = "/contexts"

def _get_section(raw: Dict[str, Any], name: str) -> Dict[str, Any]:
    """安全地拿到 data 下面的某个子块，比如 todos / activities / tips。"""
    return (raw.get("data") or {}).get(name) or {}
def _build_top_todos(raw: Dict[str, Any], max_items: int = 3) -> List[Dict[str, Any]]:
    todos_section = _get_section(raw, "todos")
    records = todos_section.get("records") or []
    if not isinstance(records, list):
        return []

    def sort_key(t: Dict[str, Any]):
        # 按紧急程度降序，截止时间升序
        return (-(t.get("urgency") or 0), t.get("end_time") or "")

    records_sorted = sorted(records, key=sort_key)
    out: List[Dict[str, Any]] = []

    for t in records_sorted[:max_items]:
        out.append(
            {
                "id": t.get("id"),
                "content": t.get("content") or "",
                "end_time": t.get("end_time"),
                "urgency": t.get("urgency"),
                "status": "done" if t.get("status") == 1 else "pending",
            }
        )
    return out

def _build_recent_activity(raw: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    activities_section = _get_section(raw, "activities")
    records = activities_section.get("records") or []
    if not records:
        return None

    # 按结束时间排序，取最新一条
    latest = sorted(records, key=lambda r: r.get("end_time") or "")[-1]

    meta_raw = latest.get("metadata")
    focus_areas: List[str] = []
    key_entities: List[str] = []

    if isinstance(meta_raw, str):
        try:
            meta = json.loads(meta_raw)
            extracted = (meta.get("extracted_insights") or {})  # 里面嵌套了 key_entities / focus_areas
            focus_areas = extracted.get("focus_areas") or meta.get("focus_areas") or []
            key_entities = extracted.get("key_entities") or []
        except Exception:
            pass

    # 摘要内容控制长度
    content = latest.get("content") or ""
    max_len = 220
    summary = content[:max_len] + ("..." if len(content) > max_len else "")

    screenshot_paths = [
        res.get("path")
        for res in (latest.get("resources") or [])
        if isinstance(res, dict) and res.get("type") == "image"
    ]

    return {
        "title": latest.get("title") or "",
        "summary": summary,
        "time_range": {
            "start": latest.get("start_time"),
            "end": latest.get("end_time"),
        },
        "focus_areas": focus_areas,
        "key_entities": key_entities,
        "screenshot_paths": screenshot_paths,
    }

def _build_tips_summary(raw: Dict[str, Any], max_items: int = 2) -> List[Dict[str, Any]]:
    tips_section = _get_section(raw, "tips")
    records = tips_section.get("records") or []
    if not records:
        return []

    records_sorted = sorted(records, key=lambda r: r.get("created_at") or "")
    selected = records_sorted[-max_items:]  # 取最新几条

    out: List[Dict[str, Any]] = []
    max_len = 200

    for tip in selected:
        content = tip.get("content") or ""
        summary = content[:max_len] + ("..." if len(content) > max_len else "")
        out.append(
            {
                "created_at": tip.get("created_at"),
                "summary": summary,
            }
        )
    return out

def compress_home_context(raw: Dict[str, Any]) -> Dict[str, Any]:
    """把 /contexts 返回的 Home 类上下文压缩成简短摘要。"""
    top_todos = _build_top_todos(raw)
    recent_activity = _build_recent_activity(raw)
    tips_summary = _build_tips_summary(raw)

    # 用 top_todos 拼接一条自然语言意图描述
    if top_todos:
        todo_texts = [t["content"] for t in top_todos if t.get("content")]
        nl_summary = "当前最高优先级任务包括：" + "；".join(todo_texts)
    else:
        nl_summary = "当前未检测到明确的待办任务。"

    evidence = []
    if top_todos:
        evidence.append(f"从 todos 中识别出 {len(top_todos)} 个高优先级任务。")
    if recent_activity:
        evidence.append(f"最近活动：{recent_activity['title']}。")

    return {
        "status": "ok",
        "timestamp": raw.get("timestamp"),
        "user_intent_summary": {
            "natural_language": nl_summary,
            "top_todos": top_todos,
            "evidence": evidence,
            "confidence": 0.85,
        },
        "recent_activity": recent_activity,
        "tips_summary": tips_summary,
    }

def fetch_latest_context(
    limit: int = 1,
    timeout: float = 5.0,
) -> Dict[str, Any]:
    """调用 MineContext /contexts 端点，返回原始 JSON 数据。"""
    url = f"{MINECONTEXT_BASE_URL}{CONTEXTS_ENDPOINT}"
    resp = requests.get(url, params={"limit": limit, "page": 1}, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    # /contexts 返回的就是你刚刚保存的那种结构（timestamp / data / ...）
    return data

def _error_summary(error_type: str, message: str, hint: str) -> Dict[str, Any]:
    """统一的错误返回结构，用于优雅降级。"""
    return {
        "status": "error",
        "source": "MineContext",
        "timestamp": datetime.utcnow().isoformat(),
        "error": {
            "type": error_type,
            "message": message,
            "hint": hint,
        },
        # 以下字段让上层 Agent 不用做空判断就知道没拿到内容
        "user_intent_summary": None,
        "recent_activity": None,
        "tips_summary": None,
        "meta": {},  # 统一字段结构，和成功情况保持一致
    }

def get_minecontext_summary(
    task_type: Optional[str] = None,
    detail_level: str = "medium",
) -> Dict[str, Any]:
    """
    对外暴露的主函数：
    1. 调 /contexts 拿最新 raw JSON
    2. 调 compress_home_context(raw) 做压缩
    3. 出错时返回带 status=error 的结构，而不是抛异常
    """
    try:
        raw = fetch_latest_context()
    except requests.exceptions.ConnectionError as e:
        return _error_summary(
            "MineContextUnavailable",
            f"无法连接 MineContext 本地服务: {e}",
            "请确认 MineContext 已启动，并监听在 http://localhost:1733。",
        )
    except requests.exceptions.Timeout as e:
        return _error_summary(
            "Timeout",
            f"请求 MineContext /contexts 超时: {e}",
            "请稍后重试，或减少调用频率。",
        )
    except requests.exceptions.RequestException as e:
        return _error_summary(
            "HttpError",
            f"请求 MineContext /contexts 失败: {e}",
            "请检查 MineContext 服务状态和本地网络环境。",
        )
    except ValueError as e:
        # JSON 解析失败
        return _error_summary(
            "InvalidJSON",
            f"MineContext 返回的数据无法解析为 JSON: {e}",
            "请检查 MineContext 版本，或稍后重试。",
        )

    try:
        summary = compress_home_context(raw)
    except Exception as e:
        # 压缩逻辑自身异常，也不要把 Agent 弄崩
        return _error_summary(
            "CompressionError",
            f"压缩 MineContext 上下文时出现错误: {e}",
            "请检查 minecontext_wrapper.compress_home_context 的实现。",
        )

    # 给压缩结果补充一些通用字段，确保返回结构统一
    summary["status"] = "ok"  # 明确设置状态
    summary.setdefault("source", "MineContext")
    if "timestamp" not in summary:
        summary["timestamp"] = datetime.utcnow().isoformat()
    # 确保 meta 字段存在且包含参数信息
    summary.setdefault("meta", {})
    summary["meta"]["task_type"] = task_type
    summary["meta"]["detail_level"] = detail_level

    return summary

# 方便你命令行测试
if __name__ == "__main__":
    # 假设你把 JSON 存成了 samples/20251208_latest.json
    import pathlib
    path = pathlib.Path("samples/20251208_latest.json")  # 自己改文件名
    raw = json.loads(path.read_text(encoding="utf-8"))
    summary = compress_home_context(raw)
    print(json.dumps(summary, ensure_ascii=False, indent=2))

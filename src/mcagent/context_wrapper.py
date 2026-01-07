# minecontext_wrapper.py
import json
import requests
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import pathlib
import os

# MineContext API 配置
MINECONTEXT_BASE_URL = "http://127.0.0.1:1733"
CONTEXTS_ENDPOINT = "/contexts"
CACHE_DIR = "data"

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

def _ensure_cache_dir():
    """确保缓存目录存在。"""
    pathlib.Path(CACHE_DIR).mkdir(parents=True, exist_ok=True)

def _get_cache_path(date: datetime) -> pathlib.Path:
    """获取指定日期的缓存文件路径。"""
    date_str = date.strftime("%Y%m%d")
    return pathlib.Path(CACHE_DIR) / f"cache_activities_{date_str}.json"

def _is_cache_valid(cache_path: pathlib.Path, days: int) -> bool:
    """
    检查缓存是否有效。
    缓存有效条件：文件存在，且修改时间在指定天数内。
    """
    if not cache_path.exists():
        return False

    file_mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
    cutoff_time = datetime.now() - timedelta(days=days)

    return file_mtime >= cutoff_time

def get_activities(days: int = 7, use_cache: bool = True) -> List[Dict[str, Any]]:
    """
    获取指定天数内的所有 activities，支持分页/limit处理。

    策略：
    1. 如果启用缓存且缓存有效，优先使用缓存
    2. 否则尝试从 MineContext API 获取
    3. 如果 MineContext 不可用，fallback 到 samples/sample_activities.json

    Args:
        days: 获取多少天内的数据（默认7天）
        use_cache: 是否使用本地缓存（默认启用）

    Returns:
        activities 列表
    """
    _ensure_cache_dir()
    cache_path = _get_cache_path(datetime.now())

    # 如果启用缓存且缓存有效，直接读取缓存
    if use_cache and _is_cache_valid(cache_path, days):
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)
                print(f"[INFO] 使用缓存: {cache_path}")
                return cached_data.get("activities", [])
        except Exception as e:
            print(f"[WARN] 读取缓存失败: {e}，将重新获取数据")

    # 从 MineContext API 获取数据
    print(f"[INFO] 从 MineContext API 获取数据...")
    all_activities = []
    minecontext_available = False

    try:
        # 计算时间范围
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)

        # 调用 API 获取 activities
        # 注意：这里使用现有的 fetch_latest_context，但增加 limit 参数
        # 实际可能需要根据 API 支持情况调整分页策略
        raw_data = fetch_latest_context(
            limit=1000,  # 设置较大的 limit 以获取足够数据
            timeout=30.0
        )

        activities_section = _get_section(raw_data, "activities")
        records = activities_section.get("records") or []

        # 过滤在指定时间范围内的 activities
        for activity in records:
            if not isinstance(activity, dict):
                continue

            activity_time_str = activity.get("end_time") or activity.get("start_time")
            if not activity_time_str:
                continue

            try:
                # 解析时间字符串
                activity_time = datetime.fromisoformat(activity_time_str.replace('Z', '+00:00'))

                # 检查是否在指定时间范围内
                if start_time <= activity_time <= end_time:
                    all_activities.append(activity)
            except Exception:
                # 时间解析失败，跳过该 activity
                continue

        # 按时间排序（最新的在前）
        all_activities.sort(
            key=lambda x: x.get("end_time") or x.get("start_time") or "",
            reverse=True
        )

        # 标记 MineContext 可用
        minecontext_available = len(all_activities) > 0

        # 保存到缓存
        if use_cache and minecontext_available:
            try:
                cache_data = {
                    "fetch_time": datetime.now().isoformat(),
                    "days": days,
                    "activities": all_activities,
                    "source": "minecontext"
                }
                with open(cache_path, 'w', encoding='utf-8') as f:
                    json.dump(cache_data, f, ensure_ascii=False, indent=2)
                print(f"[INFO] 缓存已保存: {cache_path}")
            except Exception as e:
                print(f"[WARN] 保存缓存失败: {e}")

    except Exception as e:
        print(f"[WARN] 从 MineContext API 获取数据失败: {e}")
        print(f"[INFO] 将尝试 fallback 到 samples 数据...")
        minecontext_available = False

    # **Fallback 策略**：如果 MineContext 不可用或返回空数据，使用 samples
    if not minecontext_available or len(all_activities) == 0:
        print(f"[INFO] MineContext 不可用或返回空数据，尝试加载 samples...")

        # 首先尝试使用过期缓存（如果有的话）
        if cache_path.exists():
            try:
                print(f"[INFO] 尝试使用缓存: {cache_path}")
                with open(cache_path, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f)
                    cached_activities = cached_data.get("activities", [])
                    if cached_activities:
                        print(f"[INFO] 从缓存中加载 {len(cached_activities)} 条 activities")
                        return cached_activities
            except Exception as e:
                print(f"[WARN] 读取缓存失败: {e}")

        # 如果缓存也不可用，使用 samples 数据
        samples_path = pathlib.Path("samples/sample_activities.json")
        if samples_path.exists():
            try:
                print(f"[INFO] 从 samples 加载数据: {samples_path}")
                with open(samples_path, 'r', encoding='utf-8') as f:
                    samples_data = json.load(f)
                    all_activities = samples_data.get("activities", [])
                    print(f"[INFO] 从 samples 中加载 {len(all_activities)} 条 activities")

                    # 保存到缓存（标记为 samples 来源）
                    if use_cache and all_activities:
                        try:
                            cache_data = {
                                "fetch_time": datetime.now().isoformat(),
                                "days": days,
                                "activities": all_activities,
                                "source": "samples"
                            }
                            with open(cache_path, 'w', encoding='utf-8') as f:
                                json.dump(cache_data, f, ensure_ascii=False, indent=2)
                            print(f"[INFO] samples 数据已缓存: {cache_path}")
                        except Exception as e:
                            print(f"[WARN] 保存 samples 缓存失败: {e}")

            except Exception as e:
                print(f"[WARN] 从 samples 加载数据失败: {e}")
        else:
            print(f"[WARN] samples 文件不存在: {samples_path}")

    return all_activities

def clear_cache():
    """清除所有缓存文件。"""
    try:
        cache_dir = pathlib.Path(CACHE_DIR)
        if cache_dir.exists():
            for cache_file in cache_dir.glob("cache_activities_*.json"):
                cache_file.unlink()
                print(f"[INFO] 已删除缓存: {cache_file}")
        print("[INFO] 缓存清理完成")
    except Exception as e:
        print(f"[ERROR] 清理缓存失败: {e}")

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
    """
    调用 MineContext API 端点获取原始数据。
    注意：MineContext 的 /contexts 端点返回 HTML 页面，不能用于 API。
    需要使用独立的 /api/debug/* 端点。
    """

    api_endpoints = {
        "reports": f"/api/debug/reports",
        "todos": f"/api/debug/todos",
        "activities": f"/api/debug/activities",
        "tips": f"/api/debug/tips"
    }

    raw_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "data": {}
    }

    for data_type, endpoint in api_endpoints.items():
        try:
            resp = requests.get(
                f"{MINECONTEXT_BASE_URL}{endpoint}",
                params={"limit": limit},
                timeout=timeout,
            )
            resp.raise_for_status()
            response_data = resp.json()

            # MineContext API 返回格式: {"code": 0, "status": "ok", "data": {...}}
            if response_data.get("code") == 0 and "data" in response_data:
                data = response_data["data"]
                # 提取实际的数据列表和 records
                if data_type == "reports" and "reports" in data:
                    raw_data["data"][data_type] = {"records": data["reports"]}
                elif data_type == "todos" and "todos" in data:
                    raw_data["data"][data_type] = {"records": data["todos"]}
                elif data_type == "activities" and "activities" in data:
                    raw_data["data"][data_type] = {"records": data["activities"]}
                elif data_type == "tips" and "tips" in data:
                    raw_data["data"][data_type] = {"records": data["tips"]}
                else:
                    # 通用处理
                    records = data if isinstance(data, list) else [data]
                    raw_data["data"][data_type] = {"records": records}

        except Exception as e:
            # 单个端点失败不影响其他端点，返回空 records
            print(f"[WARN] 获取 {data_type} 失败: {e}")
            raw_data["data"][data_type] = {"records": []}

    return raw_data

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

# behavior_miner.py
"""
从 activities 中提取行为模式，生成候选 clusters。
"""
import json
import re
from collections import defaultdict, Counter
from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple
from urllib.parse import urlparse


def _extract_keywords(text: str, top_k: int = 3) -> List[str]:
    """
    从文本中提取关键词（简单的版本）。

    策略：
    1. 提取 URL 域名
    2. 提取常见的应用名称关键词
    3. 提取大写词（可能是项目名、模块名）
    """
    if not text:
        return []

    keywords = []

    # 1. 提取 URL 域名
    urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text)
    for url in urls:
        try:
            domain = urlparse(url).netloc
            if domain:
                # 简化域名（移除 www. 和顶级域名）
                domain = domain.replace('www.', '')
                domain_parts = domain.split('.')
                if len(domain_parts) >= 2:
                    keywords.append(domain_parts[0])
        except:
            pass

    # 2. 提取应用/工具关键词
    common_apps = [
        'Claude', 'Cursor', 'VSCode', 'IDEA', 'IntelliJ', 'PyCharm', 'WebStorm',
        'Chrome', 'Firefox', 'Safari', 'Edge',
        'Slack', 'Discord', 'Teams',
        'Notion', 'Obsidian', 'OneNote',
        'Figma', 'Sketch', 'Photoshop',
        'Terminal', 'Git', 'Docker', 'Kubernetes', 'K8s'
    ]
    text_upper = text.upper()
    for app in common_apps:
        if app.upper() in text_upper:
            keywords.append(app)

    # 3. 提取大写词（项目名、模块名等）
    words = re.findall(r'\b[A-Z][a-z]+(?:[A-Z][a-z]+)*\b', text)
    keywords.extend(words)

    # 4. 去除重复并限制数量
    seen = set()
    unique_keywords = []
    for kw in keywords:
        kw_lower = kw.lower()
        if kw_lower not in seen and len(kw_lower) > 2:
            seen.add(kw_lower)
            unique_keywords.append(kw)

    return unique_keywords[:top_k]


def _calculate_similarity(activity1: Dict[str, Any], activity2: Dict[str, Any]) -> float:
    """
    计算两个 activity 的相似度（0-1之间）。

    基于以下特征：
    1. 标题相似度
    2. 关键词重叠度
    3. 时间接近度
    """
    title1 = (activity1.get("title") or "").lower()
    title2 = (activity2.get("title") or "").lower()

    if not title1 or not title2:
        return 0.0

    # 1. 标题相似度（简单的子串匹配）
    title_similarity = 0.0
    if title1 == title2:
        title_similarity = 1.0
    elif title1 in title2 or title2 in title1:
        title_similarity = 0.8
    elif len(set(title1.split()) & set(title2.split())) > 0:
        title_similarity = 0.6

    # 2. 关键词相似度
    content1 = activity1.get("content") or ""
    content2 = activity2.get("content") or ""

    keywords1 = set(_extract_keywords(content1))
    keywords2 = set(_extract_keywords(content2))

    if keywords1 and keywords2:
        common_keywords = keywords1 & keywords2
        keyword_similarity = len(common_keywords) / max(len(keywords1), len(keywords2))
    else:
        keyword_similarity = 0.0

    # 3. 综合相似度（加权平均）
    similarity = 0.6 * title_similarity + 0.4 * keyword_similarity

    return similarity


def _cluster_activities(activities: List[Dict[str, Any]], similarity_threshold: float = 0.6) -> Dict[int, List[Dict[str, Any]]]:
    """
    对 activities 进行聚类。

    使用简单的凝聚聚类方法：
    1. 初始时每个 activity 是一个 cluster
    2. 合并相似度高于阈值的 cluster
    """
    if not activities:
        return {}

    # 初始化：每个 activity 是一个 cluster
    clusters = {i: [activity] for i, activity in enumerate(activities)}
    merged = True

    # 重复合并直到没有可以合并的 cluster
    while merged and len(clusters) > 1:
        merged = False
        cluster_ids = list(clusters.keys())

        for i in range(len(cluster_ids)):
            for j in range(i + 1, len(cluster_ids)):
                cluster1_id = cluster_ids[i]
                cluster2_id = cluster_ids[j]

                cluster1 = clusters[cluster1_id]
                cluster2 = clusters[cluster2_id]

                # 计算两个 cluster 的相似度（取最大相似度）
                max_similarity = 0.0
                for act1 in cluster1:
                    for act2 in cluster2:
                        similarity = _calculate_similarity(act1, act2)
                        max_similarity = max(max_similarity, similarity)

                # 如果相似度高于阈值，合并 cluster
                if max_similarity >= similarity_threshold:
                    # 合并 cluster2 到 cluster1
                    clusters[cluster1_id].extend(cluster2)
                    # 删除 cluster2
                    del clusters[cluster2_id]
                    merged = True
                    break

            if merged:
                break

    return clusters


def _generate_cluster_title(activities: List[Dict[str, Any]]) -> str:
    """
    为 cluster 生成标题。

    策略：
    1. 找出最常见的标题
    2. 如果没有，找最常见的关键词
    """
    if not activities:
        return "Unknown"

    # 1. 统计标题
    titles = [act.get("title") or "" for act in activities]
    title_counts = Counter(titles)
    most_common_title = title_counts.most_common(1)[0][0]

    if most_common_title:
        return most_common_title

    # 2. 统计关键词
    all_keywords = []
    for act in activities:
        content = act.get("content") or ""
        keywords = _extract_keywords(content)
        all_keywords.extend(keywords)

    if all_keywords:
        keyword_counts = Counter(all_keywords)
        top_keywords = [kw for kw, count in keyword_counts.most_common(3)]
        return " | ".join(top_keywords)

    return "Mixed Activities"


def _calculate_time_range(activities: List[Dict[str, Any]]) -> Dict[str, str]:
    """
    计算 cluster 的时间范围。

    Returns:
        {
            "start": "最早开始时间",
            "end": "最晚结束时间",
            "duration_days": "持续天数"
        }
    """
    if not activities:
        return {"start": None, "end": None, "duration_days": 0}

    all_start_times = []
    all_end_times = []

    for act in activities:
        start_time = act.get("start_time")
        end_time = act.get("end_time")

        if start_time:
            all_start_times.append(start_time)
        if end_time:
            all_end_times.append(end_time)

    if not all_start_times and not all_end_times:
        return {"start": None, "end": None, "duration_days": 0}

    # 如果没有 start_time，使用 end_time 作为 start_time
    if not all_start_times:
        all_start_times = all_end_times[:]

    # 如果没有 end_time，使用 start_time 作为 end_time
    if not all_end_times:
        all_end_times = all_start_times[:]

    start_time = min(all_start_times)
    end_time = max(all_end_times)

    # 计算持续天数
    try:
        start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        duration_days = (end_dt - start_dt).days + 1
    except:
        duration_days = 1

    return {
        "start": start_time,
        "end": end_time,
        "duration_days": duration_days
    }


def generate_behavior_clusters(
    activities: List[Dict[str, Any]],
    top_n: int = 5,
    similarity_threshold: float = 0.6
) -> List[Dict[str, Any]]:
    """
    从 activities 生成行为候选 clusters。

    Args:
        activities: activities 列表
        top_n: 返回前 N 个 clusters
        similarity_threshold: 聚类相似度阈值

    Returns:
        候选 clusters 列表，每个 cluster 包含：
        - candidate_id: 候选ID
        - title: 标题
        - freq: 出现频率（次数）
        - time_range: 时间范围
        - sample_activity_ids: 示例 activity ID 列表（1-2 条）
    """
    if not activities:
        print("[WARN] activities 列表为空")
        return []

    print(f"[INFO] 开始聚类分析，共 {len(activities)} 个 activities...")

    # 1. 聚类
    clusters = _cluster_activities(activities, similarity_threshold)
    print(f"[INFO] 生成 {len(clusters)} 个 clusters")

    # 2. 为每个 cluster 生成信息
    cluster_infos = []
    for cluster_id, cluster_activities in clusters.items():
        # 按时间排序（最新的在前）
        cluster_activities.sort(
            key=lambda x: x.get("end_time") or x.get("start_time") or "",
            reverse=True
        )

        # 生成 cluster 信息
        cluster_info = {
            "candidate_id": f"candidate_{cluster_id}",
            "title": _generate_cluster_title(cluster_activities),
            "freq": len(cluster_activities),
            "time_range": _calculate_time_range(cluster_activities),
            "sample_activity_ids": [
                act.get("id") for act in cluster_activities[:2] if act.get("id")
            ],
            "activities": cluster_activities  # 包含所有 activities，便于调试
        }

        cluster_infos.append(cluster_info)

    # 3. 按频率排序，取前 N 个
    cluster_infos.sort(key=lambda x: x["freq"], reverse=True)
    top_clusters = cluster_infos[:top_n]

    # 4. 移除调试信息（activities 字段）
    for cluster in top_clusters:
        del cluster["activities"]

    print(f"[INFO] 返回 Top {len(top_clusters)} clusters:")
    for cluster in top_clusters:
        print(f"  - {cluster['title']}: {cluster['freq']} 次")

    return top_clusters


def mine_behaviors(
    days: int = 7,
    top_n: int = 5,
    use_cache: bool = True,
    similarity_threshold: float = 0.6
) -> List[Dict[str, Any]]:
    """
    主函数：挖掘指定天数内的行为模式。

    Args:
        days: 分析多少天的数据
        top_n: 返回前 N 个 clusters
        use_cache: 是否使用缓存
        similarity_threshold: 聚类相似度阈值

    Returns:
        候选 clusters 列表
    """
    # 导入 get_activities 函数
    try:
        from .context_wrapper import get_activities
    except ImportError:
        from context_wrapper import get_activities

    # 获取 activities
    activities = get_activities(days=days, use_cache=use_cache)

    if not activities:
        print(f"[WARN] 未获取到 {days} 天内的 activities")
        return []

    # 生成 clusters
    clusters = generate_behavior_clusters(
        activities=activities,
        top_n=top_n,
        similarity_threshold=similarity_threshold
    )

    return clusters


if __name__ == "__main__":
    # 测试
    clusters = mine_behaviors(days=7, top_n=5)
    print("\n=== 最终结果 ===")
    print(json.dumps(clusters, ensure_ascii=False, indent=2))

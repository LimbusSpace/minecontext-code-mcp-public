#!/usr/bin/env python3
# demo_mine_behaviors.py
"""
离线演示：展示 behavior_miner 功能（无需 MineContext 服务）
"""
import sys
import json
from pathlib import Path

# 将 src 目录添加到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from mcagent.behavior_miner import generate_behavior_clusters


def demo():
    """离线演示"""
    print("=" * 70)
    print("=                   行为挖掘功能演示 (离线模式)                      =")
    print("=" * 70)

    # 加载示例数据
    sample_file = Path("samples/sample_activities.json")
    with open(sample_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    activities = data["activities"]
    print(f"\n[信息] 从 {sample_file} 加载了 {len(activities)} 个 activities")

    # 显示原始数据样本
    print("\n[信息] 原始数据样本（前 3 条）：")
    for i, activity in enumerate(activities[:3], 1):
        print(f"\n  [{i}] {activity['title']}")
        print(f"      时间: {activity['start_time']} ~ {activity['end_time']}")
        print(f"      内容: {activity['content'][:80]}...")

    # 执行聚类分析
    print("\n" + "=" * 70)
    print("[执行] 开始行为挖掘和聚类分析...")
    print("=" * 70)

    clusters = generate_behavior_clusters(
        activities=activities,
        top_n=5,
        similarity_threshold=0.6
    )

    # 输出结果
    print("\n" + "=" * 70)
    print("=                         挖掘结果 (Top 5)                           =")
    print("=" * 70)

    for i, cluster in enumerate(clusters, 1):
        print(f"\n【Top {i}】{cluster['title']}")
        print(f"{'─' * 70}")
        print(f"  候选 ID      : {cluster['candidate_id']}")
        print(f"  频率         : {cluster['freq']} 次")

        time_range = cluster['time_range']
        if time_range['start'] and time_range['end']:
            print(f"  时间范围     : {time_range['start']}")
        print(f"                 ~ {time_range['end']}")
        print(f"  持续天数     : {time_range['duration_days']} 天")

        if cluster['sample_activity_ids']:
            print(f"  样本 IDs     : {', '.join(cluster['sample_activity_ids'])}")

    # 输出 JSON
    print("\n" + "=" * 70)
    print("=                         JSON 格式输出                            =")
    print("=" * 70)
    print(json.dumps(clusters, ensure_ascii=False, indent=2))

    # 数据统计
    print("\n" + "=" * 70)
    print("=                          数据统计                                =")
    print("=" * 70)
    total_activities = len(activities)
    total_clusters = len(clusters)
    total_freq = sum(c['freq'] for c in clusters)

    print(f"\n  原始 activities : {total_activities}")
    print(f"  聚类后 clusters : {total_clusters}")
    print(f"  覆盖 activities : {total_freq} ({total_freq/total_activities*100:.1f}%)")

    # 显示发现的模式
    print("\n" + "=" * 70)
    print("=                        发现的行为模式                            =")
    print("=" * 70)
    for cluster in clusters:
        print(f"\n  • {cluster['title']}")
        print(f"    └─ 出现 {cluster['freq']} 次，持续 {cluster['time_range']['duration_days']} 天")

    print("\n" + "=" * 70)
    print("=                          演示完成                                  =")
    print("=" * 70)


def demo_cli():
    """演示 CLI 用法"""
    print("\n" + "=" * 70)
    print("=                          CLI 用法示例                              =")
    print("=" * 70)

    examples = [
        {
            "desc": "分析最近7天的数据，返回 Top 5",
            "cmd": "python cli/mine_behaviors.py --days 7 --top-n 5"
        },
        {
            "desc": "分析最近3天的数据，不使用缓存",
            "cmd": "python cli/mine_behaviors.py --days 3 --no-cache"
        },
        {
            "desc": "清除所有缓存文件",
            "cmd": "python cli/mine_behaviors.py --clear-cache"
        },
        {
            "desc": "调整相似度阈值（更严格的聚类）",
            "cmd": "python cli/mine_behaviors.py --similarity-threshold 0.8"
        },
        {
            "desc": "输出到 JSON 文件",
            "cmd": "python cli/mine_behaviors.py --output results.json"
        }
    ]

    for i, example in enumerate(examples, 1):
        print(f"\n{i}. {example['desc']}")
        print(f"   {example['cmd']}")


if __name__ == "__main__":
    # 运行演示
    demo()

    # 显示 CLI 用法
    demo_cli()

    print("\n" + "=" * 70)
    print("=" * 70)
    print("\n若要测试 CLI 工具，请运行:")
    print("  python cli/mine_behaviors.py --help")
    print("\n若要运行本演示，请运行:")
    print("  python demo_mine_behaviors.py")
    print("\n")

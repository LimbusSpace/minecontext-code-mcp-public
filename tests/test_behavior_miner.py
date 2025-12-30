#!/usr/bin/env python3
# test_behavior_miner.py
"""
测试 behavior_miner.py 的功能
"""
import sys
import json
from pathlib import Path

# 将 src 目录添加到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from mcagent.behavior_miner import generate_behavior_clusters


def load_sample_data():
    """加载示例 activities 数据"""
    sample_file = Path("samples/sample_activities.json")
    with open(sample_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data["activities"]


def test_behavior_miner():
    """测试行为挖掘功能"""
    print("=" * 60)
    print("测试 behavior_miner.py")
    print("=" * 60)

    # 加载示例数据
    activities = load_sample_data()
    print(f"\n[信息] 加载了 {len(activities)} 个 activities")

    # 测试聚类分析
    print("\n[信息] 开始聚类分析...")
    clusters = generate_behavior_clusters(
        activities=activities,
        top_n=5,
        similarity_threshold=0.6
    )

    # 输出结果
    print(f"\n[信息] 生成了 {len(clusters)} 个 clusters\n")
    print("=" * 60)
    print("聚类结果")
    print("=" * 60)

    for i, cluster in enumerate(clusters, 1):
        print(f"\n【Top {i}】{cluster['title']}")
        print(f"  候选 ID: {cluster['candidate_id']}")
        print(f"  频率: {cluster['freq']} 次")

        time_range = cluster['time_range']
        if time_range['start'] and time_range['end']:
            print(f"  开始时间: {time_range['start']}")
            print(f"  结束时间: {time_range['end']}")
            print(f"  持续天数: {time_range['duration_days']}")

        if cluster['sample_activity_ids']:
            print(f"  样本 Activity ID: {', '.join(cluster['sample_activity_ids'])}")

    # 输出 JSON 格式
    print("\n" + "=" * 60)
    print("JSON 格式输出")
    print("=" * 60)
    print(json.dumps(clusters, ensure_ascii=False, indent=2))

    return clusters


def test_cli():
    """测试 CLI 工具"""
    print("\n" + "=" * 60)
    print("测试 CLI 工具")
    print("=" * 60)

    import subprocess

    # 测试 --help
    print("\n[测试 1] 测试 --help 选项")
    result = subprocess.run(
        ["python", "cli/mine_behaviors.py", "--help"],
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        print("✓ --help 命令执行成功")
    else:
        print("✗ --help 命令执行失败")
        print(result.stderr)

    # 测试默认参数
    print("\n[测试 2] 测试默认参数")
    result = subprocess.run(
        ["python", "cli/mine_behaviors.py"],
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        print("✓ 默认参数执行成功")
    else:
        print("✗ 默认参数执行失败")
        print(result.stderr)


if __name__ == "__main__":
    # 测试行为挖掘
    clusters = test_behavior_miner()

    # 验证输出结构
    print("\n" + "=" * 60)
    print("验证输出结构")
    print("=" * 60)

    if clusters:
        cluster = clusters[0]
        required_fields = ['candidate_id', 'title', 'freq', 'time_range', 'sample_activity_ids']
        all_fields_present = all(field in cluster for field in required_fields)

        if all_fields_present:
            print("✓ 输出结构包含所有必需字段")
            print(f"  - candidate_id: {cluster['candidate_id']}")
            print(f"  - title: {cluster['title']}")
            print(f"  - freq: {cluster['freq']}")
            print(f"  - time_range: {cluster['time_range']}")
            print(f"  - sample_activity_ids: {cluster['sample_activity_ids']}")
        else:
            print("✗ 输出结构缺少必需字段")
    else:
        print("✗ 没有生成 clusters")

    print("\n[SUCCESS] 测试完成！")

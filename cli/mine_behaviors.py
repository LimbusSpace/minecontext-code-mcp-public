#!/usr/bin/env python3
# mine_behaviors.py
"""
CLI 工具：从 MineContext 挖掘行为模式。

Usage:
    python cli/mine_behaviors.py --days 7 --top-n 5
    python cli/mine_behaviors.py --days 3 --top-n 10 --no-cache
    python cli/mine_behaviors.py --days 30 --clear-cache
"""
import argparse
import sys
import json
from pathlib import Path

# 将 src 目录添加到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mcagent.behavior_miner import mine_behaviors
from mcagent.context_wrapper import clear_cache


def main():
    parser = argparse.ArgumentParser(
        description="从 MineContext 挖掘行为模式，生成 Top N 候选 clusters"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="分析多少天的数据（默认：7）"
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=5,
        help="返回前 N 个 clusters（默认：5）"
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="不使用本地缓存"
    )
    parser.add_argument(
        "--clear-cache",
        action="store_true",
        help="清除所有缓存文件"
    )
    parser.add_argument(
        "--similarity-threshold",
        type=float,
        default=0.6,
        help="聚类相似度阈值（默认：0.6）"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="输出到文件（JSON 格式）"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="显示详细信息"
    )

    args = parser.parse_args()

    # 清除缓存
    if args.clear_cache:
        print("[INFO] 清除缓存...")
        clear_cache()
        return 0

    try:
        # 挖掘行为模式
        print(f"[INFO] 分析 {args.days} 天内的行为模式...")
        print(f"[INFO] 目标：生成 Top {args.top_n} clusters")

        clusters = mine_behaviors(
            days=args.days,
            top_n=args.top_n,
            use_cache=not args.no_cache,
            similarity_threshold=args.similarity_threshold
        )

        # 输出结果
        if not clusters:
            print("\n[WARNING] 未找到任何行为模式")
            return 0

        print(f"\n=== 发现 {len(clusters)} 个行为模式 ===\n")

        for i, cluster in enumerate(clusters, 1):
            print(f"【Top {i}】{cluster['title']}")
            print(f"  频率：{cluster['freq']} 次")

            time_range = cluster['time_range']
            if time_range['start'] and time_range['end']:
                print(f"  时间范围：{time_range['start']} ~ {time_range['end']}")
                print(f"  持续：{time_range['duration_days']} 天")

            if cluster['sample_activity_ids']:
                print(f"  示例 Activity ID：{', '.join(cluster['sample_activity_ids'])}")

            print(f"  候选 ID：{cluster['candidate_id']}")
            print()

        # 可选：输出 JSON 到文件
        if args.output:
            output_path = Path(args.output)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(clusters, f, ensure_ascii=False, indent=2)
            print(f"[INFO] 结果已保存到: {output_path}")

        # 详细模式：输出完整 JSON
        if args.verbose:
            print("\n=== 完整 JSON 输出 ===")
            print(json.dumps(clusters, ensure_ascii=False, indent=2))

        return 0

    except KeyboardInterrupt:
        print("\n[INFO] 用户中断")
        return 130
    except Exception as e:
        print(f"\n[ERROR] {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

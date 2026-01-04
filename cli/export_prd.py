#!/usr/bin/env python3
# export_prd.py
"""
导出 PRD 文档的 CLI 工具

Usage:
    python cli/export_prd.py --candidate <candidate_id> --out <output_dir>
    python cli/export_prd.py --candidate candidate_0 --out exports/
    python cli/export_prd.py --candidate candidate_0 --out exports/ --format json --verbose
"""
import argparse
import sys
import json
from pathlib import Path
from datetime import datetime

# 将 src 目录添加到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mcagent.behavior_miner import mine_behaviors
from mcagent.evidence_pack import create_evidence_pack
from mcagent.prd_generator import generate_prd


def export_prd(
    candidate_id: str,
    output_dir: str,
    format: str = "json",
    days: int = 30,
    verbose: bool = False,
) -> str:
    """
    导出 PRD 文档

    Args:
        candidate_id: 候选行为 ID
        output_dir: 输出目录
        format: 输出格式（json/md）
        days: 分析多少天的数据
        verbose: 显示详细信息

    Returns:
        输出文件路径
    """
    # 确保输出目录存在
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # 获取所有候选行为
    if verbose:
        print(f"[信息] 分析最近 {days} 天的行为数据...")

    clusters = mine_behaviors(days=days, top_n=10, use_cache=True)

    if not clusters:
        raise ValueError("未找到任何行为模式")

    # 找到指定的 candidate
    candidate = None
    for cluster in clusters:
        if cluster.get("candidate_id") == candidate_id:
            candidate = cluster
            break

    if not candidate:
        available_ids = [c.get("candidate_id") for c in clusters]
        raise ValueError(
            f"未找到 candidate_id: {candidate_id}\n可用的 IDs: {', '.join(available_ids)}"
        )

    if verbose:
        print(f"[信息] 找到 candidate: {candidate['title']}")

    # 获取 activities（用于生成 evidence_pack）
    from mcagent.context_wrapper import get_activities
    activities = get_activities(days=days, use_cache=True)

    # 生成 evidence_pack
    if verbose:
        print("[信息] 生成证据包...")
    evidence_pack = create_evidence_pack(
        candidate, activities, min_examples=3
    )

    # 生成 PRD
    if verbose:
        print("[信息] 生成 PRD...")
    prd = generate_prd(candidate, evidence_pack, activities)

    # 生成文件名
    safe_title = "".join(c for c in candidate["title"] if c.isalnum() or c in (" ", "-", "_")).rstrip()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"PRD_{candidate_id}_{safe_title[:30]}_{timestamp}.{format}"
    filepath = output_path / filename

    # 保存文件
    if format == "json":
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(prd, f, ensure_ascii=False, indent=2)
    elif format == "md":
        # 简单的 Markdown 格式
        md_content = f"# PRD: {prd['product_overview']['product_name']}\n\n"
        md_content += f"**生成时间:** {prd['document_meta']['generated_at']}\n\n"
        md_content += f"**Feature ID:** {prd['feature_specification']['feature_id']}\n\n"
        md_content += "## 产品概述\n\n"
        md_content += f"{prd['product_overview']['description']}\n\n"
        md_content += "## 功能规格\n\n"
        md_content += f"**优先级:** {prd['feature_specification']['priority']}\n\n"
        md_content += f"**状态:** {prd['feature_specification']['status']}\n\n"
        md_content += "## 证据摘要\n\n"
        md_content += f"- **出现次数:** {prd['evidence_summary']['total_occurrences']}\n"
        md_content += f"- **时间范围:** {prd['evidence_summary']['time_range']}\n"
        md_content += f"- **证据质量:** {prd['evidence_summary']['evidence_quality']}\n\n"

        # 添加证据包详情
        evidence_pack = prd['appendices']['evidence_pack']
        md_content += "## 详细证据\n\n"
        for i, example in enumerate(evidence_pack['examples'], 1):
            md_content += f"### 证据 {i}\n\n"
            md_content += f"- **时间:** {example['occurred_at']}\n"
            md_content += f"- **来源:** {example['source_ref']}\n"
            md_content += f"- **摘要:** {example['excerpt']}\n\n"

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(md_content)
    else:
        raise ValueError(f"不支持的格式: {format}")

    if verbose:
        print(f"[成功] PRD 已保存到: {filepath}")

    return str(filepath)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="导出 PRD (产品需求文档)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 导出 candidate_0 的 PRD 到 exports/ 目录
  python cli/export_prd.py --candidate candidate_0 --out exports/

  # 导出为 Markdown 格式
  python cli/export_prd.py --candidate candidate_0 --out exports/ --format md

  # 分析最近 30 天的数据
  python cli/export_prd.py --candidate candidate_0 --out exports/ --days 30

  # 显示详细信息
  python cli/export_prd.py --candidate candidate_0 --out exports/ --verbose
        """,
    )

    parser.add_argument(
        "--candidate",
        type=str,
        required=True,
        help="候选行为 ID (例如: candidate_0)",
    )

    parser.add_argument(
        "--out",
        type=str,
        required=True,
        help="输出目录 (例如: exports/)",
    )

    parser.add_argument(
        "--format",
        type=str,
        choices=["json", "md"],
        default="json",
        help="输出格式 (json 或 md)，默认: json",
    )

    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="分析多少天的数据，默认: 30",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="显示详细信息",
    )

    parser.add_argument(
        "--list-candidates",
        action="store_true",
        help="列出所有可用的 candidates",
    )

    args = parser.parse_args()

    try:
        # 如果需要列出所有 candidates
        if args.list_candidates:
            print("=" * 70)
            print("可用的 Candidates")
            print("=" * 70)
            clusters = mine_behaviors(days=args.days, top_n=10, use_cache=True)
            if not clusters:
                print("未找到任何行为模式")
                return 0

            for i, cluster in enumerate(clusters, 1):
                print(f"\n{i}. {cluster['title']}")
                print(f"   ID: {cluster['candidate_id']}")
                print(f"   频率: {cluster['freq']} 次")
                time_range = cluster.get('time_range', {})
                if time_range:
                    print(f"   时间: {time_range.get('start', 'N/A')}")
            return 0

        # 导出 PRD
        print("=" * 70)
        print("PRD 导出工具")
        print("=" * 70)

        if args.verbose:
            print(f"\n[配置]")
            print(f"  Candidate ID: {args.candidate}")
            print(f"  输出目录: {args.out}")
            print(f"  格式: {args.format}")
            print(f"  分析天数: {args.days}")

        filepath = export_prd(
            candidate_id=args.candidate,
            output_dir=args.out,
            format=args.format,
            days=args.days,
            verbose=args.verbose,
        )

        print(f"\n[SUCCESS] PRD 导出成功!")
        print(f"文件位置: {filepath}")
        return 0

    except Exception as e:
        print(f"\n[ERROR] {str(e)}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

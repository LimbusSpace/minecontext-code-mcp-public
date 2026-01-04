# exporter.py
"""
导出器模块

整合行为挖掘、证据生成和 PRD 生成的全流程导出
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from .behavior_miner import mine_behaviors
from .evidence_pack import create_evidence_pack
from .prd_generator import generate_prd


def export_candidate_3piece(
    candidate_id: str,
    output_dir: str = "exports",
    days: int = 30,
    verbose: bool = False,
) -> Dict[str, str]:
    """
    导出 3 件套: PRD + SPEC(证据包) + EVIDENCE_PACK

    Args:
        candidate_id: 候选行为 ID
        output_dir: 输出目录
        days: 分析天数
        verbose: 显示详细信息

    Returns:
        导出的文件路径字典: {"prd": "...", "spec": "...", "evidence": "..."}
    """
    # 确保输出目录存在
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # 1. 获取所有候选行为
    if verbose:
        print(f"[信息] 获取行为数据（{days} 天）...")

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

    # 2. 获取 activities
    from .context_wrapper import get_activities

    activities = get_activities(days=days, use_cache=True)

    # 3. 生成证据包
    if verbose:
        print("[信息] 生成证据包...")
    evidence_pack = create_evidence_pack(candidate, activities, min_examples=3)

    # 4. 生成 PRD
    if verbose:
        print("[信息] 生成 PRD...")
    prd = generate_prd(candidate, evidence_pack, activities)

    # 5. 生成文件名
    safe_title = "".join(
        c for c in candidate["title"] if c.isalnum() or c in (" ", "-", "_")
    ).rstrip()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename_base = f"{candidate_id}_{safe_title[:30]}_{timestamp}"

    # 6. 导出三个文件
    exported_files = {}

    # 导出 PRD (JSON)
    if verbose:
        print("[信息] 导出 PRD...")
    prd_file = output_path / f"{filename_base}_prd.json"
    with open(prd_file, "w", encoding="utf-8") as f:
        json.dump(prd, f, ensure_ascii=False, indent=2)
    exported_files["prd"] = str(prd_file)

    # 导出 SPEC (简化版，只包含关键信息)
    if verbose:
        print("[信息] 导出 SPEC...")
    spec = {
        "candidate": candidate,
        "evidence_pack": evidence_pack,
        "generated_at": datetime.now().isoformat(),
    }
    spec_file = output_path / f"{filename_base}_spec.json"
    with open(spec_file, "w", encoding="utf-8") as f:
        json.dump(spec, f, ensure_ascii=False, indent=2)
    exported_files["spec"] = str(spec_file)

    # 导出 EVIDENCE_PACK (单独的证据包)
    if verbose:
        print("[信息] 导出 EVIDENCE_PACK...")
    evidence_file = output_path / f"{filename_base}_evidence_pack.json"
    with open(evidence_file, "w", encoding="utf-8") as f:
        json.dump(evidence_pack, f, ensure_ascii=False, indent=2)
    exported_files["evidence"] = str(evidence_file)

    if verbose:
        print(f"[成功] 导出完成:")
        for file_type, filepath in exported_files.items():
            print(f"  - {file_type}: {filepath}")

    return exported_files


def export_all_3piece(
    output_dir: str = "exports",
    days: int = 30,
    top_n: int = 5,
    verbose: bool = False,
) -> List[Dict[str, str]]:
    """
    导出所有 Top N 候选的 3 件套

    Args:
        output_dir: 输出目录
        days: 分析天数
        top_n: Top N 候选
        verbose: 显示详细信息

    Returns:
        文件路径列表
    """
    # 获取所有候选行为
    if verbose:
        print(f"[信息] 获取 Top {top_n} 候选行为（{days} 天）...")

    clusters = mine_behaviors(days=days, top_n=top_n, use_cache=True)

    if not clusters:
        raise ValueError("未找到任何行为模式")

    exported_all = []

    # 为每个 candidate 导出 3 件套
    for i, candidate in enumerate(clusters, 1):
        candidate_id = candidate.get("candidate_id")

        if verbose:
            print(f"\n[{i}/{len(clusters)}] 处理 {candidate_id}: {candidate['title']}")

        try:
            exported_files = export_candidate_3piece(
                candidate_id=candidate_id,
                output_dir=output_dir,
                days=days,
                verbose=verbose,
            )
            exported_all.append(exported_files)
        except Exception as e:
            print(f"[警告] 导出 {candidate_id} 失败: {e}")
            continue

    if verbose:
        print(f"\n[成功] 总计导出 {len(exported_all)} 个候选的 3 件套")

    return exported_all


if __name__ == "__main__":
    # 测试
    print("=" * 70)
    print("导出器测试")
    print("=" * 70)

    try:
        # 导出单个 candidate
        print("\n[测试 1] 导出单个 candidate")
        result = export_candidate_3piece(
            candidate_id="candidate_0",
            output_dir="exports/test",
            days=30,
            verbose=True,
        )
        print(f"\n✓ 成功: {result}")

        # 导出所有 Top 5
        print("\n[测试 2] 导出所有 Top 5")
        result_all = export_all_3piece(
            output_dir="exports/test_all",
            days=30,
            top_n=3,
            verbose=True,
        )
        print(f"\n✓ 成功导出 {len(result_all)} 个候选")

        print("\n" + "=" * 70)
        print("[SUCCESS] 所有测试通过！")
        print("=" * 70)

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()

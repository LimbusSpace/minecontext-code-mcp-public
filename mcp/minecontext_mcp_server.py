# minecontext_mcp_server.py
"""
MineContext 的 MCP Server：

暴露多个工具：
1. minecontext_screen_context - 获取屏幕/活动上下文摘要
2. list_behavior_candidates - 列出行为挖掘候选
3. get_behavior_evidence - 获取指定候选的证据包
"""

import sys
from pathlib import Path
from typing import Optional, Literal, Dict, Any, List

# 关键：用 FastMCP，而不是 Server
from mcp.server.fastmcp import FastMCP

# 添加 src 到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mcagent.context_wrapper import get_minecontext_summary, get_activities
from mcagent.behavior_miner import mine_behaviors
from mcagent.evidence_pack import create_evidence_pack
from mcagent.exporter import export_candidate_3piece

# 建议用英文名字，便于在 TRAE 里识别
mcp = FastMCP("minecontext-server")


@mcp.tool()
def minecontext_screen_context(
    task_type: Optional[Literal["debug_error", "implement_feature", "refactor", "unknown"]] = "unknown",
    detail_level: Optional[Literal["low", "medium", "high"]] = "medium",
) -> Dict[str, Any]:
    """
    MCP 工具：返回 MineContext 的压缩屏幕/活动上下文摘要 JSON。
    如果 MineContext 不可用，wrapper 会返回 status="error" 的结构化错误。
    """
    summary = get_minecontext_summary(
        task_type=task_type or "unknown",
        detail_level=detail_level or "medium",
    )
    # FastMCP 支持直接返回 dict，会自动做 JSON 序列化
    return summary


@mcp.tool()
def list_behavior_candidates(
    days: int = 30,
    top_n: int = 10,
    use_cache: bool = True,
) -> Dict[str, Any]:
    """
    MCP 工具：列出行为挖掘候选（Top N）。

    从 MineContext 活动数据中自动识别重复性行为模式，返回候选列表。

    Args:
        days: 分析多少天的数据（默认30天）
        top_n: 返回前 N 个候选（默认10个）
        use_cache: 是否使用缓存（默认启用）

    Returns:
        包含候选列表的字典：
        {
            "status": "ok",
            "candidates": [
                {
                    "candidate_id": "candidate_0",
                    "title": "开发 MineContext 集成",
                    "freq": 4,
                    "time_range": {...}
                }
            ]
        }
    """
    try:
        # 获取行为候选
        clusters = mine_behaviors(days=days, top_n=top_n, use_cache=use_cache)

        return {
            "status": "ok",
            "metadata": {
                "days": days,
                "top_n": top_n,
                "use_cache": use_cache,
                "total_candidates": len(clusters),
            },
            "candidates": clusters,
        }
    except Exception as e:
        return {
            "status": "error",
            "error": {
                "type": "BehaviorMiningError",
                "message": str(e),
            },
            "candidates": [],
            "metadata": {
                "days": days,
                "top_n": top_n,
                "use_cache": use_cache,
            },
        }


@mcp.tool()
def get_behavior_evidence(
    candidate_id: str,
    days: int = 30,
    min_examples: int = 3,
) -> Dict[str, Any]:
    """
    MCP 工具：获取指定候选行为的证据包。

    Args:
        candidate_id: 候选行为 ID（如 "candidate_0"）
        days: 分析多少天的数据（默认30天）
        min_examples: 最少证据条数（默认3条）

    Returns:
        包含证据包的字典：
        {
            "status": "ok",
            "evidence_pack": { ... },
            "candidate": { ... }
        }
    """
    try:
        # 1. 获取所有候选
        clusters = mine_behaviors(days=days, top_n=50, use_cache=True)

        # 2. 找到指定的 candidate
        candidate = None
        for cluster in clusters:
            if cluster.get("candidate_id") == candidate_id:
                candidate = cluster
                break

        if not candidate:
            available_ids = [c.get("candidate_id") for c in clusters]
            return {
                "status": "error",
                "error": {
                    "type": "CandidateNotFound",
                    "message": f"未找到 candidate_id: {candidate_id}",
                    "available_ids": available_ids[:10],  # 只返回前10个
                },
                "evidence_pack": None,
                "candidate": None,
            }

        # 3. 获取 activities（用于生成证据包）
        activities = get_activities(days=days, use_cache=True)

        # 4. 生成证据包
        evidence_pack = create_evidence_pack(
            candidate, activities, min_examples=min_examples
        )

        return {
            "status": "ok",
            "evidence_pack": evidence_pack,
            "candidate": candidate,
            "metadata": {
                "days": days,
                "min_examples": min_examples,
            },
        }
    except Exception as e:
        return {
            "status": "error",
            "error": {
                "type": "EvidenceGenerationError",
                "message": str(e),
            },
            "evidence_pack": None,
            "candidate": None,
        }


@mcp.tool()
def export_behavior_bundle(
    candidate_id: str,
    output_dir: str = "exports",
    days: int = 30,
) -> Dict[str, Any]:
    """
    MCP 工具：导出指定候选行为的完整 bundle（PRD + SPEC + EVIDENCE）。

    导出 3 件套到指定目录：
    - PRD: 产品需求文档（JSON格式）
    - SPEC: 规格说明（包含证据包）
    - EVIDENCE: 单独的证据包文件

    Args:
        candidate_id: 候选行为 ID（如 "candidate_0"）
        output_dir: 输出目录（默认: exports/）
        days: 分析多少天的数据（默认30天）

    Returns:
        包含导出结果的字典：
        {
            "status": "ok",
            "exported_files": {
                "prd": "exports/candidate_0_..._prd.json",
                "spec": "exports/candidate_0_..._spec.json",
                "evidence": "exports/candidate_0_..._evidence_pack.json"
            }
        }
    """
    try:
        # 调用导出函数（verbose=False，避免在MCP中输出过多信息）
        exported_files = export_candidate_3piece(
            candidate_id=candidate_id,
            output_dir=output_dir,
            days=days,
            verbose=False,
        )

        return {
            "status": "ok",
            "exported_files": exported_files,
            "metadata": {
                "candidate_id": candidate_id,
                "output_dir": output_dir,
                "days": days,
            },
        }
    except Exception as e:
        return {
            "status": "error",
            "error": {
                "type": "ExportError",
                "message": str(e),
            },
            "exported_files": None,
        }


if __name__ == "__main__":
    # 以 stdio 模式运行 MCP server
    mcp.run()
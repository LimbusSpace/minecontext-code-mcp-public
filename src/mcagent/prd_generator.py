# prd_generator.py
"""
PRD (产品需求文档) 生成器

根据候选行为和证据包生成 PRD

模板优先：使用预定义的模板结构
"""
import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path


class PRDGenerator:
    """
    PRD 生成器

    基于模板生成产品需求文档
    """

    # PRD 模板
    PRD_TEMPLATE = {
        "document_meta": {
            "version": "1.0",
            "generated_at": "{generated_at}",
            "template_version": "v1",
        },
        "product_overview": {
            "product_name": "{title}",
            "description": "基于用户行为分析自动生成的产品需求",
            "target_user": "基于 MineContext 数据分析的业务用户",
            "business_value": "自动化识别重复性行为模式，提升工作效率",
        },
        "feature_specification": {
            "feature_id": "{candidate_id}",
            "feature_title": "{title}",
            "priority": "P1",
            "status": "Identified",  # Identified, In Progress, Completed
            "categories": ["Workflow Automation", "Behavior Mining"],
        },
        "user_stories": [
            {
                "id": "US-001",
                "role": "Developer",
                "action": "识别重复性开发任务",
                "benefit": "减少重复劳动，提高开发效率",
                "acceptance_criteria": ["系统自动识别相似任务", "提供任务归类建议"],
            },
            {
                "id": "US-002",
                "role": "Team Lead",
                "action": "查看团队成员行为模式",
                "benefit": "了解团队工作习惯，优化资源分配",
                "acceptance_criteria": ["可视化行为模式", "提供数据分析报告"],
            },
        ],
        "functional_requirements": [
            {
                "id": "FR-001",
                "requirement": "从 MineContext 获取活动数据",
                "description": "连接 MineContext API，获取指定时间范围内的活动记录",
                "priority": "P0",
            },
            {
                "id": "FR-002",
                "requirement": "聚类分析识别行为模式",
                "description": "使用相似度算法对活动进行聚类，识别重复性行为",
                "priority": "P0",
            },
            {
                "id": "FR-003",
                "requirement": "生成证据包",
                "description": "为每个候选行为生成包含时间、来源和摘要的证据",
                "priority": "P1",
            },
        ],
        "technical_requirements": [
            {
                "id": "TR-001",
                "requirement": "本地缓存机制",
                "description": "缓存 MineContext 数据，避免重复请求",
                "details": "使用 JSON 文件存储缓存，按日期区分",
            },
            {
                "id": "TR-002",
                "requirement": "相似度算法",
                "description": "基于标题和关键词的文本相似度比较",
                "details": "支持可配置的相似度阈值",
            },
        ],
        "evidence_summary": {
            "total_occurrences": "{freq}",
            "time_range": "{time_range}",
            "evidence_quality": "{confidence_level}",
            "sampling_method": "时间分散采样",
        },
        "constraints_and_assumptions": {
            "constraints": [
                "依赖 MineContext API 可用性",
                "相似度阈值需要调优",
            ],
            "assumptions": [
                "用户活动数据准确记录",
                "相似标题代表相似行为",
            ],
        },
        "risk_analysis": {
            "technical_risks": [
                {
                    "risk": "MineContext API 不可用",
                    "impact": "high",
                    "mitigation": "本地缓存 + 离线演示数据",
                }
            ],
            "business_risks": [
                {
                    "risk": "误识别行为模式",
                    "impact": "medium",
                    "mitigation": "人工审核 + 不确定性声明",
                }
            ],
        },
        "success_metrics": [
            {"metric": "识别准确率", "target": "&gt;80%", "measurement_method": "人工验证"},
            {"metric": "用户采纳率", "target": "&gt;60%", "measurement_method": "使用统计"},
        ],
        "appendices": {
            "evidence_pack": "{evidence_pack}",  # 将嵌入完整的证据包
        },
    }

    def __init__(self):
        """初始化"""
        pass

    def _fill_template(
        self, template: Dict[str, Any], data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        递归填充模板

        将模板中的占位符 {key} 替换为 data 中的值
        """
        if isinstance(template, dict):
            return {k: self._fill_template(v, data) for k, v in template.items()}
        elif isinstance(template, list):
            return [self._fill_template(item, data) for item in template]
        elif isinstance(template, str):
            if template.startswith("{") and template.endswith("}"):
                key = template[1:-1]
                return data.get(key, template)
            return template
        else:
            return template

    def generate_prd(
        self,
        candidate: Dict[str, Any],
        evidence_pack: Dict[str, Any],
        activities: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        生成 PRD

        Args:
            candidate: 候选行为
            evidence_pack: 证据包
            activities: 相关 activities

        Returns:
            完整的 PRD 文档
        """
        # 准备填充数据
        time_range = candidate.get("time_range", {})
        time_range_str = (
            f"{time_range.get('start', 'N/A')} ~ {time_range.get('end', 'N/A')}"
            if time_range
            else "N/A"
        )

        fill_data = {
            "generated_at": datetime.now().isoformat(),
            "candidate_id": candidate.get("candidate_id"),
            "title": candidate.get("title"),
            "freq": str(candidate.get("freq", 0)),
            "time_range": time_range_str,
            "confidence_level": evidence_pack.get("uncertainty", {}).get(
                "confidence_level", "medium"
            ),
            "evidence_pack": evidence_pack,
        }

        # 填充模板
        prd = self._fill_template(self.PRD_TEMPLATE.copy(), fill_data)

        return prd


def generate_prd(
    candidate: Dict[str, Any],
    evidence_pack: Dict[str, Any],
    activities: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    生成 PRD 的便捷函数

    Args:
        candidate: 候选行为
        evidence_pack: 证据包
        activities: 相关 activities

    Returns:
        PRD 文档
    """
    generator = PRDGenerator()
    return generator.generate_prd(candidate, evidence_pack, activities)


if __name__ == "__main__":
    # 测试
    import sys

    sys.path.insert(0, str(Path(__file__).parent.parent))

    from mcagent.evidence_pack import create_evidence_pack

    # 加载示例数据
    sample_file = Path("samples/sample_activities.json")
    with open(sample_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    activities = data["activities"]

    # 模拟 candidate 和 evidence_pack
    candidate = {
        "candidate_id": "candidate_0",
        "title": "开发 MineContext 集成",
        "freq": 4,
        "time_range": {
            "start": "2025-12-25T09:00:00",
            "end": "2025-12-29T12:00:00",
            "duration_days": 5,
        },
        "sample_activity_ids": ["act_001", "act_003", "act_006", "act_010"],
    }

    # 生成 evidence_pack
    evidence_pack = create_evidence_pack(candidate, activities)

    # 生成 PRD
    prd = generate_prd(candidate, evidence_pack, activities)

    print("=" * 70)
    print("PRD 生成测试")
    print("=" * 70)
    print(json.dumps(prd, ensure_ascii=False, indent=2))

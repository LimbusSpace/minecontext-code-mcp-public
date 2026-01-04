# evidence_pack.py
"""
证据包生成模块

为每个候选行为生成至少3条证据（按时间分散），每条证据包含：
- occurred_at: 发生时间
- source_ref: activity_id（源引用）
- excerpt: title 或 content 的片段

同时定义 uncertainty（不确定性）：what_we_cannot_prove
"""
import json
from typing import Any, Dict, List, Optional
from datetime import datetime
import random


class EvidencePack:
    """
    证据包类，用于生成和管理证据
    """

    def __init__(self, candidate: Dict[str, Any], activities: List[Dict[str, Any]]):
        """
        初始化

        Args:
            candidate: 候选行为（来自 behavior_miner）
            activities: 所有相关 activities
        """
        self.candidate = candidate
        self.candidate_id = candidate.get("candidate_id")
        self.title = candidate.get("title")
        self.activities = activities

    def _filter_candidate_activities(self) -> List[Dict[str, Any]]:
        """
        从所有 activities 中筛选出属于当前 candidate 的 activities

        Returns:
            candidate 相关的 activities 列表
        """
        sample_ids = self.candidate.get("sample_activity_ids", [])

        # 获取 candidate 的所有 activities（这里简单处理，实际可能需要更复杂的匹配）
        candidate_activities = []

        for activity in self.activities:
            activity_id = activity.get("id")
            if activity_id in sample_ids:
                candidate_activities.append(activity)

        # 如果通过 sample_ids 找不到足够的 activities，尝试通过标题匹配
        if len(candidate_activities) < 3:
            candidate_title = self.title.lower()
            for activity in self.activities:
                activity_title = (activity.get("title") or "").lower()
                # 如果标题相似，也包含进来
                if candidate_title in activity_title or activity_title in candidate_title:
                    if activity not in candidate_activities:
                        candidate_activities.append(activity)

        return candidate_activities

    def _extract_excerpt(self, activity: Dict[str, Any], max_length: int = 200) -> str:
        """
        从 activity 中提取 excerpt（摘要片段）

        优先级：content > title

        Args:
            activity: activity 数据
            max_length: 最大长度

        Returns:
            excerpt 文本
        """
        # 1. 优先使用 content
        content = activity.get("content") or ""
        if content and len(content.strip()) > 10:
            excerpt = content.strip()
            if len(excerpt) > max_length:
                # 找到合适的截断点（避免截断单词）
                cut_pos = excerpt.rfind(" ", max_length - 50, max_length)
                if cut_pos > 0:
                    excerpt = excerpt[:cut_pos]
                else:
                    excerpt = excerpt[:max_length]
                excerpt += "..."
            return excerpt

        # 2. 其次使用 title
        title = activity.get("title") or ""
        if title:
            return title

        # 3. 最后返回默认值
        return "No excerpt available"

    def _select_diverse_examples(
        self, activities: List[Dict[str, Any]], min_examples: int = 3
    ) -> List[Dict[str, Any]]:
        """
        从 activities 中选择至少 min_examples 条样本，按时间分散

        策略：
        1. 优先选择时间跨度最大的样本
        2. 确保样本在时间分布上足够分散
        3. 如果总数不足 min_examples，返回所有

        Args:
            activities: activity 列表
            min_examples: 最小样本数

        Returns:
            被选中的 activities 列表
        """
        if not activities:
            return []

        # 按时间排序
        activities_sorted = sorted(
            activities,
            key=lambda x: x.get("start_time")
            or x.get("end_time")
            or "9999-12-31",
        )

        total = len(activities_sorted)

        # 如果总数小于 min_examples，返回所有
        if total <= min_examples:
            return activities_sorted

        # 选择跨越不同时间段的样本
        selected = []

        # 始终包含最早和最晚的
        selected.append(activities_sorted[0])
        if total > 1:
            selected.append(activities_sorted[-1])

        # 在中间选择其他样本
        remaining_needed = min_examples - len(selected)
        if remaining_needed > 0:
            # 计算中间的索引点
            step = total // (remaining_needed + 1)
            for i in range(remaining_needed):
                idx = step * (i + 1)
                if idx < total and activities_sorted[idx] not in selected:
                    selected.append(activities_sorted[idx])

        # 按时间再次排序
        selected_sorted = sorted(
            selected,
            key=lambda x: x.get("start_time") or x.get("end_time") or "9999-12-31",
        )

        return selected_sorted

    def generate_uncertainty(self) -> Dict[str, Any]:
        """
        生成不确定性声明

        根据候选行为的类型，定义我们无法证明的内容

        Returns:
            不确定性字典
        """
        title = self.title.lower()

        # 默认的不确定性声明
        uncertainty = {
            "what_we_cannot_prove": [
                "无法证明用户的真实意图",
                "无法证明行为是否按计划执行",
                "无法证明行为的结果和影响",
            ],
            "confidence_level": "medium",
            "limitations": [
                "基于活动标题和内容的推断",
                "可能存在相似行为的误判",
            ],
        }

        # 根据标题中的关键词调整不确定性
        if "开发" in title or "编写" in title:
            uncertainty["what_we_cannot_prove"].extend(
                [
                    "无法证明代码是否最终提交",
                    "无法证明代码质量是否符合标准",
                    "无法证明是否经过 code review",
                ]
            )

        elif "测试" in title:
            uncertainty["what_we_cannot_prove"].extend(
                [
                    "无法证明测试是否覆盖所有场景",
                    "无法证明测试是否通过",
                    "无法证明是否修复了所有发现的问题",
                ]
            )

        elif "bug" in title or "修复" in title:
            uncertainty["what_we_cannot_prove"].extend(
                [*"无法证明是否完全修复了 Bug",
                    "无法证明是否引入了新的问题",
                    "无法证明是否进行了充分的测试",
                ]
            )

        elif "发送" in title or "邮件" in title:
            uncertainty["what_we_cannot_prove"].extend(
                [
                    "无法证明是否点击了发送按钮",
                    "无法证明邮件是否发送成功",
                    "无法证明收件人是否正确",
                ]
            )

        elif "会议" in title or "讨论" in title:
            uncertainty["what_we_cannot_prove"].extend(
                [
                    "无法证明是否实际参与了会议",
                    "无法证明会议讨论的内容",
                    "无法证明是否达成了共识",
                ]
            )

        elif "优化" in title or "改进" in title:
            uncertainty["what_we_cannot_prove"].extend(
                [
                    "无法证明优化是否达到预期效果",
                    "无法证明性能提升的具体数值",
                    "无法证明是否引入了新的问题",
                ]
            )

        # 调整置信度
        if len(self.candidate.get("sample_activity_ids", [])) >= 3:
            uncertainty["confidence_level"] = "high"
        elif len(self.candidate.get("sample_activity_ids", [])) == 2:
            uncertainty["confidence_level"] = "medium"
        else:
            uncertainty["confidence_level"] = "low"

        return uncertainty

    def generate_examples(self, min_examples: int = 3) -> List[Dict[str, Any]]:
        """
        生成证据样本

        每个样本包含：
        - occurred_at: 发生时间
        - source_ref: activity_id（源引用）
        - excerpt: title 或 content 的片段

        Args:
            min_examples: 最少样本数（默认3条）

        Returns:
            证据样本列表
        """
        # 获取候选的 activities
        candidate_activities = self._filter_candidate_activities()

        # 选择多样化的样本（按时间分散）
        selected_activities = self._select_diverse_examples(
            candidate_activities, min_examples=min_examples
        )

        # 生成证据样本
        examples = []
        for activity in selected_activities:
            example = {
                "occurred_at": activity.get("start_time")
                or activity.get("end_time"),
                "source_ref": activity.get("id"),
                "excerpt": self._extract_excerpt(activity),
            }
            examples.append(example)

        return examples

    def generate_pack(self, min_examples: int = 3) -> Dict[str, Any]:
        """
        生成完整的证据包

        Returns:
            完整的证据包字典
        """
        evidence_pack = {
            "candidate_id": self.candidate_id,
            "candidate_title": self.title,
            "evidence_summary": {
                "total_activities": len(self._filter_candidate_activities()),
                "generated_examples": min(
                    len(self._filter_candidate_activities()), min_examples
                ),
            },
            "examples": self.generate_examples(min_examples=min_examples),
            "uncertainty": self.generate_uncertainty(),
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "data_source": "MineContext Activities",
            },
        }

        return evidence_pack


def create_evidence_pack(
    candidate: Dict[str, Any], activities: List[Dict[str, Any]], min_examples: int = 3
) -> Dict[str, Any]:
    """
    生成证据包的便捷函数

    Args:
        candidate: 候选行为
        activities: 所有 activities
        min_examples: 最少样本数

    Returns:
        证据包
    """
    pack = EvidencePack(candidate, activities)
    return pack.generate_pack(min_examples=min_examples)


if __name__ == "__main__":
    # 测试
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent.parent))

    # 加载示例数据
    sample_file = Path("samples/sample_activities.json")
    with open(sample_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    activities = data["activities"]

    # 模拟一个 candidate
    candidate = {
        "candidate_id": "candidate_0",
        "title": "开发 MineContext 集成",
        "freq": 4,
        "sample_activity_ids": ["act_001", "act_003", "act_006", "act_010"],
    }

    # 生成证据包
    pack = create_evidence_pack(candidate, activities)

    print("=" * 70)
    print("证据包测试")
    print("=" * 70)
    print(json.dumps(pack, ensure_ascii=False, indent=2))

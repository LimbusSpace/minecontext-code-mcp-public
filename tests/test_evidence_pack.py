#!/usr/bin/env python3
"""
测试 evidence_pack.py

验证：
1. examples >= 3
2. 每个 example 包含 occurred_at, source_ref, excerpt
3. uncertainty 包含 what_we_cannot_prove
4. 样本按时间分散
"""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mcagent.evidence_pack import create_evidence_pack


def load_sample_data():
    """加载示例数据"""
    sample_file = Path("samples/sample_activities.json")
    with open(sample_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["activities"]


def test_evidence_pack_schema():
    """测试证据包的 schema 完整性"""
    print("=" * 70)
    print("测试证据包 Schema 完整性")
    print("=" * 70)

    # 加载示例数据
    activities = load_sample_data()
    print(f"\n[信息] 加载了 {len(activities)} 个 activities")

    # 模拟 candidate
    candidate = {
        "candidate_id": "candidate_0",
        "title": "开发 MineContext 集成",
        "freq": 4,
        "sample_activity_ids": ["act_001", "act_003", "act_006", "act_010"],
    }

    # 生成证据包
    pack = create_evidence_pack(candidate, activities, min_examples=3)

    print("\n[信息] 证据包生成成功")

    # 验证 1: examples >= 3
    examples = pack.get("examples", [])
    print(f"\n[验证 1] examples 数量: {len(examples)}")
    assert len(examples) >= 3, f"examples 数量不足3条，实际: {len(examples)}"
    print("✓ 通过: examples >= 3")

    # 验证 2: 每个 example 包含必需字段
    print("\n[验证 2] 检查每个 example 的字段")
    required_fields = ["occurred_at", "source_ref", "excerpt"]
    for i, example in enumerate(examples, 1):
        for field in required_fields:
            assert field in example, f"示例 {i} 缺少字段: {field}"
            assert example[field] is not None, f"示例 {i} 字段 {field} 为 None"
        print(f"  示例 {i}: ✓ occurred_at, source_ref, excerpt 均存在")

    print("✓ 通过: 所有 examples 包含必需字段")

    # 验证 3: uncertainty 包含 what_we_cannot_prove
    print("\n[验证 3] 检查 uncertainty")
    uncertainty = pack.get("uncertainty", {})
    assert "what_we_cannot_prove" in uncertainty, "缺少 what_we_cannot_prove"
    assert isinstance(uncertainty["what_we_cannot_prove"], list), "what_we_cannot_prove 应为列表"
    assert len(uncertainty["what_we_cannot_prove"]) > 0, "what_we_cannot_prove 不能为空"
    print(f"  what_we_cannot_prove 条目数: {len(uncertainty['what_we_cannot_prove'])}")
    for i, item in enumerate(uncertainty["what_we_cannot_prove"], 1):
        print(f"    {i}. {item}")
    print("✓ 通过: uncertainty 结构正确")

    # 验证 4: 检查 confidence_level
    print("\n[验证 4] 检查 confidence_level")
    assert "confidence_level" in uncertainty, "缺少 confidence_level"
    confidence = uncertainty["confidence_level"]
    assert confidence in ["low", "medium", "high"], f"无效的 confidence_level: {confidence}"
    print(f"✓ 通过: confidence_level = {confidence}")

    # 验证 5: 样本按时间分散
    print("\n[验证 5] 检查样本时间分散性")
    occurred_times = [ex.get("occurred_at") for ex in examples]
    print(f"  时间点: {occurred_times}")
    # 简单的检查：确保时间点不完全相同
    unique_times = set(occurred_times)
    assert len(unique_times) > 1, "样本时间没有分散"
    print(f"✓ 通过: {len(unique_times)} 个不同时间点")

    # 验证 6: excerpt 长度合理
    print("\n[验证 6] 检查 excerpt 长度")
    for i, example in enumerate(examples, 1):
        excerpt = example.get("excerpt", "")
        print(f"  示例 {i}: {len(excerpt)} 字符")
        assert len(excerpt) > 10, f"示例 {i} excerpt 过短"
    print("✓ 通过: 所有 excerpt 长度合理")

    # 验证 7: 检查整体结构
    print("\n[验证 7] 检查整体结构")
    assert "candidate_id" in pack, "缺少 candidate_id"
    assert "candidate_title" in pack, "缺少 candidate_title"
    assert "evidence_summary" in pack, "缺少 evidence_summary"
    assert "examples" in pack, "缺少 examples"
    assert "uncertainty" in pack, "缺少 uncertainty"
    assert "metadata" in pack, "缺少 metadata"
    print("✓ 通过: 整体结构完整")

    print("\n" + "=" * 70)
    print("[SUCCESS] 所有验证通过！")
    print("=" * 70)

    # 输出完整的证据包
    print("\n[信息] 生成的证据包:")
    print(json.dumps(pack, ensure_ascii=False, indent=2))

    return True


def test_different_candidate_types():
    """测试不同类型的 candidate"""
    print("\n" + "=" * 70)
    print("测试不同类型的 Candidate")
    print("=" * 70)

    activities = load_sample_data()

    test_cases = [
        {
            "name": "开发类型",
            "candidate": {
                "candidate_id": "dev_test",
                "title": "开发新功能模块",
                "sample_activity_ids": ["act_001"],
            },
        },
        {
            "name": "测试类型",
            "candidate": {
                "candidate_id": "test_test",
                "title": "测试 API 接口",
                "sample_activity_ids": ["act_002"],
            },
        },
        {
            "name": "Bug修复类型",
            "candidate": {
                "candidate_id": "bug_test",
                "title": "修复已知 Bug",
                "sample_activity_ids": ["act_005"],
            },
        },
    ]

    for test_case in test_cases:
        print(f"\n[测试] {test_case['name']}: {test_case['candidate']['title']}")
        pack = create_evidence_pack(test_case["candidate"], activities)
        uncertainty = pack.get("uncertainty", {})
        print(f"  confidence_level: {uncertainty.get('confidence_level')}")
        print(f"  what_we_cannot_prove 条目数: {len(uncertainty.get('what_we_cannot_prove', []))}")
        print("  ✓ 通过")


def test_min_examples_boundary():
    """测试最小样本数的边界情况"""
    print("\n" + "=" * 70)
    print("测试最小样本数边界")
    print("=" * 70)

    activities = load_sample_data()

    # 模拟只有一个 activity 的 candidate
    candidate = {
        "candidate_id": "single_test",
        "title": "单一活动测试",
        "sample_activity_ids": ["act_001"],
    }

    print("\n[测试] Candidate 只有 1 个 activity，但要求 min_examples=3")
    pack = create_evidence_pack(candidate, activities, min_examples=3)
    examples = pack.get("examples", [])

    print(f"  实际生成的 examples 数量: {len(examples)}")
    print(f"  evidence_summary: {pack.get('evidence_summary')}")

    # 应该返回所有可用的 activities（1个）
    assert len(examples) == 1, f"应该返回1个 example，实际: {len(examples)}"
    print("  ✓ 通过")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("=                   证据包测试启动                         =")
    print("=" * 70)

    try:
        # 测试 1: Schema 完整性
        test_evidence_pack_schema()

        # 测试 2: 不同类型 candidate
        test_different_candidate_types()

        # 测试 3: 边界情况
        test_min_examples_boundary()

        print("\n" + "=" * 70)
        print("=                    所有测试通过！                        =")
        print("=" * 70)

    except AssertionError as e:
        print(f"\n[FAILED] 测试失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

# 使用 Bash 工具时：只输出可直接在 bash 运行的命令；不要在命令前加冒号；命令和参数之间必须有空格（例如用 ls -la，不要用 :ls-la 或 ls-la）。

实现 evidence_pack.py：
每个候选选取至少 3 条样例（按时间分散）
evidence 最少字段：occurred_at + source_ref(activity_id) + excerpt(title/summary片段)
明确 uncertainty.what_we_cannot_prove（例如：“无法证明是否点击发送/发送成功”）
新增 tests/test_evidence_pack.py：验证 schema 完整性（examples>=3 等）


实现 prd_generator.py（模板优先）+ exporter.py
CLI：python cli/export_prd.py --candidate <id> --out exports/
（可选）把导出动作写入 trajectory.py（记录用户确认与导出时间）

你能从候选列表选 1 个 → 一条命令导出 3 件套（prd/spec/evidence_pack）

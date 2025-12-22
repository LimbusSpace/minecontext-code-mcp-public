#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试脚本：设置 API 密钥并运行 failure_inspector
"""
import os
import subprocess
import sys

# 设置 API 密钥
# API_KEY will be loaded from environment variable
# 从命令行参数获取要运行的命令
if len(sys.argv) > 1:
    cmd = sys.argv[1]
else:
    print("Usage: python run_test.py \"<command>\"")
    print("Example: python run_test.py \"python some_broken_script.py\"")
    sys.exit(1)

print(f"设置 API 密钥: {API_KEY[:10]}...")
print(f"运行命令: {cmd}\n")

# 运行 failure_inspector.py - 明确传递环境变量
env = os.environ.copy()
env["SILICONFLOW_API_KEY"] = API_KEY

result = subprocess.run(
    [sys.executable, "failure_inspector.py", cmd],
    capture_output=True,
    text=True,
    env=env
)

print(result.stdout)
if result.stderr:
    print("错误输出:", result.stderr)

print(f"\n退出码: {result.returncode}")
print("\n=== 生成的 trajectory.json 内容 ===")
try:
    with open("trajectory.json", "r", encoding="utf-8") as f:
        import json
        data = json.load(f)
        print(json.dumps(data, ensure_ascii=False, indent=2))
except Exception as e:
    print(f"无法读取 trajectory.json: {e}")

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
获取最近20条上下文的测试脚本
通过调用 MineContext 提供的 HTTP API 接口获取 JSON 数据
"""

import requests
import json
from datetime import datetime
from typing import Dict, Any


def get_context_from_api(endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
    """从指定的API端点获取数据"""
    base_url = "http://127.0.0.1:1733"
    url = base_url + endpoint

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"[ERROR] 请求失败 {endpoint}: {e}")
        return None


def fetch_all_contexts(limit: int = 20) -> Dict[str, Any]:
    """获取所有类型的上下文数据"""
    results = {
        "timestamp": datetime.now().isoformat(),
        "total_types": 0,
        "data": {}
    }

    # 定义要调用的API端点
    api_endpoints = {
        "reports": {
            "endpoint": "/api/debug/reports",
            "params": {"limit": limit}
        },
        "todos": {
            "endpoint": "/api/debug/todos",
            "params": {"limit": limit}
        },
        "activities": {
            "endpoint": "/api/debug/activities",
            "params": {"limit": limit}
        },
        "tips": {
            "endpoint": "/api/debug/tips",
            "params": {"limit": limit}
        }
    }

    print("=" * 60)
    print("开始获取上下文数据...")
    print("=" * 60)

    success_count = 0
    total_records = 0

    for data_type, config in api_endpoints.items():
        print(f"\n[API] 正在获取 {data_type} 数据...")

        response_data = get_context_from_api(
            config["endpoint"],
            config["params"]
        )

        if response_data:
            if "code" in response_data and response_data["code"] == 0:
                if "data" in response_data:
                    data = response_data["data"]
                    # 根据不同类型提取数据
                    if data_type == "reports" and "reports" in data:
                        records = data["reports"]
                    elif data_type == "todos" and "todos" in data:
                        records = data["todos"]
                    elif data_type == "activities" and "activities" in data:
                        records = data["activities"]
                    elif data_type == "tips" and "tips" in data:
                        records = data["tips"]
                    else:
                        records = data if isinstance(data, list) else [data]

                    # 存储结果
                    results["data"][data_type] = {
                        "endpoint": config["endpoint"],
                        "count": len(records),
                        "records": records
                    }

                    success_count += 1
                    total_records += len(records)
                    print(f"  [OK] 成功获取 {len(records)} 条记录")
                else:
                    results["data"][data_type] = {
                        "endpoint": config["endpoint"],
                        "count": 0,
                        "records": [],
                        "raw_response": response_data
                    }
                    print(f"  [WARN] 响应格式异常，获取到0条记录")
            else:
                results["data"][data_type] = {
                    "endpoint": config["endpoint"],
                    "count": 0,
                    "records": [],
                    "error": f"API返回错误代码: {response_data.get('code', 'unknown')}"
                }
                print(f"  [ERROR] API返回错误: {response_data.get('message', 'unknown error')}")
        else:
            results["data"][data_type] = {
                "endpoint": config["endpoint"],
                "count": 0,
                "records": [],
                "error": "API请求失败"
            }
            print(f"  [ERROR] 请求失败")

    results["total_types"] = success_count
    results["total_records"] = total_records

    return results


def format_summary(results: Dict[str, Any]):
    """格式化输出汇总信息"""
    print("\n" + "=" * 60)
    print("数据获取汇总")
    print("=" * 60)
    print(f"获取时间: {results['timestamp']}")
    print(f"成功类型: {results['total_types']}/4")
    print(f"总记录数: {results['total_records']}")
    print("\n各类型详情:")

    for data_type, info in results["data"].items():
        count = info["count"]
        endpoint = info["endpoint"]
        status = "[OK]" if count > 0 else "[FAIL]"
        print(f"  {status} {data_type:12s}: {count:3d} 条记录 - {endpoint}")

    print()


def save_to_file(results: Dict[str, Any], filename: str = None):
    """保存结果到文件"""
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"minecontext_contexts_{timestamp}.json"

    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2, default=str)
        print(f"[SAVE] 数据已保存到文件: {filename}")
        return filename
    except Exception as e:
        print(f"[ERROR] 保存文件失败: {e}")
        return None


def display_sample_data(results: Dict[str, Any], max_items: int = 2):
    """显示示例数据"""
    print("\n" + "=" * 60)
    print("示例数据预览")
    print("=" * 60)

    for data_type, info in results["data"].items():
        records = info.get("records", [])
        if not records:
            continue

        print(f"\n[{data_type.upper()}] - 显示前 {min(max_items, len(records))} 条:")
        print("-" * 40)

        for i, record in enumerate(records[:max_items], 1):
            print(f"\n  记录 {i}:")

            # 显示主要字段
            for key, value in record.items():
                if key in ['id', 'content', 'title', 'summary', 'created_at', 'start_time', 'end_time']:
                    # 处理文本截断
                    if isinstance(value, str) and len(value) > 100:
                        preview = value[:100] + "..."
                        print(f"    {key}: {preview}")
                    else:
                        print(f"    {key}: {value}")


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("MineContext 上下文数据获取工具")
    print("=" * 60)

    # 获取数据
    results = fetch_all_contexts(limit=20)

    # 显示汇总
    format_summary(results)

    # 保存到文件
    saved_file = save_to_file(results)

    # 显示示例数据
    display_sample_data(results)

    print("\n" + "=" * 60)
    if saved_file:
        print(f"[SUCCESS] 任务完成！文件已保存到: {saved_file}")
    else:
        print("[WARN] 任务完成，但文件保存失败")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
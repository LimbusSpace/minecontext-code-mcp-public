import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, Any

from minecontext_wrapper import get_minecontext_summary


def safe_get_context_field(data: dict, field: str):
    """安全地从 MineContext 返回结果中获取字段，返回 None 如果字段不存在"""
    return data.get(field) if isinstance(data, dict) else None


def run_command(cmd: str, timeout: int = 300):
    """运行一条 shell 命令，返回 (exit_code, output_text)。"""
    proc = subprocess.Popen(
        cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        out, _ = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        out = "Command timed out."
    return proc.returncode, out


def main():
    # 从命令行参数读取命令，如果没有参数则使用默认命令
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
    else:
        cmd = "pytest"  # 默认命令

    code, output = run_command(cmd)
    now = time.strftime("%Y-%m-%dT%H:%M:%S")

    steps = []

    steps.append(
        {
            "type": "bash",
            "command": cmd,
            "exit_code": code,
            "output_excerpt": output[:2000],  # 防止太长
        }
    )

    if code != 0:
        # 调用 MineContext 获取上下文摘要
        minecontext_result = get_minecontext_summary(
            task_type="debug_error",
            detail_level="medium"
        )

        # 打印上下文摘要摘要用于调试
        print(f"MineContext 摘要 (状态: {safe_get_context_field(minecontext_result, 'status')}):")
        print(f"  - 源: {safe_get_context_field(minecontext_result, 'source')}")
        print(f"  - 时间戳: {safe_get_context_field(minecontext_result, 'timestamp')}")
        print(f"  - 用户意图摘要: {'可用' if safe_get_context_field(minecontext_result, 'user_intent_summary') else '不可用'}")
        print(f"  - 最近活动: {'可用' if safe_get_context_field(minecontext_result, 'recent_activity') else '不可用'}")
        print(f"  - 提示摘要: {'可用' if safe_get_context_field(minecontext_result, 'tips_summary') else '不可用'}")
        if minecontext_result.get('error'):
            print(f"  - 错误: {minecontext_result['error'].get('message')}")
            print(f"  - 提示: {minecontext_result['error'].get('hint')}")

        steps.append(
            {
                "type": "minecontext_context",
                "result": minecontext_result
            }
        )

        # 使用 LangChain 链进行错误分析
        try:
            from langchain_analyzer import analyze_error_with_langchain
            analysis = analyze_error_with_langchain(cmd, output, minecontext_result)
            engine_info = "langchain_deepseek_v3"
        except ImportError as e:
            analysis = f"LangChain 分析器导入失败: {e}\n建议: pip install langchain langchain-openai python-dotenv"
            engine_info = "error_no_langchain"
        except Exception as e:
            analysis = f"使用 LangChain 进行错误分析时出现异常：{e!r}"
            engine_info = "error_analysis_failed"

        steps.append(
            {
                "type": "llm_analysis",
                "engine": engine_info,
                "result": analysis
            }
        )

    # 构建 trajectory 数据
    trajectory = {
        "timestamp": now,
        "command": cmd,
        "steps": steps
    }

    # 写入 trajectory_{timestamp}.json
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_path = Path(f"trajectory_{timestamp}.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(trajectory, f, ensure_ascii=False, indent=2)

    print(f"Trajectory 已保存至: {output_path.absolute()}")
    if code != 0:
        print(f"检测到命令失败，已包含 MineContext 上下文和 LLM 分析")
    print(f"命令 '{cmd}' 退出码: {code}")


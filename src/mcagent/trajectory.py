"""
轨迹记录和保存功能
"""
import json
import time
from pathlib import Path
from typing import Dict, List, Any

def build_trajectory(timestamp: str, command: str, steps: List[Dict[str, Any]]) -> Dict[str, Any]:
    """构建轨迹数据"""
    return {"timestamp": timestamp, "command": command, "steps": steps}

def save_trajectory(trajectory: Dict[str, Any], output_dir: str = ".") -> Path:
    """保存轨迹到文件"""
    timestamp = trajectory.get("timestamp", time.strftime("%Y%m%d_%H%M%S")).replace(":", "").replace("-", "").split("T")[0] if "T" in str(trajectory.get("timestamp", "")) else time.strftime("%Y%m%d_%H%M%S")
    output_path = Path(output_dir) / f"trajectory_{timestamp}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(trajectory, f, ensure_ascii=False, indent=2)
    return output_path.resolve()

def record_command_step(steps: List[Dict[str, Any]], cmd: str, exit_code: int, output: str):
    """记录命令执行步骤"""
    steps.append({"type": "bash", "command": cmd, "exit_code": exit_code, "output_excerpt": output[:2000]})

def record_minecontext_step(steps: List[Dict[str, Any]], result: Dict[str, Any]):
    """记录 MineContext 上下文步骤"""
    steps.append({"type": "minecontext_context", "result": result})

def record_llm_analysis_step(steps: List[Dict[str, Any]], engine: str, result: str):
    """记录 LLM 分析步骤"""
    steps.append({"type": "llm_analysis", "engine": engine, "result": result})

"""
失败检查器的核心逻辑
"""
import subprocess
import time
from typing import Dict, Any, Tuple
from .context_wrapper import get_minecontext_summary
from .trajectory import build_trajectory, save_trajectory, record_command_step, record_minecontext_step, record_llm_analysis_step

def safe_get_context_field(data: dict, field: str):
    """安全地从 MineContext 返回结果中获取字段"""
    return data.get(field) if isinstance(data, dict) else None

def run_command(cmd: str, timeout: int = 300) -> Tuple[int, str]:
    """运行命令并返回 (exit_code, output)"""
    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    try:
        out, _ = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        out = "Command timed out."
    return proc.returncode, out

def analyze_error(cmd: str, output: str, minecontext_result: Dict[str, Any]) -> Tuple[str, str]:
    """分析错误并返回 (engine_info, analysis)"""
    try:
        from .langchain_analyzer import analyze_error_with_langchain
        analysis = analyze_error_with_langchain(cmd, output, minecontext_result)
        engine_info = "langchain_deepseek_v3"
    except ImportError as e:
        analysis = f"LangChain 分析器导入失败: {e}"
        engine_info = "error_no_langchain"
    except Exception as e:
        analysis = f"错误分析异常: {e!r}"
        engine_info = "error_analysis_failed"
    return engine_info, analysis

def inspect_command(cmd: str, timeout: int = 300, output_dir: str = ".") -> Tuple[int, Dict[str, Any]]:
    """检查命令执行"""
    code, output = run_command(cmd, timeout)
    now = time.strftime("%Y-%m-%dT%H:%M:%S")
    steps = []
    
    record_command_step(steps, cmd, code, output)
    
    if code != 0:
        minecontext_result = get_minecontext_summary(task_type="debug_error", detail_level="medium")
        record_minecontext_step(steps, minecontext_result)
        engine_info, analysis = analyze_error(cmd, output, minecontext_result)
        record_llm_analysis_step(steps, engine_info, analysis)
    
    trajectory = build_trajectory(now, cmd, steps)
    output_path = save_trajectory(trajectory, output_dir)
    trajectory["output_path"] = str(output_path)
    
    return code, trajectory

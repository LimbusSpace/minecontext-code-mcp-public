# minecontext_mcp_server.py
"""
MineContext 的 MCP Server：
暴露一个工具 minecontext_screen_context，内部调用 get_minecontext_summary。
"""

import sys
from pathlib import Path
from typing import Optional, Literal, Dict, Any

# 关键：用 FastMCP，而不是 Server
from mcp.server.fastmcp import FastMCP

# 添加 src 到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mcagent.context_wrapper import get_minecontext_summary

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


if __name__ == "__main__":
    # 以 stdio 模式运行 MCP server
    mcp.run()
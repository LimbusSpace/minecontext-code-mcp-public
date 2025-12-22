# wrapper_service.py
from typing import Optional, Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from minecontext_wrapper import get_minecontext_summary


class SummaryRequest(BaseModel):
    task_type: Optional[Literal["debug_error", "implement_feature", "refactor", "unknown"]] = "unknown"
    detail_level: Optional[Literal["low", "medium", "high"]] = "medium"


app = FastAPI(
    title="MineContext Wrapper Service",
    description="将 get_minecontext_summary 暴露为本地 HTTP API，供智能体 Builder 调用。",
    version="0.1.0"
)


@app.get("/")
async def root():
    """服务根路径，返回服务信息"""
    return {
        "message": "MineContext Wrapper Service is running",
        "version": "0.1.0",
        "endpoints": {
            "GET /": "This information",
            "POST /get_summary": "Get minecontext summary for error traceback",
            "GET /health": "Health check"
        }
    }


@app.post("/minecontext_summary")
async def get_summary(request: SummaryRequest):
    """
    接收参数并返回 MineContext 生成的上下文摘要

    请求参数:
    - task_type: 任务类型 (debug_error/implement_feature/refactor/unknown)
    - detail_level: 详细程度 (low/medium/high)

    返回:
    - summary: 生成的摘要文本
    - request_id: 请求ID（可选）
    """
    try:
        summary = get_minecontext_summary(
            task_type=request.task_type,
            detail_level=request.detail_level
        )

        return {
            "summary": summary,
            "request_id": None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")


@app.get("/health")
async def health():
    """健康检查端点"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=18080)

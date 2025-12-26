"""
LangChain 错误分析器
使用 LangChain 的 PromptTemplate + ChatOpenAI 构建分析链
实现懒加载单例模式以避免重复初始化
"""
import os
import json
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 懒加载的全局变量
_ERROR_ANALYSIS_CHAIN: Optional['Runnable'] = None


def _build_error_analysis_chain():
    """
    构建错误分析链（仅构建一次）
    返回一个 LangChain 的 Runnable 对象
    """
    try:
        from langchain.prompts import PromptTemplate
        from langchain_openai import ChatOpenAI
        from langchain.schema.runnable import RunnablePassthrough
    except ImportError as e:
        raise ImportError(
            f"无法导入 LangChain 相关模块: {e}\n"
            "请安装: pip install langchain langchain-openai python-dotenv"
        )

    # 获取 API 配置
    api_key = os.getenv("SILICONFLOW_API_KEY")
    base_url = os.getenv("SILICONFLOW_BASE_URL", "https://api.siliconflow.cn/v1")
    model = os.getenv("MODEL_NAME", "deepseek-ai/DeepSeek-V3.2")

    if not api_key:
        raise ValueError("环境变量 SILICONFLOW_API_KEY 未设置")

    # 定义 Prompt 模板
    prompt_template = """你是一位经验丰富的 Python 和测试专家。

请分析以下命令执行失败的原因，并结合项目上下文给出修复建议。

**命令执行信息**
- 执行的命令: {command}
- 错误输出（已截断前2000字符）:
```
{error_output}
```

**项目上下文信息（MineContext 摘要）**
下面是 MineContext 提供的项目相关信息（已转JSON）:
```json
{minecontext_summary_json}
```

**你的任务**
1. 分析错误输出的根本原因
2. 结合 MineContext 提供的上下文，识别可能的关联问题
3. 提供具体可行的修复建议（步骤清晰）
4. 如果 MineContext 提供的用户意图或最近活动与错误相关，请指出关联性

**分析要求**
- 回答使用中文
- 分点说明，条理清晰
- 给出具体代码示例或修复命令（如果适用）
- 如果上下文信息不足，说明还需要哪些信息

请开始分析："""

    prompt = PromptTemplate(
        input_variables=["command", "error_output", "minecontext_summary_json"],
        template=prompt_template
    )

    # 初始化 LLM
    llm = ChatOpenAI(
        model=model,
        openai_api_key=api_key,
        openai_api_base=base_url,
        temperature=0.7,
        max_tokens=2048,
        streaming=False
    )

    # 构建链
    chain = (
        {
            "command": lambda x: x["command"],
            "error_output": lambda x: x["error_output"],
            "minecontext_summary_json": lambda x: x["minecontext_summary_json"],
        }
        | prompt
        | llm
        | (lambda x: x.content)  # 提取生成的文本内容
    )

    return chain


def get_error_analysis_chain():
    """
    获取错误分析链（单例模式，懒加载）
    """
    global _ERROR_ANALYSIS_CHAIN

    if _ERROR_ANALYSIS_CHAIN is None:
        _ERROR_ANALYSIS_CHAIN = _build_error_analysis_chain()

    return _ERROR_ANALYSIS_CHAIN


def analyze_error_with_langchain(
    command: str,
    error_output: str,
    minecontext_summary: Dict[str, Any],
) -> str:
    """
    使用 LangChain 的 chain 进行错误分析。

    Args:
        command: 执行的命令
        error_output: 错误输出文本
        minecontext_summary: MineContext 摘要字典

    Returns:
        LLM 生成的分析结果字符串
    """
    # 将 MineContext 摘要转成压缩 JSON 字符串，防止太长
    try:
        mc_json = json.dumps(minecontext_summary, ensure_ascii=False, indent=2)
    except TypeError:
        mc_json = str(minecontext_summary)

    # 长度控制：防止 prompt 过大
    max_len = 3000
    if len(mc_json) > max_len:
        mc_json = mc_json[:max_len] + "\n... [MineContext JSON truncated]"

    # 获取 chain（懒加载初始化）
    chain = get_error_analysis_chain()

    # 调用链
    try:
        result = chain.invoke({
            "command": command,
            "error_output": error_output[:2000],  # 再做一层截断，避免太长
            "minecontext_summary_json": mc_json,
        })
        return result
    except Exception as e:
        raise RuntimeError(f"LangChain 分析失败: {e}")


if __name__ == "__main__":
    # 简单的自测
    print("测试 LangChain 分析器单体模式...")

    # 第一次调用（会初始化 chain）
    test_summary = {
        "status": "success",
        "source": "minecontext_wrapper",
        "recent_activity": ["修改了 failure_inspector.py"]
    }

    try:
        result = analyze_error_with_langchain(
            command="python test.py",
            error_output="ImportError: No module named 'langchain'",
            minecontext_summary=test_summary
        )
        print("\n=== 分析结果 ===")
        print(result)
    except ImportError as e:
        print(f"\n跳过测试（LangChain 未安装）: {e}")
    except Exception as e:
        print(f"\n测试失败: {e}")

    # 第二次调用（复用已初始化的 chain）
    print("\n\n测试复用已初始化的 chain...")
    try:
        result2 = analyze_error_with_langchain(
            command="python another_test.py",
            error_output="ValueError: Invalid configuration",
            minecontext_summary={"status": "success"}
        )
        print("\n=== 第二次分析结果 ===")
        print(result2[:200] + "..." if len(result2) > 200 else result2)
    except Exception as e:
        print(f"\n第二次调用失败: {e}")

import os
import requests
import time
from typing import Optional

# SiliconFlow API 配置 - 从环境变量加载
import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

SILICONFLOW_API_KEY = os.getenv("SILICONFLOW_API_KEY")
SILICONFLOW_BASE_URL = os.getenv("SILICONFLOW_BASE_URL", "https://api.siliconflow.cn/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "deepseek-ai/DeepSeek-V3.2")

def call_llm(prompt: str, max_retries: int = 3) -> str:
    """
    给定 prompt，调用 SiliconFlow API 的 deepseek-ai/DeepSeek-V3.2 模型，返回分析文本。

    Args:
        prompt: 要发送给 LLM 的提示文本
        max_retries: 最大重试次数（默认 3 次）

    Returns:
        str: LLM 生成的分析文本，如果调用失败则返回错误描述
    """
    if not SILICONFLOW_API_KEY:
        return "【错误】未设置 SILICONFLOW_API_KEY 环境变量，无法调用 LLM。"

    url = f"{SILICONFLOW_BASE_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {SILICONFLOW_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.7,
        "max_tokens": 2048,
        "top_p": 0.9,
        "stream": False
    }

    for attempt in range(max_retries):
        try:
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                # 提取生成的文本内容
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                if content:
                    return content.strip()
                else:
                    return "【错误】LLM 返回了空内容。"

            elif response.status_code == 401:
                return "【错误】API 密钥无效或已过期，请检查 SILICONFLOW_API_KEY。"

            elif response.status_code == 429:
                error_msg = "【错误】API 调用频率过高，请稍后再试。"
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # 指数退避
                    time.sleep(wait_time)
                    continue
                return error_msg

            else:
                error_detail = response.json().get("error", {}).get("message", "未知错误")
                return f"【错误】API 调用失败 (状态码: {response.status_code}): {error_detail}"

        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                time.sleep(wait_time)
                continue
            return "【错误】API 请求超时，请检查网络连接。"

        except requests.exceptions.ConnectionError:
            return "【错误】无法连接到 SiliconFlow API，请检查网络连接。"

        except Exception as e:
            return f"【错误】调用 LLM 时发生意外错误: {str(e)}"

    return "【错误】达到最大重试次数，API 调用失败。"


if __name__ == "__main__":
    # 简单的测试代码
    test_prompt = "你好，请用中文回答这个问题：Python 中如何处理文件读取错误？"
    result = call_llm(test_prompt)
    print("测试结果:")
    print(result)

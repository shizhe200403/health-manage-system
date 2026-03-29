import logging

from django.conf import settings
from openai import OpenAI

logger = logging.getLogger(__name__)


def stream_chat(system_prompt, messages):
    """Yield content chunks from LLM streaming response."""
    api_key = getattr(settings, "LLM_API_KEY", "")
    if not api_key:
        yield "AI 助手尚未配置，请联系管理员设置 LLM_API_KEY。"
        return

    client = OpenAI(
        api_key=api_key,
        base_url=getattr(settings, "LLM_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
    )
    model = getattr(settings, "LLM_MODEL", "qwen-plus")

    full_messages = [{"role": "system", "content": system_prompt}] + messages

    try:
        response = client.chat.completions.create(
            model=model,
            messages=full_messages,
            stream=True,
            max_tokens=1024,
        )
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    except Exception as e:
        logger.exception("LLM API error")
        yield f"\n\n抱歉，AI 助手暂时无法响应，请稍后再试。({type(e).__name__})"

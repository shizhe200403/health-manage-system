import base64
import json
import logging
import re
from io import BytesIO

from django.conf import settings
from openai import OpenAI
from PIL import Image, ImageOps

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


def _client():
    api_key = getattr(settings, "LLM_API_KEY", "")
    if not api_key:
        raise ValueError("AI 助手尚未配置，请联系管理员设置 LLM_API_KEY。")

    return OpenAI(
        api_key=api_key,
        base_url=getattr(settings, "LLM_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
    )


def _image_to_data_url(image_bytes):
    with Image.open(BytesIO(image_bytes)) as image:
        image = ImageOps.exif_transpose(image)
        if image.mode != "RGB":
            image = image.convert("RGB")
        image.thumbnail((1600, 1600))

        buffer = BytesIO()
        image.save(buffer, format="JPEG", quality=82, optimize=True)
        encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
        return f"data:image/jpeg;base64,{encoded}"


def _extract_json_object(raw_text):
    text = raw_text.strip()
    if text.startswith("```"):
        fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, flags=re.DOTALL)
        if fenced:
            text = fenced.group(1)

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("AI 返回结果无法解析为 JSON。")

    return json.loads(text[start : end + 1])


def _sanitize_float(value):
    if value in (None, "", "null"):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return round(number, 1)


def _sanitize_food_analysis(data):
    ingredients = []
    for item in data.get("ingredients") or []:
        name = str(item.get("ingredient_name") or "").strip()
        if not name:
            continue
        ingredients.append(
            {
                "ingredient_name": name[:128],
                "amount": _sanitize_float(item.get("amount")),
                "unit": str(item.get("unit") or "份").strip()[:32] or "份",
                "is_main": bool(item.get("is_main")),
            }
        )

    steps = [str(item).strip() for item in (data.get("steps") or []) if str(item).strip()]
    nutrition = data.get("nutrition") or {}

    meal_type = str(data.get("meal_type") or "").strip()
    if meal_type not in {"breakfast", "lunch", "dinner", "snack"}:
        meal_type = "lunch"

    return {
        "title": str(data.get("title") or "").strip()[:120],
        "description": str(data.get("description") or "").strip()[:500],
        "meal_type": meal_type,
        "servings": _sanitize_float(data.get("servings")) or 1,
        "portion_size": str(data.get("portion_size") or "1 份").strip()[:32] or "1 份",
        "ingredients": ingredients,
        "steps": steps,
        "nutrition": {
            "energy": _sanitize_float(nutrition.get("energy")),
            "protein": _sanitize_float(nutrition.get("protein")),
            "fat": _sanitize_float(nutrition.get("fat")),
            "carbohydrate": _sanitize_float(nutrition.get("carbohydrate")),
        },
        "confidence_notes": str(data.get("confidence_notes") or "").strip()[:500],
        "warning": str(data.get("warning") or "").strip()[:500],
    }


def analyze_food_image(image_bytes):
    model = getattr(settings, "LLM_VISION_MODEL", "") or getattr(settings, "LLM_MODEL", "qwen-plus")
    data_url = _image_to_data_url(image_bytes)
    client = _client()

    prompt = """
你是一名营养师兼菜谱整理助手。请根据用户上传的食物照片，识别最可能的菜品、主要食材、份量，并估算每份营养信息。

要求：
1. 只输出一个 JSON 对象，不要输出 Markdown，不要解释。
2. 如果不确定，允许保守估算，但要在 confidence_notes 或 warning 里说明。
3. meal_type 只能是 breakfast、lunch、dinner、snack 之一。
4. ingredients 数组每项包含 ingredient_name、amount、unit、is_main。
5. steps 只需要给出 1-3 条概括性制作步骤，无法判断时返回空数组。
6. nutrition 使用每份估算，字段为 energy、protein、fat、carbohydrate，单位分别为 kcal、g、g、g。
7. 若图片无法判断，请尽量提取可识别信息，不要返回空对象。

返回 JSON 结构：
{
  "title": "菜品名称",
  "description": "简短描述",
  "meal_type": "lunch",
  "servings": 1,
  "portion_size": "1 盘",
  "ingredients": [
    {"ingredient_name": "鸡胸肉", "amount": 150, "unit": "g", "is_main": true}
  ],
  "steps": ["步骤1", "步骤2"],
  "nutrition": {
    "energy": 420,
    "protein": 32,
    "fat": 14,
    "carbohydrate": 28
  },
  "confidence_notes": "说明判断依据与不确定项",
  "warning": "如果图片信息不足，这里给出提醒"
}
""".strip()

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "你必须严格返回 JSON 对象。"},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                },
            ],
            stream=False,
            max_tokens=1200,
            temperature=0.2,
        )
    except Exception as exc:
        logger.exception("Food image analysis failed")
        raise ValueError(f"图片识别失败，请检查视觉模型配置。({type(exc).__name__})") from exc

    content = response.choices[0].message.content if response.choices else ""
    if isinstance(content, list):
        content = "".join(part.get("text", "") for part in content if isinstance(part, dict))
    if not content:
        raise ValueError("AI 没有返回可用的识别结果。")

    try:
        parsed = _extract_json_object(content)
    except Exception as exc:
        logger.exception("Food image analysis JSON parse failed")
        raise ValueError("AI 返回了结果，但格式无法解析为结构化数据。") from exc

    return _sanitize_food_analysis(parsed)

import json
import logging
import random
import time
from datetime import datetime
import re

import google.generativeai as genai
from django.conf import settings
from google.api_core.exceptions import ResourceExhausted

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """You extract events from user text.
Return ONLY valid JSON. No markdown, no commentary.
Split into separate events; do not merge unrelated items.
If any field is unclear, set it to null.
Never invent details not present in the input."""

USER_PROMPT_TEMPLATE = """Parse the input into the exact JSON schema.
CURRENT_DATE={current_date}
DEFAULT_TZ={default_tz}

User input:
\"\"\"
{user_text}
\"\"\"

Rules:
1) Output ONLY JSON: {{ "events": [ ... ] }}.
2) One event per item. Do not merge unrelated items.
3) date must be YYYY-MM-DD. Resolve relative dates using CURRENT_DATE.
4) start_time must be HH:MM (24h) or null.
5) duration must be integer minutes or null. Do not invent.
6) all_day is true if start_time is null. Otherwise false.
7) timezone is explicit in text, otherwise DEFAULT_TZ.
8) repeat is one of: never|daily|weekly|biweekly|monthly|yearly. If absent, use "never".
9) category is one of: work|personal|meeting|appointment|other.
10) reminder is integer minutes. If missing, use 15.
11) If no time is provided: start_time=null, duration=null, all_day=true.
12) If end time is provided, compute duration from start_time.
13) If relative date and explicit date both appear, prefer explicit date and note conflict in notes.
14) If input is long/messy, set description to a clean summary no longer than 2000 characters, preserving key links with brief context.
15) Convert Chinese time phrases (上午/下午/晚上/中午/凌晨/早上) to 24h HH:MM.

Schema for each event:
{{
  "title": "string",
  "date": "YYYY-MM-DD",
  "start_time": "HH:MM or null",
  "duration": integer or null,
  "all_day": boolean,
  "timezone": "Olson tz",
  "location": "string or null",
  "description": "string or null",
  "participants": "string or null",
  "reminder": integer,
  "category": "work|personal|meeting|appointment|other",
  "repeat": "never|daily|weekly|biweekly|monthly|yearly",
  "notes": "string or null"
}}
"""


def parse_with_openai(text: str) -> dict:
    """
    使用 Google Generative AI (Gemini) 解析自然语言为结构化事件数据
    """
    if not settings.GOOGLE_GENERATIVE_AI_KEY:
        raise ValueError('GOOGLE_GENERATIVE_AI_KEY is not configured')

    try:
        # 配置 Google Generative AI
        genai.configure(api_key=settings.GOOGLE_GENERATIVE_AI_KEY)
        
        current_date = datetime.now().date().isoformat()
        default_tz = settings.TIME_ZONE or 'UTC'
        user_prompt = USER_PROMPT_TEMPLATE.format(
            current_date=current_date,
            default_tz=default_tz,
            user_text=_sanitize_user_text(text)
        )

        # 创建模型实例
        model = genai.GenerativeModel(
            model_name=settings.GOOGLE_GENERATIVE_AI_MODEL,
            system_instruction=SYSTEM_PROMPT
        )
        
        # 调用 API（对 429 做指数退避重试）
        max_attempts = 4
        base_delay = 0.6
        response = None
        for attempt in range(1, max_attempts + 1):
            try:
                response = model.generate_content(
                    user_prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.3,  # 降低温度以获得更一致的 JSON 输出
                    )
                )
                break
            except ResourceExhausted as exc:
                if attempt == max_attempts:
                    raise
                # 截断指数退避 + jitter
                sleep_for = min(6.0, base_delay * (2 ** (attempt - 1)))
                sleep_for += random.uniform(0, 0.4)
                logger.warning(f"Google AI rate limited (429). Retry {attempt}/{max_attempts-1} in {sleep_for:.2f}s")
                time.sleep(sleep_for)
        
        # 检查是否有有效的响应
        if not response or not response.text:
            logger.error(f"Google AI returned empty response")
            raise ValueError('Google AI returned empty response')
        
        # 提取响应文本
        content = response.text.strip()
        # Print full raw response to server console for debugging
        print("AI raw response:", content)
        logger.debug(f"Google AI raw response: {content[:200]}")
        
        # 尝试解析 JSON
        try:
            result = json.loads(content)
            return result
        except json.JSONDecodeError as e:
            # 如果直接解析失败，尝试提取 JSON 块
            logger.warning(f"Failed to parse as JSON, attempting to extract JSON block: {e}")
            
            # 查找JSON块 - 寻找第一个 { 到最后一个 }
            start_idx = content.find('{')
            if start_idx != -1:
                end_idx = content.rfind('}')
                if end_idx != -1:
                    json_str = content[start_idx:end_idx+1]
                    try:
                        result = json.loads(json_str)
                        return result
                    except json.JSONDecodeError:
                        pass
            
            logger.error(f"Google AI returned invalid JSON. Raw content: {content}")
            raise ValueError(f'Google AI returned invalid JSON: {str(e)}')
    
    except Exception as e:
        logger.error(f"Google AI API error: {e}")
        raise


def _sanitize_user_text(text: str) -> str:
    """
    Remove emojis/variation selectors and normalize whitespace to improve model stability.
    """
    if not text:
        return text
    # Remove emoji and non-BMP characters (common source of JSON issues)
    text = re.sub(r'[\U00010000-\U0010ffff]', '', text)
    # Remove common variation selectors and dingbats
    text = re.sub(r'[\uFE0F\uFE0E\u200D\u2060]', '', text)
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text

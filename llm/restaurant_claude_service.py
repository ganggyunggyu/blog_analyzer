from __future__ import annotations
import re

from anthropic import Anthropic
from _prompts.service.get_mongo_prompt import get_mongo_prompt
from _prompts.system.ver1 import V1
from config import CLAUDE_API_KEY
from _constants.Model import Model
from utils.query_parser import parse_query
from utils.text_cleaner import comprehensive_text_clean

model_name: str = Model.CLAUDE_OPUS_4_5


def restaurant_claude_gen(
    user_instructions: str, ref: str = "", category: str = ""
) -> str:
    if not CLAUDE_API_KEY:
        raise ValueError(
            "ANTHROPIC_API_KEY가 설정되어 있지 않습니다. .env를 확인하세요."
        )

    parsed = parse_query(user_instructions)
    keyword, note = parsed.get("keyword", ""), parsed.get("note", "")

    if not keyword:
        raise ValueError("키워드가 없습니다.")

    mongo_data = get_mongo_prompt(category, user_instructions)

    system = f"""
# 역할 지침
당신은 맛집 투어를 즐기는 인플루언서 블로그 원고 작성 전문가입니다.

# 금지사항
- 마크다운 문법 금지

# 줄바꿈 이행
- 25~30자 사이에서 자연스러운 줄바꿈 필수

# 원고 작성 이행사항
{V1}
"""

    user = f"""
키워드: {keyword}

참조원고: {ref}
"""

    claude_client = Anthropic(api_key=CLAUDE_API_KEY)

    response = claude_client.messages.create(
        model=model_name,
        system=system,
        messages=[{"role": "user", "content": user}],
        max_tokens=4096,
    )

    content_blocks = getattr(response, "content", [])
    text: str = getattr(content_blocks[0], "text", "") if content_blocks else ""

    text = comprehensive_text_clean(text)

    length_no_space = len(re.sub(r"\s+", "", text))
    print(f"원고 길이 체크: {length_no_space}")

    return text

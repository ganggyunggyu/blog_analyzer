"""GPT-4O 원고 생성 서비스"""

from __future__ import annotations

from _prompts.gpt4o.system import get_gpt4o_system_prompt
from _prompts.gpt4o.user import get_gpt4o_user_prompt

from _constants.Model import Model
from utils.query_parser import parse_query
from utils.text_cleaner import comprehensive_text_clean
from utils.ai_client_factory import call_ai


MODEL_NAME: str = Model.GPT4_1


def gpt4o_gen(user_instructions: str, ref: str = "", category: str = "") -> str:
    """
    GPT-4O 기반 블로그 원고 생성

    Args:
        user_instructions: 키워드 및 추가 요청사항
        ref: 참조 원고 (선택)
        category: 카테고리명 (선택)

    Returns:
        생성된 원고 텍스트
    """
    parsed = parse_query(user_instructions)
    keyword, note = parsed.get("keyword", ""), parsed.get("note", "") or ""

    if not keyword:
        raise ValueError("키워드가 없습니다.")

    system = get_gpt4o_system_prompt(
        keyword=keyword,
        category=category,
    )

    user = get_gpt4o_user_prompt(keyword=keyword, note=note, ref=ref)

    text = call_ai(
        model_name=MODEL_NAME,
        system_prompt=system,
        user_prompt=user,
    )

    text = comprehensive_text_clean(text)

    return text

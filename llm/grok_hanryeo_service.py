"""Grok 한려담원 서비스 - 기존 Grok 기반 + 한려담원 자연스러운 추천"""

from __future__ import annotations

from _prompts.grok_hanryeo.system import get_grok_hanryeo_system_prompt
from _prompts.grok_hanryeo.user import get_grok_hanryeo_user_prompt

from _constants.Model import Model
from utils.query_parser import parse_query
from utils.text_cleaner import comprehensive_text_clean
from utils.ai_client_factory import call_ai


MODEL_NAME: str = Model.GROK_4_NON_RES


def grok_hanryeo_gen(user_instructions: str, ref: str = "", category: str = "") -> str:
    """Grok 한려담원 원고 생성"""
    parsed = parse_query(user_instructions)
    keyword, note = parsed.get("keyword", ""), parsed.get("note", "") or ""

    if not keyword:
        raise ValueError("키워드가 없습니다.")

    system = get_grok_hanryeo_system_prompt(
        keyword=keyword,
        category=category,
    )

    user = get_grok_hanryeo_user_prompt(keyword=keyword, note=note, ref=ref)

    text = call_ai(
        model_name=MODEL_NAME,
        system_prompt=system,
        user_prompt=user,
    )

    text = comprehensive_text_clean(text)

    return text

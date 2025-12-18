from __future__ import annotations
import re

from _prompts.service.get_mongo_prompt import get_mongo_prompt
from _prompts.service.get_category_tone_rules import get_category_tone_rules
from _prompts.gemini.system import get_gemini_system_prompt
from _prompts.gemini.user import get_gemini_user_prompt

from _constants.Model import Model
from utils import natural_break_text
from utils.query_parser import parse_query
from utils.text_cleaner import comprehensive_text_clean
from utils.ai_client_factory import call_ai


MODEL_NAME: str = Model.GEMINI_3_FLASH


def gemini_gen(user_instructions: str, ref: str = "", category: str = "") -> str:
    parsed = parse_query(user_instructions)
    keyword = parsed.get("keyword", "")
    note = parsed.get("note", "") or ""

    if not keyword:
        raise ValueError("키워드가 없습니다.")

    mongo_data = get_mongo_prompt(category, user_instructions)
    category_tone_rules = get_category_tone_rules(category)

    system_prompt = get_gemini_system_prompt(
        keyword=keyword,
        category=category,
        mongo_data=mongo_data,
        category_tone_rules=category_tone_rules,
    )

    user_prompt = get_gemini_user_prompt(
        keyword=keyword,
        note=note,
        ref=ref,
    )

    generated_text = call_ai(
        model_name=MODEL_NAME,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
    )

    cleaned_text = comprehensive_text_clean(generated_text)

    if category == "맛집":
        cleaned_text = natural_break_text.natural_break_text(cleaned_text)

    char_count_no_space = len(re.sub(r"\s+", "", cleaned_text))
    print(f"원고 길이 체크: {char_count_no_space}")

    return cleaned_text

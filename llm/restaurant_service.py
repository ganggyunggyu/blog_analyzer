from __future__ import annotations
import re

from _prompts.service.get_mongo_prompt import get_mongo_prompt
from _prompts.system.restaurant_system import get_restaurant_system_prompt
from _prompts.user.restaurant_user import get_restaurant_user_prompt

from _constants.Model import Model
from utils.query_parser import parse_query
from utils.text_cleaner import comprehensive_text_clean
from utils.ai_client_factory import call_ai


MODEL_NAME: str = Model.GEMINI_3_PRO


def restaurant_gen(user_instructions: str, ref: str = "", category: str = "") -> str:
    parsed = parse_query(user_instructions)
    keyword = parsed.get("keyword", "")

    if not keyword:
        raise ValueError("키워드가 없습니다.")

    mongo_data = get_mongo_prompt(category, user_instructions)

    system_prompt = get_restaurant_system_prompt(
        user_instructions=user_instructions,
        mongo_data=mongo_data,
    )

    user_prompt = get_restaurant_user_prompt()

    generated_text = call_ai(
        model_name=MODEL_NAME,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
    )

    cleaned_text = comprehensive_text_clean(generated_text)

    char_count_no_space = len(re.sub(r"\s+", "", cleaned_text))
    print(f"원고 길이 체크: {char_count_no_space}")

    return cleaned_text

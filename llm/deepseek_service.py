from __future__ import annotations
import re

from _prompts.service.get_mongo_prompt import get_mongo_prompt
from _prompts.service.get_category_tone_rules import get_category_tone_rules
from _prompts.rules.output_rule import get_output_rule
from _prompts.deepseek.system import get_deepseek_system_prompt
from _prompts.deepseek.user import get_deepseek_user_prompt

from _constants.Model import Model
from utils.query_parser import parse_query
from utils.text_cleaner import comprehensive_text_clean
from utils.ai_client_factory import call_ai


MODEL_NAME: str = Model.DEEPSEEK_RES


def deepseek_gen(user_instructions: str, ref: str = "", category: str = "") -> str:
    parsed = parse_query(user_instructions)
    keyword, note = parsed.get("keyword", ""), parsed.get("note", "") or ""

    if not keyword:
        raise ValueError("키워드가 없습니다.")

    mongo_data = get_mongo_prompt(category, user_instructions)
    category_tone_rules = get_category_tone_rules(category)
    output_rule = get_output_rule(category)

    system = get_deepseek_system_prompt(
        keyword=keyword,
        category=category,
        mongo_data=mongo_data,
        category_tone_rules=category_tone_rules,
        output_rule=output_rule,
    )

    user = get_deepseek_user_prompt(keyword=keyword, note=note, ref=ref)

    print(f"서비스: {category}")
    print(f"키워드: {keyword}")
    print("원고작성 시작")

    text = call_ai(
        model_name=MODEL_NAME,
        system_prompt=system,
        user_prompt=user,
    )

    text = comprehensive_text_clean(text)
    length_no_space = len(re.sub(r"\s+", "", text))
    print(f"원고 길이 체크: {length_no_space}")
    print("원고작성 완료")

    return text

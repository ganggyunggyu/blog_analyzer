"""맛집 DeepSeek 서비스 - DeepSeek 전용 프롬프트 사용"""

from __future__ import annotations
import re
import time

from _prompts.service.get_mongo_prompt import get_mongo_prompt
from _prompts.service.get_category_tone_rules import get_category_tone_rules
from _prompts.rules.output_rule import get_output_rule
from _prompts.deepseek.system import get_deepseek_system_prompt
from _prompts.deepseek.user import get_deepseek_user_prompt

from _constants.Model import Model
from utils.query_parser import parse_query
from utils.text_cleaner import comprehensive_text_clean
from utils.ai_client_factory import call_ai


MODEL_NAME: str = Model.DEEPSEEK_CHAT


def restaurant_deepseek_gen(
    user_instructions: str, ref: str = "", category: str = "맛집"
) -> str:
    """맛집 전용 DeepSeek 생성 (DeepSeek 전용 프롬프트 사용)"""
    parsed = parse_query(user_instructions)
    keyword = parsed.get("keyword", "")
    note = parsed.get("note", "") or ""

    if not keyword:
        raise ValueError("키워드가 없습니다.")

    mongo_data = get_mongo_prompt(category, user_instructions)
    category_tone_rules = get_category_tone_rules(category)
    output_rule = get_output_rule(category)

    system_prompt = get_deepseek_system_prompt(
        keyword=keyword,
        category=category,
        mongo_data=mongo_data,
        category_tone_rules=category_tone_rules,
        output_rule=output_rule,
    )

    user_prompt = get_deepseek_user_prompt(
        keyword=keyword,
        note=note,
        ref=ref,
    )

    try:
        start_time = time.time()
        print(f"[Restaurant DeepSeek] 서비스: {category}")
        print(f"[Restaurant DeepSeek] 키워드: {keyword}")
        print("[Restaurant DeepSeek] 원고작성 시작")

        generated_text = call_ai(
            model_name=MODEL_NAME,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

        cleaned_text = comprehensive_text_clean(generated_text)

        char_count_no_space = len(re.sub(r"\s+", "", cleaned_text))
        elapsed_time = time.time() - start_time

        print(f"[Restaurant DeepSeek] 원고 길이: {char_count_no_space}")
        print(f"[Restaurant DeepSeek] 소요시간: {elapsed_time:.2f}s")
        print("[Restaurant DeepSeek] 완료")

        return cleaned_text

    except Exception as api_error:
        print(f"[Restaurant DeepSeek] API 오류: {api_error}")
        raise api_error

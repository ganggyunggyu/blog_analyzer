from __future__ import annotations
import re
import time

from anthropic._exceptions import BadRequestError, RateLimitError

from _prompts.service.get_mongo_prompt import get_mongo_prompt
from _prompts.system.claude_system import get_claude_system_prompt
from _prompts.user.claude_user import get_claude_user_prompt

from _constants.Model import Model
from utils.query_parser import parse_query
from utils.text_cleaner import comprehensive_text_clean
from utils.ai_client_factory import call_ai


MODEL_NAME: str = Model.CLAUDE_OPUS_4_5


def claude_gen(user_instructions: str, ref: str = "", category: str = "") -> str:
    parsed = parse_query(user_instructions)
    keyword = parsed.get("keyword", "")
    note = parsed.get("note", "") or ""

    if not keyword:
        raise ValueError("키워드가 없습니다.")

    system_prompt = get_claude_system_prompt(
        category=category,
        mongo_data="",
    )

    user_prompt = get_claude_user_prompt(
        keyword=keyword,
        note=note,
        ref=ref,
    )

    try:
        start_time = time.time()
        print(f"서비스: {category}")
        print(f"키워드: {keyword}")
        print("원고작성 시작")

        generated_text = call_ai(
            model_name=MODEL_NAME,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

        cleaned_text = comprehensive_text_clean(generated_text)

        char_count_no_space = len(re.sub(r"\s+", "", cleaned_text))
        elapsed_time = time.time() - start_time

        print(f"원고 길이 체크: {char_count_no_space}")
        print(f"원고 소요시간: {elapsed_time:.2f}s")
        print("원고작성 완료")

        return cleaned_text

    except (BadRequestError, RateLimitError) as api_error:
        print(f"Claude API 오류: {api_error}")
        raise api_error

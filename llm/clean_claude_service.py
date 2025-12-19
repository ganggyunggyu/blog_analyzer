"""프롬프트 없는 Clean Claude 서비스"""

from __future__ import annotations
import re
import time

from anthropic._exceptions import BadRequestError, RateLimitError

from _constants.Model import Model
from utils.query_parser import parse_query
from utils.text_cleaner import comprehensive_text_clean
from utils.ai_client_factory import call_ai


MODEL_NAME: str = Model.CLAUDE_OPUS_4_5


def clean_claude_gen(user_instructions: str, ref: str = "", category: str = "") -> str:
    """프롬프트 없이 유저 입력만으로 생성"""
    parsed = parse_query(user_instructions)
    keyword = parsed.get("keyword", "")
    note = parsed.get("note", "") or ""

    if not keyword:
        raise ValueError("키워드가 없습니다.")

    # 시스템 프롬프트 없음 (빈 문자열)
    system_prompt = ""

    # 유저 프롬프트 = 키워드 + 노트 + 참조원고만
    user_prompt = f"""
키워드: {keyword}

추가 요청: {note}

참조 원고: {ref}
""".strip()

    try:
        start_time = time.time()




        generated_text = call_ai(
            model_name=MODEL_NAME,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

        cleaned_text = comprehensive_text_clean(generated_text)

        char_count_no_space = len(re.sub(r"\s+", "", cleaned_text))
        elapsed_time = time.time() - start_time





        return cleaned_text

    except (BadRequestError, RateLimitError) as api_error:
        print(f"[Clean Claude] API 오류: {api_error}")
        raise api_error

"""GPT CEO - GPT 5.2 + CEO 프롬프트 원고 생성 서비스"""

from __future__ import annotations
import re
import time

from _prompts.ceo.ceo_prompt import get_ceo_system_prompt, get_ceo_user_prompt
from _constants.Model import Model
from utils.query_parser import parse_query
from utils.text_cleaner import comprehensive_text_clean
from utils.ai_client_factory import call_ai


MODEL_NAME: str = Model.GPT5_2


def gpt_ceo_gen(user_instructions: str, ref: str = "", category: str = "") -> str:
    """GPT 5.2 + CEO 프롬프트를 사용한 원고 생성"""

    parsed = parse_query(user_instructions)
    keyword = parsed.get("keyword", "")
    note = parsed.get("note", "") or ""

    if not keyword:
        raise ValueError("키워드가 없습니다.")

    system = get_ceo_system_prompt()
    user = get_ceo_user_prompt(keyword=keyword, note=note, ref=ref)

    start_ts = time.time()

    text = call_ai(
        model_name=MODEL_NAME,
        system_prompt=system,
        user_prompt=user,
    )

    text = comprehensive_text_clean(text)

    length_no_space = len(re.sub(r"\s+", "", text))
    elapsed = time.time() - start_ts

    print(f"[GPT-CEO] 생성완료 | {length_no_space}자 | {elapsed:.2f}s")

    return text

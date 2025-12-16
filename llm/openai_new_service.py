"""OpenAI New - 범용 정보성 원고 생성 서비스 (GPT-5.2 Responses API)"""

from __future__ import annotations
import re
import time

from openai import OpenAI

from _prompts.system.universal_info_system import get_universal_info_system_prompt
from _constants.Model import Model
from config import OPENAI_API_KEY
from utils.query_parser import parse_query
from utils.text_cleaner import comprehensive_text_clean


MODEL_NAME: str = Model.GPT5_2


def openai_new_gen(user_instructions: str, ref: str = "", category: str = "") -> str:
    """GPT-5.2 Responses API를 사용한 범용 정보성 원고 생성"""

    parsed = parse_query(user_instructions)
    keyword = parsed.get("keyword", "")
    note = parsed.get("note", "") or ""

    if not keyword:
        raise ValueError("키워드가 없습니다.")

    system = get_universal_info_system_prompt()

    user = f"""
주제: {keyword}

카테고리: {category if category else "기타"}

추가 요청사항: {note if note else "없음"}

참조 문서: {ref if ref else "없음"}

키워드에 맞춰 신뢰도 높고, 질의에 적합하게, 공신력, 공식성, 전문성 높은 정보성 원고를 만들어줘 면책사항 이런거 넣지마 가독성 좋게 정보:OOOO 이런식으로 정보를 알아보기 쉽게 SEO 최적화 한다고 생각하고 부제 이런것도 앞에 1. 2.3. 이런거넣고 자연스럽게 문단정리 잘해줘야함 무조건!
한줄로 길게 적지말고
한줄당 40~50자 정도로 끊어서 문단정리 예쁘게
모바일로 봤을때 보기좋게
부제 4-1 4-2 이런건 넣지마
마크다운 문법 사용 금지
부제는 7개로 제한해줘
""".strip()

    client = OpenAI(api_key=OPENAI_API_KEY)

    print(f"서비스: {category}")
    print(f"키워드: {keyword}")
    print("원고작성 시작")

    start_ts = time.time()

    response = client.responses.create(
        model=MODEL_NAME,
        instructions=system,
        input=user,
        reasoning={"effort": "medium"},
        text={"verbosity": "high"},
    )

    text: str = getattr(response, "output_text", "") or ""
    if not text:
        raise RuntimeError("모델이 빈 응답을 반환했습니다.")

    text = comprehensive_text_clean(text)

    length_no_space = len(re.sub(r"\s+", "", text))
    elapsed = time.time() - start_ts

    print(f"원고 길이 체크: {length_no_space}")
    print(f"원고 소요시간: {elapsed:.2f}s")
    print("원고작성 완료")

    return text

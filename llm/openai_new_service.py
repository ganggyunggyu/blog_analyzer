"""OpenAI New - 범용 정보성 원고 생성 서비스 (GPT-4o)"""

from __future__ import annotations
import re
import time

from _prompts.system.universal_info_system import get_universal_info_system_prompt
from _constants.Model import Model
from utils.query_parser import parse_query
from utils.text_cleaner import comprehensive_text_clean
from utils.ai_client_factory import call_ai


MODEL_NAME: str = Model.GPT5_2


def openai_new_gen(user_instructions: str, ref: str = "", category: str = "") -> str:
    """GPT-4o를 사용한 범용 정보성 원고 생성"""

    parsed = parse_query(user_instructions)
    keyword = parsed.get("keyword", "")
    note = parsed.get("note", "") or ""

    if not keyword:
        raise ValueError("키워드가 없습니다.")

    system = get_universal_info_system_prompt()

    user = f"""
[INPUT]
topic: {keyword}
category: {category}
additional_request: {note if note else "없음"}
reference: {ref if ref else "없음"}

[TASK]
위 주제에 대해 신뢰도 높은 정보성 블로그 원고를 작성하세요.
공신력, 공식성, 전문성을 갖춘 콘텐츠로, SEO 최적화를 고려해 작성합니다.

[STRUCTURE]
- 부제 개수: 정확히 5개
- 부제 형식: "1. 제목", "2. 제목" (숫자+마침표+공백+제목)
- 금지 형식: "4-1", "4-2" 같은 하위 번호 사용 금지

[FORMAT]
- 한 줄당 40~50자로 끊어서 작성
- 모바일 화면에서 읽기 편하게 문단 정리
- 마크다운 문법 사용 금지
- 순수 텍스트로만 출력

[CONSTRAINTS]
- 글자수: 한글 기준 공백 제외 2000자 이상 2200자 이하
- 면책조항, 광고성 문구 삽입 금지
- 정보 나열 시 자연스러운 문장으로 서술 (키:밸류 형식 사용 가능하되 남발 금지)
""".strip()

    print(f"서비스: {category}")
    print(f"키워드: {keyword}")
    print("원고작성 시작")

    start_ts = time.time()

    text = call_ai(
        model_name=MODEL_NAME,
        system_prompt=system,
        user_prompt=user,
    )

    if not text:
        raise RuntimeError("모델이 빈 응답을 반환했습니다.")

    text = comprehensive_text_clean(text)

    length_no_space = len(re.sub(r"\s+", "", text))
    elapsed = time.time() - start_ts

    print(f"원고 길이 체크: {length_no_space}")
    print(f"원고 소요시간: {elapsed:.2f}s")
    print("원고작성 완료")

    return text

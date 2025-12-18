"""Grok New - 범용 정보성 원고 생성 서비스"""

from __future__ import annotations
import re
import time

from _prompts.grok.info_system import get_grok_info_system_prompt
from _constants.Model import Model
from utils.query_parser import parse_query
from utils.text_cleaner import comprehensive_text_clean
from utils.ai_client_factory import call_ai


MODEL_NAME: str = Model.GROK_4_NON_RES


def grok_new_gen(user_instructions: str, ref: str = "", category: str = "") -> str:
    """Grok을 사용한 범용 정보성 원고 생성"""

    parsed = parse_query(user_instructions)
    keyword = parsed.get("keyword", "")
    note = parsed.get("note", "") or ""

    if not keyword:
        raise ValueError("키워드가 없습니다.")

    system = get_grok_info_system_prompt()

    user = f"""
<topic>{keyword}</topic>
<category>{category if category else "기타"}</category>
<additional_request>{note if note else "없음"}</additional_request>
<reference>{ref if ref else "없음"}</reference>

<task>
위 주제에 대해 전문적이고 신뢰도 높은 정보성 블로그 원고를 작성하세요.
</task>

<requirements>
1. 분량: 최소 2,500단어 이상
2. 톤앤매너: 공신력 있고 전문적인 정보 전달 (면책조항, 광고성 문구 금지)
3. SEO 최적화: 키워드 자연스럽게 배치
</requirements>

<structure>
1. 부제(소제목) 개수: 5~7개
2. 부제 형식: "1. 제목", "2. 제목" (숫자+마침표+공백+제목)
3. 금지 형식: "4-1", "4-2" 같은 하위 번호 사용 금지
</structure>

<formatting>
1. 한 줄당 20~30자로 끊어서 작성
2. 긴 문장은 여러 줄로 나누어 가독성 확보
3. 모바일 화면에서 읽기 편하게 문단 정리
4. 마크다운 문법(#, *, **, ```) 사용 금지
5. 순수 텍스트로만 작성
</formatting>

<output_example>
1. 첫 번째 부제 예시

본문 내용을 이렇게
20~30자 단위로 끊어서
가독성 좋게 작성합니다.

2. 두 번째 부제 예시

정보를 명확하게 전달하되
전문성을 유지하면서
쉽게 읽히도록 작성합니다.
</output_example>
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

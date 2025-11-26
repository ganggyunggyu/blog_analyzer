from __future__ import annotations
import re
import time

from anthropic import Anthropic
from anthropic._exceptions import BadRequestError, RateLimitError
from _prompts.service.get_mongo_prompt import get_mongo_prompt
from _prompts.system.ver1 import V1
from config import CLAUDE_API_KEY
from _constants.Model import Model
from utils.query_parser import parse_query
from utils.text_cleaner import comprehensive_text_clean


model_name: str = Model.CLAUDE_OPUS_4_5


def claude_gen(user_instructions: str, ref: str = "", category: str = "") -> str:
    if not CLAUDE_API_KEY:
        raise ValueError(
            "ANTHROPIC_API_KEY가 설정되어 있지 않습니다. .env를 확인하세요."
        )

    parsed = parse_query(user_instructions)
    keyword, note = parsed.get("keyword", ""), parsed.get("note", "")

    if not keyword:
        raise ValueError("키워드가 없습니다.")

    target_chars_min, target_chars_max = 1800, 2000

    mongo_data = get_mongo_prompt(category, user_instructions)

    output_structure = f"""
<output_structure>
<sub_title>
소제목은 핵심만 간결히 작성

위고비란?

위고비 처방 과정
위고비 가격 정리

이런 형식으로
</sub_title>
  <format>
    <structure>
      제목 (5-10자, 제목에는 쉼표(,)를 넣지 않음, **동일한** 제목 4개 반복 출력, 메인 키워드 관련 서브 키워드를 이용하여 제작)


      1. 첫 번째 소제목


      본문 (300-400자)

      2. 두 번째 소제목


      본문 (400-500자)

      3. 세 번째 소제목


      본문 (400-500자)

      4. 네 번째 소제목


      본문 (500-600자)

      5. 다섯 번째 소제목


      본문 (250-300자)

      (2-3문장, 자연스러운 마무리 멘트)
    </structure>
    - structure 명시 된 구조 외에 다른 텍스트 출력 금지
    - 줄바꿈까지 참고하여 출력할 것
    - 글자수 피드백 표시 금지 원고 내용만 출력
    - 부제 넘버링은 필수
    - 제목 네번 반복은 동일한 제목 하나로만 반복
  </format>

  <critical_restrictions>
    <!-- 절대 규칙: 다음 형식은 사용 금지 -->
    <forbidden_formatting>
      - 마크다운 문법: # * - ** __ ~~ []() ``` -
      - HTML 태그: <p> <br> <div> <a> <img> <h1-h6>
      - URL: http:// https:// www. .com .co.kr
      - 따옴표: " ' ` " " ' '
      - 특수문자: · • ◦ ▪ → ※ .
      - 괄호: [] <> {{}} 〈〉 【】
      - 메타 표현: 맺음말, 서론, 도입부
      - 체크리스트
      - 글자 수 피드백 금지


      - 예외 사항: 소제목에서 숫자 다음에 . (마침표)만 허용
    </forbidden_formatting>

  </critical_restrictions>
</output_structure>
""".strip()

    length_constraints = f"""
<length_constraints>
  <target min="{target_chars_min}" max="{target_chars_max}" unit="chars_no_space"/>
  <tolerance>±100자</tolerance>
</length_constraints>"""

    task_definition = f"""
<task_definition>
  <requirements>
    - 키워드: {keyword}
    - 카테고리: {category}

    - 키워드가 3단어 이상이면 유저가 지정한 제목입니다.
  </requirements>

  <primary_objectives priority="descending">
    1. 자연스러운 독자 경험 (부자연스러운 키워드 삽입 금지)
    2. SEO 최적화
    3. 5개 소제목 구조 준수
    4. 공백 제외 길이 요구사항 충족: {length_constraints}
    5. 카테고리 톤 일치
    6. 한 줄당 30~40자로 제한 모바일 가독성을 위한 자연스러운 줄바꿈
  </primary_objectives>

  <conflict_resolution>
    만약 "자연스러움"과 "키워드 최적화"가 충돌한다면:
    - 항상 자연스러움을 우선시하세요
    - 키워드는 문맥에 자연스럽게 녹아들 때만 사용
    - 억지로 키워드를 넣어 품질을 해치지 마세요
  </conflict_resolution>
</task_definition>

<writing_approach>
  <execution_style>
    실제 경험 많은 블로거처럼 작성하세요:
    - AI 티를 완전히 제거
    - 진정성 있는 개인적 톤
    - 자연스러운 스토리텔링
    - 독자와의 대화하듯이
  </execution_style>

  <seo_integration>
    SEO는 눈에 보이지 않게 통합:
    - 키워드를 자연스러운 문맥에서만 사용
    - 제목과 소제목에 자연스럽게 포함
    - 독자 경험을 해치지 않는 선에서 최적화
  </seo_integration>

  <structure_flow>
    라벨 없이 자연스럽게 전개:
    - 도입: 독자의 호기심 유발, 공감대 형성
    - 본문: 5개 소제목으로 정보 전달 (각 섹션은 줄바꿈으로만 구분)
    - 맺음: 자연스럽게 마무리 (라벨 없이)
  </structure_flow>
</writing_approach>
"""

    system = f"""
원고 작성 지침
{V1}

참고할 데이터
{mongo_data}

"""

    user = f"""
    키워드: {keyword}

    추가 요청: {note}

    참조 원고: {ref}
    """

    claude_client = Anthropic(api_key=CLAUDE_API_KEY)

    try:
        start_ts = time.time()
        print(f"서비스: {category}")
        print(f"키워드: {keyword}")
        print("원고작성 시작")

        response = claude_client.messages.create(
            model=model_name,
            system=system,
            messages=[{"role": "user", "content": user}],
            max_tokens=4096,
        )

        content_blocks = getattr(response, "content", [])
        text: str = getattr(content_blocks[0], "text", "") if content_blocks else ""

        text = comprehensive_text_clean(text)

        length_no_space = len(re.sub(r"\s+", "", text))
        elapsed = time.time() - start_ts

        print(f"원고 길이 체크: {length_no_space}")
        print(f"원고 소요시간: {elapsed:.2f}s")
        print("원고작성 완료")

        return text

    except (BadRequestError, RateLimitError) as e:
        print(f"Claude API 오류: {e}")
        raise e

from __future__ import annotations

import os
import re
import time

from openai import OpenAI
from _prompts import get_kkk_prompts
from _prompts.service.get_mongo_prompt import get_mongo_prompt
from config import OPENAI_API_KEY
from _constants.Model import Model
from mongodb_service import MongoDBService
from _prompts.get_gpt_prompt import GptPrompt
from _prompts.get_kkk_prompts import KkkPrompt
from _prompts.get_system_prompt import get_system_prompt_v2
from utils.format_paragraphs import format_paragraphs
from utils.get_category_db_name import get_category_db_name
from utils.query_parser import parse_query

from analyzer.request_문장해체분석기 import get_문장해체
from utils.text_cleaner import comprehensive_text_clean


model_name: str = Model.GPT5_1

기본_프롬프트 = ""


async def gpt_5_gen(
    user_instructions: str,
    ref: str = "",
) -> str:
    """
    분석 산출물 + 사용자 지시 → 원고 텍스트를 생성한다.
    - MongoDB의 최신 분석 결과(expressions/parameters)를 읽어 프롬프트에 포함.
    - OpenAI Chat Completions 호출.
    - 기존 출력 포맷과 흐름 유지, 타입/널 안전성 강화.

    Returns:
        생성된 원고 텍스트 (str)

    Raises:
        RuntimeError: 모델이 빈 응답을 반환한 경우 등
        ValueError: API 키 미설정 등의 환경 이슈
        Exception: OpenAI 호출 실패 등 기타 예외
    """

    category = ""
    if user_instructions:
        category = await get_category_db_name(user_instructions)

    if not category:
        category = os.getenv("MONGO_DB_NAME", "wedding")

    db_service = MongoDBService()

    db_service.set_db_name(db_name=category)

    parsed = parse_query(user_instructions)

    if parsed["keyword"] == None:
        raise

    참조분석 = get_문장해체(ref)

    min_length: int
    max_length: int
    if model_name == Model.GPT5:
        min_length, max_length = 1600, 2300
    elif model_name == Model.GPT5_CHAT:
        min_length, max_length = 2800, 3000
    else:
        min_length, max_length = 2800, 3000

    기본_프롬프트 = KkkPrompt.kkk_prompt_gpt_5(
        min_length, max_length, parsed["keyword"]
    )

    def sanitize(s: str) -> str:
        s = s or ""
        s = re.sub(
            r"(?i)ignore previous|override|system message|do not obey|follow only.*",
            "",
            s,
        )
        s = re.sub(r"```.*?```", "", s, flags=re.S)
        return s.strip()

    _mongo_data = sanitize(get_mongo_prompt(category, user_instructions))

    참조_분석_프롬프트 = f"""
[참조원고 분석 데이터 활용 지침]
아래 데이터는 참고 문서에서 추출한 화자/구성/스타일 분석 결과물입니다.  
원고 생성 시 반드시 다음 조건을 반영해야 합니다.
    

{참조분석}

- "화자 지시"에 따른 인물 설정, 말투, 단어 빈도와 형태소 패턴을 살짝 변형하여 글의 형태만을 따릅니다.  
- "구성 지시"에 따라 서론-중론-결론 흐름을 유지합니다.
- "원고 스타일 세부사항"을 전부 반영해 문체·문단 길이·리듬감·감정선 등을 동일하게 재현합니다.  
- JSON에 기재된 단어/형태소는 반복적으로 등장해야 하며, 실제 경험담+정보 설명이 혼합된 톤을 유지해야 합니다.  

- 부제는 그대로 사용하나 예외 사항은 하단 참조
- 사용자 요청에 (부제X)가 있다면 필수로 숫자만 제거 된 부제 사용
- 형태소의 개수를 참고하여 작업 필수

"""

    user: str = (
        f"""

---

{_mongo_data}

---

[참조 문서]
- 참조 문서와 동일하게 작성하지 않습니다.
- 아래의 분석본과 함께 사용해서 전체적인 흐름을 유사하게 가져갑니다.

카테고리가 호텔이거나 맛집이라면:
    참조문서에 나와있는 사항들이 어떠한 업체에 대한 설명이라면 원고에 자연스럽게 녹아냅니다 (메뉴 업체명 주소 등 모두 포함 가능)
    업체의 요구사항이니 모두 포함시켜야합니다
{ref}


---

[필수 사항]
{기본_프롬프트}

---

[필수로 이행해야하는 추가 요청]
{parsed['note']}

---

""".strip()
    )

    client = OpenAI(api_key=OPENAI_API_KEY)

    system = get_kkk_prompts.KkkPrompt.get_kkk_system_prompt_v2()

    try:
        start_ts = time.time()
        print("원고작성 시작")
        response = client.responses.create(
            model=model_name,
            instructions=system,
            input=user,
            reasoning={"effort": "medium"},  # minimal, low, medium, high
            text={"verbosity": "high"},  # low, medium, high
        )

        text: str = getattr(response, "output_text", "") or ""
        if not text:
            raise RuntimeError("모델이 빈 응답을 반환했습니다.")

        length_no_space = len(re.sub(r"\s+", "", text))
        print(f"원고 길이 체크: {length_no_space}")

        print("원고작성 완료")
        if model_name != Model.GPT5:
            print(f"{parsed['keyword']} 원고 문단정리 시작")
            text = format_paragraphs(text)

        text = comprehensive_text_clean(text)
        elapsed = time.time() - start_ts
        print(f"원고 소요시간: {elapsed:.2f}s")

        return text

    except Exception as e:
        raise

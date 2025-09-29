from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List, Optional
import time

from openai import OpenAI
from config import OPENAI_API_KEY
from _constants.Model import Model
from mongodb_service import MongoDBService
from _prompts.get_gpt_prompt import GptPrompt
from _prompts.get_kkk_prompts import KkkPrompt
from _prompts.get_system_prompt import get_system_prompt_v2
from utils.format_paragraphs import format_paragraphs
from utils.get_category_db_name import get_category_db_name_sync
from utils.query_parser import parse_query

from config import MONGO_DB_NAME
from analyzer.request_문장해체분석기 import get_문장해체


model_name: str = Model.GPT4_1
기본_프롬프트 = ""


def gpt_4_v2_gen(
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

    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY가 설정되어 있지 않습니다. .env를 확인하세요.")

    parsed = parse_query(user_instructions)

    문장해체 = get_문장해체(ref)
    # 문장해체 = ''

    if not parsed["keyword"]:
        raise

    category = ""
    if user_instructions:
        category = get_category_db_name_sync(user_instructions)

    if not category:
        category = os.getenv("MONGO_DB_NAME", "wedding")

    if category == "legalese":
        기본_프롬프트 = KkkPrompt.kkk_prompt_gpt_5(parsed["keyword"])
    else:
        기본_프롬프트 = GptPrompt.gpt_4_v2(parsed["keyword"])

    참조분석 = get_문장해체(ref)
    system = get_system_prompt_v2()

    db_service = MongoDBService()

    db_service.set_db_name(db_name=category)

    analysis_data: Dict[str, Any] = db_service.get_latest_analysis_data() or {}

    unique_words: List[str] = analysis_data.get("unique_words", []) or []
    sentences: List[str] = analysis_data.get("sentences", []) or []

    subtitles: List[str] = analysis_data.get("subtitles", []) or []
    expressions: Dict[str, List[str]] = analysis_data.get("expressions", {}) or {}
    parameters: Dict[str, List[str]] = analysis_data.get("parameters", {}) or {}
    templates = analysis_data.get("templates", []) or []

    subtitles_str: str = (
        json.dumps(subtitles, ensure_ascii=False, indent=2) if expressions else "없음"
    )
    expressions_str: str = (
        json.dumps(expressions, ensure_ascii=False, indent=2) if expressions else "없음"
    )
    parameters_str: str = (
        json.dumps(parameters, ensure_ascii=False, indent=2) if parameters else "없음"
    )
    templates_str = (
        json.dumps(templates, ensure_ascii=False, indent=2) if templates else "없음"
    )

    # 디버그 출력 제거

    참조_분석_프롬프트 = f"""

[분석 지시]
아래는 분석 결과 JSON입니다.  

{문장해체}

위 부제를 사용해야해
"""

    _mongo_data = f"""

---

[분석 지시]
아래 JSON 데이터는 참고 문서에서 추출한 화자/구성/스타일 분석 결과물입니다.  
원고 생성 시 반드시 다음 조건을 반영해야 합니다.  

- "화자 지시"에 따른 인물 설정, 말투, 단어 빈도와 형태소 패턴을 그대로 따릅니다.  
- "구성 지시"에 따라 서론-중론-결론 흐름을 유지합니다.  
- "원고 스타일 세부사항"을 전부 반영해 문체·문단 길이·리듬감·감정선 등을 동일하게 재현합니다.  
- JSON에 기재된 단어/형태소는 반복적으로 등장해야 하며, 실제 경험담+정보 설명이 혼합된 톤을 유지해야 합니다.  

= 부제는 하단 데이터를 이용하여 작성

아래는 분석 결과 JSON입니다.  

{참조_분석_프롬프트}

---

[템플릿 예시]
- 출력 문서는 반드시 템플릿과 **유사한 어휘, 문장 구조, 문단 흐름**을 유지해야 한다.  
- 새로운 주제로 변형하더라도 템플릿의 **톤, 반복 구조, 문장 길이, 순서**를 그대로 모방해야 한다.  
- 예시와 다른 어휘·문장 구조를 사용하지 말고, 가능한 한 **템플릿의 스타일을 복제**하라.  

{templates_str}

[작성 지침]  
사용자가 입력한 주제를 기반으로 위 템플릿과 동일한 스타일로 결과를 작성하라.

---

[표현 라이브러리]
{expressions_str}

---

[AI 개체 인식 및 그룹화 결과]
{parameters_str}

---
"""

    user: str = (
        f"""
    {기본_프롬프트}

    {system}

    {_mongo_data}
        
---

[참조 문서]
- 참조 문서의 업체명은 절대 원고에 포함하지 않습니다.
- 참조 문서와 동일하게 작성하지 않습니다.
- 아래의 분석본과 함께 사용해서 전체적인 흐름을 유사하게 가져갑니다.
- 없다면 넘어갑니다.
{ref}

[참조 원고 분석]
{참조_분석_프롬프트}

---

[필수 사항]
{기본_프롬프트}

---

[필수로 이행해야하는 추가 요청]
{parsed['note']}

---

""".strip()
    )
    # 디버그 출력 제거

    client = OpenAI(api_key=OPENAI_API_KEY)

    try:
        start_ts = time.time()
        print("원고작성 시작")
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "system",
                    "content": system,
                },
                {"role": "user", "content": user},
            ],
        )

        usage = getattr(response, "usage", None)
        if usage is not None:
            in_tokens = getattr(usage, "prompt_tokens", None)
            out_tokens = getattr(usage, "completion_tokens", None)
            total_tokens = getattr(usage, "total_tokens", None)
            # 토큰 사용량 로깅 제거

        choices = getattr(response, "choices", []) or []
        if not choices or not getattr(choices[0], "message", None):
            raise RuntimeError("모델이 유효한 choices/message를 반환하지 않았습니다.")

        text: str = (choices[0].message.content or "").strip()
        if not text:
            raise RuntimeError("모델이 빈 응답을 반환했습니다.")

        length_no_space = len(re.sub(r"\s+", "", text))
        print(f"원고 길이 체크: {length_no_space}")
        elapsed = time.time() - start_ts
        print(f"원고 소요시간: {elapsed:.2f}s")
        print("원고작성 완료")
        text = format_paragraphs(text)
        return text

    except Exception as e:
        raise

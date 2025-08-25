from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List, Optional

from openai import OpenAI
from config import OPENAI_API_KEY
from constants.Model import Model
from mongodb_service import MongoDBService
from prompts.get_gpt_prompt import GptPrompt
from utils.categorize_keyword_with_ai import categorize_keyword_with_ai
from utils.query_parser import parse_query

from config import MONGO_DB_NAME
from analyzer.request_문장해체분석기 import get_문장해체


model_name: str = Model.GPT5


def gpt_5_gen(
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

    if not parsed["keyword"]:
        raise
    user_prompt: str = GptPrompt.gpt_5(parsed["keyword"])

    category = ""
    if user_instructions:
        category = categorize_keyword_with_ai(user_instructions)

    if not category:
        category = os.getenv("MONGO_DB_NAME", "wedding")

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

    print(f"지금 연결 된 DB: {db_service.db.name}")

    _분석본 = f"""
[분석 지시]
아래 JSON 데이터는 참고 문서에서 추출한 화자/구성/스타일 분석 결과물입니다.  
원고 생성 시 반드시 다음 조건을 반영해야 합니다.  

- "화자 지시"에 따른 인물 설정, 말투, 단어 빈도와 형태소 패턴을 그대로 따릅니다.  
- "구성 지시"에 따라 서론-중론-결론 흐름을 유지합니다.  
- "원고 스타일 세부사항"을 전부 반영해 문체·문단 길이·리듬감·감정선 등을 동일하게 재현합니다.  
- JSON에 기재된 단어/형태소는 반복적으로 등장해야 하며, 실제 경험담+정보 설명이 혼합된 톤을 유지해야 합니다.  

- 사용자 요청에 (부제 넘버링 제거)가 있다면 필수로 숫자 제거 된 부제 사용

아래는 분석 결과 JSON입니다.  

{문장해체}
"""

    _mongo_data = f"""

[부제 예시]
{subtitles_str}

---

[템플릿 예시]
- 출력 문서는 반드시 템플릿과 **유사한 어휘, 문장 구조, 문단 흐름**을 유지해야 한다.  
- 새로운 주제로 변형하더라도 템플릿의 **톤, 반복 구조, 문장 길이, 순서**를 그대로 모방해야 한다.  
- 예시와 다른 어휘·문장 구조를 사용하지 말고, 가능한 한 **템플릿의 스타일을 복제**하라.  

{templates_str}

[작성 지침]  
사용자가 입력한 주제를 기반으로 위 템플릿과 동일한 스타일로 결과를 작성하라.

- 문체는 딱딱하게 하지 않고 아래처럼 부드러운 문체를 사용한다.

- 예시1: (저처럼 짐이 많거나, 아이가 있거나,

부모님을 모시고 가는 여행은

인천공항 콜밴만한 교통수단이 없어요 -)
- 예시2: (가족여행 or 골프여행 or 짐이 많거나

유모차가 있다?!

아묻따 에이스팀 인천공항 콜밴 이용이 답이에요!)

- 예시3: (대중교통 이용했으면 피곤해서 못 내렸을수도..

만약 자차를 가지고 갔다면?

와... 그 피곤함에 운전까지

절대 상상도 못해요!

졸음운전 정말 위험하잖아요 ㅠ_ㅠ)

- 예시4: (

콜택시 기사님께서 짐을 실어주셔서

저는 두 손 편하게 탑승 후 정말

1시간동안 곯아 떨어졌답니다 ㅋㅋㅋ)

---

[표현 라이브러리]
{expressions_str}

---

[AI 개체 인식 및 그룹화 결과]
{parameters_str}
"""

    prompt: str = (
        f"""

---

{_mongo_data}

---

[사용자 지시사항]
{parsed['note']}

---

[참고 문서]
- 참고문서의 업체명은 절대 원고에 포함하지 않습니다.
{ref}

---

[요청]
{user_prompt}

---

{_분석본}

---

""".strip()
    )
    print(parsed)

    client = OpenAI(api_key=OPENAI_API_KEY)

    try:
        print(f"GPT 생성 시작 | keyword={user_instructions!r} | model={model_name}")
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional blog post writer.",
                },
                {"role": "user", "content": prompt},
            ],
        )

        usage = getattr(response, "usage", None)
        if usage is not None:
            in_tokens = getattr(usage, "prompt_tokens", None)
            out_tokens = getattr(usage, "completion_tokens", None)
            total_tokens = getattr(usage, "total_tokens", None)
            print(f"tokens in={in_tokens}, out={out_tokens}, total={total_tokens}")

        choices = getattr(response, "choices", []) or []
        if not choices or not getattr(choices[0], "message", None):
            raise RuntimeError("모델이 유효한 choices/message를 반환하지 않았습니다.")

        text: str = (choices[0].message.content or "").strip()
        if not text:
            raise RuntimeError("모델이 빈 응답을 반환했습니다.")

        length_no_space = len(re.sub(r"\s+", "", text))
        print(f"{model_name} 문서 생성 완료 (공백 제외 길이: {length_no_space})")

        return text

    except Exception as e:

        print("OpenAI 호출 실패:", repr(e))
        raise

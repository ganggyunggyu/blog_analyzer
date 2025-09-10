from __future__ import annotations

import json
import re
from typing import Any, Dict, List
import time

from openai import OpenAI
from analyzer.request_문장해체분석기 import get_문장해체
from config import OPENAI_API_KEY
from _constants.Model import Model
from mongodb_service import MongoDBService
from _prompts.get_gpt_prompt import GptPrompt
from _prompts.get_gemini_prompt import get_gemini_v2_prompt
from _prompts.get_system_prompt import get_system_prompt

from config import GEMINI_API_KEY

from google import genai
from google.genai import types

from utils.query_parser import parse_query


def get_gemini_response(
    user_instructions: str,
    ref: str = "",
    model: str = "gemini-2.5-pro",
) -> str:
    """
    분석 산출물 + 사용자 지시 → 원고 텍스트를 생성한다.
    - MongoDB의 최신 분석 결과(expressions/parameters/subtitles/templates)를 읽어 프롬프트에 포함.
    - OpenAI Chat Completions 호출.
    - 출력 형식/흐름은 기존 유지, 타입/널 안전성 강화.

    Returns:
        생성된 원고 텍스트 (str)

    Raises:
        RuntimeError: 모델이 빈 응답을 반환한 경우 등
        ValueError: API 키 미설정
        Exception: OpenAI 호출 실패 등
    """

    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY가 설정되어 있지 않습니다. .env를 확인하세요.")

    parsed = parse_query(user_instructions)

    if parsed["keyword"] == None:
        raise

    sys_prompt: str = get_system_prompt()
    user_prompt: str = GptPrompt.gpt_5_v2(keyword=parsed["keyword"])
    문장해체 = get_문장해체(ref)
    model_name = model

    db_service = MongoDBService()
    analysis_data: Dict[str, Any] = db_service.get_latest_analysis_data() or {}

    unique_words: List[str] = analysis_data.get("unique_words", []) or []
    sentences: List[str] = analysis_data.get("sentences", []) or []

    subtitles: List[str] = analysis_data.get("subtitles", []) or []
    expressions: Dict[str, List[str]] = analysis_data.get("expressions", {}) or {}
    parameters: Dict[str, List[str]] = analysis_data.get("parameters", {}) or {}
    templates: List[Dict[str, Any]] = analysis_data.get("templates", []) or []

    subtitles_str: str = (
        json.dumps(subtitles, ensure_ascii=False, indent=2) if subtitles else "없음"
    )
    expressions_str: str = (
        json.dumps(expressions, ensure_ascii=False, indent=2) if expressions else "없음"
    )
    parameters_str: str = (
        json.dumps(parameters, ensure_ascii=False, indent=2) if parameters else "없음"
    )
    templates_str: str = (
        json.dumps(templates, ensure_ascii=False, indent=2) if templates else "없음"
    )

    _분석본 = f"""
[참조원고 분석 데이터 활용 지침]
아래 데이터는 참고 문서에서 추출한 화자/구성/스타일 분석 결과물입니다.  
원고 생성 시 반드시 다음 조건을 반영해야 합니다.  

{문장해체}

- "화자 지시"에 따른 인물 설정, 말투, 단어 빈도와 형태소 패턴을 그대로 따릅니다.  
- "구성 지시"에 따라 서론-중론-결론 흐름을 유지합니다.
- "원고 스타일 세부사항"을 전부 반영해 문체·문단 길이·리듬감·감정선 등을 동일하게 재현합니다.  
- JSON에 기재된 단어/형태소는 반복적으로 등장해야 하며, 실제 경험담+정보 설명이 혼합된 톤을 유지해야 합니다.  

- 사용자 요청에 (부제 넘버링 제거)가 있다면 필수로 숫자 제거 된 부제 사용

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

---

[표현 라이브러리]
{expressions_str}

---

[AI 개체 인식 및 그룹화 결과]
{parameters_str}
"""

    user: str = (
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

    client = OpenAI(api_key=OPENAI_API_KEY)

    try:
        start_ts = time.time()
        print("원고작성 시작")
        client = genai.Client(api_key=GEMINI_API_KEY)
        res = client.models.generate_content(
            model=model,
            config=types.GenerateContentConfig(
                system_instruction=sys_prompt,
            ),
            contents=user,
        )

        try:
            meta = getattr(res, "usage_metadata", None)
            if meta:
                in_tokens = getattr(meta, "prompt_token_count", None)
                out_tokens = getattr(meta, "candidates_token_count", None)
                total = (in_tokens or 0) + (out_tokens or 0)
                # 토큰 사용량 로깅 제거
        except Exception:
            pass

        text: str = getattr(res, "text", "") or ""
        if not text:

            candidates = getattr(res, "candidates", None)
            if candidates and len(candidates) > 0:

                first = candidates[0]
                text = getattr(first, "content", "")
                if hasattr(text, "parts"):

                    parts = getattr(text, "parts", []) or []
                    text = "".join(getattr(p, "text", "") for p in parts)
                elif isinstance(text, str):
                    pass
                else:
                    text = ""
        if not text:
            raise RuntimeError("Gemini가 빈 응답을 반환했습니다.")

        length_no_space = len(re.sub(r"\s+", "", text))
        print(f"원고 길이 체크: {length_no_space}")
        elapsed = time.time() - start_ts
        print(f"원고 소요시간: {elapsed:.2f}s")
        print("원고작성 완료")

        return text

    except Exception as e:
        raise

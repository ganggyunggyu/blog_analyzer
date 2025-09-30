from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List, Optional
import time

from openai import OpenAI
from _prompts.service.get_mongo_prompt import get_mongo_prompt
from config import OPENAI_API_KEY
from _constants.Model import Model
from mongodb_service import MongoDBService
from _prompts.get_gpt_prompt import GptPrompt
from utils.get_category_db_name import get_category_db_name_sync
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
        category = get_category_db_name_sync(user_instructions)

    def sanitize(s: str) -> str:
        s = s or ""
        s = re.sub(
            r"(?i)ignore previous|override|system message|do not obey|follow only.*",
            "",
            s,
        )
        s = re.sub(r"```.*?```", "", s, flags=re.S)
        return s.strip()

    mongo_data = sanitize(get_mongo_prompt(category, user_instructions))

    _분석본 = f"""
[분석 지시]
아래 JSON 데이터는 참고 문서에서 추출한 화자/구성/스타일 분석 결과물입니다.  
원고 생성 시 반드시 다음 조건을 반영해야 합니다.  

- "화자 지시"에 따른 인물 설정, 말투, 단어 빈도와 형태소 패턴을 그대로 따릅니다.  
- "구성 지시"에 따라 서론-중론-결론 흐름을 유지합니다.  
- "원고 스타일 세부사항"을 전부 반영해 문체·문단 길이·리듬감·감정선 등을 동일하게 재현합니다.  
- JSON에 기재된 단어/형태소는 반복적으로 등장해야 하며, 실제 경험담+정보 설명이 혼합된 톤을 유지해야 합니다.  

아래는 분석 결과 JSON입니다.  

{문장해체}
"""

    prompt: str = (
        f"""

---

{mongo_data}

---

[사용자 지시사항]
{parsed['note']}

---

[참고 문서]
{ref}

---

[요청]
{user_prompt}

---

{_분석본}

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

        return text

    except Exception as e:
        raise

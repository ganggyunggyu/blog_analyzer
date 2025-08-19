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

from config import MONGO_DB_NAME

model_name: str = Model.GPT4_1

def manuscript_generator(
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

    


    
    user_prompt: str = GptPrompt.gpt_4(keyword=user_instructions)
    
    category = ''
    if user_instructions:
        category = categorize_keyword_with_ai(keyword=user_instructions)

    if not category:
        category = os.getenv("MONGO_DB_NAME", "wedding")
    
    db_service = MongoDBService()

    db_service.set_db_name(db_name=category)

    print(f'지금 연결 된 DB: {db_service.db.name}')

    analysis_data: Dict[str, Any] = db_service.get_latest_analysis_data() or {}

    unique_words: List[str] = analysis_data.get("unique_words", []) or []
    sentences: List[str] = analysis_data.get("sentences", []) or []

    subtitles: List[str] = analysis_data.get('subtitles', []) or []
    expressions: Dict[str, List[str]] = analysis_data.get("expressions", {}) or {}
    parameters: Dict[str, List[str]] = analysis_data.get("parameters", {}) or {}
    templates  = analysis_data.get("templates", []) or []


    subtitles_str: str = json.dumps(subtitles, ensure_ascii=False, indent=2) if expressions else "없음"
    expressions_str: str = json.dumps(expressions, ensure_ascii=False, indent=2) if expressions else "없음"
    parameters_str: str = json.dumps(parameters, ensure_ascii=False, indent=2) if parameters else "없음"
    templates_str  = json.dumps(templates,  ensure_ascii=False, indent=2) if templates  else "없음"

    prompt: str = f"""
[표현 라이브러리]
{expressions_str}

[AI 개체 인식 및 그룹화 결과]
{parameters_str}

[부제 예시]
{subtitles_str}

[사용자 지시사항]
{user_instructions}

[참고 문서]
{ref}

[템플릿]
{templates_str}

[요청]
{user_prompt}
""".strip()

    
    client = OpenAI(api_key=OPENAI_API_KEY)

    try:
        print(f"GPT 생성 시작 | keyword={user_instructions!r} | model={model_name}")
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are a professional blog post writer."},
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
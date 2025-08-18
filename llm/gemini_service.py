from __future__ import annotations

import json
import re
from typing import Any, Dict, List

from openai import OpenAI
from config import OPENAI_API_KEY
from constants.Model import Model
from mongodb_service import MongoDBService
from prompts.get_gpt_prompt import GptPrompt
from prompts.get_system_prompt import get_system_prompt

from config import GEMINI_API_KEY

from google import genai
from google.genai import types



def get_gemini_response(
    user_instructions: str,
    ref: str = "",
    model: str = "gemini-2.5-flash",
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
    # --- 환경 체크 ---
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY가 설정되어 있지 않습니다. .env를 확인하세요.")



    # 사용자 프롬프트(지시사항을 기반으로 본문 작성 지시)
    sys_prompt: str = get_system_prompt()
    user_prompt: str = GptPrompt.gpt_4(keyword=user_instructions)
    model_name = model

    # --- DB에서 최신 분석 데이터 로딩 ---
    db_service = MongoDBService()
    analysis_data: Dict[str, Any] = db_service.get_latest_analysis_data() or {}

    unique_words: List[str] = analysis_data.get("unique_words", []) or []
    sentences: List[str] = analysis_data.get("sentences", []) or []

    subtitles: List[str] = analysis_data.get("subtitles", []) or []
    expressions: Dict[str, List[str]] = analysis_data.get("expressions", {}) or {}
    parameters: Dict[str, List[str]] = analysis_data.get("parameters", {}) or {}
    templates: List[Dict[str, Any]] = analysis_data.get("templates", []) or []

    # --- 직렬화 (보기 좋게) ---
    subtitles_str: str   = json.dumps(subtitles,  ensure_ascii=False, indent=2) if subtitles   else "없음"
    expressions_str: str = json.dumps(expressions, ensure_ascii=False, indent=2) if expressions else "없음"
    parameters_str: str  = json.dumps(parameters, ensure_ascii=False, indent=2) if parameters  else "없음"
    templates_str: str   = json.dumps(templates,  ensure_ascii=False, indent=2) if templates   else "없음"

    # --- 최종 프롬프트 ---
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

    # --- OpenAI 호출 ---
    client = OpenAI(api_key=OPENAI_API_KEY)

    try:
        print(f"GEMINI 생성 시작 | keyword={user_instructions!r} | model={model}")
        client = genai.Client(api_key=GEMINI_API_KEY)
        res = client.models.generate_content(
            model=model,
            config=types.GenerateContentConfig(
            system_instruction=sys_prompt,
            ),
            contents=prompt,
        )

                # 토큰 사용량 로그 (가능하면)
        try:
            meta = getattr(res, "usage_metadata", None)
            if meta:
                in_tokens = getattr(meta, "prompt_token_count", None)
                out_tokens = getattr(meta, "candidates_token_count", None)
                total = (in_tokens or 0) + (out_tokens or 0)
                print(f"입력 토큰: {in_tokens}, 출력 토큰: {out_tokens}, 총 토큰: {total}")
        except Exception:
            pass  # 사용량 정보가 없는 모델/버전 대비

        # 본문 텍스트 추출
        text: str = getattr(res, "text", "") or ""
        if not text:
            # 후보 구조에서 추출 시도 (SDK 버전에 따라)
            candidates = getattr(res, "candidates", None)
            if candidates and len(candidates) > 0:
                # 첫 후보의 텍스트 파싱
                first = candidates[0]
                text = getattr(first, "content", '')
                if hasattr(text, "parts"):
                    # parts의 text 합치기
                    parts = getattr(text, "parts", []) or []
                    text = "".join(getattr(p, "text", "") for p in parts)
                elif isinstance(text, str):
                    pass
                else:
                    text = ""
        if not text:
            raise RuntimeError("Gemini가 빈 응답을 반환했습니다.")

        # 길이 로그
        length_no_space = len(re.sub(r"\s+", "", text))
        print(f"{model} 문서 생성 완료 (공백 제외 길이: {length_no_space})")

        return text

    except Exception as e:
        print("OpenAI 호출 실패:", repr(e))
        raise
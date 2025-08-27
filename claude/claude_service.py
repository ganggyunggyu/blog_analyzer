from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List, Optional

from analyzer.request_문장해체분석기 import get_문장해체
from config import MONGO_DB_NAME
from mongodb_service import MongoDBService
from prompts.get_gpt_prompt import GptPrompt
from prompts.get_system_prompt import get_system_prompt_v2
from utils.categorize_keyword_with_ai import categorize_keyword_with_ai
from utils.query_parser import parse_query


def claude_blog_generator(
    keyword: str,
    ref: str = "",
    min_length: int = 1700,
    max_length: int = 2000,
    note: str = "",
) -> str:
    """
    Claude를 사용한 블로그 원고 생성기
    MongoDB 데이터와 gpt_v2 프롬프트를 결합하여 원고 생성

    Args:
        keyword: 블로그 원고의 키워드
        ref: 참조할 문서 (선택사항)
        min_length: 최소 글자수 (공백 제외)
        max_length: 최대 글자수 (공백 제외)
        note: 추가 요청사항

    Returns:
        생성된 블로그 원고 텍스트
    """

    category = ""
    if keyword:
        category = categorize_keyword_with_ai(keyword)

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
        json.dumps(subtitles, ensure_ascii=False, indent=2) if subtitles else "없음"
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

    print(f"연결된 DB: {db_service.db.name}")

    참조분석 = get_문장해체(ref) if ref else ""

    기본_프롬프트 = GptPrompt.gpt_4_v2(
        keyword=keyword, min_length=min_length, max_length=max_length, note=note
    )

    참조_분석_프롬프트 = (
        f"""
[참조원고 분석 데이터 활용 지침]
아래 데이터는 참고 문서에서 추출한 화자/구성/스타일 분석 결과물입니다.  
원고 생성 시 반드시 다음 조건을 반영해야 합니다.

{참조분석}

- "화자 지시"에 따른 인물 설정, 말투, 단어 빈도와 형태소 패턴을 살짝 변형하여 글의 형태만을 따릅니다.  
- "구성 지시"에 따라 서론-중론-결론 흐름을 유지합니다.
- "원고 스타일 세부사항"을 전부 반영해 문체·문단 길이·리듬감·감정선 등을 동일하게 재현합니다.  
- JSON에 기재된 단어/형태소는 반복적으로 등장해야 하며, 실제 경험담+정보 설명이 혼합된 톤을 유지해야 합니다.  

- 부제는 그대로 사용하나 예외 사항은 하단 참조
- 사용자 요청에 (부제X)가 있다면 필수로 숫자만 제거된 부제 사용
"""
        if 참조분석
        else ""
    )

    mongo_data_prompt = f"""

---

[분석 지시]
아래 JSON 데이터는 참고 문서에서 추출한 화자/구성/스타일 분석 결과물입니다.  
원고 생성 시 반드시 다음 조건을 반영해야 합니다.  

- "화자 지시"에 따른 인물 설정, 말투, 단어 빈도와 형태소 패턴을 그대로 따릅니다.  
- "구성 지시"에 따라 서론-중론-결론 흐름을 유지합니다.  
- "원고 스타일 세부사항"을 전부 반영해 문체·문단 길이·리듬감·감정선 등을 동일하게 재현합니다.  
- JSON에 기재된 단어/형태소는 반복적으로 등장해야 하며, 실제 경험담+정보 설명이 혼합된 톤을 유지해야 합니다.  

= 부제는 하단 데이터를 이용하여 작성
- 부제 형식은
    1. 부제1
    2. 부제2
    ... 5개
- 사용자 요청에 (부제X)가 있다면 필수로 숫자만 제거된 부제 사용

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

    final_prompt = f"""

---

{mongo_data_prompt}

---

[참조 문서]
- 참조 문서의 업체명은 절대 원고에 포함하지 않습니다.
- 참조 문서와 동일하게 작성하지 않습니다.
- 아래의 분석본과 함께 사용해서 전체적인 흐름을 유사하게 가져갑니다.
{ref}

[참조 원고 분석]
{참조_분석_프롬프트}

---

[필수 사항]
{기본_프롬프트}

---

[필수로 이행해야하는 추가 요청]
{note}

---

""".strip()

    return final_prompt


def generate_blog_content(
    keyword: str,
    ref: str = "",
    min_length: int = 1700,
    max_length: int = 2000,
    note: str = "",
) -> str:
    """
    블로그 콘텐츠 생성 (프롬프트만 반환)
    실제 AI 모델 호출은 별도로 처리
    """
    return claude_blog_generator(keyword, ref, min_length, max_length, note)


def save_blog_content(content: str, keyword: str, output_dir: str = "output") -> str:
    """
    생성된 블로그 콘텐츠를 파일로 저장

    Args:
        content: 생성된 블로그 원고
        keyword: 키워드 (파일명에 사용)
        output_dir: 저장할 디렉토리

    Returns:
        저장된 파일의 경로
    """

    length = len(re.sub(r"\s+", "", content))

    clean_keyword = keyword.replace(" ", "").replace("/", "")
    filename = f"{clean_keyword}_{length}자.txt"

    output_path = os.path.join(output_dir, filename)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"블로그 원고 저장 완료: {output_path} ({length}자)")
    return output_path

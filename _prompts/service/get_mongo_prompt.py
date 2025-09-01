from __future__ import annotations

import json
from typing import List, Dict, Any
from mongodb_service import MongoDBService


def get_mongo_prompt():
    db_service = MongoDBService()

    analysis_data: Dict[str, Any] = db_service.get_latest_analysis_data() or {}

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

    _mongo_prompt = f"""

    [부제 예시]
    - 부제는 간결하게 작성합니다.
    - 참조 분석지시의 부제의 흐름과 부제 예시 데이터를 참고해서 작성합니다.
    - 부제는 본문과 자연스럽게 내용이 이어져야 합니다.

    {subtitles_str}

    ---

    [표현 라이브러리]
    {expressions_str}

    ---

    [형태소 라이브러리]
    {parameters_str}

    - 스타일을 복제하나 형태소를 가져다 쓸 경우에는 변경될 수 있는 값은 유동적으로 변경해야합니다.
    - 예시: 33평 -> 28평
    - 예시: 60L -> 90L
    - 예시: 50db -> 50db
    - 예시: A씨 -> F씨

    ---

    [템플릿 예시]
    - 출력 문서는 반드시 템플릿과 **유사한 어휘, 문장 구조, 문단 흐름**을 유지해야 한다.
    - 새로운 주제로 변형하더라도 템플릿의 **톤, 반복 구조, 문장 길이, 순서**를 그대로 모방해야 한다.
    - 예시와 다른 어휘·문장 구조를 사용하지 말고, 가능한 한 **템플릿의 스타일을 복제**하라.
    - 사용자가 입력한 주제를 기반으로 템플릿과 동일한 스타일로 원고를 작성합니다.
    - 템플릿의 [] 부분은 위 표현 라이브러리, 파라미터 라이브러리로 채운다.

    {templates_str}

    ---

    """

    return _mongo_prompt

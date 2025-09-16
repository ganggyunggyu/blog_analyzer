from __future__ import annotations

import json
from typing import List, Dict, Any
from bson import ObjectId
from mongodb_service import MongoDBService


def get_mongo_prompt(category: str) -> str:
    db_service = MongoDBService()
    db_service.set_db_name(category)

    analysis_data: Dict[str, Any] = db_service.get_latest_analysis_data() or {}

    subtitles_raw = analysis_data.get("subtitles") or []
    expressions_raw = analysis_data.get("expressions") or {}
    parameters_raw = analysis_data.get("parameters") or {}
    templates_raw = analysis_data.get("templates") or []

    subtitles: List[str] = [
        str(s).strip() for s in list(subtitles_raw) if str(s).strip()
    ]
    expressions: Dict[str, List[str]] = {
        str(k): [str(vv).strip() for vv in (v or []) if str(vv).strip()]
        for k, v in dict(expressions_raw).items()
    }
    parameters: Dict[str, List[str]] = {
        str(k): [str(vv).strip() for vv in (v or []) if str(vv).strip()]
        for k, v in dict(parameters_raw).items()
    }
    templates: List[Any] = list(templates_raw)

    chunk_size = 5
    chunks: List[List[str]] = [
        subtitles[i : i + chunk_size] for i in range(0, len(subtitles), chunk_size)
    ]
    output: List[str] = []
    for idx, group in enumerate(chunks, start=1):
        joined = ", ".join(group)
        output.append(f"{idx}: {{{joined}}}")

    subtitles_str: str = "\n".join(output) if output else "없음"

    def _default(o):
        if isinstance(o, ObjectId):
            return str(o)
        raise TypeError(f"Type not serializable: {type(o)}")

    expressions_str: str = (
        json.dumps(expressions, ensure_ascii=False, indent=2, default=_default)
        if expressions
        else "없음"
    )
    parameters_str: str = (
        json.dumps(parameters, ensure_ascii=False, indent=2, default=_default)
        if parameters
        else "없음"
    )
    templates_str: str = (
        json.dumps(templates, ensure_ascii=False, indent=2, default=_default)
        if templates
        else "없음"
    )

    # 디버그 출력 제거

    _mongo_prompt = f"""

[소제목 예시]
- {{소제목}}는 간결하게 하단을 참고하여 창의적으로 작성해
- {{소제목}}는 키워드와 본문과 자연스럽게 내용이 이어져야해
- {{소제목}}은 무조건 한줄로 작성해
{subtitles_str}

---

[표현 라이브러리]
{expressions_str}

---

[형태소 라이브러리]
{parameters_str}

- 형태소를 가져다 쓸 경우에는 변경될 수 있는 값은 유동적으로 변경해야합니다.
- 예시: 33평 -> 28평
- 예시: 60L -> 90L
- 예시: 50db -> 50db
- 예시: A씨 -> F씨

---

[템플릿 예시]
- 출력 문서는 반드시 템플릿과 **유사한 어휘, 문장 구조, 문단 흐름**을 유지해야 한다.
- 예시와 다른 어휘·문장 구조를 사용하지 말고, 가능한 한 **템플릿의 스타일을 복제**하라.
- 사용자가 입력한 주제를 기반으로 템플릿과 동일한 스타일로 원고를 작성합니다.
- 템플릿의 [] 부분은 위 표현 라이브러리, 파라미터 라이브러리로 채운다.

{templates_str}

---
""".strip(
        "\n"
    )

    return _mongo_prompt

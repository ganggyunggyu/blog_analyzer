from __future__ import annotations
import random

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
    templates_str: str = ""
    if templates:
        random_template = random.choice(templates)
        templates_str: str = json.dumps(
            random_template,
            ensure_ascii=False,
            indent=2,
        )
    else:
        templates_str = "없음"

    clean_templates_str = templates_str.replace("\n", "")
    clean_templates_str = templates_str.replace("\\n", "")

    print(clean_templates_str)
    t_len = len(clean_templates_str)
    print(t_len)
    _mongo_prompt = f"""
[소제목 작성 가이드]
- {{소제목}}은 한 줄로 간결하게 작성하세요.
- 키워드와 본문 흐름에 자연스럽게 이어지도록 만드세요.
- 아래 소제목 예시를 참고하되 그대로 복사하지 말고 창의적으로 변형하세요.
- 소제목은 5개로 고정
    서론
    1. 소제목
        본문
    2. 소제목
        본문
    3. 소제목
        본문
    4. 소제목
        본문
    5. 소제목
        본문
    마무리 멘트 (2~3줄 정도로 간단히)

{subtitles_str}

---

[표현 라이브러리]
{expressions_str}

[형태소 라이브러리]
{parameters_str}

※ 형태소를 사용할 때는 값이 상황에 맞게 바뀔 수 있도록 조정하세요.
   예: 33평 → 28평 / 60L → 90L / A씨 → F씨

---

[템플릿 예시]
- 템플릿 안의 대괄호([ ])는 변수 표시용이니 그대로 쓰지 말고 알맞은 단어로 교체하세요.
- 제품 브랜드명, 작성자 이름 등은 그대로 쓰지 말고 반찬이라는 이름을 사용해요.
- 이모지, ㅎㅎ, ㅋㅋ, ㅠㅠ, !! 같은 감정 표현은 템플릿에 있는 경우 자연스럽게 포함하세요.
- 결과 글의 길이는 공백 제외 2200~2400자 사이여야 하며, 가능 한 템플릿 길이와 비슷하게 맞추세요.
- 업체명은 그대로 노출하지 말고, 필요하면 “한 업체”, “어느 브랜드”처럼 모호하게 표현하세요.
- 템플릿의 화자를 분석하고 그 화자와 다른 화자 설정을 하세요.
- 창의적인 화자 설정과 스토리 텔링을 필수로 이행해주세요

---

[템플릿 원문]
{clean_templates_str}
"""

    return _mongo_prompt

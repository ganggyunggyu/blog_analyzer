from __future__ import annotations
import random
import re

import json
from typing import List, Dict, Any
from bson import ObjectId
from mongodb_service import MongoDBService
from utils.select_template import select_template


def get_mongo_prompt(category: str, keyword: str = "") -> str:

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
    template_info = ""
    if templates:
        result = select_template(
            collection=db_service.db["templates"],
            templates=templates,
            keyword=keyword,
            top_n=3,
        )

        print("=== SELECT_TEMPLATE RESULT ===")
        print(f"Selection Method: {result['selection_method']}")
        print(f"카테고리: {category}")
        print("=" * 30)

        selected_template = result["selected_template"]
        selection_method = result["selection_method"]

        if selected_template:
            template_file_name = selected_template.get("file_name", "파일명 없음")
            template_id = str(selected_template.get("_id", "ID 없음"))
            template_info = f"{template_file_name}:{template_id} ({selection_method})"

            templates_str: str = json.dumps(
                selected_template,
                ensure_ascii=False,
                indent=2,
            )
        else:
            templates_str = "없음"
            template_info = "템플릿 선택 실패"
    else:
        templates_str = "없음"
        template_info = "템플릿 없음"

    clean_templates_str = templates_str.replace("\n", "")
    clean_templates_str = templates_str.replace("\\n", "")

    t_len = len(clean_templates_str)
    print(f"템플릿 [START] {template_info}")
    print(f"템플릿 길이: {t_len}자")
    _mongo_prompt = f"""
[소제목 작성 가이드]
- 소제목은 반드시 5개로 고정합니다.
- 각 소제목은 한 줄로 간결하게, 본문 흐름과 키워드를 자연스럽게 연결하세요.
- 소제목 앞에는 넘버링을 필수로 넣어주세요.

[구조 예시]
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
마무리 멘트 (간단히 2~3줄)

<<<SUb_TITLE_DATA
{subtitles_str}
>>>

---
<<<EXP_DATA
[표현 라이브러리]
{expressions_str}
>>>

---

<<<PARAM_DATA
[형태소 라이브러리]
{parameters_str}
>>>
* 형태소를 사용할 때는 값이 상황에 맞게 바뀔 수 있도록 조정하세요.
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
- 참고 파일: {template_info}
<<<TEM_DATA
{clean_templates_str}
>>>
"""

    return _mongo_prompt

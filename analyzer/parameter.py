from __future__ import annotations
from datetime import datetime
from typing import Dict, List, Optional
import time
import json
import re

from _constants.Model import Model
from mongodb_service import MongoDBService
from utils.ai_client_factory import call_ai


model_name: str = Model.GROK_4_NON_RES


def parameter_gen(
    docs: str, category: str = "", file_name: str = "", model_name_override: Optional[str] = None
) -> Dict[str, List[str]]:
    db_service = MongoDBService()
    model = model_name_override or model_name
    if category:
        db_service.set_db_name(category)

    # 파일명 중복 체크 (파일명이 있는 경우에만) - AI 요청 전에 체크!
    if file_name.strip():
        existing_params = db_service.find_documents(
            "parameters", {"file_name": file_name.strip()}
        )
        if existing_params:
            print(f"이미 분석된 파일입니다: {file_name}")
            print("기존 파라미터를 반환합니다. (AI 요청 없음 - 비용 절약!)")

            # 기존 데이터를 dict 형태로 재구성해서 반환
            result_dict = {}
            for param_doc in existing_params:
                cat = param_doc.get("category", "")
                par = param_doc.get("parameter", "")
                if cat and par:
                    if cat not in result_dict:
                        result_dict[cat] = []
                    if par not in result_dict[cat]:
                        result_dict[cat].append(par)

            db_service.close_connection()
            return result_dict

    print(f"새로운 파일 분석 시작: {file_name or '파일명 없음'}")

    system = """
You are an expert in Named Entity Recognition and text analysis. Extract key entities and group them semantically. Return ONLY JSON.
""".strip()

    prompt = f"""
다음은 여러 블로그 원고를 합친 텍스트입니다.

[원고 내용]
{docs}

[요청]
위 원고 내용에서 반복적으로 나타나거나, 대체 가능한 핵심 개체(entity)들을 모두 추출해주세요.
추출된 개체들을 의미적으로 유사한 항목끼리 그룹화하고, 각 그룹을 대표할 수 있는 가장 적절한 "대표 키워드"를 한 단어로 지정해주세요.
예: '땀땀', '토끼정' → '상호명',  '갤럭시S24', '아이폰16' → '제품명'

반드시 아래 JSON 형식으로만 반환하세요(문자 이외 설명 금지).
{{
  "대표 키워드1": ["추출된 개체1", "추출된 개체2"],
  "대표 키워드2": ["추출된 개체3", "추출된 개체4"]
}}
""".strip()

    start_ts = time.time()

    text_content = call_ai(
        model_name=model,
        system_prompt=system,
        user_prompt=prompt,
    )

    parameters = parse_parameter_response(text_content)

    # MongoDB에 저장
    now = datetime.now()
    docs_to_save = [
        {
            "timestamp": now,
            "file_name": file_name,
            "db_category": category,
            "category": cat,
            "parameter": par,
        }
        for cat, pars in parameters.items()
        for par in pars
    ]

    if docs_to_save:
        try:
            result = db_service.upsert_many_documents(
                "parameters", docs_to_save, ["category", "parameter"]
            )
            print(f"신규 파라미터: {result['upserted']}개, 중복 제외: {result['matched']}개")
        except Exception as e:
            print(f"파라미터 저장 중 오류 (계속 진행): {e}")
            result = {"upserted": 0, "matched": 0}

    elapsed = time.time() - start_ts
    print(f"{category}-파라미터 추출 소요시간: {elapsed:.2f}s")
    print(f"추출된 파라미터: {len(docs_to_save)}개")

    db_service.close_connection()

    return parameters


def parse_parameter_response(text_content: str) -> Dict[str, List[str]]:
    try:
        json_text = extract_json_block(text_content)
        if not json_text:
            return {}
        data = json.loads(json_text)
        if not isinstance(data, dict):
            return {}
        cleaned: Dict[str, List[str]] = {}
        for key, value in data.items():
            if not isinstance(key, str):
                continue
            if isinstance(value, list):
                cleaned[key] = [
                    str(item)
                    for item in value
                    if isinstance(item, (str, int, float)) and str(item).strip()
                ]
            elif isinstance(value, (str, int, float)):
                text = str(value).strip()
                if text:
                    cleaned[key] = [text]
        return cleaned
    except Exception:
        return {}


def extract_json_block(text: str) -> Optional[str]:
    if not text:
        return None
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(
            r"^```(?:json)?\s*|\s*```$",
            "",
            stripped,
            flags=re.IGNORECASE | re.DOTALL,
        ).strip()
    if is_json(stripped):
        return stripped
    match = re.search(r"\{.*\}", stripped, flags=re.DOTALL)
    if match:
        candidate = match.group(0)
        if is_json(candidate):
            return candidate
    return None


def is_json(text: str) -> bool:
    try:
        json.loads(text)
        return True
    except Exception:
        return False



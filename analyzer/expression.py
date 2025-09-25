from __future__ import annotations
from datetime import datetime
from typing import Dict, List
import time
import json
import re

from openai import OpenAI
from config import OPENAI_API_KEY
from _constants.Model import Model
from mongodb_service import MongoDBService


model_name: str = Model.GPT5_MINI
client = OpenAI(api_key=OPENAI_API_KEY)


def gen_expressions(
    text: str, category: str = "", file_name: str = ""
) -> Dict[str, List[str]]:
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY가 설정되어 있지 않습니다. .env를 확인하세요.")

    db_service = MongoDBService()
    if category:
        db_service.set_db_name(category)

    # 파일명 중복 체크 (파일명이 있는 경우에만) - AI 요청 전에 체크!
    if file_name.strip():
        existing_expressions = db_service.find_documents(
            "expressions", {"file_name": file_name.strip()}
        )
        if existing_expressions:
            print(f"이미 분석된 파일입니다: {file_name}")
            print("기존 표현을 반환합니다. (AI 요청 없음 - 비용 절약!)")

            # 기존 데이터를 dict 형태로 재구성해서 반환
            result_dict = {}
            for expr_doc in existing_expressions:
                cat = expr_doc.get("category", "")
                expr = expr_doc.get("expression", "")
                if cat and expr:
                    if cat not in result_dict:
                        result_dict[cat] = []
                    if expr not in result_dict[cat]:
                        result_dict[cat].append(expr)

            db_service.close_connection()
            return result_dict

    print(f"새로운 파일 분석 시작: {file_name or '파일명 없음'}")

    system = """
You are an expert in marketing content analysis. Your task is to extract useful expressions from the given text, categorize them into mid-level categories, and return them in a JSON format of 'category_key': ['expression1', 'expression2'].
""".strip()

    prompt = f"""
다음은 블로그 원고의 일부입니다.

[원고 내용]
{text}

[요청]
위 원고 내용에서 마케팅/콘텐츠 제작에 유용하게 활용될 수 있는 '표현'들을 추출해주세요.
'표현'은 특정 중분류(예: '긍정적 평가', '부정적 평가', '제품 특징', '서비스 장점', '사용 후기', '감성 표현', '행동 유도', '문제점 제시', '해결책 제시', '비교/대조', '수치/통계', '질문 유도')에 적합한 단어 또는 짧은 문장(구)입니다.
각 표현은 해당 중분류의 '키'에 해당하는 '밸류'로 매칭시켜주세요.
결과는 반드시 다음 JSON 형식으로 반환해주세요.

{{
  "중분류_키1": ["표현1", "표현2"],
  "중분류_키2": ["표현3", "표현4"]
}}
""".strip()

    start_ts = time.time()

    res = get_openai(model=model_name, user=prompt, system=system)
    text_content = get_openai_text(res)

    expressions = parse_expressions_response(text_content)

    now = datetime.now()
    docs = [
        {
            "timestamp": now,
            "file_name": file_name,
            "db_category": category,
            "category": cat,
            "expression": expr,
        }
        for cat, exprs in expressions.items()
        for expr in exprs
    ]

    if docs:
        try:
            result = db_service.upsert_many_documents(
                "expressions", docs, ["category", "expression"]
            )
            print(f"신규 표현: {result['upserted']}개, 중복 제외: {result['matched']}개")
        except Exception as e:
            print(f"표현 저장 중 오류 (계속 진행): {e}")
            result = {"upserted": 0, "matched": 0}

    elapsed = time.time() - start_ts
    print(f"{category}-표현 추출 소요시간: {elapsed:.2f}s")
    print(f"추출된 표현: {len(docs)}개")

    db_service.close_connection()

    return expressions


def parse_expressions_response(text_content: str) -> Dict[str, List[str]]:
    try:
        cleaned = strip_code_fence(text_content.strip())
        data = json.loads(cleaned)
        if isinstance(data, dict):
            return {
                str(k): [
                    str(item).strip()
                    for item in (values or [])
                    if isinstance(item, (str, int, float)) and str(item).strip()
                ]
                for k, values in data.items()
                if isinstance(values, list)
            }
    except Exception:
        pass
    return {}


def strip_code_fence(text: str) -> str:
    if text.startswith("```"):
        return re.sub(
            r"^```(?:json)?\s*|\s*```$",
            "",
            text,
            flags=re.IGNORECASE | re.DOTALL,
        ).strip()
    return text


def get_openai(model, user, system):
    return client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )


def get_openai_text(res):
    return res.choices[0].message.content or "".strip()

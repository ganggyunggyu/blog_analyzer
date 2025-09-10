from __future__ import annotations

import time
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool

from config import UPSTAGE_API_KEY, solar_client
from mongodb_service import MongoDBService
from schema.generate import GenerateRequest
from utils.get_category_db_name import get_category_db_name
from utils.query_parser import parse_query
from _prompts.get_kkk_prompts import KkkPrompt
from _prompts.service.get_ref_prompt import get_ref_prompt
from utils.text_cleaner import comprehensive_text_clean
from utils.format_paragraphs import format_paragraphs


router = APIRouter()

SOLAR_MODEL_NAME = "solar-pro2"


def _build_solar_prompts(
    keyword: str, note: Optional[str], ref: str, category: str
) -> tuple[str, str]:
    parsed_note = note or ""
    기본_프롬프트 = KkkPrompt.kkk_prompt_gpt_5(keyword=keyword, note=parsed_note)
    참조_분석_프롬프트 = get_ref_prompt(ref)
    system = KkkPrompt.get_kkk_system_prompt_v2(category)

    user = f"""
글자수 2000단어 이상
② 이런거 쓰지마
블로거 이름 바꾸거나 다른거로 대체해 예를 들면 20대 직장인입니다 이런거
그리고 예는 예시니까 그대로 쓰지말고 독창적으로 만들어
독창적인 스토리라인 필수

포만감을 오래 유지시켜 주는 거예요.

가격 및 처방 조건

국내에는 2023년 10월 출시되었고, 저는 처방비 1만 원

이렇게 쓸거면 부제로 포함시켜

{system}
[참조 원고 분석]
{ref}
{참조_분석_프롬프트}

---

[필수 사항]
{기본_프롬프트}

---

[필수로 이행해야하는 추가 요청]
{parsed_note}

---
""".strip()

    return system, user


def solar_generate(user_instructions: str, ref: str = "", category: str = "") -> str:
    print(UPSTAGE_API_KEY)
    if not UPSTAGE_API_KEY:
        raise ValueError("UPSTAGE_API_KEY가 설정되어 있지 않습니다. .env를 확인하세요.")

    parsed = parse_query(user_instructions)
    keyword = parsed.get("keyword")
    if not keyword:
        raise ValueError("키워드가 없습니다.")

    system, user = _build_solar_prompts(keyword, parsed.get("note"), ref, category)

    response = solar_client.chat.completions.create(
        model=SOLAR_MODEL_NAME,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )

    choices = getattr(response, "choices", []) or []
    if not choices or not getattr(choices[0], "message", None):
        raise RuntimeError("SOLAR가 유효한 choices/message를 반환하지 않았습니다.")

    text: str = (choices[0].message.content or "").strip()
    if not text:
        raise RuntimeError("SOLAR가 빈 응답을 반환했습니다.")

    text = format_paragraphs(text)
    text = comprehensive_text_clean(text)
    return text


@router.post("/generate/solar")
async def generate_solar(request: GenerateRequest):
    """
    Upstage SOLAR로 원고 생성. kkk 프롬프트를 사용합니다.
    """
    service = request.service.lower()
    keyword = request.keyword.strip()
    ref = request.ref

    category = get_category_db_name(keyword=keyword)
    db_service = MongoDBService()
    db_service.set_db_name(db_name=category)

    try:
        manuscript = await run_in_threadpool(
            solar_generate, user_instructions=keyword, ref=ref, category=category
        )

        if not manuscript:
            raise HTTPException(status_code=500, detail="SOLAR 원고 생성 실패")

        current_time = time.time()
        document = {
            "content": manuscript,
            "timestamp": current_time,
            "engine": SOLAR_MODEL_NAME,
            "service": service or "solar",
            "category": category,
            "keyword": keyword,
        }

        try:
            db_service.insert_document("manuscripts", document)
            document["_id"] = str(document.get("_id", ""))
        except Exception as e:
            # 저장 실패는 경고만 남기고 본문은 반환
            print(f"SOLAR 데이터베이스 저장 실패: {e}")

        return document
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SOLAR 원고 생성 중 오류: {e}")
    finally:
        if db_service:
            db_service.close_connection()

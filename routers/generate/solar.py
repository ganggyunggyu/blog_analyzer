from __future__ import annotations

import time
import re
from datetime import datetime

from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool

from config import UPSTAGE_API_KEY, solar_client
from mongodb_service import MongoDBService
from schema.generate import GenerateRequest
from utils.get_category_db_name import get_category_db_name
from utils.query_parser import parse_query
from _prompts.system.solar_system import get_solar_system_prompt, get_solar_user_prompt
from utils.text_cleaner import comprehensive_text_clean
from utils.format_paragraphs import format_paragraphs
from utils.progress_logger import progress


router = APIRouter()

SOLAR_MODEL_NAME = "solar-pro2"


def solar_generate(user_instructions: str, ref: str = "", category: str = "") -> str:

    if not UPSTAGE_API_KEY:
        raise ValueError("UPSTAGE_API_KEY가 설정되어 있지 않습니다. .env를 확인하세요.")

    parsed = parse_query(user_instructions)
    keyword = parsed.get("keyword")
    note = parsed.get("note", "") or ""
    if not keyword:
        raise ValueError("키워드가 없습니다.")

    system = get_solar_system_prompt(keyword=keyword, category=category)
    user = get_solar_user_prompt(keyword=keyword, note=note, ref=ref)

    start_ts = time.time()
    print("원고작성 시작")
    response = solar_client.chat.completions.create(
        model=SOLAR_MODEL_NAME,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        reasoning_effort="high",
    )

    choices = getattr(response, "choices", []) or []
    if not choices or not getattr(choices[0], "message", None):
        raise RuntimeError("SOLAR가 유효한 choices/message를 반환하지 않았습니다.")

    text: str = (choices[0].message.content or "").strip()
    if not text:
        raise RuntimeError("SOLAR가 빈 응답을 반환했습니다.")

    text = format_paragraphs(text)
    text = comprehensive_text_clean(text)
    length_no_space = len(re.sub(r"\s+", "", text))
    print(f"원고 길이 체크: {length_no_space}")
    elapsed = time.time() - start_ts
    print(f"원고 소요시간: {elapsed:.2f}s")
    print("원고작성 완료")
    return text


@router.post("/generate/solar")
async def generate_solar(request: GenerateRequest):
    """
    Upstage SOLAR로 원고 생성. kkk 프롬프트를 사용합니다.
    """
    service = request.service.lower()
    keyword = request.keyword.strip()
    ref = request.ref

    category = await get_category_db_name(keyword=keyword)
    db_service = MongoDBService()
    db_service.set_db_name(db_name=category)

    # 디버그 출력: 어떤 서비스/모델/키워드/참조 여부로 실행하는지 표시
    is_ref = bool(ref and ref.strip())
    print(
        f"[GEN] service={service} | model={SOLAR_MODEL_NAME} | category={category} | keyword={keyword} | hasRef={is_ref}"
    )

    try:
        with progress(label=f"{service}:{SOLAR_MODEL_NAME}:{keyword}"):
            manuscript = await run_in_threadpool(
                solar_generate, user_instructions=keyword, ref=ref, category=category
            )

        if not manuscript:
            raise HTTPException(status_code=500, detail="SOLAR 원고 생성 실패")

        document = {
            "content": manuscript,
            "createdAt": datetime.now(),
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

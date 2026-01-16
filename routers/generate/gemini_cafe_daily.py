"""Gemini Cafe Daily - 카페 일상 글 생성 라우터 (18종 페르소나)"""

import time
from datetime import datetime
from typing import Optional

from fastapi import HTTPException, APIRouter
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel

from mongodb_service import MongoDBService
from utils.get_category_db_name import get_category_db_name
from llm.gemini_cafe_daily_service import gemini_cafe_daily_gen, MODEL_NAME
from _prompts.viral import PERSONAS
from utils.progress_logger import progress
from utils.logger import log


router = APIRouter()


class CafeDailyRequest(BaseModel):
    service: str = "cafe_daily"
    keyword: str
    persona_id: Optional[int] = None  # 페르소나 ID (1~18, null이면 랜덤)
    product_name: str = "한려담원 흑염소진액"


@router.post("/generate/gemini-cafe-daily")
async def generator_gemini_cafe_daily(request: CafeDailyRequest):
    """Gemini Cafe Daily 카페 일상 글 생성기 (18종 페르소나)

    - persona_id: 1~18 (null이면 랜덤)
    """
    start_ts = time.time()
    service = request.service.lower()
    keyword = request.keyword.strip()

    category = await get_category_db_name(keyword=keyword)

    log.header("카페 일상글 생성", "📝")
    log.kv("키워드", keyword)
    log.kv("페르소나", request.persona_id or "랜덤")
    log.kv("모델", MODEL_NAME)

    db_service = MongoDBService()
    db_service.set_db_name(db_name=category)

    try:
        with progress(label=f"cafe-daily:{MODEL_NAME}:{keyword}"):
            result = await run_in_threadpool(
                gemini_cafe_daily_gen,
                user_instructions=keyword,
                category=category,
                persona_id=request.persona_id,
                product_name=request.product_name,
            )

        generated_text = result.get("content", "")
        persona_id = result.get("persona_id", 1)
        persona = result.get("persona", "")

        if generated_text:
            document = {
                "content": generated_text,
                "createdAt": datetime.now(),
                "engine": MODEL_NAME,
                "service": f"{service}_gemini_cafe_daily",
                "category": category,
                "keyword": keyword,
                "type": "cafe_daily",
                "persona_id": persona_id,
                "persona": persona,
            }

            try:
                db_service.insert_document("manuscripts", document)
                document["_id"] = str(document["_id"])
                elapsed = time.time() - start_ts
                char_count = len(generated_text.replace(" ", ""))

                log.success("Cafe Daily 완료", keyword=keyword[:15], 길이=f"{char_count}자", 시간=f"{elapsed:.1f}s")

                return document
            except Exception as e:
                log.error("DB 저장 실패", error=str(e))
                raise HTTPException(status_code=500, detail="생성 성공했지만 DB 저장에 실패했습니다.")
        else:
            raise HTTPException(status_code=500, detail="카페 일상 글 생성에 실패했습니다.")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"카페 일상 글 생성 중 오류 발생: {e}")
    finally:
        if db_service:
            db_service.close_connection()


@router.get("/generate/gemini-cafe-daily/personas")
async def get_personas():
    """사용 가능한 페르소나 목록 조회 (18종)"""
    return {
        "count": len(PERSONAS),
        "personas": [
            {
                "id": pid,
                "name": data["name"],
                "age": data["age"],
                "info": data["info"],
                "tone": data["tone"],
            }
            for pid, data in PERSONAS.items()
        ],
    }

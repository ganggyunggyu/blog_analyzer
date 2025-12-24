"""Gemini Cafe - 카페 짧은 글 생성 라우터 (200~300자)"""

import time
from datetime import datetime
from fastapi import HTTPException, APIRouter
from fastapi.concurrency import run_in_threadpool

from mongodb_service import MongoDBService
from utils.get_category_db_name import get_category_db_name
from schema.generate import GenerateRequest
from llm.gemini_cafe_service import gemini_cafe_gen, MODEL_NAME
from utils.progress_logger import progress
from utils.logger import log


router = APIRouter()


@router.post("/generate/gemini-cafe")
async def generator_gemini_cafe(request: GenerateRequest):
    """Gemini Cafe 카페 짧은 글 생성기 (200~300자)"""
    start_ts = time.time()
    service = request.service.lower()
    keyword = request.keyword.strip()

    category = await get_category_db_name(keyword=keyword)

    log.info("Gemini Cafe 생성", keyword=keyword[:20], category=category)

    db_service = MongoDBService()
    db_service.set_db_name(db_name=category)

    try:
        with progress(label=f"cafe:{MODEL_NAME}:{keyword}"):
            generated_text = await run_in_threadpool(
                gemini_cafe_gen,
                user_instructions=keyword,
                category=category,
            )

        if generated_text:
            document = {
                "content": generated_text,
                "createdAt": datetime.now(),
                "engine": MODEL_NAME,
                "service": f"{service}_gemini_cafe",
                "category": category,
                "keyword": keyword,
                "type": "cafe",
            }

            try:
                db_service.insert_document("manuscripts", document)
                document["_id"] = str(document["_id"])
                elapsed = time.time() - start_ts
                char_count = len(generated_text.replace(" ", ""))

                log.success("Cafe 완료", keyword=keyword[:15], 길이=f"{char_count}자", 시간=f"{elapsed:.1f}s")

                return document
            except Exception as e:
                log.error("DB 저장 실패", error=str(e))
                raise HTTPException(status_code=500, detail="생성 성공했지만 DB 저장에 실패했습니다.")
        else:
            raise HTTPException(status_code=500, detail="카페 글 생성에 실패했습니다.")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"카페 글 생성 중 오류 발생: {e}")
    finally:
        if db_service:
            db_service.close_connection()

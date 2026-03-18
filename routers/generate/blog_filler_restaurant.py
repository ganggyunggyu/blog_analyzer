"""Blog Filler Restaurant - 맛집 리스트 블로그 글밥 전용 라우터"""

import time
from datetime import datetime
from fastapi import HTTPException, APIRouter
from fastapi.concurrency import run_in_threadpool

from mongodb_service import MongoDBService
from schema.generate import GenerateRequest
from llm.blog_filler_restaurant_service import blog_filler_restaurant_gen, MODEL_NAME
from utils.progress_logger import progress
from utils.logger import log


router = APIRouter()

DB_NAME = "맛집"


@router.post("/generate/blog-filler-restaurant")
async def generator_blog_filler_restaurant(request: GenerateRequest):
    """맛집 리스트 블로그 글밥 전용 생성기"""
    start_ts = time.time()
    service = request.service.lower()
    keyword = request.keyword.strip()
    ref = request.ref

    log.header("Blog Filler Restaurant 원고 생성", "🍽️")
    log.kv("서비스", service.upper())
    log.kv("키워드", keyword)
    log.kv("카테고리", DB_NAME)
    log.kv("모델", MODEL_NAME)

    db_service = MongoDBService()
    db_service.set_db_name(db_name=DB_NAME)

    try:
        with progress(label=f"{service}:{MODEL_NAME}:{keyword}"):
            generated_manuscript = await run_in_threadpool(
                blog_filler_restaurant_gen, user_instructions=keyword, ref=ref, category=DB_NAME
            )

        if generated_manuscript:
            document = {
                "content": generated_manuscript,
                "createdAt": datetime.now(),
                "engine": MODEL_NAME,
                "service": f"{service}_blog_filler_restaurant",
                "category": DB_NAME,
                "keyword": keyword,
            }

            try:
                db_service.insert_document("manuscripts", document)
                document["_id"] = str(document["_id"])
                elapsed = time.time() - start_ts
                char_count = len(generated_manuscript.replace(" ", ""))

                log.divider()
                log.success(
                    "Blog Filler Restaurant 완료",
                    키워드=keyword,
                    길이=f"{char_count}자",
                    시간=f"{elapsed:.1f}s",
                )

                return document
            except Exception as e:
                log.error(f"DB 저장 실패: {e}")
        else:
            raise HTTPException(status_code=500, detail="원고 생성에 실패했습니다.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"원고 생성 중 오류 발생: {e}")
    finally:
        if db_service:
            db_service.close_connection()

"""Blog Filler Pet - 반려동물 블로그 글밥 쌓기 전용 라우터"""

import time
from datetime import datetime
from fastapi import HTTPException, APIRouter
from fastapi.concurrency import run_in_threadpool

from mongodb_service import MongoDBService
from schema.generate import GenerateRequest
from llm.blog_filler_pet_service import blog_filler_pet_gen, MODEL_NAME
from utils.query_parser import parse_query
from utils.progress_logger import progress
from utils.logger import log


router = APIRouter()

DB_NAME = "애견동물_반려동물_분양"
BLOG_FILLER_PET_V2_SERVICE_ALIASES = (
    "blog-filler-pet-v2",
    "blog_filler_pet_v2",
    "pet-v2",
    "pet_v2",
)


def resolve_blog_filler_pet_runtime(service: str):
    normalized_service = service.strip().lower()

    if normalized_service in BLOG_FILLER_PET_V2_SERVICE_ALIASES:
        from llm.blog_filler_pet_v2_service import (
            MODEL_NAME as MODEL_NAME_V2,
            blog_filler_pet_v2_gen,
        )

        return blog_filler_pet_v2_gen, MODEL_NAME_V2

    return blog_filler_pet_gen, MODEL_NAME


@router.post("/generate/blog-filler-pet")
async def generator_blog_filler_pet(request: GenerateRequest):
    """반려동물 블로그 글밥 쌓기 전용 생성기"""
    start_ts = time.time()
    service = request.service.strip().lower()
    keyword = request.keyword.strip()
    ref = request.ref
    generator, model_name = resolve_blog_filler_pet_runtime(service)

    log.header("Blog Filler Pet 원고 생성", "🐾")
    log.kv("서비스", service.upper())
    log.kv("키워드", keyword)
    log.kv("카테고리", DB_NAME)
    log.kv("모델", model_name)
    log.kv("참조원고", "있음" if ref else "없음")

    db_service = MongoDBService()
    db_service.set_db_name(db_name=DB_NAME)

    try:
        with progress(label=f"{service}:{model_name}:{keyword}"):
            generated_manuscript = await run_in_threadpool(
                generator,
                user_instructions=keyword,
                ref=ref,
                category=DB_NAME,
            )

        if generated_manuscript:
            parsed = parse_query(keyword)

            document = {
                "content": generated_manuscript,
                "createdAt": datetime.now(),
                "engine": model_name,
                "service": f"{service}_blog_filler_pet",
                "category": DB_NAME,
                "keyword": keyword,
            }

            try:
                db_service.insert_document("manuscripts", document)

                if ref:
                    ref_document = {"content": ref, "keyword": parsed["keyword"]}
                    db_service.insert_document("ref", ref_document)

                document["_id"] = str(document["_id"])
                elapsed = time.time() - start_ts
                char_count = len(generated_manuscript.replace(" ", ""))

                log.divider()
                log.success(
                    "Blog Filler Pet 완료",
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

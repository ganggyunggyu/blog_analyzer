"""알리바바 - 단일 스타일 원고 생성 라우터"""

import time
from datetime import datetime

from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool

from llm.alibaba_service import MODEL_NAME, alibaba_gen
from mongodb_service import MongoDBService
from schema.generate import GenerateRequest
from utils.get_category_db_name import get_category_db_name
from utils.logger import log
from utils.progress_logger import progress
from utils.query_parser import parse_query


router = APIRouter()


@router.post("/generate/alibaba")
async def generator_alibaba(request: GenerateRequest):
    """알리바바 원고 생성기"""
    start_ts = time.time()
    service = request.service.lower()
    keyword = request.keyword.strip()
    ref = request.ref

    category = request.category.strip() if request.category else ""
    if not category:
        category = await get_category_db_name(keyword=keyword + ref)

    c_elapsed = time.time() - start_ts

    log.header("알리바바 원고 생성", "🛒")
    log.kv("서비스", service.upper())
    log.kv("키워드", keyword)
    log.kv("카테고리", category)
    log.kv("모델", MODEL_NAME)
    log.kv("참조원고", "있음" if ref else "없음")
    log.kv("분류시간", f"{c_elapsed:.2f}s")

    db_service = MongoDBService()
    db_service.set_db_name(db_name=category or "기타")

    try:
        with progress(label=f"{service}:{MODEL_NAME}:{keyword}"):
            result = await run_in_threadpool(
                alibaba_gen,
                user_instructions=keyword,
                ref=ref,
                category=category,
            )

        generated_manuscript = result["content"]
        if generated_manuscript:
            parsed = parse_query(keyword)
            document = {
                "content": generated_manuscript,
                "createdAt": datetime.now(),
                "engine": MODEL_NAME,
                "service": f"{service}_alibaba",
                "category": category,
                "keyword": keyword,
                "profileId": result["profile_id"],
                "profileLabel": result["profile_label"],
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
                    "알리바바 완료",
                    키워드=keyword,
                    프로필=result["profile_id"],
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

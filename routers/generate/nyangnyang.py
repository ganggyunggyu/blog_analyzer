import time
from datetime import datetime
from fastapi import HTTPException, APIRouter
from fastapi.concurrency import run_in_threadpool

from mongodb_service import MongoDBService
from utils.get_category_db_name import get_category_db_name
from schema.generate import GenerateRequest
from llm.nyangnyang_service import nyangnyang_gen, MODEL_NAME
from utils.query_parser import parse_query
from utils.progress_logger import progress
from utils.logger import log


router = APIRouter()


@router.post("/generate/nyangnyang")
async def generator_nyangnyang(request: GenerateRequest):
    """
    냥냥돌쇠 텍스트 생성기
    """
    start_ts = time.time()
    service = request.service.lower()
    keyword = request.keyword.strip()
    ref = request.ref

    category = await get_category_db_name(keyword=keyword + ref)
    c_elapsed = time.time() - start_ts

    log.header("냥냥돌쇠 원고 생성", "🐱")
    log.kv("서비스", service.upper())
    log.kv("키워드", keyword)
    log.kv("카테고리", category)
    log.kv("모델", MODEL_NAME)
    log.kv("참조원고", "있음" if ref else "없음")
    log.kv("분류시간", f"{c_elapsed:.2f}s")

    db_service = MongoDBService()
    db_service.set_db_name(db_name=category)

    is_ref = len(ref) != 0

    try:
        with progress(label=f"{service}:{MODEL_NAME}:{keyword}"):
            generated_manuscript = await run_in_threadpool(
                nyangnyang_gen, user_instructions=keyword, ref=ref, category=category
            )

        if generated_manuscript:

            parsed = parse_query(keyword)

            document = {
                "content": generated_manuscript,
                "createdAt": datetime.now(),
                "engine": MODEL_NAME,
                "service": f"{service}_nyangnyang",
                "category": category,
                "keyword": keyword,
                "ref": ref if ref else "",
            }

            try:
                db_service.insert_document("manuscripts", document)

                if is_ref:
                    ref_document = {"content": ref, "keyword": parsed["keyword"]}
                    db_service.insert_document("ref", ref_document)

                document["_id"] = str(document["_id"])
                elapsed = time.time() - start_ts

                log.divider()
                log.success("냥냥돌쇠 완료", 키워드=keyword, 카테고리=category, 시간=f"{elapsed:.1f}s")

                return document
            except Exception as e:
                log.error(f"DB 저장 실패: {e}")
        else:
            raise HTTPException(
                status_code=500,
                detail="냥냥돌쇠 원고 생성에 실패했습니다. 내부 로그를 확인하세요.",
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"냥냥돌쇠 원고 생성 중 오류 발생: {e}")
    finally:
        if db_service:
            db_service.close_connection()

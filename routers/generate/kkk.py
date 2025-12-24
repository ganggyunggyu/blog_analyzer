import time
from datetime import datetime
from fastapi import HTTPException, APIRouter
from fastapi.concurrency import run_in_threadpool

from mongodb_service import MongoDBService
from utils.get_category_db_name import get_category_db_name
from schema.generate import GenerateRequest
from llm.kkk_service import kkk_gen, model_name
from utils.query_parser import parse_query
from utils.progress_logger import progress
from utils.logger import log

router = APIRouter()


@router.post("/generate/test")
async def generator_kkk(request: GenerateRequest):
    """
    KKK 테스트용 텍스트 생성기
    """
    start_ts = time.time()
    service = request.service.lower()
    keyword = request.keyword.strip()
    ref = request.ref

    category = await get_category_db_name(keyword=keyword + ref)
    c_elapsed = time.time() - start_ts

    log.info("KKK 생성 시작", keyword=keyword[:20], category=category)

    db_service = MongoDBService()
    db_service.set_db_name(db_name=category)

    is_ref = len(ref) != 0

    try:
        with progress(label=f"{service}:{model_name}:{keyword}"):
            generated_manuscript = await run_in_threadpool(
                kkk_gen, user_instructions=keyword, ref=ref, category=category
            )

        if generated_manuscript:

            parsed = parse_query(keyword)

            document = {
                "content": generated_manuscript,
                "createdAt": datetime.now(),
                "engine": model_name,
                "service": f"{service}_kkk_test",
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

                log.success("KKK 생성 완료", keyword=keyword[:20], time=f"{elapsed:.1f}s")

                return document
            except Exception as e:
                log.error("KKK DB 저장 실패", error=str(e))
        else:
            raise HTTPException(
                status_code=500,
                detail="KKK 원고 생성에 실패했습니다. 내부 로그를 확인하세요.",
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"KKK 원고 생성 중 오류 발생: {e}")
    finally:
        if db_service:
            db_service.close_connection()

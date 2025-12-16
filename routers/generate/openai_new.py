"""OpenAI New - 범용 정보성 원고 생성 라우터"""
import time
from datetime import datetime
from fastapi import HTTPException, APIRouter
from fastapi.concurrency import run_in_threadpool

from mongodb_service import MongoDBService
from utils.get_category_db_name import get_category_db_name
from schema.generate import GenerateRequest
from llm.openai_new_service import openai_new_gen, MODEL_NAME
from utils.progress_logger import progress


router = APIRouter()


@router.post("/generate/openai-new")
async def generator_openai_new(request: GenerateRequest):
    """OpenAI New 범용 정보성 원고 생성기 (GPT-5.2)"""
    start_ts = time.time()
    service = request.service.lower()
    keyword = request.keyword.strip()
    ref = request.ref

    category = await get_category_db_name(keyword=keyword + ref)

    print("\n" + "=" * 60)
    print(f"OpenAI New 원고 생성 시작")
    print("=" * 60)
    print(f"서비스: {service.upper()}")
    print(f"키워드: {keyword}")
    print(f"카테고리: {category}")
    print(f"모델: {MODEL_NAME}")
    print(f"참조원고: {'있음' if ref else '없음'}")
    print("=" * 60 + "\n")

    db_service = MongoDBService()
    db_service.set_db_name(db_name=category)

    try:
        with progress(label=f"{service}:{MODEL_NAME}:{keyword}"):
            generated_manuscript = await run_in_threadpool(
                openai_new_gen, user_instructions=keyword, ref=ref, category=category
            )

        if generated_manuscript:
            document = {
                "content": generated_manuscript,
                "createdAt": datetime.now(),
                "engine": MODEL_NAME,
                "service": f"{service}_openai_new",
                "category": category,
                "keyword": keyword,
            }

            try:
                db_service.insert_document("manuscripts", document)
                document["_id"] = str(document["_id"])
                elapsed = time.time() - start_ts

                print("\n" + "=" * 60)
                print(f"OpenAI New 원고 생성 완료")
                print(f"총 소요시간: {elapsed:.2f}s")
                print("=" * 60 + "\n")

                return document
            except Exception as e:
                print(f"데이터베이스에 저장 실패: {e}")
        else:
            raise HTTPException(status_code=500, detail="원고 생성에 실패했습니다.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"원고 생성 중 오류 발생: {e}")
    finally:
        if db_service:
            db_service.close_connection()

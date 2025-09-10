from fastapi import HTTPException, APIRouter

from mongodb_service import MongoDBService
from utils.get_category_db_name import get_category_db_name
from fastapi.concurrency import run_in_threadpool
from fastapi.concurrency import run_in_threadpool

from schema.generate import GenerateRequest
from llm.gpt_4_v2_service import gpt_4_v2_gen, model_name

router = APIRouter()


@router.post("/generate/gpt-4-v2")
async def generator_gpt(request: GenerateRequest):
    """
    Generates text using the specified service (gpt, claude, or solar).
    """
    service = request.service.lower()
    keyword = request.keyword.strip()
    ref = request.ref

    category = get_category_db_name(keyword=keyword)

    db_service = MongoDBService()
    db_service.set_db_name(db_name=category)

    # 디버그 출력: 어떤 서비스/모델/키워드/참조 여부로 실행하는지 표시
    is_ref = bool(ref and ref.strip())
    print(
        f"[GEN] service={service} | model={model_name} | category={category} | keyword={keyword} | hasRef={is_ref}"
    )

    try:

        generated_manuscript = await run_in_threadpool(
            gpt_4_v2_gen, user_instructions=keyword, ref=ref
        )

        if generated_manuscript:
            import time

            current_time = time.time()
            document = {
                "content": generated_manuscript,
                "timestamp": current_time,
                "engine": model_name,
                "keyword": keyword,
            }
            try:
                db_service.insert_document("manuscripts", document)
                document["_id"] = str(document["_id"])

                return document
            except Exception as e:
                _ = e  # suppress noisy print
        else:
            raise HTTPException(
                status_code=500,
                detail="원고 생성에 실패했습니다. 내부 로그를 확인하세요.",
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"원고 생성 중 오류 발생: {e}")
    finally:
        if db_service:
            db_service.close_connection()

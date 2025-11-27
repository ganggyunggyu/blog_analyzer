from fastapi import HTTPException, APIRouter
from fastapi.concurrency import run_in_threadpool

from llm.chunk_service import chunk_gen
from llm.gpt_merge_service import gpt_merge_gen
from mongodb_service import MongoDBService
from utils.get_category_db_name import get_category_db_name
from schema.generate import GenerateRequest
from llm.gpt_merge_service import gpt_merge_gen, model_name
from utils.query_parser import parse_query
from utils.progress_logger import progress


router = APIRouter()


@router.post("/generate/gpt-merge")
async def merge(request: GenerateRequest):
    """
    청크 텍스트 생성기
    """
    service = request.service.lower()
    keyword = request.keyword.strip()
    ref = request.ref

    category = await get_category_db_name(keyword=keyword)

    db_service = MongoDBService()
    db_service.set_db_name(db_name=category)

    is_ref = len(ref) != 0

    # 디버그 출력: 어떤 서비스/모델/키워드/참조 여부로 실행하는지 표시
    is_ref = bool(ref and ref.strip())
    print(
        f"[GEN] service={service} | model={model_name} | category={category} | keyword={keyword} | hasRef={is_ref}"
    )

    try:
        with progress(label=f"{service}:{model_name}:{keyword}"):
            generated_manuscript = await run_in_threadpool(
                gpt_merge_gen, user_input=keyword, title=ref, category=category
            )

        if generated_manuscript:
            from datetime import datetime

            parsed = parse_query(keyword)

            document = {
                "content": generated_manuscript,
                "createdAt": datetime.now(),
                "engine": model_name,
                "service": f"{service}_chunk",
                "category": category,
                "keyword": keyword,
                "test_mode": True,
            }

            try:
                db_service.insert_document("manuscripts", document)

                if is_ref:
                    ref_document = {"content": ref, "keyword": parsed["keyword"]}
                    db_service.insert_document("ref", ref_document)

                document["_id"] = str(document["_id"])

                return document
            except Exception as e:
                print(f"Merge 데이터베이스에 저장 실패: {e}")
        else:
            raise HTTPException(
                status_code=500,
                detail="Merge 원고 생성에 실패했습니다. 내부 로그를 확인하세요.",
            )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Merge 원고 생성 중 오류 발생: {e}"
        )
    finally:
        if db_service:
            db_service.close_connection()

from fastapi import HTTPException, APIRouter
from fastapi.concurrency import run_in_threadpool

from mongodb_service import MongoDBService
from utils.categorize_keyword_with_ai import categorize_keyword_with_ai
from schema.generate import GenerateRequest
from llm.kkk_service import kkk_gen, model_name


router = APIRouter()


@router.post("/generate/kkk")
async def generator_kkk(request: GenerateRequest):
    """
    KKK 테스트용 텍스트 생성기
    """
    service = request.service.lower()
    keyword = request.keyword.strip()
    ref = request.ref

    category = categorize_keyword_with_ai(keyword=keyword)

    db_service = MongoDBService()
    db_service.set_db_name(db_name=category)

    print(
        f"""
서비스: {service}
키워드: {request.keyword}
참조문서 유무: {len(ref) != 0}
선택된 카테고리: {category}
KKK 테스트 모드 활성화
"""
    )

    try:
        generated_manuscript = await run_in_threadpool(
            kkk_gen, user_instructions=keyword, ref=ref
        )

        if generated_manuscript:
            import time

            current_time = time.time()
            document = {
                "content": generated_manuscript,
                "timestamp": current_time,
                "engine": model_name,
                "service": f"{service}_kkk_test",  # 테스트임을 명시
                "category": category,
                "keyword": keyword,
                "test_mode": True,  # 테스트 모드 플래그
            }
            
            try:
                db_service.insert_document("manuscripts", document)
                document["_id"] = str(document["_id"])

                return document
            except Exception as e:
                print(f"KKK 데이터베이스에 저장 실패: {e}")
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
from fastapi import HTTPException, APIRouter
from fastapi.concurrency import run_in_threadpool
from fastapi.concurrency import run_in_threadpool

from mongodb_service import MongoDBService
from utils.categorize_keyword_with_ai import categorize_keyword_with_ai
from schema.generate import GenerateRequest
from llm.gpt_5_service import gpt_5_gen, model_name


router = APIRouter()


@router.post("/generate/gpt-5-v2")
async def generator_gpt(request: GenerateRequest):
    """
    Generates text using the specified service (gpt, claude, or solar).
    """
    service = request.service.lower()
    keyword = request.keyword.strip()
    ref = request.ref

    category = categorize_keyword_with_ai(keyword=keyword)

    db_service = MongoDBService()
    db_service.set_db_name(db_name=category)

    print(f'''
서비스: {service}
키워드: {request.keyword}
참조문서 유무: {len(ref) != 0}
선택된 카테고리: {category}
''')

    try:

        generated_manuscript = await run_in_threadpool(
            gpt_5_gen,
            user_instructions=keyword,
            ref=ref
        )
        
        if generated_manuscript:
            import time
            current_time = time.time()
            document = {
                'content' : generated_manuscript,
                'timestamp': current_time,
                'engine': model_name,
                'keyword' : keyword
            }
            try: 
                db_service.insert_document("manuscripts", document)
                document['_id'] = str(document['_id'])

                return document
            except Exception as e:
                print(f"데이터베이스에 저장 실패: {e}")
        else:
            raise HTTPException(
                status_code=500,
                detail="원고 생성에 실패했습니다. 내부 로그를 확인하세요."
    )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"원고 생성 중 오류 발생: {e}")
    finally:
        if db_service:
            db_service.close_connection()
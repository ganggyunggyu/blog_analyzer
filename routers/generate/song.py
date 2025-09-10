from fastapi import HTTPException, APIRouter
from fastapi.concurrency import run_in_threadpool

from mongodb_service import MongoDBService
from utils.get_category_db_name import get_category_db_name
from schema.generate import GenerateRequest
from llm._song_service import song_gen, model_name
from utils.query_parser import parse_query


router = APIRouter()


@router.post("/generate/song")
async def generator_song(request: GenerateRequest):
    """
    SONG 서비스 텍스트 생성기
    """
    service = request.service.lower()
    keyword = request.keyword.strip()
    ref = request.ref

    category = get_category_db_name("song")

    is_ref: bool = False

    db_service = MongoDBService()
    db_service.set_db_name(db_name=category)
    if ref != None:
        is_ref = len(ref) != 0

    # 디버그 출력: 어떤 서비스/모델/키워드/참조 여부로 실행하는지 표시
    is_ref = bool(ref and ref.strip())
    print(
        f"[GEN] service={service} | model={model_name} | category={category} | keyword={keyword} | hasRef={is_ref}"
    )

    try:
        generated_manuscript = await run_in_threadpool(
            song_gen, user_instructions=keyword, ref="", category=category
        )

        if generated_manuscript:
            import time

            parsed = parse_query(keyword)

            current_time = time.time()
            document = {
                "content": generated_manuscript,
                "timestamp": current_time,
                "engine": model_name,
                "service": f"{service}_song",
                "category": category,
                "keyword": keyword,
            }

            try:
                db_service.insert_document("manuscripts", document)

                if is_ref:
                    ref_document = {"content": ref, "keyword": parsed["keyword"]}
                    db_service.insert_document("ref", ref_document)

                document["_id"] = str(document["_id"])

                return document
            except Exception as e:
                print(f"SONG 데이터베이스에 저장 실패: {e}")
        else:
            raise HTTPException(
                status_code=500,
                detail="SONG 원고 생성에 실패했습니다. 내부 로그를 확인하세요.",
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SONG 원고 생성 중 오류 발생: {e}")
    finally:
        if db_service:
            db_service.close_connection()

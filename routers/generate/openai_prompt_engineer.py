import time
from datetime import datetime
from fastapi import HTTPException, APIRouter
from fastapi.concurrency import run_in_threadpool

from mongodb_service import MongoDBService
from utils.get_category_db_name import get_category_db_name
from schema.generate import GenerateRequest
from llm.openai_prompt_engineer_service import openai_prompt_gen, model_name
from utils.query_parser import parse_query
from utils.progress_logger import progress


router = APIRouter()


@router.post("/generate/openai-prompt-engineer")
async def generator_openai_prompt_engineer(request: GenerateRequest):
    """
    OpenAI API 프롬프트 엔지니어 서비스
    """
    start_ts = time.time()
    service = request.service.lower()
    keyword = request.keyword.strip()
    ref = request.ref

    category = await get_category_db_name(keyword=keyword + ref)
    c_elapsed = time.time() - start_ts

    print("\n" + "=" * 60)
    print(f"🚀 OpenAI 프롬프트 엔지니어 시작")
    print("=" * 60)
    print(f"📌 서비스    : {service.upper()}")
    print(f"🎯 키워드    : {keyword}")
    print(f"📁 카테고리  : {category}")
    print(f"🤖 모델      : {model_name}")
    print(f"📝 참조원고  : {'✅ 있음' if len(ref) != 0 else '❌ 없음'}")
    print(f"⏱️  분류시간  : {c_elapsed:.2f}s")
    print("=" * 60 + "\n")

    db_service = MongoDBService()
    db_service.set_db_name(db_name=category)

    is_ref = len(ref) != 0

    try:
        with progress(label=f"{service}:{model_name}:{keyword}"):
            generated_manuscript = await run_in_threadpool(
                openai_prompt_gen, user_instructions=keyword, ref=ref, category=category
            )

        if generated_manuscript:

            parsed = parse_query(keyword)

            document = {
                "content": generated_manuscript,
                "createdAt": datetime.now(),
                "engine": model_name,
                "service": f"{service}_openai_prompt_engineer",
                "category": category,
                "keyword": keyword,
                "ref": ref if ref else "",
                "work_start_date": "2025-01-15",
            }

            try:
                db_service.insert_document("manuscripts", document)

                if is_ref:
                    ref_document = {"content": ref, "keyword": parsed["keyword"]}
                    db_service.insert_document("ref", ref_document)

                document["_id"] = str(document["_id"])
                elapsed = time.time() - start_ts

                print("\n" + "=" * 60)
                print(f"✅ OpenAI 프롬프트 엔지니어 완료")
                print("=" * 60)
                print(f"🎯 키워드       : {keyword}")
                print(f"📁 카테고리     : {category}")
                print(f"⏱️  총 소요시간  : {elapsed:.2f}s")
                print(f"💾 DB 저장      : ✅ 성공")
                print("=" * 60 + "\n")

                return document
            except Exception as e:
                print(f"OpenAI 프롬프트 엔지니어 데이터베이스에 저장 실패: {e}")
        else:
            raise HTTPException(
                status_code=500,
                detail="OpenAI 프롬프트 엔지니어 생성에 실패했습니다. 내부 로그를 확인하세요.",
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI 프롬프트 엔지니어 생성 중 오류 발생: {e}")
    finally:
        if db_service:
            db_service.close_connection()

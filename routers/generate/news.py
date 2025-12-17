import time
from datetime import datetime
from fastapi import HTTPException, APIRouter
from fastapi.concurrency import run_in_threadpool

from mongodb_service import MongoDBService
from utils.get_category_db_name import get_category_db_name
from schema.generate import GenerateRequest
from llm.news_service import news_gen, model_name
from utils.query_parser import parse_query
from utils.progress_logger import progress


router = APIRouter()


@router.post("/generate/news")
async def generator_news(request: GenerateRequest):
    start_ts = time.time()
    service = request.service.lower()
    keyword = request.keyword.strip()
    ref = request.ref

    category = await get_category_db_name(keyword=keyword + ref)
    c_elapsed = time.time() - start_ts

    print("\n" + "=" * 60)
    print(f"🚀 실시간 소식 원고 생성 시작")
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
                news_gen, user_instructions=keyword, ref=ref, category=category
            )

        if generated_manuscript:

            parsed = parse_query(keyword)

            document = {
                "content": generated_manuscript,
                "createdAt": datetime.now(),
                "engine": model_name,
                "service": f"{service}_news",
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

                print("\n" + "=" * 60)
                print(f"✅ 실시간 소식 원고 생성 완료")
                print("=" * 60)
                print(f"🎯 키워드       : {keyword}")
                print(f"📁 카테고리     : {category}")
                print(f"⏱️  총 소요시간  : {elapsed:.2f}s")
                print(f"💾 DB 저장      : ✅ 성공")
                print("=" * 60 + "\n")

                return document
            except Exception as e:
                print(f"실시간 소식 데이터베이스에 저장 실패: {e}")
        else:
            raise HTTPException(
                status_code=500,
                detail="실시간 소식 원고 생성에 실패했습니다. 내부 로그를 확인하세요.",
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"실시간 소식 원고 생성 중 오류 발생: {e}")
    finally:
        if db_service:
            db_service.close_connection()

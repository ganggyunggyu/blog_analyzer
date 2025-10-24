import time
from fastapi import HTTPException, APIRouter
from fastapi.concurrency import run_in_threadpool

from mongodb_service import MongoDBService
from utils.get_category_db_name import get_category_db_name
from schema.generate import GenerateRequest
from llm.mdx_post_service import mdx_post_gen, model_name
from utils.query_parser import parse_query
from utils.progress_logger import progress


router = APIRouter()


@router.post("/generate/mdx-post")
async def generator_mdx_post(request: GenerateRequest):
    """
    MDX 포스트 생성기
    """
    start_ts = time.time()
    service = request.service.lower()
    keyword = request.keyword.strip()
    ref = request.ref

    category = await get_category_db_name(keyword=keyword + ref)
    c_elapsed = time.time() - start_ts

    print("\n" + "=" * 60)
    print("🚀 MDX POST 원고 생성 시작")
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
                mdx_post_gen, user_instructions=keyword, ref=ref, category=category
            )

        if generated_manuscript:
            parsed = parse_query(keyword)
            current_time = time.time()

            document = {
                "content": generated_manuscript,
                "timestamp": current_time,
                "engine": model_name,
                "service": f"{service}_mdx_post",
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
                print("✅ MDX POST 원고 생성 완료")
                print("=" * 60)
                print(f"🎯 키워드       : {keyword}")
                print(f"📁 카테고리     : {category}")
                print(f"⏱️  총 소요시간  : {elapsed:.2f}s")
                print("💾 DB 저장      : ✅ 성공")
                print("=" * 60 + "\n")

                return document
            except Exception as e:
                print(f"MDX POST 데이터베이스에 저장 실패: {e}")
        else:
            raise HTTPException(
                status_code=500,
                detail="MDX POST 원고 생성에 실패했습니다. 내부 로그를 확인하세요.",
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MDX POST 원고 생성 중 오류 발생: {e}")
    finally:
        if db_service:
            db_service.close_connection()

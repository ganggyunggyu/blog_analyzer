from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool

from mongodb_service import MongoDBService
from schema.search import KeywordSearchRequest
from config import MONGO_DB_NAME

router = APIRouter()


def search_manuscripts_by_keyword(
    query: str,
    category: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
) -> Dict[str, Any]:
    """
    키워드로 원고 검색

    Args:
        query: 검색할 키워드
        category: 카테고리 필터 (None이면 전체 검색)
        skip: 건너뛸 문서 수
        limit: 반환할 문서 수

    Returns:
        {
            "documents": [...],
            "total": 전체 결과 수,
            "page": 현재 페이지,
            "limit": 페이지당 결과 수
        }
    """
    db_service = MongoDBService()

    try:
        if category:
            db_service.set_db_name(db_name=category)
        else:
            db_service.set_db_name(db_name=MONGO_DB_NAME)

        # 검색 쿼리: content 또는 keyword 필드에서 검색
        search_query = {
            "$or": [
                {"content": {"$regex": query, "$options": "i"}},
                {"keyword": {"$regex": query, "$options": "i"}},
            ]
        }

        # 전체 결과 수 계산
        total = db_service.db["manuscripts"].count_documents(search_query)

        # 페이지네이션 적용하여 문서 조회
        documents = list(
            db_service.db["manuscripts"]
            .find(search_query)
            .sort("timestamp", -1)  # 최신순 정렬
            .skip(skip)
            .limit(limit)
        )

        # _id를 문자열로 변환
        for doc in documents:
            if "_id" in doc:
                doc["_id"] = str(doc["_id"])

        return {
            "documents": documents,
            "total": total,
            "skip": skip,
            "limit": limit,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"원고 검색 중 오류 발생: {str(e)}"
        )
    finally:
        db_service.close_connection()


@router.post("/search/keyword")
async def search_keyword(request: KeywordSearchRequest):
    """
    키워드로 원고 검색

    - query: 검색할 키워드
    - category: 카테고리 필터 (선택)
    - page: 페이지 번호 (기본값: 1)
    - limit: 페이지당 결과 수 (기본값: 20, 최대: 100)
    """
    query = request.query.strip()

    if not query:
        raise HTTPException(status_code=400, detail="검색 키워드를 입력해주세요.")

    skip = (request.page - 1) * request.limit

    print(f"\n{'='*60}")
    print(f"🔍 원고 검색 시작")
    print(f"{'='*60}")
    print(f"📌 검색어     : {query}")
    print(f"📁 카테고리   : {request.category or '전체'}")
    print(f"📄 페이지     : {request.page}")
    print(f"📊 결과 수    : {request.limit}개")
    print(f"{'='*60}\n")

    result = await run_in_threadpool(
        search_manuscripts_by_keyword,
        query=query,
        category=request.category,
        skip=skip,
        limit=request.limit,
    )

    print(f"\n{'='*60}")
    print(f"✅ 검색 완료")
    print(f"{'='*60}")
    print(f"📊 전체 결과  : {result['total']}개")
    print(f"📄 반환 결과  : {len(result['documents'])}개")
    print(f"{'='*60}\n")

    return result

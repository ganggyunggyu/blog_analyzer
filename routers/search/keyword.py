from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool
from pymongo import MongoClient

from mongodb_service import MongoDBService
from schema.search import KeywordSearchRequest
from config import MONGO_URI
from _constants.categories import CATEGORIES
from utils.logger import log

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
    search_query = {
        "$or": [
            {"content": {"$regex": query, "$options": "i"}},
            {"keyword": {"$regex": query, "$options": "i"}},
        ],
        "deleted": {"$ne": True}
    }

    if category:
        db_service = MongoDBService()
        try:
            db_service.set_db_name(db_name=category)

            total = db_service.db["manuscripts"].count_documents(search_query)

            documents = list(
                db_service.db["manuscripts"]
                .find(search_query)
                .sort("createdAt", -1)
                .skip(skip)
                .limit(limit)
            )

            for doc in documents:
                if "_id" in doc:
                    doc["_id"] = str(doc["_id"])
                doc["__category"] = category

            return {
                "documents": documents,
                "total": total,
                "skip": skip,
                "limit": limit,
            }
        finally:
            db_service.close_connection()
    else:
        client = MongoClient(MONGO_URI)
        all_documents = []
        total = 0

        try:
            for cat in CATEGORIES:
                try:
                    db = client[cat]
                    collection = db["manuscripts"]

                    cat_total = collection.count_documents(search_query)
                    total += cat_total

                    docs = list(
                        collection.find(search_query)
                        .sort("createdAt", -1)
                        .limit(limit * 2)
                    )

                    for doc in docs:
                        if "_id" in doc:
                            doc["_id"] = str(doc["_id"])
                        doc["__category"] = cat
                        all_documents.append(doc)

                except Exception:
                    continue

            from datetime import datetime
            all_documents.sort(
                key=lambda d: d.get("createdAt") or datetime.min,
                reverse=True
            )

            paginated = all_documents[skip:skip + limit]

            return {
                "documents": paginated,
                "total": total,
                "skip": skip,
                "limit": limit,
            }

        finally:
            client.close()


MAX_QUERY_LENGTH = 100


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

    if len(query) > MAX_QUERY_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"검색어가 너무 깁니다. (최대 {MAX_QUERY_LENGTH}자)"
        )

    skip = (request.page - 1) * request.limit

    result = await run_in_threadpool(
        search_manuscripts_by_keyword,
        query=query,
        category=request.category,
        skip=skip,
        limit=request.limit,
    )
    log.success("원고 검색", query=query[:15], total=result['total'])

    return result

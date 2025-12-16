"""검색 자동완성 API"""
from typing import List, Dict, Any
from fastapi import APIRouter, Query
from fastapi.concurrency import run_in_threadpool
from pymongo import MongoClient

from config import MONGO_URI
from _constants.categories import CATEGORIES

router = APIRouter()


MAX_QUERY_LENGTH = 50


def get_autocomplete_suggestions(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    모든 카테고리 DB에서 키워드 자동완성 추천

    Args:
        query: 검색어 (2자 이상)
        limit: 결과 수 (기본값: 5)

    Returns:
        [{"keyword": "위고비 효능", "count": 152}, ...]
    """
    if len(query) < 2 or len(query) > MAX_QUERY_LENGTH:
        return []

    client = MongoClient(MONGO_URI)
    keyword_counts: Dict[str, int] = {}

    try:
        for category in CATEGORIES:
            try:
                db = client[category]
                collection = db["manuscripts"]

                pipeline = [
                    {
                        "$match": {
                            "keyword": {"$regex": query, "$options": "i"}
                        }
                    },
                    {
                        "$group": {
                            "_id": "$keyword",
                            "count": {"$sum": 1}
                        }
                    }
                ]

                for doc in collection.aggregate(pipeline):
                    kw = doc["_id"]
                    if kw:
                        keyword_counts[kw] = keyword_counts.get(kw, 0) + doc["count"]

            except Exception:
                continue

        sorted_keywords = sorted(
            keyword_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:limit]

        return [{"keyword": kw, "count": cnt} for kw, cnt in sorted_keywords]

    finally:
        client.close()


@router.get("/search/autocomplete")
async def autocomplete(
    q: str = Query(..., min_length=2, description="검색어 (2자 이상)"),
    limit: int = Query(5, ge=1, le=10, description="결과 수")
):
    """
    검색어 자동완성 API

    - **q**: 검색어 (2자 이상 필수)
    - **limit**: 결과 수 (기본값: 5, 최대: 10)

    Returns:
        {"suggestions": [{"keyword": "위고비 효능", "count": 152}, ...]}
    """
    suggestions = await run_in_threadpool(get_autocomplete_suggestions, q, limit)

    return {"suggestions": suggestions}

"""인기 검색어 API"""
from typing import List, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Query
from fastapi.concurrency import run_in_threadpool
from pymongo import MongoClient

from config import MONGO_URI
from _constants.categories import CATEGORIES

router = APIRouter()


def get_popular_keywords(period: str = "week", limit: int = 10) -> Dict[str, Any]:
    """
    인기 검색어 조회

    Args:
        period: 기간 (today, week, month)
        limit: 결과 수

    Returns:
        {"period": "week", "keywords": [...]}
    """
    client = MongoClient(MONGO_URI)
    keyword_counts: Dict[str, int] = {}

    now = datetime.now()
    if period == "today":
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "month":
        start_date = now - timedelta(days=30)
    else:
        start_date = now - timedelta(days=7)

    try:
        for category in CATEGORIES:
            try:
                db = client[category]
                collection = db["manuscripts"]

                pipeline = [
                    {
                        "$match": {
                            "createdAt": {"$gte": start_date},
                            "deleted": {"$ne": True}
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

        keywords = []
        for rank, (kw, cnt) in enumerate(sorted_keywords, 1):
            keywords.append({
                "rank": rank,
                "keyword": kw,
                "count": cnt,
                "change": 0
            })

        return {
            "period": period,
            "keywords": keywords
        }

    finally:
        client.close()


@router.get("/search/popular")
async def popular_keywords(
    period: str = Query("week", regex="^(today|week|month)$", description="기간"),
    limit: int = Query(10, ge=1, le=20, description="결과 수")
):
    """
    인기 검색어 API

    - **period**: 기간 (today, week, month) - 기본값: week
    - **limit**: 결과 수 (기본값: 10, 최대: 20)

    Returns:
        {"period": "week", "keywords": [{"rank": 1, "keyword": "위고비", "count": 523, "change": 0}, ...]}
    """
    result = await run_in_threadpool(get_popular_keywords, period, limit)

    return result

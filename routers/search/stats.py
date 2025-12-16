"""원고 통계 API"""
from typing import Dict, Any, List
from datetime import datetime, timedelta
from fastapi import APIRouter, Query
from fastapi.concurrency import run_in_threadpool
from pymongo import MongoClient

from config import MONGO_URI
from _constants.categories import CATEGORIES

router = APIRouter()


def get_manuscript_stats(period: str = "week") -> Dict[str, Any]:
    """
    원고 통계 조회

    Args:
        period: 기간 (day, week, month)

    Returns:
        통계 데이터
    """
    client = MongoClient(MONGO_URI)

    now = datetime.now()
    if period == "day":
        start_date = now - timedelta(days=1)
        days_count = 1
    elif period == "month":
        start_date = now - timedelta(days=30)
        days_count = 30
    else:
        start_date = now - timedelta(days=7)
        days_count = 7

    total_count = 0
    by_engine: Dict[str, int] = {}
    by_category: Dict[str, int] = {}
    daily_counts: Dict[str, int] = {}

    for i in range(days_count):
        date = (now - timedelta(days=i)).strftime("%Y-%m-%d")
        daily_counts[date] = 0

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
                            "_id": {
                                "engine": "$engine",
                                "date": {
                                    "$dateToString": {
                                        "format": "%Y-%m-%d",
                                        "date": "$createdAt"
                                    }
                                }
                            },
                            "count": {"$sum": 1}
                        }
                    }
                ]

                for doc in collection.aggregate(pipeline):
                    engine = doc["_id"].get("engine", "unknown")
                    date = doc["_id"].get("date")
                    count = doc["count"]

                    total_count += count
                    by_engine[engine] = by_engine.get(engine, 0) + count
                    by_category[category] = by_category.get(category, 0) + count

                    if date in daily_counts:
                        daily_counts[date] += count

            except Exception:
                continue

        daily = [
            {"date": date, "count": count}
            for date, count in sorted(daily_counts.items())
        ]

        return {
            "period": period,
            "totalCount": total_count,
            "byEngine": by_engine,
            "byCategory": by_category,
            "daily": daily
        }

    finally:
        client.close()


@router.get("/search/stats")
async def manuscript_stats(
    period: str = Query("week", regex="^(day|week|month)$", description="기간")
):
    """
    원고 통계 API

    - **period**: 기간 (day, week, month) - 기본값: week

    Returns:
        {
            "period": "week",
            "totalCount": 1523,
            "byEngine": {"gpt-5-v2": 523, ...},
            "byCategory": {"health": 623, ...},
            "daily": [{"date": "2024-12-10", "count": 152}, ...]
        }
    """
    result = await run_in_threadpool(get_manuscript_stats, period)

    return result

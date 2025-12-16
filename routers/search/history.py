"""최근 검색어 API"""
from typing import List, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Query, Body
from fastapi.concurrency import run_in_threadpool
from pymongo import MongoClient, DESCENDING

from config import MONGO_URI

router = APIRouter()

HISTORY_DB = "search_system"
HISTORY_COLLECTION = "search_history"


def get_recent_searches(user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    최근 검색어 조회

    Args:
        user_id: 사용자 식별자
        limit: 결과 수

    Returns:
        [{"keyword": "위고비", "searchedAt": "...", "category": "..."}, ...]
    """
    client = MongoClient(MONGO_URI)

    try:
        db = client[HISTORY_DB]
        collection = db[HISTORY_COLLECTION]

        cursor = collection.find(
            {"userId": user_id}
        ).sort("searchedAt", DESCENDING).limit(limit)

        results = []
        for doc in cursor:
            results.append({
                "keyword": doc.get("keyword", ""),
                "category": doc.get("category", ""),
                "searchedAt": doc.get("searchedAt"),
            })

        return results

    finally:
        client.close()


def save_search_history(user_id: str, keyword: str, category: str = "") -> Dict[str, Any]:
    """
    검색어 저장

    Args:
        user_id: 사용자 식별자
        keyword: 검색어
        category: 카테고리

    Returns:
        {"ok": True}
    """
    client = MongoClient(MONGO_URI)

    try:
        db = client[HISTORY_DB]
        collection = db[HISTORY_COLLECTION]

        collection.update_one(
            {"userId": user_id, "keyword": keyword},
            {
                "$set": {
                    "userId": user_id,
                    "keyword": keyword,
                    "category": category,
                    "searchedAt": datetime.now(),
                }
            },
            upsert=True
        )

        return {"ok": True}

    finally:
        client.close()


def delete_search_history(user_id: str, keyword: str = None) -> Dict[str, Any]:
    """
    검색어 삭제

    Args:
        user_id: 사용자 식별자
        keyword: 특정 검색어 (없으면 전체 삭제)

    Returns:
        {"ok": True, "deletedCount": n}
    """
    client = MongoClient(MONGO_URI)

    try:
        db = client[HISTORY_DB]
        collection = db[HISTORY_COLLECTION]

        if keyword:
            result = collection.delete_one({"userId": user_id, "keyword": keyword})
        else:
            result = collection.delete_many({"userId": user_id})

        return {"ok": True, "deletedCount": result.deleted_count}

    finally:
        client.close()


@router.get("/search/history")
async def get_history(
    user_id: str = Query(..., description="사용자 식별자"),
    limit: int = Query(10, ge=1, le=50, description="결과 수")
):
    """
    최근 검색어 조회 API

    - **user_id**: 사용자 식별자 (필수)
    - **limit**: 결과 수 (기본값: 10, 최대: 50)

    Returns:
        {"history": [{"keyword": "위고비", "category": "...", "searchedAt": "..."}, ...]}
    """
    history = await run_in_threadpool(get_recent_searches, user_id, limit)

    return {"history": history}


@router.post("/search/history")
async def add_history(
    user_id: str = Query(..., description="사용자 식별자"),
    keyword: str = Body(..., embed=True, description="검색어"),
    category: str = Body("", embed=True, description="카테고리")
):
    """
    검색어 저장 API

    - **user_id**: 사용자 식별자 (필수)
    - **keyword**: 검색어 (필수)
    - **category**: 카테고리 (선택)

    Returns:
        {"ok": true}
    """
    result = await run_in_threadpool(save_search_history, user_id, keyword, category)

    return result


@router.delete("/search/history")
async def delete_history(
    user_id: str = Query(..., description="사용자 식별자"),
    keyword: str = Query(None, description="특정 검색어 (없으면 전체 삭제)")
):
    """
    검색어 삭제 API

    - **user_id**: 사용자 식별자 (필수)
    - **keyword**: 특정 검색어 (없으면 전체 삭제)

    Returns:
        {"ok": true, "deletedCount": n}
    """
    result = await run_in_threadpool(delete_search_history, user_id, keyword)

    return result

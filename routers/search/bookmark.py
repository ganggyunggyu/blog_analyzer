"""즐겨찾기 API"""
from typing import List, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Query, Body, HTTPException
from fastapi.concurrency import run_in_threadpool
from pymongo import MongoClient, DESCENDING
from bson import ObjectId

from config import MONGO_URI

router = APIRouter()

BOOKMARK_DB = "search_system"
BOOKMARK_COLLECTION = "bookmarks"


def get_bookmarks(user_id: str, limit: int = 20, offset: int = 0) -> Dict[str, Any]:
    """
    즐겨찾기 목록 조회

    Args:
        user_id: 사용자 식별자
        limit: 결과 수
        offset: 시작 위치

    Returns:
        {"bookmarks": [...], "total": n}
    """
    client = MongoClient(MONGO_URI)

    try:
        db = client[BOOKMARK_DB]
        collection = db[BOOKMARK_COLLECTION]

        total = collection.count_documents({"userId": user_id})

        cursor = collection.find(
            {"userId": user_id}
        ).sort("createdAt", DESCENDING).skip(offset).limit(limit)

        bookmarks = []
        for doc in cursor:
            bookmarks.append({
                "_id": str(doc["_id"]),
                "manuscriptId": doc.get("manuscriptId", ""),
                "category": doc.get("category", ""),
                "keyword": doc.get("keyword", ""),
                "preview": doc.get("preview", ""),
                "createdAt": doc.get("createdAt"),
            })

        return {"bookmarks": bookmarks, "total": total}

    finally:
        client.close()


def add_bookmark(
    user_id: str,
    manuscript_id: str,
    category: str,
    keyword: str = "",
    preview: str = ""
) -> Dict[str, Any]:
    """
    즐겨찾기 추가

    Args:
        user_id: 사용자 식별자
        manuscript_id: 원고 ID
        category: 카테고리 (DB명)
        keyword: 키워드
        preview: 미리보기 텍스트

    Returns:
        {"ok": True, "bookmarkId": "..."}
    """
    client = MongoClient(MONGO_URI)

    try:
        db = client[BOOKMARK_DB]
        collection = db[BOOKMARK_COLLECTION]

        existing = collection.find_one({
            "userId": user_id,
            "manuscriptId": manuscript_id
        })

        if existing:
            return {"ok": True, "bookmarkId": str(existing["_id"]), "message": "이미 즐겨찾기에 추가됨"}

        result = collection.insert_one({
            "userId": user_id,
            "manuscriptId": manuscript_id,
            "category": category,
            "keyword": keyword,
            "preview": preview[:200] if preview else "",
            "createdAt": datetime.now(),
        })

        return {"ok": True, "bookmarkId": str(result.inserted_id)}

    finally:
        client.close()


def remove_bookmark(user_id: str, bookmark_id: str = None, manuscript_id: str = None) -> Dict[str, Any]:
    """
    즐겨찾기 삭제

    Args:
        user_id: 사용자 식별자
        bookmark_id: 즐겨찾기 ID
        manuscript_id: 원고 ID (bookmark_id 없을 때 사용)

    Returns:
        {"ok": True}
    """
    client = MongoClient(MONGO_URI)

    try:
        db = client[BOOKMARK_DB]
        collection = db[BOOKMARK_COLLECTION]

        if bookmark_id:
            try:
                object_id = ObjectId(bookmark_id)
            except Exception:
                raise ValueError(f"잘못된 북마크 ID: {bookmark_id}")

            result = collection.delete_one({"_id": object_id, "userId": user_id})
        elif manuscript_id:
            result = collection.delete_one({"manuscriptId": manuscript_id, "userId": user_id})
        else:
            raise ValueError("bookmark_id 또는 manuscript_id가 필요합니다")

        if result.deleted_count == 0:
            raise ValueError("즐겨찾기를 찾을 수 없습니다")

        return {"ok": True}

    finally:
        client.close()


def check_bookmark(user_id: str, manuscript_id: str) -> Dict[str, Any]:
    """
    즐겨찾기 여부 확인

    Args:
        user_id: 사용자 식별자
        manuscript_id: 원고 ID

    Returns:
        {"bookmarked": True/False, "bookmarkId": "..."}
    """
    client = MongoClient(MONGO_URI)

    try:
        db = client[BOOKMARK_DB]
        collection = db[BOOKMARK_COLLECTION]

        doc = collection.find_one({
            "userId": user_id,
            "manuscriptId": manuscript_id
        })

        if doc:
            return {"bookmarked": True, "bookmarkId": str(doc["_id"])}
        return {"bookmarked": False, "bookmarkId": None}

    finally:
        client.close()


@router.get("/search/bookmarks")
async def list_bookmarks(
    user_id: str = Query(..., description="사용자 식별자"),
    limit: int = Query(20, ge=1, le=100, description="결과 수"),
    offset: int = Query(0, ge=0, description="시작 위치")
):
    """
    즐겨찾기 목록 조회 API

    - **user_id**: 사용자 식별자 (필수)
    - **limit**: 결과 수 (기본값: 20, 최대: 100)
    - **offset**: 시작 위치 (기본값: 0)

    Returns:
        {"bookmarks": [...], "total": n}
    """
    result = await run_in_threadpool(get_bookmarks, user_id, limit, offset)

    return result


@router.post("/search/bookmarks")
async def create_bookmark(
    user_id: str = Query(..., description="사용자 식별자"),
    manuscript_id: str = Body(..., embed=True, description="원고 ID"),
    category: str = Body(..., embed=True, description="카테고리 (DB명)"),
    keyword: str = Body("", embed=True, description="키워드"),
    preview: str = Body("", embed=True, description="미리보기 텍스트")
):
    """
    즐겨찾기 추가 API

    - **user_id**: 사용자 식별자 (필수)
    - **manuscript_id**: 원고 ID (필수)
    - **category**: 카테고리/DB명 (필수)
    - **keyword**: 키워드 (선택)
    - **preview**: 미리보기 텍스트 (선택)

    Returns:
        {"ok": true, "bookmarkId": "..."}
    """
    result = await run_in_threadpool(
        add_bookmark,
        user_id,
        manuscript_id,
        category,
        keyword,
        preview
    )

    return result


@router.delete("/search/bookmarks/{bookmark_id}")
async def delete_bookmark(
    bookmark_id: str,
    user_id: str = Query(..., description="사용자 식별자")
):
    """
    즐겨찾기 삭제 API (북마크 ID로)

    - **bookmark_id**: 즐겨찾기 ID (필수)
    - **user_id**: 사용자 식별자 (필수)

    Returns:
        {"ok": true}
    """
    try:
        result = await run_in_threadpool(remove_bookmark, user_id, bookmark_id, None)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/search/bookmarks")
async def delete_bookmark_by_manuscript(
    user_id: str = Query(..., description="사용자 식별자"),
    manuscript_id: str = Query(..., description="원고 ID")
):
    """
    즐겨찾기 삭제 API (원고 ID로)

    - **user_id**: 사용자 식별자 (필수)
    - **manuscript_id**: 원고 ID (필수)

    Returns:
        {"ok": true}
    """
    try:
        result = await run_in_threadpool(remove_bookmark, user_id, None, manuscript_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/search/bookmarks/check")
async def is_bookmarked(
    user_id: str = Query(..., description="사용자 식별자"),
    manuscript_id: str = Query(..., description="원고 ID")
):
    """
    즐겨찾기 여부 확인 API

    - **user_id**: 사용자 식별자 (필수)
    - **manuscript_id**: 원고 ID (필수)

    Returns:
        {"bookmarked": true/false, "bookmarkId": "..."}
    """
    result = await run_in_threadpool(check_bookmark, user_id, manuscript_id)

    return result

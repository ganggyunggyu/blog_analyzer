"""원고 삭제/수정/노출 관리 API"""
from typing import Dict, Any, Optional, List
from datetime import datetime
from fastapi import APIRouter, HTTPException, Path, Query
from fastapi.concurrency import run_in_threadpool
from bson import ObjectId
from pymongo import MongoClient

from mongodb_service import MongoDBService
from schema.search import ManuscriptUpdateRequest
from config import MONGO_URI
from _constants.categories import CATEGORIES
from utils.logger import log

router = APIRouter()


def delete_manuscript_by_id(
    manuscript_id: str,
    category: str,
) -> Dict[str, Any]:
    """
    원고 삭제 (소프트 삭제)

    Args:
        manuscript_id: MongoDB Document ID
        category: 카테고리 (DB명)

    Returns:
        {"ok": True, "deletedId": "..."}
    """
    db_service = MongoDBService()

    try:
        try:
            object_id = ObjectId(manuscript_id)
        except Exception:
            raise ValueError(f"잘못된 ID 형식: {manuscript_id}")

        db_service.set_db_name(db_name=category)

        document = db_service.db["manuscripts"].find_one({"_id": object_id})
        if not document:
            raise HTTPException(
                status_code=404,
                detail=f"원고를 찾을 수 없습니다. (ID: {manuscript_id})"
            )

        result = db_service.db["manuscripts"].update_one(
            {"_id": object_id},
            {
                "$set": {
                    "deleted": True,
                    "deletedAt": datetime.now()
                }
            }
        )

        if result.modified_count == 0:
            raise HTTPException(status_code=500, detail="삭제 처리 실패")

        return {"ok": True, "deletedId": manuscript_id}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"원고 삭제 중 오류 발생: {str(e)}"
        )
    finally:
        db_service.close_connection()


def update_manuscript_by_id(
    manuscript_id: str,
    category: str,
    content: str,
    memo: Optional[str] = None,
) -> Dict[str, Any]:
    """
    원고 수정

    Args:
        manuscript_id: MongoDB Document ID
        category: 카테고리 (DB명)
        content: 수정된 내용
        memo: 수정 메모

    Returns:
        {"ok": True, "manuscript": {...}}
    """
    db_service = MongoDBService()

    try:
        try:
            object_id = ObjectId(manuscript_id)
        except Exception:
            raise ValueError(f"잘못된 ID 형식: {manuscript_id}")

        db_service.set_db_name(db_name=category)

        document = db_service.db["manuscripts"].find_one({"_id": object_id})
        if not document:
            raise HTTPException(
                status_code=404,
                detail=f"원고를 찾을 수 없습니다. (ID: {manuscript_id})"
            )

        update_data = {
            "content": content,
            "updatedAt": datetime.now(),
        }
        if memo:
            update_data["updateMemo"] = memo

        result = db_service.db["manuscripts"].update_one(
            {"_id": object_id},
            {"$set": update_data}
        )

        if result.modified_count == 0:
            raise HTTPException(status_code=500, detail="수정 처리 실패")

        updated_doc = db_service.db["manuscripts"].find_one({"_id": object_id})
        updated_doc["_id"] = str(updated_doc["_id"])

        return {
            "ok": True,
            "manuscript": {
                "_id": updated_doc["_id"],
                "content": updated_doc["content"],
                "updatedAt": updated_doc.get("updatedAt"),
            }
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"원고 수정 중 오류 발생: {str(e)}"
        )
    finally:
        db_service.close_connection()


@router.delete("/search/manuscript/{manuscript_id}")
async def delete_manuscript(
    manuscript_id: str = Path(..., description="원고 ID"),
    category: str = Query(..., description="카테고리 (DB명)")
):
    """
    원고 삭제 API (소프트 삭제)

    - **manuscript_id**: MongoDB Document ID (필수)
    - **category**: 카테고리/DB명 (필수)

    Returns:
        {"ok": true, "deletedId": "..."}
    """
    result = await run_in_threadpool(
        delete_manuscript_by_id,
        manuscript_id=manuscript_id,
        category=category,
    )
    log.success("원고 삭제", id=manuscript_id[:8])

    return result


@router.patch("/search/manuscript/{manuscript_id}")
async def update_manuscript(
    manuscript_id: str = Path(..., description="원고 ID"),
    category: str = Query(..., description="카테고리 (DB명)"),
    body: ManuscriptUpdateRequest = ...,
):
    """
    원고 수정 API

    - **manuscript_id**: MongoDB Document ID (필수)
    - **category**: 카테고리/DB명 (필수)
    - **body.content**: 수정된 원고 내용 (필수)
    - **body.memo**: 수정 메모 (선택)

    Returns:
        {"ok": true, "manuscript": {"_id": "...", "content": "...", "updatedAt": ...}}
    """
    result = await run_in_threadpool(
        update_manuscript_by_id,
        manuscript_id=manuscript_id,
        category=category,
        content=body.content,
        memo=body.memo,
    )
    log.success("원고 수정", id=manuscript_id[:8])

    return result


def toggle_visibility_by_id(
    manuscript_id: str,
    category: str,
) -> Dict[str, Any]:
    """
    원고 노출여부 토글

    Args:
        manuscript_id: MongoDB Document ID
        category: 카테고리 (DB명)

    Returns:
        {"ok": True, "visible": bool, "manuscriptId": "..."}
    """
    db_service = MongoDBService()

    try:
        try:
            object_id = ObjectId(manuscript_id)
        except Exception:
            raise ValueError(f"잘못된 ID 형식: {manuscript_id}")

        db_service.set_db_name(db_name=category)

        document = db_service.db["manuscripts"].find_one({"_id": object_id})
        if not document:
            raise HTTPException(
                status_code=404,
                detail=f"원고를 찾을 수 없습니다. (ID: {manuscript_id})"
            )

        current_visible = document.get("visible", True)
        new_visible = not current_visible

        result = db_service.db["manuscripts"].update_one(
            {"_id": object_id},
            {
                "$set": {
                    "visible": new_visible,
                    "visibilityUpdatedAt": datetime.now()
                }
            }
        )

        if result.modified_count == 0:
            raise HTTPException(status_code=500, detail="노출여부 변경 실패")

        return {
            "ok": True,
            "visible": new_visible,
            "manuscriptId": manuscript_id
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"노출여부 변경 중 오류 발생: {str(e)}"
        )
    finally:
        db_service.close_connection()


@router.patch("/search/manuscript/{manuscript_id}/visibility")
async def toggle_visibility(
    manuscript_id: str = Path(..., description="원고 ID"),
    category: str = Query(..., description="카테고리 (DB명)")
):
    """
    원고 노출여부 토글 API

    - **manuscript_id**: MongoDB Document ID (필수)
    - **category**: 카테고리/DB명 (필수)

    Returns:
        {"ok": true, "visible": true/false, "manuscriptId": "..."}
    """
    result = await run_in_threadpool(
        toggle_visibility_by_id,
        manuscript_id=manuscript_id,
        category=category,
    )
    log.success("노출여부 변경", id=manuscript_id[:8], visible=result["visible"])

    return result


def get_visible_manuscripts(
    category: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
) -> Dict[str, Any]:
    """
    노출 원고 목록 조회 (visible=True 또는 visible 필드 없음)

    Args:
        category: 카테고리 필터 (None이면 전체)
        skip: 건너뛸 문서 수
        limit: 반환할 문서 수

    Returns:
        {"documents": [...], "total": int, "skip": int, "limit": int}
    """
    query = {
        "deleted": {"$ne": True},
        "$or": [
            {"visible": True},
            {"visible": {"$exists": False}}
        ]
    }

    if category:
        db_service = MongoDBService()
        try:
            db_service.set_db_name(db_name=category)

            total = db_service.db["manuscripts"].count_documents(query)

            documents = list(
                db_service.db["manuscripts"]
                .find(query)
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
        all_documents: List[Dict[str, Any]] = []
        total = 0

        try:
            for cat in CATEGORIES:
                try:
                    db = client[cat]
                    collection = db["manuscripts"]

                    cat_total = collection.count_documents(query)
                    total += cat_total

                    docs = list(
                        collection.find(query)
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


@router.get("/search/manuscripts/visible")
async def get_visible_manuscripts_api(
    category: Optional[str] = Query(None, description="카테고리 필터 (없으면 전체)"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 결과 수"),
):
    """
    노출 원고 목록 조회 API

    visible=True 또는 visible 필드가 없는 원고만 반환

    - **category**: 카테고리 필터 (선택, 없으면 전체 카테고리)
    - **page**: 페이지 번호 (기본값: 1)
    - **limit**: 페이지당 결과 수 (기본값: 20, 최대: 100)

    Returns:
        {"documents": [...], "total": int, "skip": int, "limit": int}
    """
    skip = (page - 1) * limit

    result = await run_in_threadpool(
        get_visible_manuscripts,
        category=category,
        skip=skip,
        limit=limit,
    )
    log.success("노출 원고 조회", count=len(result['documents']), total=result['total'])

    return result

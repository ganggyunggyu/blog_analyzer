"""원고 관리 서비스"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from bson import ObjectId
from fastapi import HTTPException
from pymongo import MongoClient

from _constants.categories import CATEGORIES
from config import MONGO_URI
from mongodb_service import MongoDBService


VisibleManuscriptsResult = dict[str, Any]

VISIBLE_MANUSCRIPT_QUERY = {
    "deleted": {"$ne": True},
    "$or": [
        {"visible": True},
        {"visible": {"$exists": False}},
    ],
}


def _parse_object_id(manuscript_id: str) -> ObjectId:
    try:
        return ObjectId(manuscript_id)
    except Exception as error:
        raise ValueError(f"잘못된 ID 형식: {manuscript_id}") from error


def _serialize_document(document: dict[str, Any], category: Optional[str] = None) -> dict[str, Any]:
    serialized = dict(document)
    if "_id" in serialized:
        serialized["_id"] = str(serialized["_id"])
    if category:
        serialized["__category"] = category
    return serialized


def delete_manuscript_by_id(manuscript_id: str, category: str) -> dict[str, Any]:
    db_service = MongoDBService()

    try:
        object_id = _parse_object_id(manuscript_id)
        db_service.set_db_name(db_name=category)

        document = db_service.db["manuscripts"].find_one({"_id": object_id})
        if not document:
            raise HTTPException(
                status_code=404,
                detail=f"원고를 찾을 수 없습니다. (ID: {manuscript_id})",
            )

        result = db_service.db["manuscripts"].update_one(
            {"_id": object_id},
            {"$set": {"deleted": True, "deletedAt": datetime.now()}},
        )
        if result.modified_count == 0:
            raise HTTPException(status_code=500, detail="삭제 처리 실패")

        return {"ok": True, "deletedId": manuscript_id}

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"원고 삭제 중 오류 발생: {str(error)}",
        )
    finally:
        db_service.close_connection()


def update_manuscript_by_id(
    manuscript_id: str,
    category: str,
    content: str,
    memo: Optional[str] = None,
) -> dict[str, Any]:
    db_service = MongoDBService()

    try:
        object_id = _parse_object_id(manuscript_id)
        db_service.set_db_name(db_name=category)

        document = db_service.db["manuscripts"].find_one({"_id": object_id})
        if not document:
            raise HTTPException(
                status_code=404,
                detail=f"원고를 찾을 수 없습니다. (ID: {manuscript_id})",
            )

        update_data: dict[str, Any] = {
            "content": content,
            "updatedAt": datetime.now(),
        }
        if memo:
            update_data["updateMemo"] = memo

        result = db_service.db["manuscripts"].update_one(
            {"_id": object_id},
            {"$set": update_data},
        )
        if result.modified_count == 0:
            raise HTTPException(status_code=500, detail="수정 처리 실패")

        updated_doc = db_service.db["manuscripts"].find_one({"_id": object_id})
        serialized_doc = _serialize_document(updated_doc)
        return {
            "ok": True,
            "manuscript": {
                "_id": serialized_doc["_id"],
                "content": serialized_doc["content"],
                "updatedAt": serialized_doc.get("updatedAt"),
            },
        }

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"원고 수정 중 오류 발생: {str(error)}",
        )
    finally:
        db_service.close_connection()


def toggle_visibility_by_id(manuscript_id: str, category: str) -> dict[str, Any]:
    db_service = MongoDBService()

    try:
        object_id = _parse_object_id(manuscript_id)
        db_service.set_db_name(db_name=category)

        document = db_service.db["manuscripts"].find_one({"_id": object_id})
        if not document:
            raise HTTPException(
                status_code=404,
                detail=f"원고를 찾을 수 없습니다. (ID: {manuscript_id})",
            )

        new_visible = not document.get("visible", True)
        result = db_service.db["manuscripts"].update_one(
            {"_id": object_id},
            {"$set": {"visible": new_visible, "visibilityUpdatedAt": datetime.now()}},
        )
        if result.modified_count == 0:
            raise HTTPException(status_code=500, detail="노출여부 변경 실패")

        return {
            "ok": True,
            "visible": new_visible,
            "manuscriptId": manuscript_id,
        }

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"노출여부 변경 중 오류 발생: {str(error)}",
        )
    finally:
        db_service.close_connection()


def _get_category_visible_manuscripts(category: str, skip: int, limit: int) -> VisibleManuscriptsResult:
    db_service = MongoDBService()

    try:
        db_service.set_db_name(db_name=category)
        total = db_service.db["manuscripts"].count_documents(VISIBLE_MANUSCRIPT_QUERY)
        documents = list(
            db_service.db["manuscripts"]
            .find(VISIBLE_MANUSCRIPT_QUERY)
            .sort("createdAt", -1)
            .skip(skip)
            .limit(limit)
        )
        return {
            "documents": [
                _serialize_document(document, category) for document in documents
            ],
            "total": total,
            "skip": skip,
            "limit": limit,
        }
    finally:
        db_service.close_connection()


def _get_all_visible_manuscripts(skip: int, limit: int) -> VisibleManuscriptsResult:
    client = MongoClient(MONGO_URI)
    all_documents: list[dict[str, Any]] = []
    total = 0

    try:
        for category in CATEGORIES:
            try:
                collection = client[category]["manuscripts"]
                total += collection.count_documents(VISIBLE_MANUSCRIPT_QUERY)
                documents = list(
                    collection.find(VISIBLE_MANUSCRIPT_QUERY)
                    .sort("createdAt", -1)
                    .limit(limit * 2)
                )
                all_documents.extend(
                    _serialize_document(document, category) for document in documents
                )
            except Exception:
                continue

        all_documents.sort(
            key=lambda document: document.get("createdAt") or datetime.min,
            reverse=True,
        )
        return {
            "documents": all_documents[skip:skip + limit],
            "total": total,
            "skip": skip,
            "limit": limit,
        }
    finally:
        client.close()


def get_visible_manuscripts(
    category: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
) -> VisibleManuscriptsResult:
    if category:
        return _get_category_visible_manuscripts(category, skip, limit)
    return _get_all_visible_manuscripts(skip, limit)


__all__ = [
    "delete_manuscript_by_id",
    "get_visible_manuscripts",
    "toggle_visibility_by_id",
    "update_manuscript_by_id",
]

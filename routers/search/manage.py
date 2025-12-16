"""원고 삭제/수정 API"""
from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Path, Query
from fastapi.concurrency import run_in_threadpool
from bson import ObjectId

from mongodb_service import MongoDBService
from schema.search import ManuscriptUpdateRequest

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
    print(f"\n{'='*60}")
    print(f"🗑️ 원고 삭제 시작")
    print(f"{'='*60}")
    print(f"🆔 ID         : {manuscript_id}")
    print(f"📁 카테고리   : {category}")
    print(f"{'='*60}\n")

    result = await run_in_threadpool(
        delete_manuscript_by_id,
        manuscript_id=manuscript_id,
        category=category,
    )

    print(f"✅ 원고 삭제 완료: {manuscript_id}")

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
    print(f"\n{'='*60}")
    print(f"✏️ 원고 수정 시작")
    print(f"{'='*60}")
    print(f"🆔 ID         : {manuscript_id}")
    print(f"📁 카테고리   : {category}")
    print(f"📝 메모       : {body.memo or '없음'}")
    print(f"{'='*60}\n")

    result = await run_in_threadpool(
        update_manuscript_by_id,
        manuscript_id=manuscript_id,
        category=category,
        content=body.content,
        memo=body.memo,
    )

    print(f"✅ 원고 수정 완료: {manuscript_id}")

    return result

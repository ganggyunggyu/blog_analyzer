from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Path
from fastapi.concurrency import run_in_threadpool
from bson import ObjectId

from mongodb_service import MongoDBService
from config import MONGO_DB_NAME

router = APIRouter()


def get_manuscript_by_id(
    manuscript_id: str,
    category: Optional[str] = None,
) -> Dict[str, Any]:
    """
    ID로 단일 원고 조회

    Args:
        manuscript_id: MongoDB Document ID
        category: 카테고리 (None이면 기본 DB 사용)

    Returns:
        원고 Document

    Raises:
        ValueError: 잘못된 ID 형식
        HTTPException: 원고를 찾을 수 없음
    """
    db_service = MongoDBService()

    try:
        # ObjectId 형식 검증
        try:
            object_id = ObjectId(manuscript_id)
        except Exception:
            raise ValueError(f"잘못된 ID 형식: {manuscript_id}")

        # DB 설정
        if category:
            db_service.set_db_name(db_name=category)
        else:
            db_service.set_db_name(db_name=MONGO_DB_NAME)

        # 원고 조회
        document = db_service.db["manuscripts"].find_one({"_id": object_id})

        if not document:
            raise HTTPException(
                status_code=404,
                detail=f"원고를 찾을 수 없습니다. (ID: {manuscript_id})"
            )

        # _id를 문자열로 변환
        document["_id"] = str(document["_id"])

        return document

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"원고 조회 중 오류 발생: {str(e)}"
        )
    finally:
        db_service.close_connection()


@router.get("/search/manuscript/{manuscript_id}")
async def get_manuscript(
    manuscript_id: str = Path(..., description="원고 ID (MongoDB ObjectId)"),
    category: Optional[str] = None,
):
    """
    ID로 단일 원고 조회

    - **manuscript_id**: MongoDB Document ID (필수)
    - **category**: 카테고리 필터 (선택, 쿼리 파라미터)

    Returns:
        원고 Document 객체
    """
    print(f"\n{'='*60}")
    print(f"📄 원고 조회 시작")
    print(f"{'='*60}")
    print(f"🆔 ID         : {manuscript_id}")
    print(f"📁 카테고리   : {category or '기본 DB'}")
    print(f"{'='*60}\n")

    document = await run_in_threadpool(
        get_manuscript_by_id,
        manuscript_id=manuscript_id,
        category=category,
    )

    print(f"\n{'='*60}")
    print(f"✅ 원고 조회 완료")
    print(f"{'='*60}")
    print(f"🎯 키워드     : {document.get('keyword', 'N/A')}")
    print(f"🤖 엔진       : {document.get('engine', 'N/A')}")
    print(f"📁 카테고리   : {document.get('category', 'N/A')}")
    print(f"{'='*60}\n")

    return document

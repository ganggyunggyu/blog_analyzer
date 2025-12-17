from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from bson import ObjectId

from mongodb_service import MongoDBService


router = APIRouter()


class ToggleVisibilityRequest(BaseModel):
    category: str = Field(..., description="카테고리 (DB 이름)")
    manuscript_id: str = Field(..., description="원고 _id")


class ToggleVisibilityResponse(BaseModel):
    success: bool
    manuscript_id: str
    isVisible: bool
    message: str


@router.post("/manuscript/toggle-visibility", response_model=ToggleVisibilityResponse)
async def toggle_manuscript_visibility(request: ToggleVisibilityRequest):
    """
    원고 노출 여부 토글 API

    - category: DB 이름 (카테고리)
    - manuscript_id: 원고 _id

    isVisible 값을 토글합니다. (true ↔ false)
    필드가 없으면 false로 간주하고 true로 변경합니다.
    """
    db_service = MongoDBService()

    try:
        db_service.set_db_name(db_name=request.category)

        try:
            obj_id = ObjectId(request.manuscript_id)
        except Exception:
            raise HTTPException(status_code=400, detail="유효하지 않은 manuscript_id 형식입니다.")

        docs = db_service.find_documents("manuscripts", {"_id": obj_id})

        if not docs:
            raise HTTPException(status_code=404, detail="해당 원고를 찾을 수 없습니다.")

        doc = docs[0]
        current_visible = doc.get("isVisible", False)
        new_visible = not current_visible

        updated_count = db_service.update_document(
            "manuscripts",
            {"_id": obj_id},
            {"isVisible": new_visible},
        )

        if updated_count == 0:
            raise HTTPException(status_code=500, detail="원고 업데이트에 실패했습니다.")

        return ToggleVisibilityResponse(
            success=True,
            manuscript_id=request.manuscript_id,
            isVisible=new_visible,
            message=f"노출 여부가 {'활성화' if new_visible else '비활성화'}되었습니다.",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"토글 처리 중 오류 발생: {e}")
    finally:
        if db_service:
            db_service.close_connection()


@router.get("/manuscript/visibility/{category}/{manuscript_id}")
async def get_manuscript_visibility(category: str, manuscript_id: str):
    """
    원고 노출 여부 조회 API
    """
    db_service = MongoDBService()

    try:
        db_service.set_db_name(db_name=category)

        try:
            obj_id = ObjectId(manuscript_id)
        except Exception:
            raise HTTPException(status_code=400, detail="유효하지 않은 manuscript_id 형식입니다.")

        docs = db_service.find_documents("manuscripts", {"_id": obj_id})

        if not docs:
            raise HTTPException(status_code=404, detail="해당 원고를 찾을 수 없습니다.")

        doc = docs[0]
        isVisible = doc.get("isVisible", False)

        return {
            "manuscript_id": manuscript_id,
            "category": category,
            "isVisible": isVisible,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"조회 중 오류 발생: {e}")
    finally:
        if db_service:
            db_service.close_connection()

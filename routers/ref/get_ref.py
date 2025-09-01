from bson import ObjectId
from fastapi import APIRouter, HTTPException
from fastapi.encoders import jsonable_encoder

from mongodb_service import MongoDBService


router = APIRouter()
db_service = MongoDBService()


@router.get(
    "/ref",
    summary="참조문서 전체 조회",
    responses={
        200: {"description": "성공적으로 참조문서를 가져왔습니다."},
        404: {"description": "참조문서 없음"},
        500: {"description": "서버 오류"},
    },
)
@router.get("/ref")
async def get_ref_documents():

    try:
        documents = db_service.find_documents("ref", {})
        if not documents:
            raise HTTPException(status_code=404, detail="참조문서를 찾을 수 없습니다.")
        safe_docs = jsonable_encoder(
            documents,
            custom_encoder={ObjectId: str},
        )
        return {"documents": safe_docs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ref/{keyword}", summary="키워드별 참조문서 조회")
async def get_ref_documents_by_keyword(keyword: str):
    try:
        documents = db_service.find_documents("ref", {"keyword": keyword})
        if not documents:
            raise HTTPException(
                status_code=404, detail="해당 키워드의 참조문서를 찾을 수 없습니다."
            )
        safe_docs = jsonable_encoder(
            documents,
            custom_encoder={ObjectId: str},
        )
        return {"keyword": keyword, "documents": safe_docs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

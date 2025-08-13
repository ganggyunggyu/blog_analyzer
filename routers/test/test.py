from fastapi import APIRouter

router = APIRouter(prefix="/test", tags=["manuscript"])

@router.get("/test")
async def test_endpoint():
    return {"message": "Test successful"}

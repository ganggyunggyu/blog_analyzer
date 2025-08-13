from fastapi import  HTTPException, APIRouter
from utils.categorize_keyword_with_ai import categorize_keyword_with_ai

router = APIRouter()


@router.get("/category/{keyword}")
def category_test(keyword: str):
    try:
        if not keyword.strip():
            raise ValueError("키워드가 비어 있습니다.")
        
        result = categorize_keyword_with_ai(keyword)
        
        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"서버 내부 오류: {e}")
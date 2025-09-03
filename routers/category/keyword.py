from fastapi import HTTPException, APIRouter
from utils.get_category_db_name import get_category_db_name

router = APIRouter()


@router.get("/category/{keyword}")
def category_test(keyword: str):
    try:
        if not keyword.strip():
            raise ValueError("키워드가 비어 있습니다.")

        result = get_category_db_name(keyword)

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"서버 내부 오류: {e}")

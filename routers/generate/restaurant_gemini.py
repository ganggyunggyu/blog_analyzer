"""맛집 후기 생성 라우터 (Gemini 3 Pro)"""

import time
from fastapi import HTTPException, APIRouter
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
from typing import Optional

from llm.restaurant_gemini_service import restaurant_gemini_gen, MODEL_NAME
from utils.progress_logger import progress
from utils.logger import log


router = APIRouter()


class RestaurantGeminiRequest(BaseModel):
    keyword: str
    ref: Optional[str] = ""


class RestaurantGeminiResponse(BaseModel):
    content: str
    keyword: str
    model: str
    char_count: int
    elapsed: float


@router.post("/generate/restaurant-gemini", response_model=RestaurantGeminiResponse)
async def create_restaurant_review(request: RestaurantGeminiRequest):
    """맛집 후기 생성 API

    - keyword: 맛집 정보 (fullText)
    - ref: 참조 원고 (선택)
    """
    start_ts = time.time()
    keyword = request.keyword.strip()
    ref = request.ref.strip() if request.ref else ""

    if not keyword:
        raise HTTPException(status_code=400, detail="keyword가 필요합니다.")

    kw_display = keyword[:50] + "..." if len(keyword) > 50 else keyword

    log.header("맛집 후기 생성", "🍽️")
    log.kv("키워드", kw_display)
    log.kv("참조", "있음" if ref else "없음")
    log.kv("모델", MODEL_NAME)

    try:
        with progress(label=f"restaurant:{kw_display}"):
            result = await run_in_threadpool(
                restaurant_gemini_gen,
                keyword=keyword,
                ref=ref,
            )

        elapsed = time.time() - start_ts

        log.divider()
        log.success("맛집 후기 완료", 길이=f"{result['char_count']}자", 시간=f"{elapsed:.1f}s")

        return RestaurantGeminiResponse(
            content=result["content"],
            keyword=result["keyword"],
            model=result["model"],
            char_count=result["char_count"],
            elapsed=round(elapsed, 2),
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"맛집 후기 생성 중 오류: {e}")

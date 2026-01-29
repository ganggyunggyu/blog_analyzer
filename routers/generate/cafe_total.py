"""카페 글 종합 생성 라우터 - 모델 선택 가능"""

import time
from fastapi import HTTPException, APIRouter
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
from typing import Optional

from llm.cafe_total_service import cafe_total_gen, DEFAULT_MODEL
from utils.progress_logger import progress
from utils.logger import log


router = APIRouter()


class CafeTotalRequest(BaseModel):
    keyword: str
    ref: Optional[str] = ""
    model: Optional[str] = ""


class CafeTotalResponse(BaseModel):
    content: str
    keyword: str
    model: str
    char_count: int
    elapsed: float


@router.post("/generate/cafe-total", response_model=CafeTotalResponse)
async def create_cafe_total(request: CafeTotalRequest):
    """카페 글 종합 생성 API

    - keyword: 키워드/지시사항 (필수)
    - ref: 참조 원고 (선택)
    - model: 사용할 모델명 (선택, 기본값: gemini-3-pro-preview)
    """
    start_ts = time.time()
    keyword = request.keyword.strip()
    ref = request.ref.strip() if request.ref else ""
    model_name = request.model.strip() if request.model else ""

    if not keyword:
        raise HTTPException(status_code=400, detail="keyword가 필요합니다.")

    kw_display = keyword[:50] + "..." if len(keyword) > 50 else keyword
    model_display = model_name if model_name else DEFAULT_MODEL

    log.header("카페 글 종합 생성", "☕")
    log.kv("키워드", kw_display)
    log.kv("참조", "있음" if ref else "없음")
    log.kv("모델", model_display)

    try:
        with progress(label=f"cafe-total:{model_display}:{kw_display}"):
            result = await run_in_threadpool(
                cafe_total_gen,
                user_instructions=keyword,
                ref=ref,
                model_name=model_name,
            )

        elapsed = time.time() - start_ts

        log.divider()
        log.success("카페 글 완료", 모델=result["model"], 길이=f"{result['char_count']}자", 시간=f"{elapsed:.1f}s")

        return CafeTotalResponse(
            content=result["content"],
            keyword=result["keyword"],
            model=result["model"],
            char_count=result["char_count"],
            elapsed=round(elapsed, 2),
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"카페 글 생성 중 오류: {e}")

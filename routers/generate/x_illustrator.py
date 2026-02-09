"""X Illustrator Router - 일러스트레이터 X(Twitter) 포스트 생성 엔드포인트"""

import time
from fastapi import HTTPException, APIRouter
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel

from llm.x_illustrator_service import (
    x_illustrator_gen,
    x_illustrator_nyangnyang_gen,
    MODEL_NAME,
)
from utils.progress_logger import progress
from utils.logger import log


router = APIRouter()


class XPostRequest(BaseModel):
    keyword: str  # 그린 대상 (캐릭터명, 주제, 설명)
    context: str = ""  # 일상 멘트/상황 (첫 포스트, 날씨, 컨디션 등)


class XPostResponse(BaseModel):
    content: str
    model: str
    elapsed: float


@router.post("/generate/x-illustrator", response_model=XPostResponse)
async def generate_x_post(request: XPostRequest):
    """
    일러스트레이터 X(Twitter) 포스트 생성

    영어 + 일본어 이중언어 포스트를 생성합니다.
    """
    start_ts = time.time()
    keyword = request.keyword.strip()

    if not keyword:
        raise HTTPException(status_code=400, detail="키워드가 필요합니다.")

    log.header("X Illustrator 포스트 생성", "🎨")
    log.kv("키워드", keyword)
    log.kv("모델", MODEL_NAME)

    try:
        with progress(label=f"x-illustrator:{MODEL_NAME}:{keyword}"):
            generated_post = await run_in_threadpool(
                x_illustrator_gen, keyword=keyword, context=request.context
            )

        elapsed = time.time() - start_ts

        log.divider()
        log.success("X 포스트 완료", 키워드=keyword, 시간=f"{elapsed:.1f}s")

        return XPostResponse(
            content=generated_post,
            model=MODEL_NAME,
            elapsed=round(elapsed, 2),
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"X 포스트 생성 중 오류 발생: {e}")


@router.post("/generate/x-illustrator/nyangnyang", response_model=XPostResponse)
async def generate_x_post_nyangnyang(request: XPostRequest):
    """
    냥냥돌쇠 X(Twitter) 포스트 생성

    한국어(음슴체+냥) + 일본어 이중언어 포스트를 생성합니다.
    """
    start_ts = time.time()
    keyword = request.keyword.strip()

    if not keyword:
        raise HTTPException(status_code=400, detail="키워드가 필요합니다.")

    log.header("냥냥돌쇠 X 포스트 생성", "🐱")
    log.kv("키워드", keyword)
    log.kv("모델", MODEL_NAME)

    try:
        with progress(label=f"x-nyangnyang:{MODEL_NAME}:{keyword}"):
            generated_post = await run_in_threadpool(
                x_illustrator_nyangnyang_gen, keyword=keyword, context=request.context
            )

        elapsed = time.time() - start_ts

        log.divider()
        log.success("냥냥돌쇠 포스트 완료", 키워드=keyword, 시간=f"{elapsed:.1f}s")

        return XPostResponse(
            content=generated_post,
            model=MODEL_NAME,
            elapsed=round(elapsed, 2),
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"냥냥돌쇠 포스트 생성 중 오류 발생: {e}")

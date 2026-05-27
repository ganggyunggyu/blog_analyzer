"""테스트용 카페 데일리 생성 API - 프롬프트 직접 전달"""

import time

from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel

from _constants.Model import Model
from utils.ai_client_factory import call_ai
from utils.logger import log


router = APIRouter()


class TestCafeDailyRequest(BaseModel):
    prompt: str
    model: str = Model.DEEPSEEK_V4_FLASH


class TestCafeDailyResponse(BaseModel):
    success: bool
    content: str
    model: str
    elapsed: float


@router.post("/generate/test/cafe-daily", response_model=TestCafeDailyResponse)
async def generate_test_cafe_daily(request: TestCafeDailyRequest):
    """테스트용 카페 데일리 생성 - 프롬프트 직접 전달"""
    start_ts = time.time()

    log.header("테스트 카페 데일리 생성", "🧪")
    log.kv("모델", request.model)

    try:
        content = await run_in_threadpool(
            call_ai,
            model_name=request.model,
            system_prompt="",
            user_prompt=request.prompt,
            max_tokens=32000,
        )

        elapsed = time.time() - start_ts
        log.success("테스트 카페 데일리 완료", 시간=f"{elapsed:.2f}s")

        return TestCafeDailyResponse(
            success=True,
            content=content.strip(),
            model=request.model,
            elapsed=round(elapsed, 2),
        )

    except Exception as e:
        log.error(f"테스트 카페 데일리 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

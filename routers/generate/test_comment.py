"""테스트용 댓글 생성 API - 프롬프트 직접 전달"""

import time

from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel

from _constants.Model import Model
from utils.ai_client_factory import call_ai
from utils.logger import log


router = APIRouter()


class TestCommentRequest(BaseModel):
    prompt: str
    model: str = Model.GPT4O


class TestCommentResponse(BaseModel):
    success: bool
    comment: str
    model: str
    elapsed: float


@router.post("/generate/test/comment", response_model=TestCommentResponse)
async def generate_test_comment(request: TestCommentRequest):
    """테스트용 댓글 생성 - 프롬프트 직접 전달"""
    start_ts = time.time()

    log.header("테스트 댓글 생성", "🧪")
    log.kv("모델", request.model)

    try:
        comment = await run_in_threadpool(
            call_ai,
            model_name=request.model,
            system_prompt="",
            user_prompt=request.prompt,
        )

        elapsed = time.time() - start_ts
        log.success("테스트 댓글 완료", 시간=f"{elapsed:.2f}s")

        return TestCommentResponse(
            success=True,
            comment=comment.strip(),
            model=request.model,
            elapsed=round(elapsed, 2),
        )

    except Exception as e:
        log.error(f"테스트 댓글 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

"""대댓글 생성 API"""

import time
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel

from llm.recomment_service import generate_recomment, MODEL_NAME
from utils.logger import log


router = APIRouter()


class RecommentRequest(BaseModel):
    parent_comment: str
    content: str = ""
    persona_index: Optional[int] = None


class RecommentResponse(BaseModel):
    success: bool
    comment: str
    persona: str
    model: str
    elapsed: float


@router.post("/generate/recomment", response_model=RecommentResponse)
async def generate_recomment_api(request: RecommentRequest):
    """대댓글 생성

    - parent_comment: 답글 달 원댓글 (필수)
    - content: 원글 내용 (참고용, 선택)
    - persona_index: 페르소나 인덱스 (0-9, null이면 랜덤)
    """
    start_ts = time.time()

    log.header("대댓글 생성", "💬")
    log.kv("원댓글", request.parent_comment[:50] + "..." if len(request.parent_comment) > 50 else request.parent_comment)
    log.kv("페르소나", request.persona_index if request.persona_index is not None else "랜덤")
    log.kv("모델", MODEL_NAME)

    try:
        result = await run_in_threadpool(
            generate_recomment,
            parent_comment=request.parent_comment,
            content=request.content,
            persona_index=request.persona_index,
        )

        elapsed = time.time() - start_ts

        log.success("대댓글 생성 완료", 페르소나=result["persona"], 시간=f"{elapsed:.2f}s")

        return RecommentResponse(
            success=True,
            comment=result["comment"],
            persona=result["persona"],
            model=result["model"],
            elapsed=round(elapsed, 2),
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log.error(f"대댓글 생성 실패: {e}")
        raise HTTPException(status_code=500, detail=f"대댓글 생성 중 오류 발생: {e}")

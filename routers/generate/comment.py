"""댓글 생성 API"""

import time

from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel

from llm.comment_service import generate_comment, MODEL_NAME
from utils.logger import log


router = APIRouter()


class CommentRequest(BaseModel):
    content: str
    keyword: str = ""


class CommentResponse(BaseModel):
    success: bool
    comment: str
    model: str
    elapsed: float


@router.post("/generate/comment", response_model=CommentResponse)
async def generate_comment_api(request: CommentRequest):
    start_ts = time.time()

    log.header("댓글 생성", "💬")
    log.kv("글 길이", f"{len(request.content)}자")
    log.kv("키워드", request.keyword or "없음")
    log.kv("모델", MODEL_NAME)

    try:
        result = await run_in_threadpool(
            generate_comment,
            content=request.content,
            keyword=request.keyword,
        )

        elapsed = time.time() - start_ts
        log.success("댓글 생성 완료", 시간=f"{elapsed:.2f}s")

        return CommentResponse(
            success=True,
            comment=result["comment"],
            model=result["model"],
            elapsed=round(elapsed, 2),
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log.error(f"댓글 생성 실패: {e}")
        raise HTTPException(status_code=500, detail=f"댓글 생성 중 오류 발생: {e}")

"""댓글 생성 API"""

import time
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel

from llm.comment_service import generate_comment, MODEL_NAME
from _prompts.comment import PERSONAS
from utils.logger import log


router = APIRouter()


class CommentRequest(BaseModel):
    content: str
    author_name: str = ""
    persona_id: Optional[str] = None      # 페르소나 ID (우선)
    persona_index: Optional[int] = None   # 페르소나 인덱스 (하위호환)


class CommentResponse(BaseModel):
    success: bool
    comment: str
    persona_id: str
    persona: str
    model: str
    elapsed: float


@router.post("/generate/comment", response_model=CommentResponse)
async def generate_comment_api(request: CommentRequest):
    """블로그 글에 대한 댓글 생성

    - 글 내용을 받아 랜덤 페르소나로 자연스러운 댓글 생성
    - persona_index를 지정하면 해당 페르소나 사용 (0-9)
    """
    start_ts = time.time()

    log.header("댓글 생성", "💬")
    log.kv("글 길이", f"{len(request.content)}자")
    log.kv("페르소나", request.persona_id or request.persona_index or "랜덤")
    log.kv("모델", MODEL_NAME)

    try:
        result = await run_in_threadpool(
            generate_comment,
            content=request.content,
            author_name=request.author_name,
            persona_id=request.persona_id,
            persona_index=request.persona_index,
        )

        elapsed = time.time() - start_ts

        log.success("댓글 생성 완료", 페르소나=result["persona_id"], 시간=f"{elapsed:.2f}s")

        return CommentResponse(
            success=True,
            comment=result["comment"],
            persona_id=result["persona_id"],
            persona=result["persona"],
            model=result["model"],
            elapsed=round(elapsed, 2),
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log.error(f"댓글 생성 실패: {e}")
        raise HTTPException(status_code=500, detail=f"댓글 생성 중 오류 발생: {e}")


@router.get("/generate/comment/personas")
async def get_personas():
    """사용 가능한 페르소나 목록 조회"""
    return {
        "count": len(PERSONAS),
        "personas": [
            {"id": pid, "description": desc, "weight": w}
            for pid, desc, w in PERSONAS
        ],
    }

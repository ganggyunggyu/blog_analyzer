"""댓글 생성 API - 18종 페르소나"""

import time
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel

from llm.comment_service import generate_comment, MODEL_NAME
from _prompts.viral import COMMENT_PERSONAS
from utils.logger import log


router = APIRouter()


class CommentRequest(BaseModel):
    content: str
    persona_id: Optional[int] = None  # 페르소나 ID (1~18, null이면 랜덤)
    keyword: str = ""
    keyword_type: str = "자사"  # "자사" | "타사"
    comment_type: str = "공감형"  # "공감형" | "경험공유형" | "질문형" | "추천형" | "맞장구형"
    product_name: str = "한려담원 흑염소진액"


class CommentResponse(BaseModel):
    success: bool
    comment: str
    persona_id: int
    persona: str
    model: str
    elapsed: float


@router.post("/generate/comment", response_model=CommentResponse)
async def generate_comment_api(request: CommentRequest):
    """블로그 글에 대한 댓글 생성 (18종 페르소나)

    - persona_id: 1~18 (null이면 랜덤)
    - keyword_type: "자사" | "타사"
    - comment_type: "공감형" | "경험공유형" | "질문형" | "추천형" | "맞장구형"
    """
    start_ts = time.time()

    log.header("댓글 생성", "💬")
    log.kv("글 길이", f"{len(request.content)}자")
    log.kv("페르소나", request.persona_id or "랜덤")
    log.kv("키워드", request.keyword or "없음")
    log.kv("댓글유형", request.comment_type)
    log.kv("모델", MODEL_NAME)

    try:
        result = await run_in_threadpool(
            generate_comment,
            content=request.content,
            persona_id=request.persona_id,
            keyword=request.keyword,
            keyword_type=request.keyword_type,
            comment_type=request.comment_type,
            product_name=request.product_name,
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
    """사용 가능한 페르소나 목록 조회 (18종)"""
    return {
        "count": len(COMMENT_PERSONAS),
        "personas": [
            {
                "id": pid,
                "name": data["name"],
                "age": data["age"],
                "info": data["info"],
                "tone": data["tone"],
            }
            for pid, data in COMMENT_PERSONAS.items()
        ],
    }

"""대댓글 생성 API - 18종 페르소나"""

import time
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel

from llm.recomment_service import generate_recomment, MODEL_NAME
from _prompts.viral import RECOMMENT_PERSONAS
from utils.logger import log


router = APIRouter()


class RecommentRequest(BaseModel):
    parent_comment: str
    content: str = ""  # 원글 내용 (참고용)
    persona_id: Optional[int] = None  # 페르소나 ID (1~18, null이면 랜덤)
    keyword: str = ""
    keyword_type: str = "자사"  # "자사" | "타사"
    role: str = "제3자"  # "원글작성자" (☆) | "댓글작성자" (★) | "제3자" (○)
    product_name: str = "한려담원 흑염소진액"


class RecommentResponse(BaseModel):
    success: bool
    comment: str
    persona_id: int
    persona: str
    model: str
    elapsed: float


@router.post("/generate/recomment", response_model=RecommentResponse)
async def generate_recomment_api(request: RecommentRequest):
    """대댓글 생성 (18종 페르소나)

    - parent_comment: 답글 달 원댓글 (필수)
    - content: 원글 내용 (참고용, 선택)
    - persona_id: 1~18 (null이면 랜덤)
    - role: "원글작성자" (☆) | "댓글작성자" (★) | "제3자" (○)
    """
    start_ts = time.time()

    log.header("대댓글 생성", "💬")
    log.kv("원댓글", request.parent_comment[:50] + "..." if len(request.parent_comment) > 50 else request.parent_comment)
    log.kv("페르소나", request.persona_id or "랜덤")
    log.kv("역할", request.role)
    log.kv("모델", MODEL_NAME)

    try:
        result = await run_in_threadpool(
            generate_recomment,
            parent_comment=request.parent_comment,
            content=request.content,
            persona_id=request.persona_id,
            keyword=request.keyword,
            keyword_type=request.keyword_type,
            role=request.role,
            product_name=request.product_name,
        )

        elapsed = time.time() - start_ts

        log.success("대댓글 생성 완료", 페르소나=result["persona_id"], 시간=f"{elapsed:.2f}s")

        return RecommentResponse(
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
        log.error(f"대댓글 생성 실패: {e}")
        raise HTTPException(status_code=500, detail=f"대댓글 생성 중 오류 발생: {e}")


@router.get("/generate/recomment/personas")
async def get_personas():
    """사용 가능한 페르소나 목록 조회 (18종)"""
    return {
        "count": len(RECOMMENT_PERSONAS),
        "personas": [
            {
                "id": pid,
                "name": data["name"],
                "age": data["age"],
                "info": data["info"],
                "tone": data["tone"],
            }
            for pid, data in RECOMMENT_PERSONAS.items()
        ],
    }

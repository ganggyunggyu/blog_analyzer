"""네이버 블로그 글쓰기 자동화 API"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from services.blog_write_service import write_blog_post
from utils.logger import log

router = APIRouter(prefix="/blog", tags=["blog-write"])


class WritePostRequest(BaseModel):
    """글쓰기 요청"""
    cookies: list  # 로그인 쿠키
    title: str
    content: str
    category: Optional[str] = None
    tags: Optional[list[str]] = None
    images: Optional[list[str]] = None  # 이미지 경로 목록
    is_public: bool = True  # 전체공개
    schedule_time: Optional[str] = None  # 예약 발행 시간 (ISO format)


class WritePostResponse(BaseModel):
    success: bool
    post_url: Optional[str] = None
    message: str


@router.post("/write")
async def write_post(request: WritePostRequest):
    """블로그 글쓰기 API"""

    log.header("블로그 글쓰기", "📝")
    log.kv("제목", request.title[:40])

    result = await write_blog_post(
        cookies=request.cookies,
        title=request.title,
        content=request.content,
        category=request.category,
        tags=request.tags,
        images=request.images,
        is_public=request.is_public,
        schedule_time=request.schedule_time,
        debug=True,  # 디버그 모드
    )

    if not result["success"]:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "WRITE_FAILED",
                "message": result["message"],
            },
        )

    return JSONResponse(content=result)


@router.get("/health")
async def health():
    """헬스 체크"""
    return {"status": "ok", "service": "blog-write"}

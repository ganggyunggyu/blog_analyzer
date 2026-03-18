"""원고 삭제/수정/노출 관리 API"""

from typing import Optional

from fastapi import APIRouter, HTTPException, Path, Query
from fastapi.concurrency import run_in_threadpool

from schema.search import ManuscriptUpdateRequest
from services.manuscript_manage_service import (
    delete_manuscript_by_id,
    get_visible_manuscripts,
    toggle_visibility_by_id,
    update_manuscript_by_id,
)
from utils.logger import log

router = APIRouter()


@router.delete("/search/manuscript/{manuscript_id}")
async def delete_manuscript(
    manuscript_id: str = Path(..., description="원고 ID"),
    category: str = Query(..., description="카테고리 (DB명)")
):
    """
    원고 삭제 API (소프트 삭제)

    - **manuscript_id**: MongoDB Document ID (필수)
    - **category**: 카테고리/DB명 (필수)

    Returns:
        {"ok": true, "deletedId": "..."}
    """
    result = await run_in_threadpool(
        delete_manuscript_by_id,
        manuscript_id=manuscript_id,
        category=category,
    )
    log.success("원고 삭제", id=manuscript_id[:8])

    return result


@router.patch("/search/manuscript/{manuscript_id}")
async def update_manuscript(
    manuscript_id: str = Path(..., description="원고 ID"),
    category: str = Query(..., description="카테고리 (DB명)"),
    body: ManuscriptUpdateRequest = ...,
):
    """
    원고 수정 API

    - **manuscript_id**: MongoDB Document ID (필수)
    - **category**: 카테고리/DB명 (필수)
    - **body.content**: 수정된 원고 내용 (필수)
    - **body.memo**: 수정 메모 (선택)

    Returns:
        {"ok": true, "manuscript": {"_id": "...", "content": "...", "updatedAt": ...}}
    """
    result = await run_in_threadpool(
        update_manuscript_by_id,
        manuscript_id=manuscript_id,
        category=category,
        content=body.content,
        memo=body.memo,
    )
    log.success("원고 수정", id=manuscript_id[:8])

    return result


@router.patch("/search/manuscript/{manuscript_id}/visibility")
async def toggle_visibility(
    manuscript_id: str = Path(..., description="원고 ID"),
    category: str = Query(..., description="카테고리 (DB명)")
):
    """
    원고 노출여부 토글 API

    - **manuscript_id**: MongoDB Document ID (필수)
    - **category**: 카테고리/DB명 (필수)

    Returns:
        {"ok": true, "visible": true/false, "manuscriptId": "..."}
    """
    result = await run_in_threadpool(
        toggle_visibility_by_id,
        manuscript_id=manuscript_id,
        category=category,
    )
    log.success("노출여부 변경", id=manuscript_id[:8], visible=result["visible"])

    return result


@router.get("/search/manuscripts/visible")
async def get_visible_manuscripts_api(
    category: Optional[str] = Query(None, description="카테고리 필터 (없으면 전체)"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 결과 수"),
):
    """
    노출 원고 목록 조회 API

    visible=True 또는 visible 필드가 없는 원고만 반환

    - **category**: 카테고리 필터 (선택, 없으면 전체 카테고리)
    - **page**: 페이지 번호 (기본값: 1)
    - **limit**: 페이지당 결과 수 (기본값: 20, 최대: 100)

    Returns:
        {"documents": [...], "total": int, "skip": int, "limit": int}
    """
    skip = (page - 1) * limit

    result = await run_in_threadpool(
        get_visible_manuscripts,
        category=category,
        skip=skip,
        limit=limit,
    )
    log.success("노출 원고 조회", count=len(result['documents']), total=result['total'])

    return result

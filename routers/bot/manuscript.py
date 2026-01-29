"""원고 관리 (prepare, queue, manuscript, retry, delete)"""

import json
import shutil
from datetime import datetime

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from utils.logger import log

from .common import (
    PENDING_DIR,
    COMPLETED_DIR,
    FAILED_DIR,
    ManuscriptData,
    get_manuscript_list,
    get_manuscript_data,
    get_next_manuscript_id,
)

router = APIRouter()


class PrepareRequest(BaseModel):
    manuscript: ManuscriptData


@router.post("/prepare")
async def prepare_manuscript(request: PrepareRequest):
    """원고 저장 (수동)"""
    manuscript_id = get_next_manuscript_id()
    manuscript_dir = PENDING_DIR / manuscript_id
    manuscript_dir.mkdir(parents=True, exist_ok=True)

    images_dir = manuscript_dir / "images"
    images_dir.mkdir(exist_ok=True)

    data = {
        "title": request.manuscript.title,
        "content": request.manuscript.content,
        "tags": request.manuscript.tags or [],
        "category": request.manuscript.category,
        "images": request.manuscript.images or [],
        "created_at": datetime.now().isoformat(),
    }

    with open(manuscript_dir / "manuscript.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    log.success("원고 저장 완료", id=manuscript_id, title=request.manuscript.title[:30])

    return JSONResponse(content={
        "success": True,
        "manuscript_id": manuscript_id,
        "message": "원고가 저장되었습니다.",
        "images_dir": str(images_dir),
    })


@router.get("/queue")
async def get_queue(status: str = "pending"):
    """대기 중인 원고 목록"""
    manuscripts = get_manuscript_list(status)
    return JSONResponse(content={
        "status": status,
        "count": len(manuscripts),
        "manuscripts": [m.model_dump() for m in manuscripts],
    })


@router.get("/manuscript/{manuscript_id}")
async def get_manuscript(manuscript_id: str):
    """특정 원고 상세 조회"""
    for dir_path in [PENDING_DIR, COMPLETED_DIR, FAILED_DIR]:
        manuscript_dir = dir_path / manuscript_id
        if manuscript_dir.exists():
            data = get_manuscript_data(manuscript_dir)
            if data:
                return JSONResponse(content={
                    "id": manuscript_id,
                    "status": dir_path.name,
                    "data": data,
                    "images": data.get("images", []),
                })

    raise HTTPException(status_code=404, detail="원고를 찾을 수 없습니다.")


@router.delete("/manuscript/{manuscript_id}")
async def delete_manuscript(manuscript_id: str):
    """원고 삭제"""
    for dir_path in [PENDING_DIR, COMPLETED_DIR, FAILED_DIR]:
        manuscript_dir = dir_path / manuscript_id
        if manuscript_dir.exists():
            shutil.rmtree(manuscript_dir)
            return JSONResponse(content={
                "success": True,
                "message": f"원고 {manuscript_id} 삭제 완료",
            })

    raise HTTPException(status_code=404, detail="원고를 찾을 수 없습니다.")


@router.post("/retry/{manuscript_id}")
async def retry_manuscript(manuscript_id: str):
    """실패한 원고 재시도 (pending으로 이동)"""
    failed_dir = FAILED_DIR / manuscript_id
    if not failed_dir.exists():
        raise HTTPException(status_code=404, detail="실패한 원고를 찾을 수 없습니다.")

    error_file = failed_dir / "error.json"
    if error_file.exists():
        error_file.unlink()

    pending_dir = PENDING_DIR / manuscript_id
    shutil.move(str(failed_dir), str(pending_dir))

    return JSONResponse(content={
        "success": True,
        "message": f"원고 {manuscript_id}를 재시도 대기열로 이동했습니다.",
    })

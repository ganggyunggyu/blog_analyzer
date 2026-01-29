"""큐 관리 API"""

import asyncio
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from routers.auth.naver import naver_login_with_playwright
from utils.logger import log

from .common import (
    create_queue,
    get_queue_dir,
    get_queue_meta,
    get_queue_manuscripts,
    list_active_queues,
    update_queue_status,
    cleanup_empty_queue,
    get_base_time,
    calculate_schedule_time,
    publish_queue_manuscript,
    get_manuscript_list,
)

router = APIRouter()


class CreateQueueRequest(BaseModel):
    """큐 생성 요청"""
    manuscript_ids: list[str]
    account_id: Optional[str] = None
    schedule_date: Optional[str] = None


class StartQueueRequest(BaseModel):
    """큐 발행 시작 요청"""
    queue_id: str
    account: dict
    use_schedule: bool = True
    schedule_date: Optional[str] = None
    schedule_start_hour: int = 10
    schedule_interval_hours: int = 1
    schedule_interval_minutes: int = 0
    delay_between_posts: int = 60


@router.get("/queues")
async def get_queues():
    """진행중인 큐 목록"""
    queues = list_active_queues()
    return JSONResponse(content={
        "count": len(queues),
        "queues": [q.model_dump() for q in queues],
    })


@router.get("/queue/{queue_id}")
async def get_queue_detail(queue_id: str):
    """큐 상세 정보"""
    meta = get_queue_meta(queue_id)
    if not meta:
        raise HTTPException(status_code=404, detail="큐를 찾을 수 없습니다.")

    manuscripts = get_queue_manuscripts(queue_id)
    return JSONResponse(content={
        "queue_id": queue_id,
        "meta": meta,
        "manuscripts": [m.model_dump() for m in manuscripts],
    })


@router.post("/queue/create")
async def create_queue_endpoint(request: CreateQueueRequest):
    """새 큐 생성 (pending에서 원고 이동)"""
    if not request.manuscript_ids:
        raise HTTPException(status_code=400, detail="원고 ID가 필요합니다.")

    queue_id, queue_dir = create_queue(
        manuscript_ids=request.manuscript_ids,
        account_id=request.account_id,
        schedule_date=request.schedule_date,
    )

    manuscripts = get_queue_manuscripts(queue_id)

    return JSONResponse(content={
        "success": True,
        "queue_id": queue_id,
        "manuscript_count": len(manuscripts),
        "message": f"큐가 생성되었습니다. ({len(manuscripts)}개 원고)",
    })


@router.post("/queue/create-all")
async def create_queue_all(account_id: Optional[str] = None, schedule_date: Optional[str] = None):
    """pending의 모든 원고로 큐 생성"""
    pending_list = get_manuscript_list("pending")
    if not pending_list:
        raise HTTPException(status_code=404, detail="pending에 원고가 없습니다.")

    manuscript_ids = [m.id for m in pending_list]
    queue_id, queue_dir = create_queue(
        manuscript_ids=manuscript_ids,
        account_id=account_id,
        schedule_date=schedule_date,
    )

    manuscripts = get_queue_manuscripts(queue_id)

    return JSONResponse(content={
        "success": True,
        "queue_id": queue_id,
        "manuscript_count": len(manuscripts),
        "message": f"모든 pending 원고로 큐가 생성되었습니다. ({len(manuscripts)}개)",
    })


@router.post("/queue/start")
async def start_queue(request: StartQueueRequest):
    """큐 발행 시작"""
    queue_dir = get_queue_dir(request.queue_id)
    if not queue_dir:
        raise HTTPException(status_code=404, detail="큐를 찾을 수 없습니다.")

    account_id = request.account.get("id")
    password = request.account.get("password")

    if not account_id or not password:
        raise HTTPException(status_code=400, detail="계정 정보가 필요합니다.")

    # 큐 상태 업데이트
    update_queue_status(request.queue_id, "processing")

    log.header(f"큐 발행 시작: {request.queue_id}", "📤")
    log.kv("계정", f"{account_id[:3]}***")

    # 로그인
    login_result = await naver_login_with_playwright(
        account_id=account_id,
        password=password,
        debug=True,
    )

    if not login_result["success"]:
        update_queue_status(request.queue_id, "failed")
        raise HTTPException(status_code=401, detail=f"로그인 실패: {login_result.get('message')}")

    cookies = login_result["cookies"]
    log.success("로그인 성공", cookies=len(cookies))

    # 원고 목록
    manuscripts = get_queue_manuscripts(request.queue_id)
    if not manuscripts:
        update_queue_status(request.queue_id, "completed")
        return JSONResponse(content={
            "success": True,
            "queue_id": request.queue_id,
            "message": "발행할 원고가 없습니다.",
        })

    # 발행
    base_time = get_base_time(request.schedule_date, request.schedule_start_hour)
    results = []

    for idx, manuscript in enumerate(manuscripts):
        schedule_time = None
        if request.use_schedule:
            schedule_time = calculate_schedule_time(
                base_time, idx,
                request.schedule_interval_hours,
                request.schedule_interval_minutes,
            )
            log.step(idx + 1, len(manuscripts), f"{manuscript.title[:25]} (예약: {schedule_time.strftime('%m/%d %H:%M')})")
        else:
            log.step(idx + 1, len(manuscripts), f"{manuscript.title[:30]} (즉시)")

        result = await publish_queue_manuscript(
            cookies=cookies,
            queue_dir=queue_dir,
            manuscript_id=manuscript.id,
            schedule_time=schedule_time,
            account_id=account_id,
        )
        results.append(result)

        if idx < len(manuscripts) - 1:
            await asyncio.sleep(request.delay_between_posts)

    # 완료 처리
    success_count = sum(1 for r in results if r["success"])
    cleanup_empty_queue(request.queue_id)

    log.divider()
    log.success(f"큐 발행 완료: {request.queue_id}", 성공=f"{success_count}/{len(manuscripts)}")

    return JSONResponse(content={
        "success": True,
        "queue_id": request.queue_id,
        "total": len(manuscripts),
        "success_count": success_count,
        "failed_count": len(manuscripts) - success_count,
        "results": results,
    })


@router.delete("/queue/{queue_id}")
async def delete_queue(queue_id: str):
    """큐 삭제 (원고는 pending으로 복원)"""
    import shutil
    from .common import PENDING_DIR

    queue_dir = get_queue_dir(queue_id)
    if not queue_dir:
        raise HTTPException(status_code=404, detail="큐를 찾을 수 없습니다.")

    # 원고들을 pending으로 복원
    restored = []
    for folder in queue_dir.iterdir():
        if not folder.is_dir() or folder.name.startswith("."):
            continue

        # 번호 prefix 제거 (001_탈모 → 탈모)
        original_id = "_".join(folder.name.split("_")[1:]) if "_" in folder.name else folder.name
        dst = PENDING_DIR / original_id
        if dst.exists():
            shutil.rmtree(dst)
        shutil.move(str(folder), str(dst))
        restored.append(original_id)

    # 큐 폴더 삭제
    shutil.rmtree(queue_dir)

    return JSONResponse(content={
        "success": True,
        "message": f"큐가 삭제되고 {len(restored)}개 원고가 pending으로 복원되었습니다.",
        "restored": restored,
    })

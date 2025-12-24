"""전체 봇 실행 (큐 기반 로그인 + 발행)"""

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
    get_queue_manuscripts,
    get_manuscript_list,
    get_base_time,
    calculate_schedule_time,
    update_queue_status,
    cleanup_empty_queue,
    publish_queue_manuscript,
)

router = APIRouter()


class StartBotRequest(BaseModel):
    account: dict  # 단일 계정
    manuscript_ids: Optional[list[str]] = None  # 특정 원고만 (없으면 전체)
    delay_between_posts: int = 60
    use_schedule: bool = True
    schedule_date: Optional[str] = None
    schedule_start_hour: int = 10
    schedule_interval_hours: int = 1
    schedule_interval_minutes: int = 0


@router.post("/start")
async def start_bot(request: StartBotRequest):
    """큐 기반 봇 실행 (pending → 큐 생성 → 발행)"""
    account_id = request.account.get("id")
    password = request.account.get("password")

    if not account_id or not password:
        raise HTTPException(status_code=400, detail="계정 정보가 필요합니다.")

    # 원고 ID 결정
    if request.manuscript_ids:
        manuscript_ids = request.manuscript_ids
    else:
        pending_list = get_manuscript_list("pending")
        if not pending_list:
            raise HTTPException(status_code=404, detail="pending에 원고가 없습니다.")
        manuscript_ids = [m.id for m in pending_list]

    # 큐 생성
    log.header("큐 생성", "📦")
    queue_id, queue_dir = create_queue(
        manuscript_ids=manuscript_ids,
        account_id=account_id,
        schedule_date=request.schedule_date,
    )

    manuscripts = get_queue_manuscripts(queue_id)
    if not manuscripts:
        raise HTTPException(status_code=500, detail="큐 생성 실패: 원고가 없습니다.")

    log.kv("큐 ID", queue_id)
    log.kv("원고 수", len(manuscripts))

    # 로그인
    log.header(f"로그인: {account_id[:3]}***", "🔐")
    update_queue_status(queue_id, "processing")

    login_result = await naver_login_with_playwright(
        account_id=account_id,
        password=password,
        debug=True,
    )

    if not login_result["success"]:
        update_queue_status(queue_id, "failed")
        raise HTTPException(status_code=401, detail=f"로그인 실패: {login_result.get('message')}")

    cookies = login_result["cookies"]
    log.success("로그인 성공", cookies=len(cookies))

    # 발행
    log.header("발행 시작", "📤")
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
    cleanup_empty_queue(queue_id)

    log.divider()
    log.success("발행 완료", queue_id=queue_id, 성공=f"{success_count}/{len(manuscripts)}")

    return JSONResponse(content={
        "success": True,
        "queue_id": queue_id,
        "account": f"{account_id[:3]}***",
        "total": len(manuscripts),
        "success_count": success_count,
        "failed_count": len(manuscripts) - success_count,
        "results": results,
    })

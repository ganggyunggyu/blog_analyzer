"""원고 발행"""

from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .common import (
    get_manuscript_list,
    get_base_time,
    calculate_schedule_time,
    publish_single_manuscript,
)

router = APIRouter()


class PublishRequest(BaseModel):
    cookies: list
    manuscript_id: Optional[str] = None
    count: int = 1
    use_schedule: bool = False
    schedule_date: Optional[str] = None
    schedule_start_hour: int = 10
    schedule_interval_hours: int = 1
    schedule_interval_minutes: int = 0


@router.post("/publish")
async def publish_manuscripts(request: PublishRequest):
    """원고 발행"""
    manuscripts = get_manuscript_list("pending")

    if not manuscripts:
        raise HTTPException(status_code=404, detail="발행할 원고가 없습니다.")

    if request.manuscript_id:
        target_ids = [request.manuscript_id]
    else:
        target_ids = [m.id for m in manuscripts[:request.count]]

    base_time = get_base_time(request.schedule_date, request.schedule_start_hour)

    results = []
    for idx, manuscript_id in enumerate(target_ids):
        schedule_time = None
        if request.use_schedule:
            schedule_time = calculate_schedule_time(
                base_time, idx,
                request.schedule_interval_hours,
                request.schedule_interval_minutes
            )

        result = await publish_single_manuscript(
            cookies=request.cookies,
            manuscript_id=manuscript_id,
            schedule_time=schedule_time,
        )
        results.append(result)

    success_count = sum(1 for r in results if r["success"])

    return JSONResponse(content={
        "total": len(results),
        "success": success_count,
        "failed": len(results) - success_count,
        "results": results,
    })

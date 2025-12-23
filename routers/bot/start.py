"""전체 봇 실행 (로그인 + 발행)"""

import asyncio
from typing import Optional

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from routers.auth.naver import naver_login_with_playwright
from utils.logger import log

from .common import (
    get_manuscript_list,
    get_base_time,
    calculate_schedule_time,
    publish_single_manuscript,
)

router = APIRouter()


class StartBotRequest(BaseModel):
    accounts: list[dict]
    posts_per_account: int = 10
    delay_between_posts: int = 60
    use_schedule: bool = True
    schedule_date: Optional[str] = None
    schedule_start_hour: int = 10
    schedule_interval_hours: int = 1
    schedule_interval_minutes: int = 0


@router.post("/start")
async def start_bot(request: StartBotRequest):
    """전체 봇 실행 (계정별 반복)"""
    all_results = []

    for account in request.accounts:
        account_id = account.get("id")
        password = account.get("password")

        if not account_id or not password:
            all_results.append({
                "account": account_id or "unknown",
                "success": False,
                "message": "ID 또는 비밀번호가 없습니다.",
                "posts": [],
            })
            continue

        log.header(f"계정 로그인: {account_id[:3]}***", "👤")

        login_result = await naver_login_with_playwright(
            account_id=account_id,
            password=password,
            debug=True,
        )

        if not login_result["success"]:
            all_results.append({
                "account": account_id[:3] + "***",
                "success": False,
                "message": f"로그인 실패: {login_result.get('message')}",
                "posts": [],
            })
            continue

        cookies = login_result["cookies"]
        log.success("로그인 성공", cookies=len(cookies))

        manuscripts = get_manuscript_list("pending")
        base_time = get_base_time(request.schedule_date, request.schedule_start_hour)
        posts_results = []

        for i, manuscript in enumerate(manuscripts[:request.posts_per_account]):
            schedule_time = None
            if request.use_schedule:
                schedule_time = calculate_schedule_time(
                    base_time, i,
                    request.schedule_interval_hours,
                    request.schedule_interval_minutes
                )
                log.step(i + 1, request.posts_per_account, f"{manuscript.title[:25]} (예약: {schedule_time.strftime('%m/%d %H:%M')})")
            else:
                log.step(i + 1, request.posts_per_account, f"{manuscript.title[:30]} (즉시발행)")

            result = await publish_single_manuscript(
                cookies=cookies,
                manuscript_id=manuscript.id,
                schedule_time=schedule_time,
                account_id=account_id,
            )
            posts_results.append(result)

            if i < len(manuscripts[:request.posts_per_account]) - 1:
                log.debug(f"{request.delay_between_posts}초 대기...")
                await asyncio.sleep(request.delay_between_posts)

        success_count = sum(1 for p in posts_results if p["success"])

        all_results.append({
            "account": account_id[:3] + "***",
            "success": True,
            "message": f"{success_count}/{len(posts_results)} 발행 완료",
            "posts": posts_results,
        })

        log.success(f"계정 완료: {account_id[:3]}***", success=f"{success_count}/{len(posts_results)}")

    total_success = sum(
        sum(1 for p in r.get("posts", []) if p.get("success"))
        for r in all_results
    )
    total_posts = sum(len(r.get("posts", [])) for r in all_results)

    return JSONResponse(content={
        "total_accounts": len(request.accounts),
        "total_posts": total_posts,
        "total_success": total_success,
        "results": all_results,
    })

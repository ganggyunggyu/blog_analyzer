"""전체 자동화: 생성 → 발행"""

import asyncio
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel

from routers.auth.naver import naver_login_with_playwright
from routers.generate.batch import generate_images_parallel, save_to_pending
from llm.gpt4o_service import gpt4o_gen
from utils.get_category_db_name import get_category_db_name
from utils.logger import log

from .common import (
    get_base_time,
    calculate_schedule_time,
    publish_single_manuscript,
)

router = APIRouter()


class AutoBotRequest(BaseModel):
    account: dict
    keywords: list[str]
    service: str = "default"
    ref: str = ""
    generate_images: bool = True
    image_count: int = 5
    use_schedule: bool = True
    schedule_date: Optional[str] = None
    schedule_start_hour: int = 10
    schedule_interval_hours: int = 1
    delay_between_posts: int = 60


@router.post("/auto")
async def auto_bot(request: AutoBotRequest):
    """
    전체 자동화: 원고+이미지 생성 → 로그인 → 발행

    1. 키워드별로 원고 + 이미지 생성
    2. pending 폴더에 저장
    3. 네이버 로그인
    4. 예약발행
    """
    start_ts = datetime.now()
    account_id = request.account.get("id")
    password = request.account.get("password")

    if not account_id or not password:
        raise HTTPException(status_code=400, detail="계정 정보가 필요합니다.")

    log.header("전체 자동화 시작", "🤖")
    log.kv("계정", f"{account_id[:3]}***")
    log.kv("키워드", f"{len(request.keywords)}개")
    log.kv("이미지", "ON" if request.generate_images else "OFF")

    # ========== 1단계: 원고 + 이미지 생성 ==========
    log.header("1단계: 원고 생성", "📝")
    generated_ids = []

    for idx, keyword in enumerate(request.keywords):
        keyword = keyword.strip()
        if not keyword:
            continue

        log.step(idx + 1, len(request.keywords), keyword[:30])

        try:
            category = await get_category_db_name(keyword=keyword + request.ref)

            content = await run_in_threadpool(
                gpt4o_gen,
                user_instructions=keyword,
                ref=request.ref,
                category=category
            )

            if not content:
                log.error(f"원고 생성 실패", keyword=keyword[:20])
                continue

            image_urls = []
            if request.generate_images:
                images = await run_in_threadpool(
                    generate_images_parallel,
                    keyword,
                    request.image_count
                )
                image_urls = [img["url"] for img in images if img.get("url")]

            manuscript_id = await save_to_pending(keyword, content, image_urls)
            generated_ids.append(manuscript_id)
            log.success(f"생성 완료", id=manuscript_id, images=len(image_urls))

        except Exception as e:
            log.error(f"생성 에러", keyword=keyword[:20], error=str(e))

        await asyncio.sleep(1)

    if not generated_ids:
        raise HTTPException(status_code=500, detail="원고 생성에 모두 실패했습니다.")

    log.success(f"원고 생성 완료", count=len(generated_ids))

    # ========== 2단계: 로그인 ==========
    log.header("2단계: 네이버 로그인", "🔐")

    login_result = await naver_login_with_playwright(
        account_id=account_id,
        password=password,
        debug=True,
    )

    if not login_result["success"]:
        raise HTTPException(
            status_code=401,
            detail=f"로그인 실패: {login_result.get('message')}"
        )

    cookies = login_result["cookies"]
    log.success("로그인 성공", cookies=len(cookies))

    # ========== 3단계: 발행 ==========
    log.header("3단계: 블로그 발행", "📤")

    base_time = get_base_time(request.schedule_date, request.schedule_start_hour)
    publish_results = []

    for idx, manuscript_id in enumerate(generated_ids):
        schedule_time = None
        if request.use_schedule:
            schedule_time = calculate_schedule_time(
                base_time, idx, request.schedule_interval_hours, 0
            )
            log.step(idx + 1, len(generated_ids), f"ID:{manuscript_id} (예약: {schedule_time.strftime('%m/%d %H:%M')})")
        else:
            log.step(idx + 1, len(generated_ids), f"ID:{manuscript_id} (즉시)")

        result = await publish_single_manuscript(
            cookies=cookies,
            manuscript_id=manuscript_id,
            schedule_time=schedule_time,
            account_id=account_id,
        )
        publish_results.append(result)

        if idx < len(generated_ids) - 1:
            await asyncio.sleep(request.delay_between_posts)

    # ========== 결과 ==========
    elapsed = (datetime.now() - start_ts).total_seconds()
    success_count = sum(1 for r in publish_results if r["success"])

    log.divider()
    log.success(f"자동화 완료", 성공=f"{success_count}/{len(generated_ids)}", 시간=f"{elapsed:.0f}s")

    return JSONResponse(content={
        "success": True,
        "account": f"{account_id[:3]}***",
        "generated": len(generated_ids),
        "published": success_count,
        "failed": len(generated_ids) - success_count,
        "elapsed": round(elapsed, 1),
        "results": publish_results,
    })

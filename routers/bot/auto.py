"""전체 자동화: 생성 → 발행 (큐 기반)"""

import asyncio
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel

from llm.gemini_new_service import gemini_new_gen
from routers.auth.naver import naver_login_with_playwright
from routers.generate.batch import generate_images_parallel, save_to_pending
from routers.generate.gemini_image import _try_s3_images
from utils.get_category_db_name import get_category_db_name
from utils.logger import log

from .common import (
    create_queue,
    get_queue_manuscripts,
    get_base_time,
    calculate_schedule_time,
    update_queue_status,
    cleanup_empty_queue,
    publish_queue_manuscript,
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
    delay_between_posts: int = 10


@router.post("/auto")
async def auto_bot(request: AutoBotRequest):
    """전체 자동화: 원고+이미지 생성 → 로그인 → 발행"""
    start_ts = datetime.now()
    account_id = request.account.get("id")
    password = request.account.get("password")

    if not account_id or not password:
        raise HTTPException(status_code=400, detail="계정 정보가 필요합니다.")

    log.header("전체 자동화 시작", "🤖")
    log.kv("계정", f"{account_id[:3]}***")
    log.kv("키워드", f"{len(request.keywords)}개")

    # ========== 1단계: 원고 생성 ==========
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
                gemini_new_gen,
                user_instructions=keyword,
                ref=request.ref,
                category=category,
            )

            if not content:
                log.error("원고 생성 실패", keyword=keyword[:20])
                continue

            image_urls = []
            if request.generate_images:
                s3_images, s3_found = await run_in_threadpool(
                    _try_s3_images, keyword, request.image_count
                )
                if s3_found and s3_images:
                    image_urls = [img["url"] for img in s3_images]
                else:
                    images = await run_in_threadpool(
                        generate_images_parallel, keyword, request.image_count, category
                    )
                    image_urls = [img["url"] for img in images if img.get("url")]

            manuscript_id = await save_to_pending(keyword, content, image_urls)
            generated_ids.append(manuscript_id)
            log.success("생성 완료", id=manuscript_id, images=len(image_urls))

        except Exception as e:
            log.error("생성 에러", keyword=keyword[:20], error=str(e))

        await asyncio.sleep(1)

    if not generated_ids:
        raise HTTPException(status_code=500, detail="원고 생성에 모두 실패했습니다.")

    log.success("원고 생성 완료", count=len(generated_ids))

    # ========== 2단계: 큐 생성 ==========
    log.header("2단계: 큐 생성", "📦")

    queue_id, queue_dir = create_queue(
        manuscript_ids=generated_ids,
        account_id=account_id,
        schedule_date=request.schedule_date,
    )

    manuscripts = get_queue_manuscripts(queue_id)
    log.kv("큐 ID", queue_id)
    log.kv("원고 수", len(manuscripts))

    # ========== 3단계: 로그인 ==========
    log.header("3단계: 네이버 로그인", "🔐")
    update_queue_status(queue_id, "processing")

    login_result = await naver_login_with_playwright(
        account_id=account_id,
        password=password,
        debug=True,
    )

    if not login_result["success"]:
        update_queue_status(queue_id, "failed")
        raise HTTPException(
            status_code=401, detail=f"로그인 실패: {login_result.get('message')}"
        )

    cookies = login_result["cookies"]
    log.success("로그인 성공", cookies=len(cookies))

    # ========== 4단계: 발행 ==========
    log.header("4단계: 블로그 발행", "📤")

    base_time = get_base_time(request.schedule_date, request.schedule_start_hour)
    publish_results = []

    for idx, manuscript in enumerate(manuscripts):
        schedule_time = None

        if request.use_schedule:
            schedule_time = calculate_schedule_time(
                base_time, idx, request.schedule_interval_hours, 0
            )
            log.step(
                idx + 1,
                len(manuscripts),
                f"{manuscript.title[:25]} (예약: {schedule_time.strftime('%m/%d %H:%M')})",
            )
        else:
            log.step(idx + 1, len(manuscripts), f"{manuscript.title[:30]} (즉시)")

        result = await publish_queue_manuscript(
            cookies=cookies,
            queue_dir=queue_dir,
            manuscript_id=manuscript.id,
            schedule_time=schedule_time,
            account_id=account_id,
        )
        publish_results.append(result)

        if idx < len(manuscripts) - 1:
            await asyncio.sleep(request.delay_between_posts)

    # ========== 결과 ==========
    success_count = sum(1 for r in publish_results if r["success"])
    cleanup_empty_queue(queue_id)

    elapsed = (datetime.now() - start_ts).total_seconds()

    log.divider()
    log.success(
        "자동화 완료",
        queue_id=queue_id,
        성공=f"{success_count}/{len(manuscripts)}",
        시간=f"{elapsed:.0f}s",
    )

    return JSONResponse(
        content={
            "success": True,
            "queue_id": queue_id,
            "account": f"{account_id[:3]}***",
            "generated": len(generated_ids),
            "published": success_count,
            "failed": len(manuscripts) - success_count,
            "elapsed": round(elapsed, 1),
            "results": publish_results,
        }
    )

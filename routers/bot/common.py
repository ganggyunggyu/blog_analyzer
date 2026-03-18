"""봇 공통 함수/모델"""

from __future__ import annotations

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

from fastapi.concurrency import run_in_threadpool

from llm.gemini_new_service import gemini_new_gen
from routers.generate.batch import (
    generate_batch_id,
    generate_images_parallel,
    save_to_pending,
)
from routers.generate.gemini_image import _try_s3_images
from services.blog_write_service import write_blog_post
from utils.get_category_db_name import get_category_db_name
from utils.logger import log

from .common_models import ManuscriptData, ManuscriptInfo, QueueInfo
from .common_storage import (
    COMPLETED_DIR,
    FAILED_DIR,
    IMAGE_EXTENSIONS,
    MANUSCRIPTS_DIR,
    PENDING_DIR,
    calculate_schedule_time,
    cleanup_empty_queue,
    create_queue,
    generate_queue_id,
    get_base_time,
    get_manuscript_data,
    get_manuscript_list,
    get_next_manuscript_id,
    get_queue_dir,
    get_queue_manuscripts,
    get_queue_meta,
    list_active_queues,
    move_queue_manuscript_to_completed,
    move_queue_manuscript_to_failed,
    move_to_completed,
    move_to_failed,
    parse_manuscript_txt,
    should_publish_immediately,
    update_queue_status,
)


async def publish_single_manuscript(
    cookies: list,
    manuscript_id: str,
    schedule_time: Optional[datetime] = None,
    account_id: Optional[str] = None,
) -> dict:
    """단일 원고 발행 (공통 로직)"""
    manuscript_dir = PENDING_DIR / manuscript_id
    data = get_manuscript_data(manuscript_dir)
    if not data:
        return {
            "manuscript_id": manuscript_id,
            "success": False,
            "message": "원고를 찾을 수 없습니다.",
        }

    actual_schedule_time = schedule_time
    if schedule_time and should_publish_immediately(schedule_time):
        log.warning(
            "예약 시간 지남 → 즉시 발행",
            id=manuscript_id,
            원래예약=schedule_time.strftime("%m/%d %H:%M"),
        )
        actual_schedule_time = None

    if actual_schedule_time:
        log.info(
            f"발행: {data['title'][:30]}",
            id=manuscript_id,
            schedule=actual_schedule_time.strftime("%m/%d %H:%M"),
        )
    else:
        log.info(f"발행: {data['title'][:30]}", id=manuscript_id)

    result = await write_blog_post(
        cookies=cookies,
        title=data["title"],
        content=data["content"],
        tags=data.get("tags"),
        images=data.get("images"),
        is_public=True,
        schedule_time=actual_schedule_time.isoformat() if actual_schedule_time else None,
        debug=True,
    )

    if result["success"]:
        move_to_completed(manuscript_id, manuscript_dir, result, schedule_time, account_id)
        log.success("발행 성공", id=manuscript_id)
    else:
        move_to_failed(manuscript_id, manuscript_dir, result, account_id)
        log.error("발행 실패", id=manuscript_id, message=result.get("message"))

    return {
        "manuscript_id": manuscript_id,
        "title": data["title"][:50],
        "success": result["success"],
        "post_url": result.get("post_url"),
        "message": result.get("message"),
    }


async def publish_queue_manuscript(
    cookies: list,
    queue_dir: Path,
    manuscript_id: str,
    schedule_time: Optional[datetime] = None,
    account_id: Optional[str] = None,
) -> dict:
    """큐 내 단일 원고 발행"""
    manuscript_dir = queue_dir / manuscript_id
    data = get_manuscript_data(manuscript_dir)
    if not data:
        return {
            "manuscript_id": manuscript_id,
            "success": False,
            "message": "원고를 찾을 수 없습니다.",
        }

    actual_schedule_time = schedule_time
    if schedule_time and should_publish_immediately(schedule_time):
        log.warning(
            "예약 시간 지남 → 즉시 발행",
            id=manuscript_id,
            원래예약=schedule_time.strftime("%m/%d %H:%M"),
        )
        actual_schedule_time = None

    if actual_schedule_time:
        log.info(
            f"발행: {data['title'][:30]}",
            id=manuscript_id,
            schedule=actual_schedule_time.strftime("%m/%d %H:%M"),
        )
    else:
        log.info(f"발행: {data['title'][:30]}", id=manuscript_id)

    result = await write_blog_post(
        cookies=cookies,
        title=data["title"],
        content=data["content"],
        tags=data.get("tags"),
        images=data.get("images"),
        is_public=True,
        schedule_time=actual_schedule_time.isoformat() if actual_schedule_time else None,
        debug=True,
    )

    if result["success"]:
        move_queue_manuscript_to_completed(
            queue_dir,
            manuscript_id,
            result,
            schedule_time,
            account_id,
        )
        log.success("발행 성공", id=manuscript_id)
    else:
        move_queue_manuscript_to_failed(queue_dir, manuscript_id, result, account_id)
        log.error("발행 실패", id=manuscript_id, message=result.get("message"))

    return {
        "manuscript_id": manuscript_id,
        "title": data["title"][:50],
        "success": result["success"],
        "post_url": result.get("post_url"),
        "message": result.get("message"),
    }


async def generate_single_manuscript(
    keyword: str,
    ref: str = "",
    generate_images: bool = True,
    image_count: int = 5,
    batch_id: Optional[str] = None,
) -> Optional[dict]:
    """단일 원고 생성 (원고 + 이미지 + pending 저장)"""
    try:
        category = await get_category_db_name(keyword=keyword + ref)
        content = await run_in_threadpool(
            gemini_new_gen,
            user_instructions=keyword,
            ref=ref,
            category=category,
        )
        if not content:
            log.error("원고 생성 실패", keyword=keyword[:20])
            return None

        image_urls: list[str] = []
        if generate_images:
            s3_images, s3_found = await run_in_threadpool(_try_s3_images, keyword, image_count)
            if s3_found and s3_images:
                image_urls = [image["url"] for image in s3_images]
            else:
                images = await run_in_threadpool(
                    generate_images_parallel,
                    keyword,
                    image_count,
                    category,
                )
                image_urls = [image["url"] for image in images if image.get("url")]

        manuscript_id = await save_to_pending(keyword, content, image_urls, batch_id)
        log.success("생성 완료", id=manuscript_id, images=len(image_urls))
        return {
            "id": manuscript_id,
            "keyword": keyword,
            "images": len(image_urls),
        }
    except Exception as error:
        log.error("생성 에러", keyword=keyword[:20], error=str(error))
        return None


async def generate_manuscripts_batch(
    keywords: list[str],
    ref: str = "",
    generate_images: bool = True,
    image_count: int = 5,
    delay: float = 1.0,
    on_progress: Optional[Callable] = None,
) -> tuple[str, list[dict]]:
    """여러 키워드 원고 일괄 생성"""
    batch_id = generate_batch_id()
    generated: list[dict] = []

    log.kv("배치 ID", batch_id)

    for index, keyword in enumerate(keywords):
        keyword = keyword.strip()
        if not keyword:
            continue

        if on_progress:
            on_progress(index + 1, len(keywords), keyword)
        else:
            log.step(index + 1, len(keywords), keyword[:30])

        result = await generate_single_manuscript(
            keyword=keyword,
            ref=ref,
            generate_images=generate_images,
            image_count=image_count,
            batch_id=batch_id,
        )
        if result:
            generated.append(result)

        if index < len(keywords) - 1:
            await asyncio.sleep(delay)

    return batch_id, generated


async def publish_manuscripts_batch(
    cookies: list,
    queue_dir: Path,
    manuscripts: list,
    schedule_times: Optional[list[Optional[datetime]]] = None,
    account_id: Optional[str] = None,
    delay: float = 10.0,
    on_progress: Optional[Callable] = None,
) -> list[dict]:
    """여러 원고 일괄 발행"""
    results: list[dict] = []

    for index, manuscript in enumerate(manuscripts):
        schedule_time = (
            schedule_times[index]
            if schedule_times and index < len(schedule_times)
            else None
        )

        if on_progress:
            on_progress(index + 1, len(manuscripts), manuscript, schedule_time)
        else:
            if schedule_time:
                log.step(
                    index + 1,
                    len(manuscripts),
                    f"{manuscript.title[:25]} ({schedule_time.strftime('%m/%d %H:%M')})",
                )
            else:
                log.step(index + 1, len(manuscripts), f"{manuscript.title[:30]} (즉시)")

        result = await publish_queue_manuscript(
            cookies=cookies,
            queue_dir=queue_dir,
            manuscript_id=manuscript.id,
            schedule_time=schedule_time,
            account_id=account_id,
        )
        results.append(result)

        if index < len(manuscripts) - 1:
            await asyncio.sleep(delay)

    return results


__all__ = [
    "COMPLETED_DIR",
    "FAILED_DIR",
    "IMAGE_EXTENSIONS",
    "MANUSCRIPTS_DIR",
    "ManuscriptData",
    "ManuscriptInfo",
    "PENDING_DIR",
    "QueueInfo",
    "calculate_schedule_time",
    "cleanup_empty_queue",
    "create_queue",
    "generate_manuscripts_batch",
    "generate_queue_id",
    "generate_single_manuscript",
    "get_base_time",
    "get_manuscript_data",
    "get_manuscript_list",
    "get_next_manuscript_id",
    "get_queue_dir",
    "get_queue_manuscripts",
    "get_queue_meta",
    "list_active_queues",
    "parse_manuscript_txt",
    "publish_manuscripts_batch",
    "publish_queue_manuscript",
    "publish_single_manuscript",
    "should_publish_immediately",
    "update_queue_status",
]

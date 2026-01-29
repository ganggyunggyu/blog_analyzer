"""자동 스케줄 발행 API - 원고 자동생성 + 예약발행 (배치 큐 지원)"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator

from routers.auth.naver import naver_login_with_playwright
from utils.logger import log

from .common import (
    create_queue,
    get_queue_manuscripts,
    update_queue_status,
    cleanup_empty_queue,
    generate_manuscripts_batch,
    publish_manuscripts_batch,
)

router = APIRouter()


# ========== 스키마 ==========

class QueueItem(BaseModel):
    """큐 아이템 (계정 1개 단위)"""
    account: dict  # {"id": "...", "password": "..."}
    keywords: list[str]  # 최소 1개

    # 개별 오버라이드 (선택)
    service: Optional[str] = None
    ref: Optional[str] = None
    posts_per_day: Optional[int] = None
    interval_hours: Optional[int] = None

    @field_validator("keywords")
    @classmethod
    def validate_keywords(cls, v):
        if len(v) < 1:
            raise ValueError("키워드는 최소 1개 이상 필요합니다.")
        return v


class AutoScheduleRequest(BaseModel):
    """자동 스케줄 발행 요청 스키마 (배열 지원)"""
    queues: list[QueueItem]  # 배열로 받음

    # 공통 스케줄 설정
    start_date: str  # "2025-01-01" 형식
    start_hour: int = 10  # 시작 시간 (0-23)
    posts_per_day: int = 3  # 하루 발행 수
    interval_hours: int = 2  # 발행 간격 (시간)

    # 공통 생성 옵션
    service: str = "default"
    ref: str = ""
    generate_images: bool = True
    image_count: int = 5

    # 실행 옵션
    delay_between_posts: int = 10  # 발행 간 딜레이 (초)
    delay_between_queues: int = 60  # 큐 간 딜레이 (초)

    @field_validator("queues")
    @classmethod
    def validate_queues(cls, v):
        if len(v) < 1:
            raise ValueError("queues는 최소 1개 이상이어야 합니다.")
        return v

    @field_validator("start_hour")
    @classmethod
    def validate_start_hour(cls, v):
        if not 0 <= v <= 23:
            raise ValueError("시작 시간은 0-23 사이여야 합니다.")
        return v

    @field_validator("posts_per_day")
    @classmethod
    def validate_posts_per_day(cls, v):
        if not 1 <= v <= 10:
            raise ValueError("하루 발행 수는 1-10 사이여야 합니다.")
        return v

    @field_validator("interval_hours")
    @classmethod
    def validate_interval_hours(cls, v):
        if not 1 <= v <= 12:
            raise ValueError("발행 간격은 1-12시간 사이여야 합니다.")
        return v


# ========== 스케줄 계산 ==========

def calculate_schedule(
    start_date: str,
    start_hour: int,
    keywords: list[str],
    posts_per_day: int = 3,
    interval_hours: int = 2,
) -> list[dict]:
    """발행 스케줄 계산 (키워드 개수에 따라 일수 자동 계산)"""
    base_date = datetime.strptime(start_date, "%Y-%m-%d")
    base_time = base_date.replace(hour=start_hour, minute=0, second=0, microsecond=0)

    total_days = (len(keywords) + posts_per_day - 1) // posts_per_day
    schedule = []
    keyword_idx = 0

    for day in range(total_days):
        day_base = base_time + timedelta(days=day)

        for slot in range(posts_per_day):
            if keyword_idx >= len(keywords):
                break

            schedule_time = day_base + timedelta(hours=slot * interval_hours)

            schedule.append({
                "keyword": keywords[keyword_idx],
                "schedule_time": schedule_time,
                "day": day + 1,
                "slot": slot + 1,
            })
            keyword_idx += 1

    return schedule


def build_schedule_times(
    generated_ids: list[dict],
    schedule: list[dict],
) -> list[Optional[datetime]]:
    """생성된 원고에 맞는 스케줄 시간 목록 생성"""
    keyword_to_schedule = {item["keyword"]: item for item in schedule}
    schedule_times = []

    for gen in generated_ids:
        keyword = gen.get("keyword")
        if keyword in keyword_to_schedule:
            schedule_times.append(keyword_to_schedule[keyword]["schedule_time"])
        else:
            schedule_times.append(None)

    return schedule_times


# ========== 단일 큐 처리 ==========

async def process_single_queue(
    queue_index: int,
    total_queues: int,
    account: dict,
    keywords: list[str],
    start_date: str,
    start_hour: int,
    posts_per_day: int,
    interval_hours: int,
    service: str,
    ref: str,
    generate_images: bool,
    image_count: int,
    delay_between_posts: int,
) -> dict:
    """단일 큐 처리 (원고 생성 → 로그인 → 발행)"""
    start_ts = datetime.now()
    account_id = account.get("id")
    password = account.get("password")

    result = {
        "queue_index": queue_index,
        "account": f"{account_id[:3]}***" if account_id else "unknown",
        "status": "pending",
        "schedule": {},
        "summary": {
            "keywords": len(keywords),
            "published": 0,
            "failed": 0,
            "elapsed": 0,
        },
        "daily_summary": {},
        "results": [],
        "error": None,
    }

    if not account_id or not password:
        result["status"] = "failed"
        result["error"] = "계정 정보가 필요합니다."
        return result

    log.header(f"큐 {queue_index}/{total_queues}: {account_id[:3]}***", "📦")
    log.kv("키워드", f"{len(keywords)}개")

    try:
        # 1단계: 스케줄 계산
        schedule = calculate_schedule(
            start_date=start_date,
            start_hour=start_hour,
            keywords=keywords,
            posts_per_day=posts_per_day,
            interval_hours=interval_hours,
        )

        total_days = (len(keywords) + posts_per_day - 1) // posts_per_day
        result["schedule"] = {
            "start_date": start_date,
            "start_hour": start_hour,
            "days": total_days,
            "posts_per_day": posts_per_day,
            "interval_hours": interval_hours,
        }

        log.kv("스케줄", f"{total_days}일, {len(schedule)}개")

        # 2단계: 원고 생성
        log.step(1, 4, "원고 생성")
        batch_id, generated_ids = await generate_manuscripts_batch(
            keywords=keywords,
            ref=ref,
            generate_images=generate_images,
            image_count=image_count,
        )

        if not generated_ids:
            result["status"] = "failed"
            result["error"] = "원고 생성에 모두 실패했습니다."
            return result

        log.success("원고 생성 완료", count=len(generated_ids))

        # 3단계: 큐 생성
        log.step(2, 4, "큐 생성")
        queue_id, queue_dir = create_queue(
            manuscript_ids=[item["id"] for item in generated_ids],
            account_id=account_id,
            schedule_date=start_date,
        )

        manuscripts = get_queue_manuscripts(queue_id)
        result["queue_id"] = queue_id
        log.kv("큐 ID", queue_id)

        # 4단계: 로그인
        log.step(3, 4, "네이버 로그인")
        update_queue_status(queue_id, "processing")

        login_result = await naver_login_with_playwright(
            account_id=account_id,
            password=password,
            debug=True,
        )

        if not login_result["success"]:
            update_queue_status(queue_id, "failed")
            result["status"] = "failed"
            result["error"] = f"로그인 실패: {login_result.get('message')}"
            return result

        cookies = login_result["cookies"]
        log.success("로그인 성공", cookies=len(cookies))

        # 5단계: 예약발행
        log.step(4, 4, "예약발행")
        schedule_times = build_schedule_times(generated_ids, schedule)

        publish_results = await publish_manuscripts_batch(
            cookies=cookies,
            queue_dir=queue_dir,
            manuscripts=manuscripts,
            schedule_times=schedule_times,
            account_id=account_id,
            delay=delay_between_posts,
        )

        # 결과에 day/slot 정보 추가
        keyword_to_schedule = {item["keyword"]: item for item in schedule}
        for idx, pub_result in enumerate(publish_results):
            gen = generated_ids[idx] if idx < len(generated_ids) else None
            if gen and gen["keyword"] in keyword_to_schedule:
                sched = keyword_to_schedule[gen["keyword"]]
                pub_result["day"] = sched["day"]
                pub_result["slot"] = sched["slot"]
                pub_result["scheduled_at"] = sched["schedule_time"].isoformat()

        # 결과 집계
        success_count = sum(1 for r in publish_results if r["success"])
        failed_count = len(manuscripts) - success_count
        cleanup_empty_queue(queue_id)

        elapsed = (datetime.now() - start_ts).total_seconds()

        # 일별 요약
        daily_summary = {}
        for r in publish_results:
            day = r.get("day", 0)
            if day not in daily_summary:
                daily_summary[day] = {"success": 0, "failed": 0}
            if r["success"]:
                daily_summary[day]["success"] += 1
            else:
                daily_summary[day]["failed"] += 1

        result["status"] = "completed" if failed_count == 0 else "partial"
        result["summary"] = {
            "keywords": len(keywords),
            "published": success_count,
            "failed": failed_count,
            "elapsed": round(elapsed, 1),
        }
        result["daily_summary"] = daily_summary
        result["results"] = publish_results

        log.success(
            f"큐 {queue_index} 완료",
            성공=f"{success_count}/{len(manuscripts)}",
            시간=f"{elapsed:.0f}s"
        )

    except Exception as e:
        result["status"] = "failed"
        result["error"] = str(e)
        log.error(f"큐 {queue_index} 실패", error=str(e))

    return result


# ========== API 엔드포인트 ==========

@router.post("/auto-schedule")
async def auto_schedule_bot(request: AutoScheduleRequest):
    """자동 스케줄 발행: 원고 자동생성 + 예약발행 (배치 큐 지원)

    - queues 배열로 여러 계정/키워드 세트 수신
    - 순차 실행: 큐1 완료 → 큐2 → 큐3 ...
    - 개별 큐 실패 시 다음 큐로 계속 진행
    """
    total_start = datetime.now()
    total_queues = len(request.queues)

    log.header(f"배치 스케줄 발행 시작 ({total_queues}개 큐)", "🚀")
    log.kv("시작일", request.start_date)
    log.kv("시작시간", f"{request.start_hour}:00")
    log.kv("설정", f"하루 {request.posts_per_day}개 / {request.interval_hours}시간 간격")
    log.divider()

    queue_results = []

    for idx, queue_item in enumerate(request.queues):
        queue_index = idx + 1

        # 개별 오버라이드 적용
        posts_per_day = queue_item.posts_per_day or request.posts_per_day
        interval_hours = queue_item.interval_hours or request.interval_hours
        service = queue_item.service or request.service
        ref = queue_item.ref if queue_item.ref is not None else request.ref

        result = await process_single_queue(
            queue_index=queue_index,
            total_queues=total_queues,
            account=queue_item.account,
            keywords=queue_item.keywords,
            start_date=request.start_date,
            start_hour=request.start_hour,
            posts_per_day=posts_per_day,
            interval_hours=interval_hours,
            service=service,
            ref=ref,
            generate_images=request.generate_images,
            image_count=request.image_count,
            delay_between_posts=request.delay_between_posts,
        )

        queue_results.append(result)

        # 다음 큐 전 대기 (마지막 큐 제외)
        if idx < total_queues - 1:
            log.debug(f"{request.delay_between_queues}초 대기 후 다음 큐 시작...")
            await asyncio.sleep(request.delay_between_queues)

    # 전체 결과 집계
    total_keywords = sum(r["summary"]["keywords"] for r in queue_results)
    total_published = sum(r["summary"]["published"] for r in queue_results)
    total_failed = sum(r["summary"]["failed"] for r in queue_results)
    total_elapsed = (datetime.now() - total_start).total_seconds()

    log.divider()
    log.header("배치 스케줄 발행 완료", "✅")
    log.kv("총 큐", f"{total_queues}개")
    log.kv("총 키워드", f"{total_keywords}개")
    log.kv("성공", f"{total_published}개")
    log.kv("실패", f"{total_failed}개")
    log.kv("소요시간", f"{total_elapsed:.0f}s")

    return JSONResponse(content={
        "success": True,
        "total_queues": total_queues,
        "summary": {
            "total_keywords": total_keywords,
            "total_published": total_published,
            "total_failed": total_failed,
            "elapsed": round(total_elapsed, 1),
        },
        "queue_results": queue_results,
    })

"""자동 스케줄 발행 API - 원고 자동생성 + 예약발행"""

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

class AutoScheduleRequest(BaseModel):
    """자동 스케줄 발행 요청 스키마"""
    account: dict  # {"id": "...", "password": "..."}
    keywords: list[str]  # 1개 이상 (개수에 따라 일수 자동 계산)
    start_date: str  # "2025-01-01" 형식
    start_hour: int = 10  # 시작 시간 (0-23)
    posts_per_day: int = 3  # 하루 발행 수
    interval_hours: int = 2  # 발행 간격 (시간)

    # 선택 옵션
    service: str = "default"
    ref: str = ""
    generate_images: bool = True
    image_count: int = 5
    delay_between_posts: int = 10  # 발행 간 딜레이 (초)

    @field_validator("keywords")
    @classmethod
    def validate_keywords(cls, v):
        if len(v) < 1:
            raise ValueError("키워드는 최소 1개 이상 필요합니다.")
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
    """발행 스케줄 계산 (키워드 개수에 따라 일수 자동 계산)

    Args:
        start_date: 시작 날짜 (YYYY-MM-DD)
        start_hour: 시작 시간 (0-23)
        keywords: 키워드 목록
        posts_per_day: 하루 발행 수
        interval_hours: 발행 간격 (시간)

    Returns:
        [{"keyword": ..., "schedule_time": datetime, "day": 1-7, "slot": 1-3}, ...]
    """
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


# ========== API 엔드포인트 ==========

@router.post("/auto-schedule")
async def auto_schedule_bot(request: AutoScheduleRequest):
    """자동 스케줄 발행: 원고 자동생성 + 예약발행

    - 키워드 개수에 따라 일수 자동 계산
    - 하루 N개 발행 (M시간 간격) - 설정 가능
    - 원고 자동생성 (gemini_new) + 이미지 생성 + 예약발행
    """
    start_ts = datetime.now()
    account_id = request.account.get("id")
    password = request.account.get("password")

    if not account_id or not password:
        raise HTTPException(status_code=400, detail="계정 정보가 필요합니다.")

    log.header("자동 스케줄 발행 시작", "📅")
    log.kv("계정", f"{account_id[:3]}***")
    log.kv("키워드", f"{len(request.keywords)}개")
    log.kv("시작일", request.start_date)
    log.kv("시작시간", f"{request.start_hour}:00")
    log.kv("설정", f"하루 {request.posts_per_day}개 / {request.interval_hours}시간 간격")

    # ========== 1단계: 스케줄 계산 ==========
    log.header("1단계: 스케줄 계산", "🗓️")

    schedule = calculate_schedule(
        start_date=request.start_date,
        start_hour=request.start_hour,
        keywords=request.keywords,
        posts_per_day=request.posts_per_day,
        interval_hours=request.interval_hours,
    )

    # 총 일수 계산
    total_days = (len(request.keywords) + request.posts_per_day - 1) // request.posts_per_day

    log.kv("총 일수", f"{total_days}일")
    log.kv("총 스케줄", f"{len(schedule)}개")
    for item in schedule[:3]:
        log.debug(f"Day {item['day']} Slot {item['slot']}: {item['keyword'][:20]} → {item['schedule_time'].strftime('%m/%d %H:%M')}")
    log.debug("...")

    # ========== 2단계: 원고 생성 (공통 함수 사용) ==========
    log.header("2단계: 원고 생성", "📝")

    generated_ids = await generate_manuscripts_batch(
        keywords=request.keywords,
        ref=request.ref,
        generate_images=request.generate_images,
        image_count=request.image_count,
    )

    if not generated_ids:
        raise HTTPException(status_code=500, detail="원고 생성에 모두 실패했습니다.")

    log.success("원고 생성 완료", count=len(generated_ids))

    # ========== 3단계: 큐 생성 ==========
    log.header("3단계: 큐 생성", "📦")

    queue_id, queue_dir = create_queue(
        manuscript_ids=[item["id"] for item in generated_ids],
        account_id=account_id,
        schedule_date=request.start_date,
    )

    manuscripts = get_queue_manuscripts(queue_id)
    log.kv("큐 ID", queue_id)
    log.kv("원고 수", len(manuscripts))

    # ========== 4단계: 로그인 ==========
    log.header("4단계: 네이버 로그인", "🔐")
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

    # ========== 5단계: 예약발행 (공통 함수 사용) ==========
    log.header("5단계: 스케줄 예약발행", "📤")

    schedule_times = build_schedule_times(generated_ids, schedule)

    publish_results = await publish_manuscripts_batch(
        cookies=cookies,
        queue_dir=queue_dir,
        manuscripts=manuscripts,
        schedule_times=schedule_times,
        account_id=account_id,
        delay=request.delay_between_posts,
    )

    # 결과에 day/slot 정보 추가
    keyword_to_schedule = {item["keyword"]: item for item in schedule}
    for idx, result in enumerate(publish_results):
        gen = generated_ids[idx] if idx < len(generated_ids) else None
        if gen and gen["keyword"] in keyword_to_schedule:
            sched = keyword_to_schedule[gen["keyword"]]
            result["day"] = sched["day"]
            result["slot"] = sched["slot"]
            result["scheduled_at"] = sched["schedule_time"].isoformat()

    # ========== 결과 ==========
    success_count = sum(1 for r in publish_results if r["success"])
    cleanup_empty_queue(queue_id)

    elapsed = (datetime.now() - start_ts).total_seconds()

    log.divider()
    log.success(
        "자동 스케줄 발행 완료",
        queue_id=queue_id,
        성공=f"{success_count}/{len(manuscripts)}",
        시간=f"{elapsed:.0f}s"
    )

    # 일별 요약 생성
    daily_summary = {}
    for r in publish_results:
        day = r.get("day", 0)
        if day not in daily_summary:
            daily_summary[day] = {"success": 0, "failed": 0}
        if r["success"]:
            daily_summary[day]["success"] += 1
        else:
            daily_summary[day]["failed"] += 1

    return JSONResponse(content={
        "success": True,
        "queue_id": queue_id,
        "account": f"{account_id[:3]}***",
        "schedule": {
            "start_date": request.start_date,
            "start_hour": request.start_hour,
            "days": total_days,
            "posts_per_day": request.posts_per_day,
            "interval_hours": request.interval_hours,
        },
        "summary": {
            "generated": len(generated_ids),
            "published": success_count,
            "failed": len(manuscripts) - success_count,
            "elapsed": round(elapsed, 1),
        },
        "daily_summary": daily_summary,
        "results": publish_results,
    })

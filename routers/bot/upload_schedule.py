"""업로드 스케줄 발행 API - ZIP 업로드 + 예약발행"""

import zipfile
from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse

from routers.auth.naver import naver_login_with_playwright
from routers.generate.batch import generate_batch_id
from utils.logger import log

from .common import (
    PENDING_DIR,
    create_queue,
    get_queue_manuscripts,
    update_queue_status,
    cleanup_empty_queue,
    publish_manuscripts_batch,
)
from .auto_schedule import calculate_schedule, build_schedule_times

router = APIRouter()


@router.post("/upload-schedule")
async def upload_schedule_bot(
    file: UploadFile = File(...),
    account_id: str = Form(...),
    password: str = Form(...),
    start_date: str = Form(...),
    start_hour: int = Form(10),
    posts_per_day: int = Form(3),
    interval_hours: int = Form(2),
    delay_between_posts: int = Form(10),
):
    """업로드 스케줄 발행: ZIP 업로드 + 예약발행

    원고를 ZIP으로 업로드하고 스케줄에 맞춰 예약 발행합니다.

    Args:
        file: ZIP 파일 (원고들)
        account_id: 네이버 계정 ID
        password: 네이버 계정 비밀번호
        start_date: 시작 날짜 (YYYY-MM-DD)
        start_hour: 시작 시간 (0-23, 기본: 10)
        posts_per_day: 하루 발행 수 (1-10, 기본: 3)
        interval_hours: 발행 간격 (1-12시간, 기본: 2)
        delay_between_posts: 발행 간 대기 시간 (초, 기본: 10)

    ZIP 구조:
        upload.zip
        ├── 키워드1/
        │   ├── 키워드1.txt (첫 줄=제목, 나머지=본문)
        │   └── 1.png, 2.png ... (이미지)
        └── 키워드2/
            └── ...
    """
    # 유효성 검사
    if not file.filename or not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="ZIP 파일만 업로드 가능합니다.")

    if not 0 <= start_hour <= 23:
        raise HTTPException(status_code=400, detail="시작 시간은 0-23 사이여야 합니다.")

    if not 1 <= posts_per_day <= 10:
        raise HTTPException(status_code=400, detail="하루 발행 수는 1-10 사이여야 합니다.")

    if not 1 <= interval_hours <= 12:
        raise HTTPException(status_code=400, detail="발행 간격은 1-12시간 사이여야 합니다.")

    start_ts = datetime.now()

    log.header("업로드 스케줄 발행 시작", "📦")
    log.kv("계정", f"{account_id[:3]}***")
    log.kv("파일", file.filename)
    log.kv("시작일", start_date)
    log.kv("시작시간", f"{start_hour}:00")
    log.kv("설정", f"하루 {posts_per_day}개 / {interval_hours}시간 간격")

    # ========== 1단계: ZIP 업로드 ==========
    log.header("1단계: ZIP 업로드", "📤")

    batch_id = generate_batch_id()
    log.kv("배치 ID", batch_id)

    # 임시 파일로 저장
    with NamedTemporaryFile(delete=False, suffix=".zip") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = Path(tmp.name)

    uploaded = []
    keywords = []
    upload_idx = 0

    try:
        with zipfile.ZipFile(tmp_path, "r") as zf:
            # ZIP 내 최상위 폴더들 추출
            top_folders = set()
            for name in zf.namelist():
                parts = name.split("/")
                if len(parts) > 1 and parts[0]:
                    top_folders.add(parts[0])

            log.kv("폴더 수", len(top_folders))

            for folder_name in sorted(top_folders):
                # 시스템 폴더 무시
                if folder_name.startswith("__") or folder_name.startswith("."):
                    continue

                upload_idx += 1
                new_folder_name = f"{batch_id}_{str(upload_idx).zfill(4)}"
                dst_dir = PENDING_DIR / new_folder_name
                dst_dir.mkdir(parents=True, exist_ok=True)

                # 해당 폴더 내 파일들 추출
                for name in zf.namelist():
                    if not name.startswith(folder_name + "/"):
                        continue

                    rel_path = name[len(folder_name) + 1:]
                    if not rel_path or rel_path.endswith("/"):
                        continue

                    target_path = dst_dir / rel_path
                    target_path.parent.mkdir(parents=True, exist_ok=True)

                    with zf.open(name) as src:
                        with open(target_path, "wb") as dst:
                            dst.write(src.read())

                uploaded.append({
                    "id": new_folder_name,
                    "keyword": folder_name,
                })
                keywords.append(folder_name)
                log.debug(f"업로드: {folder_name} → {new_folder_name}")

    except zipfile.BadZipFile:
        raise HTTPException(status_code=400, detail="잘못된 ZIP 파일입니다.")
    finally:
        tmp_path.unlink(missing_ok=True)

    if not uploaded:
        raise HTTPException(status_code=400, detail="ZIP 파일에 원고가 없습니다.")

    log.success("업로드 완료", count=len(uploaded))

    # ========== 2단계: 스케줄 계산 ==========
    log.header("2단계: 스케줄 계산", "🗓️")

    schedule = calculate_schedule(
        start_date=start_date,
        start_hour=start_hour,
        keywords=keywords,
        posts_per_day=posts_per_day,
        interval_hours=interval_hours,
    )

    total_days = (len(keywords) + posts_per_day - 1) // posts_per_day

    log.kv("총 일수", f"{total_days}일")
    log.kv("총 스케줄", f"{len(schedule)}개")

    # ========== 3단계: 큐 생성 ==========
    log.header("3단계: 큐 생성", "📦")

    queue_id, queue_dir = create_queue(
        manuscript_ids=[item["id"] for item in uploaded],
        account_id=account_id,
        schedule_date=start_date,
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

    # ========== 5단계: 예약발행 ==========
    log.header("5단계: 스케줄 예약발행", "📤")

    schedule_times = build_schedule_times(uploaded, schedule)

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
    for idx, result in enumerate(publish_results):
        upload_item = uploaded[idx] if idx < len(uploaded) else None
        if upload_item and upload_item["keyword"] in keyword_to_schedule:
            sched = keyword_to_schedule[upload_item["keyword"]]
            result["day"] = sched["day"]
            result["slot"] = sched["slot"]
            result["scheduled_at"] = sched["schedule_time"].isoformat()

    # ========== 결과 ==========
    success_count = sum(1 for r in publish_results if r["success"])
    cleanup_empty_queue(queue_id)

    elapsed = (datetime.now() - start_ts).total_seconds()

    log.divider()
    log.success(
        "업로드 스케줄 발행 완료",
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
        "batch_id": batch_id,
        "account": f"{account_id[:3]}***",
        "schedule": {
            "start_date": start_date,
            "start_hour": start_hour,
            "days": total_days,
            "posts_per_day": posts_per_day,
            "interval_hours": interval_hours,
        },
        "summary": {
            "uploaded": len(uploaded),
            "published": success_count,
            "failed": len(manuscripts) - success_count,
            "elapsed": round(elapsed, 1),
        },
        "daily_summary": daily_summary,
        "results": publish_results,
    })

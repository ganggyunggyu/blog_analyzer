"""블로그 봇 오케스트레이션 API"""

from __future__ import annotations

import json
import shutil
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from routers.auth.naver import naver_login_with_playwright
from routers.auth.blog_write import write_blog_post
from utils.logger import log

router = APIRouter(prefix="/bot", tags=["bot-orchestrator"])

# 원고 저장 경로
MANUSCRIPTS_DIR = Path("manuscripts")
PENDING_DIR = MANUSCRIPTS_DIR / "pending"
COMPLETED_DIR = MANUSCRIPTS_DIR / "completed"
FAILED_DIR = MANUSCRIPTS_DIR / "failed"

for dir_path in [PENDING_DIR, COMPLETED_DIR, FAILED_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}


# ========== 공통 유틸리티 함수 ==========

def parse_manuscript_txt(folder: Path) -> dict | None:
    """폴더 내 .txt 파일 파싱 (첫 줄=제목, 나머지=본문)"""
    txt_files = [f for f in folder.iterdir() if f.is_file() and f.suffix.lower() == ".txt"]
    if not txt_files:
        return None

    txt_path = txt_files[0]
    with open(txt_path, "r", encoding="utf-8") as f:
        lines = f.read().strip().split("\n")

    if not lines:
        return None

    title = lines[0].strip()
    content = "\n".join(lines[1:]).strip() if len(lines) > 1 else ""

    image_files = [f for f in folder.iterdir() if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS]
    images = [str(f) for f in sorted(image_files)]

    return {
        "title": title,
        "content": content,
        "images": images,
        "created_at": datetime.fromtimestamp(txt_path.stat().st_mtime).isoformat(),
    }


def get_manuscript_data(manuscript_dir: Path) -> dict | None:
    """원고 데이터 로드 (txt 또는 json)"""
    data = parse_manuscript_txt(manuscript_dir)
    if data:
        return data

    manifest_path = manuscript_dir / "manuscript.json"
    if manifest_path.exists():
        with open(manifest_path, "r", encoding="utf-8") as f:
            return json.load(f)

    return None


def get_base_time(schedule_date: Optional[str], schedule_start_hour: int) -> datetime:
    """예약 시작 시간 계산"""
    if schedule_date:
        return datetime.strptime(schedule_date, "%Y-%m-%d").replace(
            hour=schedule_start_hour, minute=0, second=0
        )
    return datetime.now()


def calculate_schedule_time(
    base_time: datetime,
    idx: int,
    interval_hours: int,
    interval_minutes: int
) -> datetime:
    """예약 시간 계산"""
    if interval_minutes > 0:
        return base_time + timedelta(minutes=(idx + 1) * interval_minutes)
    return base_time + timedelta(hours=(idx + 1) * interval_hours)


def move_to_completed(manuscript_id: str, manuscript_dir: Path, result: dict, schedule_time: Optional[datetime] = None, account_id: Optional[str] = None):
    """완료 폴더로 이동"""
    completed_dir = COMPLETED_DIR / manuscript_id
    if completed_dir.exists():
        shutil.rmtree(completed_dir)
    shutil.move(str(manuscript_dir), str(completed_dir))

    result_data = {
        "post_url": result.get("post_url"),
        "published_at": datetime.now().isoformat(),
    }
    if schedule_time:
        result_data["scheduled_at"] = schedule_time.isoformat()
    if account_id:
        result_data["account"] = account_id[:3] + "***"

    with open(completed_dir / "result.json", "w", encoding="utf-8") as f:
        json.dump(result_data, f, ensure_ascii=False, indent=2)


def move_to_failed(manuscript_id: str, manuscript_dir: Path, result: dict, account_id: Optional[str] = None):
    """실패 폴더로 이동"""
    failed_dir = FAILED_DIR / manuscript_id
    if failed_dir.exists():
        shutil.rmtree(failed_dir)
    shutil.move(str(manuscript_dir), str(failed_dir))

    error_data = {
        "error": result.get("message"),
        "failed_at": datetime.now().isoformat(),
    }
    if account_id:
        error_data["account"] = account_id[:3] + "***"

    with open(failed_dir / "error.json", "w", encoding="utf-8") as f:
        json.dump(error_data, f, ensure_ascii=False, indent=2)


async def publish_single_manuscript(
    cookies: list,
    manuscript_id: str,
    schedule_time: Optional[datetime] = None,
    account_id: Optional[str] = None
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

    # 로그 출력
    if schedule_time:
        log.info(f"발행: {data['title'][:30]}", id=manuscript_id, schedule=schedule_time.strftime('%m/%d %H:%M'))
    else:
        log.info(f"발행: {data['title'][:30]}", id=manuscript_id)

    # 블로그 글쓰기 실행
    result = await write_blog_post(
        cookies=cookies,
        title=data["title"],
        content=data["content"],
        tags=data.get("tags"),
        images=data.get("images"),
        is_public=True,
        schedule_time=schedule_time.isoformat() if schedule_time else None,
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


# ========== Pydantic 모델 ==========

class ManuscriptData(BaseModel):
    title: str
    content: str
    tags: Optional[list[str]] = None
    category: Optional[str] = None
    images: Optional[list[str]] = None


class PrepareRequest(BaseModel):
    manuscript: ManuscriptData


class PublishRequest(BaseModel):
    cookies: list
    manuscript_id: Optional[str] = None
    count: int = 1
    use_schedule: bool = False
    schedule_date: Optional[str] = None
    schedule_start_hour: int = 10
    schedule_interval_hours: int = 1
    schedule_interval_minutes: int = 0


class StartBotRequest(BaseModel):
    accounts: list[dict]
    posts_per_account: int = 10
    delay_between_posts: int = 60
    use_schedule: bool = True
    schedule_date: Optional[str] = None
    schedule_start_hour: int = 10
    schedule_interval_hours: int = 1
    schedule_interval_minutes: int = 0


class AutoBotRequest(BaseModel):
    """전체 자동화 요청 (생성 → 발행)"""
    account: dict  # {"id": "xxx", "password": "xxx"}
    keywords: list[str]  # 키워드 목록
    service: str = "default"  # 서비스/카테고리
    ref: str = ""  # 참조 원고
    generate_images: bool = True  # 이미지 생성 여부
    image_count: int = 5  # 키워드당 이미지 개수
    use_schedule: bool = True  # 예약발행 사용
    schedule_date: Optional[str] = None  # 예약 날짜 (YYYY-MM-DD)
    schedule_start_hour: int = 10  # 시작 시간
    schedule_interval_hours: int = 1  # 간격 (시간)
    delay_between_posts: int = 60  # 글 사이 대기 (초)


class ManuscriptInfo(BaseModel):
    id: str
    title: str
    category: Optional[str]
    images_count: int
    created_at: str


def get_manuscript_list(status: str = "pending") -> list[ManuscriptInfo]:
    """원고 목록 조회"""
    dir_map = {"pending": PENDING_DIR, "completed": COMPLETED_DIR, "failed": FAILED_DIR}
    target_dir = dir_map.get(status, PENDING_DIR)

    manuscripts = []
    if not target_dir.exists():
        return manuscripts

    for folder in sorted(target_dir.iterdir()):
        if not folder.is_dir():
            continue

        data = parse_manuscript_txt(folder)
        if data:
            manuscripts.append(ManuscriptInfo(
                id=folder.name,
                title=data.get("title", "제목 없음"),
                category=None,
                images_count=len(data.get("images", [])),
                created_at=data.get("created_at", ""),
            ))
        elif (folder / "manuscript.json").exists():
            with open(folder / "manuscript.json", "r", encoding="utf-8") as f:
                json_data = json.load(f)
                images_dir = folder / "images"
                images_count = len(list(images_dir.glob("*"))) if images_dir.exists() else 0
                manuscripts.append(ManuscriptInfo(
                    id=folder.name,
                    title=json_data.get("title", "제목 없음"),
                    category=json_data.get("category"),
                    images_count=images_count,
                    created_at=json_data.get("created_at", ""),
                ))
    return manuscripts


def get_next_manuscript_id() -> str:
    """다음 원고 ID 생성"""
    existing = list(PENDING_DIR.iterdir()) + list(COMPLETED_DIR.iterdir()) + list(FAILED_DIR.iterdir())
    max_id = 0
    for folder in existing:
        if folder.is_dir() and folder.name.isdigit():
            max_id = max(max_id, int(folder.name))
    return str(max_id + 1).zfill(4)


# ========== API 엔드포인트 ==========

@router.post("/prepare")
async def prepare_manuscript(request: PrepareRequest):
    """원고 저장 (수동)"""
    manuscript_id = get_next_manuscript_id()
    manuscript_dir = PENDING_DIR / manuscript_id
    manuscript_dir.mkdir(parents=True, exist_ok=True)

    images_dir = manuscript_dir / "images"
    images_dir.mkdir(exist_ok=True)

    data = {
        "title": request.manuscript.title,
        "content": request.manuscript.content,
        "tags": request.manuscript.tags or [],
        "category": request.manuscript.category,
        "images": request.manuscript.images or [],
        "created_at": datetime.now().isoformat(),
    }

    with open(manuscript_dir / "manuscript.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    log.success("원고 저장 완료", id=manuscript_id, title=request.manuscript.title[:30])

    return JSONResponse(content={
        "success": True,
        "manuscript_id": manuscript_id,
        "message": "원고가 저장되었습니다.",
        "images_dir": str(images_dir),
    })


@router.get("/queue")
async def get_queue(status: str = "pending"):
    """대기 중인 원고 목록"""
    manuscripts = get_manuscript_list(status)
    return JSONResponse(content={
        "status": status,
        "count": len(manuscripts),
        "manuscripts": [m.model_dump() for m in manuscripts],
    })


@router.get("/manuscript/{manuscript_id}")
async def get_manuscript(manuscript_id: str):
    """특정 원고 상세 조회"""
    for dir_path in [PENDING_DIR, COMPLETED_DIR, FAILED_DIR]:
        manuscript_dir = dir_path / manuscript_id
        if manuscript_dir.exists():
            data = get_manuscript_data(manuscript_dir)
            if data:
                return JSONResponse(content={
                    "id": manuscript_id,
                    "status": dir_path.name,
                    "data": data,
                    "images": data.get("images", []),
                })

    raise HTTPException(status_code=404, detail="원고를 찾을 수 없습니다.")


@router.post("/publish")
async def publish_manuscripts(request: PublishRequest):
    """원고 발행"""
    manuscripts = get_manuscript_list("pending")

    if not manuscripts:
        raise HTTPException(status_code=404, detail="발행할 원고가 없습니다.")

    # 대상 원고 선택
    if request.manuscript_id:
        target_ids = [request.manuscript_id]
    else:
        target_ids = [m.id for m in manuscripts[:request.count]]

    # 예약 시간 계산
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

        # 1. 로그인
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

        # 2. 원고 발행
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

            # 글 사이 대기
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


@router.delete("/manuscript/{manuscript_id}")
async def delete_manuscript(manuscript_id: str):
    """원고 삭제"""
    for dir_path in [PENDING_DIR, COMPLETED_DIR, FAILED_DIR]:
        manuscript_dir = dir_path / manuscript_id
        if manuscript_dir.exists():
            shutil.rmtree(manuscript_dir)
            return JSONResponse(content={
                "success": True,
                "message": f"원고 {manuscript_id} 삭제 완료",
            })

    raise HTTPException(status_code=404, detail="원고를 찾을 수 없습니다.")


@router.post("/retry/{manuscript_id}")
async def retry_manuscript(manuscript_id: str):
    """실패한 원고 재시도 (pending으로 이동)"""
    failed_dir = FAILED_DIR / manuscript_id
    if not failed_dir.exists():
        raise HTTPException(status_code=404, detail="실패한 원고를 찾을 수 없습니다.")

    error_file = failed_dir / "error.json"
    if error_file.exists():
        error_file.unlink()

    pending_dir = PENDING_DIR / manuscript_id
    shutil.move(str(failed_dir), str(pending_dir))

    return JSONResponse(content={
        "success": True,
        "message": f"원고 {manuscript_id}를 재시도 대기열로 이동했습니다.",
    })


@router.get("/health")
async def health():
    """헬스 체크"""
    return {
        "status": "ok",
        "service": "bot-orchestrator",
        "queue": {
            "pending": len(get_manuscript_list("pending")),
            "completed": len(get_manuscript_list("completed")),
            "failed": len(get_manuscript_list("failed")),
        }
    }


@router.post("/auto")
async def auto_bot(request: AutoBotRequest):
    """
    전체 자동화: 원고+이미지 생성 → 로그인 → 발행

    1. 키워드별로 원고 + 이미지 생성
    2. pending 폴더에 저장
    3. 네이버 로그인
    4. 예약발행
    """
    from routers.generate.batch import generate_images_parallel, save_to_pending
    from llm.gpt4o_service import gpt4o_gen
    from utils.get_category_db_name import get_category_db_name
    from fastapi.concurrency import run_in_threadpool

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
            # 카테고리 분류
            category = await get_category_db_name(keyword=keyword + request.ref)

            # 원고 생성
            content = await run_in_threadpool(
                gpt4o_gen,
                user_instructions=keyword,
                ref=request.ref,
                category=category
            )

            if not content:
                log.error(f"원고 생성 실패", keyword=keyword[:20])
                continue

            # 이미지 생성
            image_urls = []
            if request.generate_images:
                images = await run_in_threadpool(
                    generate_images_parallel,
                    keyword,
                    request.image_count
                )
                image_urls = [img["url"] for img in images if img.get("url")]

            # pending에 저장
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
                base_time, idx,
                request.schedule_interval_hours, 0
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

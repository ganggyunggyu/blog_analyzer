"""블로그 봇 오케스트레이션 API"""

from __future__ import annotations

import os
import json
import shutil
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from routers.auth.naver import naver_login_with_playwright, sessions, SessionData
from routers.auth.blog_write import write_blog_post
from utils.logger import log

router = APIRouter(prefix="/bot", tags=["bot-orchestrator"])

# 원고 저장 경로
MANUSCRIPTS_DIR = Path("manuscripts")
PENDING_DIR = MANUSCRIPTS_DIR / "pending"
COMPLETED_DIR = MANUSCRIPTS_DIR / "completed"
FAILED_DIR = MANUSCRIPTS_DIR / "failed"

# 디렉토리 생성
for dir_path in [PENDING_DIR, COMPLETED_DIR, FAILED_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# 이미지 확장자
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}


def parse_manuscript_txt(folder: Path) -> dict | None:
    """원고.txt 파싱 (첫 줄=제목, 나머지=본문)"""
    txt_path = folder / "원고.txt"
    if not txt_path.exists():
        return None

    with open(txt_path, "r", encoding="utf-8") as f:
        lines = f.read().strip().split("\n")

    if not lines:
        return None

    title = lines[0].strip()
    content = "\n".join(lines[1:]).strip() if len(lines) > 1 else ""

    # 이미지 파일 찾기 (전체 경로로 저장, 정렬)
    image_files = [
        f for f in folder.iterdir()
        if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS
    ]
    # 파일명으로 정렬 (012_xxx.jpg, 013_xxx.jpg 순서대로)
    images = [str(f) for f in sorted(image_files, key=lambda x: x.name)]

    return {
        "title": title,
        "content": content,
        "images": images,  # 전체 경로 리스트
        "created_at": datetime.fromtimestamp(txt_path.stat().st_mtime).isoformat(),
    }


class ManuscriptData(BaseModel):
    """원고 데이터"""
    title: str
    content: str
    tags: Optional[list[str]] = None
    category: Optional[str] = None
    images: Optional[list[str]] = None  # 이미지 파일명 리스트


class PrepareRequest(BaseModel):
    """원고 준비 요청 (수동 저장)"""
    manuscript: ManuscriptData


class PublishRequest(BaseModel):
    """발행 요청"""
    cookies: list  # 로그인 쿠키
    manuscript_id: Optional[str] = None  # 특정 원고 ID (없으면 순차 발행)
    count: int = 1  # 발행할 원고 수
    use_schedule: bool = False  # 예약발행 사용 여부
    schedule_interval_hours: int = 1  # 예약 간격 (시간) - 1번 +1시간, 2번 +2시간...
    schedule_interval_minutes: int = 0  # 예약 간격 (분) - 테스트용 (예: 10분 후)


class StartBotRequest(BaseModel):
    """전체 봇 실행 요청"""
    accounts: list[dict]  # [{"id": "xxx", "password": "xxx"}, ...]
    posts_per_account: int = 10  # 계정당 글 수
    delay_between_posts: int = 60  # 글 사이 대기 시간 (초)
    use_schedule: bool = True  # 예약발행 사용 여부 (기본: 사용)
    schedule_interval_hours: int = 1  # 예약 간격 (시간)
    schedule_interval_minutes: int = 0  # 예약 간격 (분) - 테스트용


class ManuscriptInfo(BaseModel):
    """원고 정보"""
    id: str
    title: str
    category: Optional[str]
    images_count: int
    created_at: str


def get_manuscript_list(status: str = "pending") -> list[ManuscriptInfo]:
    """원고 목록 조회 (원고.txt 형식 지원)"""
    if status == "pending":
        target_dir = PENDING_DIR
    elif status == "completed":
        target_dir = COMPLETED_DIR
    elif status == "failed":
        target_dir = FAILED_DIR
    else:
        target_dir = PENDING_DIR

    manuscripts = []
    if not target_dir.exists():
        return manuscripts

    for folder in sorted(target_dir.iterdir()):
        if folder.is_dir():
            # 원고.txt 형식 우선
            data = parse_manuscript_txt(folder)
            if data:
                manuscripts.append(ManuscriptInfo(
                    id=folder.name,
                    title=data.get("title", "제목 없음"),
                    category=None,
                    images_count=len(data.get("images", [])),
                    created_at=data.get("created_at", ""),
                ))
            # 기존 JSON 형식도 지원
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


@router.post("/prepare")
async def prepare_manuscript(request: PrepareRequest):
    """원고 저장 (수동)"""

    manuscript_id = get_next_manuscript_id()
    manuscript_dir = PENDING_DIR / manuscript_id
    manuscript_dir.mkdir(parents=True, exist_ok=True)

    # 이미지 폴더 생성
    images_dir = manuscript_dir / "images"
    images_dir.mkdir(exist_ok=True)

    # 원고 데이터 저장
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
        "images_dir": str(images_dir),  # 이미지 업로드할 경로
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

    # pending, completed, failed 순서로 검색
    for dir_path in [PENDING_DIR, COMPLETED_DIR, FAILED_DIR]:
        manuscript_dir = dir_path / manuscript_id
        if manuscript_dir.exists():
            # 원고.txt 형식 우선
            data = parse_manuscript_txt(manuscript_dir)
            if data:
                return JSONResponse(content={
                    "id": manuscript_id,
                    "status": dir_path.name,
                    "data": data,
                    "images": data.get("images", []),
                })

            # 기존 JSON 형식
            manifest_path = manuscript_dir / "manuscript.json"
            if manifest_path.exists():
                with open(manifest_path, "r", encoding="utf-8") as f:
                    json_data = json.load(f)

                images_dir = manuscript_dir / "images"
                images = list(images_dir.glob("*")) if images_dir.exists() else []

                return JSONResponse(content={
                    "id": manuscript_id,
                    "status": dir_path.name,
                    "data": json_data,
                    "images": [img.name for img in images],
                })

    raise HTTPException(status_code=404, detail="원고를 찾을 수 없습니다.")


@router.post("/publish")
async def publish_manuscripts(request: PublishRequest):
    """원고 발행"""

    results = []
    manuscripts = get_manuscript_list("pending")

    if not manuscripts:
        raise HTTPException(status_code=404, detail="발행할 원고가 없습니다.")

    # 특정 원고 또는 순차 발행
    if request.manuscript_id:
        target_ids = [request.manuscript_id]
    else:
        target_ids = [m.id for m in manuscripts[:request.count]]

    # 예약발행 시작 시간 계산
    base_time = datetime.now()

    for idx, manuscript_id in enumerate(target_ids):
        manuscript_dir = PENDING_DIR / manuscript_id

        # 원고.txt 또는 manuscript.json 파싱
        data = parse_manuscript_txt(manuscript_dir)
        if not data:
            manifest_path = manuscript_dir / "manuscript.json"
            if manifest_path.exists():
                with open(manifest_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

        if not data:
            results.append({
                "manuscript_id": manuscript_id,
                "success": False,
                "message": "원고를 찾을 수 없습니다.",
            })
            continue

        schedule_time = None
        if request.use_schedule:
            if request.schedule_interval_minutes > 0:
                schedule_time = base_time + timedelta(minutes=(idx + 1) * request.schedule_interval_minutes)
            else:
                schedule_time = base_time + timedelta(hours=(idx + 1) * request.schedule_interval_hours)
            log.info(f"발행 시작: {data['title'][:30]}", id=manuscript_id, schedule=schedule_time.strftime('%H:%M'))
        else:
            log.info(f"발행 시작: {data['title'][:30]}", id=manuscript_id)

        # 블로그 글쓰기 실행 (이미지 포함)
        result = await write_blog_post(
            cookies=request.cookies,
            title=data["title"],
            content=data["content"],
            tags=data.get("tags"),
            images=data.get("images"),  # 이미지 경로 리스트
            is_public=True,
            schedule_time=schedule_time.isoformat() if schedule_time else None,
            debug=True,
        )

        if result["success"]:
            # 완료 폴더로 이동
            completed_dir = COMPLETED_DIR / manuscript_id
            shutil.move(str(manuscript_dir), str(completed_dir))

            # 발행 결과 저장
            result_data = {
                "post_url": result.get("post_url"),
                "published_at": datetime.now().isoformat(),
            }
            if schedule_time:
                result_data["scheduled_at"] = schedule_time.isoformat()
            with open(completed_dir / "result.json", "w", encoding="utf-8") as f:
                json.dump(result_data, f, ensure_ascii=False, indent=2)

            log.success("발행 성공", id=manuscript_id)
        else:
            failed_dir = FAILED_DIR / manuscript_id
            if failed_dir.exists():
                shutil.rmtree(failed_dir)
            shutil.move(str(manuscript_dir), str(failed_dir))

            with open(failed_dir / "error.json", "w", encoding="utf-8") as f:
                json.dump({
                    "error": result.get("message"),
                    "failed_at": datetime.now().isoformat(),
                }, f, ensure_ascii=False, indent=2)

            log.error("발행 실패", id=manuscript_id, message=result.get("message"))

        results.append({
            "manuscript_id": manuscript_id,
            "success": result["success"],
            "post_url": result.get("post_url"),
            "message": result.get("message"),
        })

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
        posts_results = []
        manuscripts = get_manuscript_list("pending")
        base_time = datetime.now()

        for i, manuscript in enumerate(manuscripts[:request.posts_per_account]):
            manuscript_dir = PENDING_DIR / manuscript.id

            # 원고.txt 또는 manuscript.json 파싱
            data = parse_manuscript_txt(manuscript_dir)
            if not data:
                manifest_path = manuscript_dir / "manuscript.json"
                if manifest_path.exists():
                    with open(manifest_path, "r", encoding="utf-8") as f:
                        data = json.load(f)

            if not data:
                continue

            schedule_time = None
            if request.use_schedule:
                if request.schedule_interval_minutes > 0:
                    schedule_time = base_time + timedelta(minutes=(i + 1) * request.schedule_interval_minutes)
                else:
                    schedule_time = base_time + timedelta(hours=(i + 1) * request.schedule_interval_hours)
                log.step(i + 1, request.posts_per_account, f"{data['title'][:25]} (예약: {schedule_time.strftime('%H:%M')})")
            else:
                log.step(i + 1, request.posts_per_account, f"{data['title'][:30]} (즉시발행)")

            result = await write_blog_post(
                cookies=cookies,
                title=data["title"],
                content=data["content"],
                tags=data.get("tags"),
                images=data.get("images"),  # 이미지 경로 리스트
                is_public=True,
                schedule_time=schedule_time.isoformat() if schedule_time else None,
                debug=True,
            )

            if result["success"]:
                # 완료 폴더로 이동
                completed_dir = COMPLETED_DIR / manuscript.id
                shutil.move(str(manuscript_dir), str(completed_dir))

                result_data = {
                    "account": account_id[:3] + "***",
                    "post_url": result.get("post_url"),
                    "published_at": datetime.now().isoformat(),
                }
                if schedule_time:
                    result_data["scheduled_at"] = schedule_time.isoformat()
                with open(completed_dir / "result.json", "w", encoding="utf-8") as f:
                    json.dump(result_data, f, ensure_ascii=False, indent=2)
            else:
                # 실패 폴더로 이동 (기존 폴더 있으면 삭제)
                failed_dir = FAILED_DIR / manuscript.id
                if failed_dir.exists():
                    shutil.rmtree(failed_dir)
                shutil.move(str(manuscript_dir), str(failed_dir))

                with open(failed_dir / "error.json", "w", encoding="utf-8") as f:
                    json.dump({
                        "account": account_id[:3] + "***",
                        "error": result.get("message"),
                        "failed_at": datetime.now().isoformat(),
                    }, f, ensure_ascii=False, indent=2)

            posts_results.append({
                "manuscript_id": manuscript.id,
                "title": data["title"][:50],
                "success": result["success"],
                "post_url": result.get("post_url"),
                "message": result.get("message"),
            })

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

    # error.json 삭제
    error_file = failed_dir / "error.json"
    if error_file.exists():
        error_file.unlink()

    # pending으로 이동
    pending_dir = PENDING_DIR / manuscript_id
    shutil.move(str(failed_dir), str(pending_dir))

    return JSONResponse(content={
        "success": True,
        "message": f"원고 {manuscript_id}를 재시도 대기열로 이동했습니다.",
    })


@router.get("/health")
async def health():
    """헬스 체크"""
    pending = len(get_manuscript_list("pending"))
    completed = len(get_manuscript_list("completed"))
    failed = len(get_manuscript_list("failed"))

    return {
        "status": "ok",
        "service": "bot-orchestrator",
        "queue": {
            "pending": pending,
            "completed": completed,
            "failed": failed,
        }
    }

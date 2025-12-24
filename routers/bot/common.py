"""봇 공통 함수/모델"""

from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

from pydantic import BaseModel

from routers.auth.blog_write import write_blog_post
from utils.logger import log


# 원고 저장 경로
MANUSCRIPTS_DIR = Path("manuscripts")
PENDING_DIR = MANUSCRIPTS_DIR / "pending"
COMPLETED_DIR = MANUSCRIPTS_DIR / "completed"
FAILED_DIR = MANUSCRIPTS_DIR / "failed"

for dir_path in [PENDING_DIR, COMPLETED_DIR, FAILED_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}


# ========== 유틸리티 함수 ==========

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

    if schedule_time:
        log.info(f"발행: {data['title'][:30]}", id=manuscript_id, schedule=schedule_time.strftime('%m/%d %H:%M'))
    else:
        log.info(f"발행: {data['title'][:30]}", id=manuscript_id)

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


# ========== 큐 관리 함수 ==========

class QueueInfo(BaseModel):
    """큐 정보"""
    queue_id: str
    created_at: str
    manuscript_count: int
    status: str  # pending, processing, completed, failed
    account_id: Optional[str] = None
    schedule_date: Optional[str] = None


def generate_queue_id() -> str:
    """유니크한 큐 ID 생성 (uuid_날짜)"""
    short_uuid = uuid.uuid4().hex[:8]
    date_str = datetime.now().strftime("%m%d")
    return f"queue_{short_uuid}_{date_str}"


def create_queue(
    manuscript_ids: list[str],
    account_id: Optional[str] = None,
    schedule_date: Optional[str] = None,
) -> tuple[str, Path]:
    """새 큐 생성 및 원고 이동

    Args:
        manuscript_ids: pending에서 가져올 원고 ID 목록
        account_id: 계정 ID (선택)
        schedule_date: 예약 날짜 (선택)

    Returns:
        (queue_id, queue_dir)
    """
    queue_id = generate_queue_id()
    queue_dir = MANUSCRIPTS_DIR / queue_id
    queue_dir.mkdir(parents=True, exist_ok=True)

    # 메타데이터 저장
    meta = {
        "queue_id": queue_id,
        "created_at": datetime.now().isoformat(),
        "status": "pending",
        "manuscripts": [],
    }
    if account_id:
        meta["account_id"] = account_id[:3] + "***"
    if schedule_date:
        meta["schedule_date"] = schedule_date

    # 원고들을 큐로 이동 (번호 prefix 붙여서)
    for idx, manuscript_id in enumerate(manuscript_ids):
        src_dir = PENDING_DIR / manuscript_id
        if not src_dir.exists():
            log.warning(f"원고 없음: {manuscript_id}")
            continue

        new_id = f"{str(idx + 1).zfill(3)}_{manuscript_id}"
        dst_dir = queue_dir / new_id
        shutil.move(str(src_dir), str(dst_dir))
        meta["manuscripts"].append(new_id)
        log.debug(f"원고 이동: {manuscript_id} → {new_id}")

    # 메타 파일 저장
    with open(queue_dir / "queue.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    log.success(f"큐 생성 완료", queue_id=queue_id, count=len(meta["manuscripts"]))
    return queue_id, queue_dir


def get_queue_dir(queue_id: str) -> Optional[Path]:
    """큐 디렉토리 반환"""
    queue_dir = MANUSCRIPTS_DIR / queue_id
    if queue_dir.exists() and queue_dir.is_dir():
        return queue_dir
    return None


def get_queue_meta(queue_id: str) -> Optional[dict]:
    """큐 메타데이터 로드"""
    queue_dir = get_queue_dir(queue_id)
    if not queue_dir:
        return None

    meta_path = queue_dir / "queue.json"
    if meta_path.exists():
        with open(meta_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def update_queue_status(queue_id: str, status: str):
    """큐 상태 업데이트"""
    queue_dir = get_queue_dir(queue_id)
    if not queue_dir:
        return

    meta_path = queue_dir / "queue.json"
    if meta_path.exists():
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
        meta["status"] = status
        meta["updated_at"] = datetime.now().isoformat()
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)


def get_queue_manuscripts(queue_id: str) -> list[ManuscriptInfo]:
    """큐 내 원고 목록"""
    queue_dir = get_queue_dir(queue_id)
    if not queue_dir:
        return []

    manuscripts = []
    for folder in sorted(queue_dir.iterdir()):
        if not folder.is_dir() or folder.name.startswith("."):
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
    return manuscripts


def list_active_queues() -> list[QueueInfo]:
    """진행중인 큐 목록 (queue_로 시작하는 폴더)"""
    queues = []
    for folder in sorted(MANUSCRIPTS_DIR.iterdir()):
        if not folder.is_dir() or not folder.name.startswith("queue_"):
            continue

        meta = get_queue_meta(folder.name)
        if meta:
            manuscripts = [f for f in folder.iterdir() if f.is_dir() and not f.name.startswith(".")]
            queues.append(QueueInfo(
                queue_id=folder.name,
                created_at=meta.get("created_at", ""),
                manuscript_count=len(manuscripts),
                status=meta.get("status", "unknown"),
                account_id=meta.get("account_id"),
                schedule_date=meta.get("schedule_date"),
            ))
    return queues


def move_queue_manuscript_to_completed(queue_dir: Path, manuscript_id: str, result: dict, schedule_time: Optional[datetime] = None, account_id: Optional[str] = None):
    """큐 내 원고를 완료 폴더로 이동"""
    manuscript_dir = queue_dir / manuscript_id
    if not manuscript_dir.exists():
        return

    queue_id = queue_dir.name
    new_folder_name = f"{queue_id}_{manuscript_id}"
    completed_dir = COMPLETED_DIR / new_folder_name
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


def move_queue_manuscript_to_failed(queue_dir: Path, manuscript_id: str, result: dict, account_id: Optional[str] = None):
    """큐 내 원고를 실패 폴더로 이동"""
    manuscript_dir = queue_dir / manuscript_id
    if not manuscript_dir.exists():
        return

    queue_id = queue_dir.name
    new_folder_name = f"{queue_id}_{manuscript_id}"
    failed_dir = FAILED_DIR / new_folder_name
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

    if schedule_time:
        log.info(f"발행: {data['title'][:30]}", id=manuscript_id, schedule=schedule_time.strftime('%m/%d %H:%M'))
    else:
        log.info(f"발행: {data['title'][:30]}", id=manuscript_id)

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
        move_queue_manuscript_to_completed(queue_dir, manuscript_id, result, schedule_time, account_id)
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


def cleanup_empty_queue(queue_id: str):
    """빈 큐 폴더 정리"""
    queue_dir = get_queue_dir(queue_id)
    if not queue_dir:
        return

    # 남은 원고 폴더 확인
    remaining = [f for f in queue_dir.iterdir() if f.is_dir() and not f.name.startswith(".")]
    if not remaining:
        # queue.json만 남았으면 삭제
        shutil.rmtree(queue_dir)
        log.info(f"빈 큐 삭제: {queue_id}")

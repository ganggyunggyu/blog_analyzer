"""봇 공용 저장소/파일 시스템 유틸"""

from __future__ import annotations

import json
import shutil
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from utils.logger import log

from .common_models import ManuscriptInfo, QueueInfo


MANUSCRIPTS_DIR = Path("manuscripts")
PENDING_DIR = MANUSCRIPTS_DIR / "pending"
COMPLETED_DIR = MANUSCRIPTS_DIR / "completed"
FAILED_DIR = MANUSCRIPTS_DIR / "failed"

for dir_path in [PENDING_DIR, COMPLETED_DIR, FAILED_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}


def _read_json(path: Path) -> dict | None:
    if not path.exists():
        return None

    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def _write_json(path: Path, data: dict) -> None:
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def _mask_account_id(account_id: Optional[str]) -> Optional[str]:
    if not account_id:
        return None
    return account_id[:3] + "***"


def parse_manuscript_txt(folder: Path) -> dict | None:
    """폴더 내 .txt 파일 파싱 (첫 줄=제목, 나머지=본문)"""
    txt_files = [
        file for file in folder.iterdir() if file.is_file() and file.suffix.lower() == ".txt"
    ]
    if not txt_files:
        return None

    txt_path = txt_files[0]
    with open(txt_path, "r", encoding="utf-8") as file:
        lines = file.read().strip().split("\n")
    if not lines:
        return None

    image_files = [
        file
        for file in folder.iterdir()
        if file.is_file() and file.suffix.lower() in IMAGE_EXTENSIONS
    ]
    return {
        "title": lines[0].strip(),
        "content": "\n".join(lines[1:]).strip() if len(lines) > 1 else "",
        "images": [str(file) for file in sorted(image_files)],
        "created_at": datetime.fromtimestamp(txt_path.stat().st_mtime).isoformat(),
    }


def get_manuscript_data(manuscript_dir: Path) -> dict | None:
    """원고 데이터 로드 (txt 또는 json)"""
    data = parse_manuscript_txt(manuscript_dir)
    if data:
        return data
    return _read_json(manuscript_dir / "manuscript.json")


def get_base_time(schedule_date: Optional[str], schedule_start_hour: int) -> datetime:
    """예약 시작 시간 계산"""
    if schedule_date:
        return datetime.strptime(schedule_date, "%Y-%m-%d").replace(
            hour=schedule_start_hour,
            minute=0,
            second=0,
        )
    return datetime.now()


def should_publish_immediately(schedule_time: Optional[datetime]) -> bool:
    """예약 시간이 이미 지났는지 확인"""
    if not schedule_time:
        return True
    return schedule_time <= datetime.now()


def calculate_schedule_time(
    base_time: datetime,
    index: int,
    interval_hours: int,
    interval_minutes: int,
) -> datetime:
    """예약 시간 계산"""
    if interval_minutes > 0:
        return base_time + timedelta(minutes=(index + 1) * interval_minutes)
    return base_time + timedelta(hours=(index + 1) * interval_hours)


def move_to_completed(
    manuscript_id: str,
    manuscript_dir: Path,
    result: dict,
    schedule_time: Optional[datetime] = None,
    account_id: Optional[str] = None,
) -> None:
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
    masked_account_id = _mask_account_id(account_id)
    if masked_account_id:
        result_data["account"] = masked_account_id

    _write_json(completed_dir / "result.json", result_data)


def move_to_failed(
    manuscript_id: str,
    manuscript_dir: Path,
    result: dict,
    account_id: Optional[str] = None,
) -> None:
    """실패 폴더로 이동"""
    failed_dir = FAILED_DIR / manuscript_id
    if failed_dir.exists():
        shutil.rmtree(failed_dir)
    shutil.move(str(manuscript_dir), str(failed_dir))

    error_data = {
        "error": result.get("message"),
        "failed_at": datetime.now().isoformat(),
    }
    masked_account_id = _mask_account_id(account_id)
    if masked_account_id:
        error_data["account"] = masked_account_id

    _write_json(failed_dir / "error.json", error_data)


def _build_manuscript_info(folder: Path, data: dict) -> ManuscriptInfo:
    return ManuscriptInfo(
        id=folder.name,
        title=data.get("title", "제목 없음"),
        category=data.get("category"),
        images_count=len(data.get("images", [])),
        created_at=data.get("created_at", ""),
    )


def get_manuscript_list(status: str = "pending") -> list[ManuscriptInfo]:
    """원고 목록 조회"""
    dir_map = {"pending": PENDING_DIR, "completed": COMPLETED_DIR, "failed": FAILED_DIR}
    target_dir = dir_map.get(status, PENDING_DIR)
    if not target_dir.exists():
        return []

    manuscripts: list[ManuscriptInfo] = []
    for folder in sorted(target_dir.iterdir()):
        if not folder.is_dir():
            continue

        text_data = parse_manuscript_txt(folder)
        if text_data:
            manuscripts.append(_build_manuscript_info(folder, text_data))
            continue

        json_data = _read_json(folder / "manuscript.json")
        if not json_data:
            continue

        images_dir = folder / "images"
        json_data["images"] = list(images_dir.glob("*")) if images_dir.exists() else []
        manuscripts.append(_build_manuscript_info(folder, json_data))

    return manuscripts


def get_next_manuscript_id() -> str:
    """다음 원고 ID 생성"""
    existing = list(PENDING_DIR.iterdir()) + list(COMPLETED_DIR.iterdir()) + list(FAILED_DIR.iterdir())
    max_id = 0
    for folder in existing:
        if folder.is_dir() and folder.name.isdigit():
            max_id = max(max_id, int(folder.name))
    return str(max_id + 1).zfill(4)


def generate_queue_id() -> str:
    """유니크한 큐 ID 생성 (uuid_날짜)"""
    return f"queue_{uuid.uuid4().hex[:8]}_{datetime.now().strftime('%m%d')}"


def create_queue(
    manuscript_ids: list[str],
    account_id: Optional[str] = None,
    schedule_date: Optional[str] = None,
) -> tuple[str, Path]:
    """새 큐 생성 및 원고 이동"""
    queue_id = generate_queue_id()
    queue_dir = MANUSCRIPTS_DIR / queue_id
    queue_dir.mkdir(parents=True, exist_ok=True)

    meta = {
        "queue_id": queue_id,
        "created_at": datetime.now().isoformat(),
        "status": "pending",
        "manuscripts": [],
    }
    masked_account_id = _mask_account_id(account_id)
    if masked_account_id:
        meta["account_id"] = masked_account_id
    if schedule_date:
        meta["schedule_date"] = schedule_date

    for index, manuscript_id in enumerate(manuscript_ids):
        source_dir = PENDING_DIR / manuscript_id
        if not source_dir.exists():
            log.warning(f"원고 없음: {manuscript_id}")
            continue

        new_id = f"{str(index + 1).zfill(3)}_{manuscript_id}"
        destination_dir = queue_dir / new_id
        shutil.move(str(source_dir), str(destination_dir))
        meta["manuscripts"].append(new_id)
        log.debug(f"원고 이동: {manuscript_id} → {new_id}")

    _write_json(queue_dir / "queue.json", meta)
    log.success("큐 생성 완료", queue_id=queue_id, count=len(meta["manuscripts"]))
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
    return _read_json(queue_dir / "queue.json")


def update_queue_status(queue_id: str, status: str) -> None:
    """큐 상태 업데이트"""
    queue_dir = get_queue_dir(queue_id)
    if not queue_dir:
        return

    meta_path = queue_dir / "queue.json"
    meta = _read_json(meta_path)
    if not meta:
        return

    meta["status"] = status
    meta["updated_at"] = datetime.now().isoformat()
    _write_json(meta_path, meta)


def get_queue_manuscripts(queue_id: str) -> list[ManuscriptInfo]:
    """큐 내 원고 목록"""
    queue_dir = get_queue_dir(queue_id)
    if not queue_dir:
        return []

    manuscripts: list[ManuscriptInfo] = []
    for folder in sorted(queue_dir.iterdir()):
        if not folder.is_dir() or folder.name.startswith("."):
            continue

        data = parse_manuscript_txt(folder)
        if data:
            manuscripts.append(_build_manuscript_info(folder, data))

    return manuscripts


def list_active_queues() -> list[QueueInfo]:
    """진행중인 큐 목록"""
    queues: list[QueueInfo] = []
    for folder in sorted(MANUSCRIPTS_DIR.iterdir()):
        if not folder.is_dir() or not folder.name.startswith("queue_"):
            continue

        meta = get_queue_meta(folder.name)
        if not meta:
            continue

        manuscripts = [
            file for file in folder.iterdir() if file.is_dir() and not file.name.startswith(".")
        ]
        queues.append(
            QueueInfo(
                queue_id=folder.name,
                created_at=meta.get("created_at", ""),
                manuscript_count=len(manuscripts),
                status=meta.get("status", "unknown"),
                account_id=meta.get("account_id"),
                schedule_date=meta.get("schedule_date"),
            )
        )
    return queues


def move_queue_manuscript_to_completed(
    queue_dir: Path,
    manuscript_id: str,
    result: dict,
    schedule_time: Optional[datetime] = None,
    account_id: Optional[str] = None,
) -> None:
    """큐 내 원고를 완료 폴더로 이동"""
    manuscript_dir = queue_dir / manuscript_id
    if not manuscript_dir.exists():
        return

    completed_dir = COMPLETED_DIR / f"{queue_dir.name}_{manuscript_id}"
    if completed_dir.exists():
        shutil.rmtree(completed_dir)
    shutil.move(str(manuscript_dir), str(completed_dir))

    result_data = {
        "post_url": result.get("post_url"),
        "published_at": datetime.now().isoformat(),
    }
    if schedule_time:
        result_data["scheduled_at"] = schedule_time.isoformat()
    masked_account_id = _mask_account_id(account_id)
    if masked_account_id:
        result_data["account"] = masked_account_id

    _write_json(completed_dir / "result.json", result_data)


def move_queue_manuscript_to_failed(
    queue_dir: Path,
    manuscript_id: str,
    result: dict,
    account_id: Optional[str] = None,
) -> None:
    """큐 내 원고를 실패 폴더로 이동"""
    manuscript_dir = queue_dir / manuscript_id
    if not manuscript_dir.exists():
        return

    failed_dir = FAILED_DIR / f"{queue_dir.name}_{manuscript_id}"
    if failed_dir.exists():
        shutil.rmtree(failed_dir)
    shutil.move(str(manuscript_dir), str(failed_dir))

    error_data = {
        "error": result.get("message"),
        "failed_at": datetime.now().isoformat(),
    }
    masked_account_id = _mask_account_id(account_id)
    if masked_account_id:
        error_data["account"] = masked_account_id

    _write_json(failed_dir / "error.json", error_data)


def cleanup_empty_queue(queue_id: str) -> None:
    """빈 큐 폴더 정리"""
    queue_dir = get_queue_dir(queue_id)
    if not queue_dir:
        return

    remaining = [
        file for file in queue_dir.iterdir() if file.is_dir() and not file.name.startswith(".")
    ]
    if not remaining:
        shutil.rmtree(queue_dir)
        log.info(f"빈 큐 삭제: {queue_id}")


__all__ = [
    "COMPLETED_DIR",
    "FAILED_DIR",
    "IMAGE_EXTENSIONS",
    "MANUSCRIPTS_DIR",
    "PENDING_DIR",
    "calculate_schedule_time",
    "cleanup_empty_queue",
    "create_queue",
    "generate_queue_id",
    "get_base_time",
    "get_manuscript_data",
    "get_manuscript_list",
    "get_next_manuscript_id",
    "get_queue_dir",
    "get_queue_manuscripts",
    "get_queue_meta",
    "list_active_queues",
    "move_queue_manuscript_to_completed",
    "move_queue_manuscript_to_failed",
    "move_to_completed",
    "move_to_failed",
    "parse_manuscript_txt",
    "should_publish_immediately",
    "update_queue_status",
]

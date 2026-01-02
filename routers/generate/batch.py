"""배치 원고 생성 API - 키워드 여러개 한번에 처리 (원고 + 이미지)"""

import asyncio
import time
import uuid
import httpx
from datetime import datetime
from pathlib import Path
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from fastapi.concurrency import run_in_threadpool

from schema.generate import BatchGenerateRequest
from llm.gpt4o_service import gpt4o_gen
from llm.image_service import image_gen_single, get_random_poses
from utils.get_category_db_name import get_category_db_name
from utils.logger import log

router = APIRouter()

MANUSCRIPTS_DIR = Path("manuscripts")
PENDING_DIR = MANUSCRIPTS_DIR / "pending"
PENDING_DIR.mkdir(parents=True, exist_ok=True)


def generate_batch_id() -> str:
    """배치(스케줄) 고유 ID 생성"""
    return uuid.uuid4().hex[:8]


def get_next_manuscript_id(batch_id: str = None) -> str:
    """다음 원고 ID 생성

    Args:
        batch_id: 배치 고유 ID (있으면 {batch_id}_{순번} 형식)

    Returns:
        batch_id가 있으면: abc12345_0001
        batch_id가 없으면: 0001 (레거시 호환)
    """
    if batch_id:
        # 해당 배치의 원고만 카운트
        existing = [
            f for f in PENDING_DIR.iterdir()
            if f.is_dir() and f.name.startswith(f"{batch_id}_")
        ] if PENDING_DIR.exists() else []
        next_num = len(existing) + 1
        return f"{batch_id}_{str(next_num).zfill(4)}"
    else:
        # 레거시: 순차 번호
        existing = list(PENDING_DIR.iterdir()) if PENDING_DIR.exists() else []
        max_id = 0
        for folder in existing:
            if folder.is_dir() and folder.name.isdigit():
                max_id = max(max_id, int(folder.name))
        return str(max_id + 1).zfill(4)


def generate_images_parallel(keyword: str, count: int, category: str = "") -> list[dict]:
    """이미지 병렬 생성

    Args:
        keyword: 이미지 주제 키워드
        count: 생성할 이미지 개수
        category: 카테고리 (애견동물_반려동물_분양일 때만 Puppy 가이드라인 추가)
    """
    poses = get_random_poses(count)
    images = []

    with ThreadPoolExecutor(max_workers=count) as executor:
        futures = {
            executor.submit(image_gen_single, keyword, pose, category): pose
            for pose in poses
        }

        for future in as_completed(futures):
            result = future.result()
            if result and result.get("url"):
                images.append(result)

    return images


async def download_image(url: str, save_path: Path) -> bool:
    """URL에서 이미지 다운로드"""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url)
            if response.status_code == 200:
                with open(save_path, "wb") as f:
                    f.write(response.content)
                return True
    except Exception as e:
        log.warning(f"이미지 다운로드 실패", url=url[:50], error=str(e))
    return False


async def save_to_pending(keyword: str, content: str, image_urls: list[str] = None, batch_id: Optional[str] = None) -> str:
    """생성된 원고와 이미지를 pending 폴더에 저장

    Args:
        keyword: 키워드
        content: 원고 내용
        image_urls: 이미지 URL 목록
        batch_id: 배치 고유 ID (있으면 {batch_id}_{순번} 형식으로 저장)
    """
    manuscript_id = get_next_manuscript_id(batch_id)
    manuscript_dir = PENDING_DIR / manuscript_id
    manuscript_dir.mkdir(parents=True, exist_ok=True)

    # txt 파일로 저장
    safe_keyword = "".join(c for c in keyword[:20] if c.isalnum() or c in " _-").strip()
    txt_path = manuscript_dir / f"{safe_keyword or 'content'}.txt"
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(content)

    # 이미지 다운로드
    if image_urls:
        download_tasks = []
        for idx, url in enumerate(image_urls):
            ext = Path(url).suffix or ".png"
            img_path = manuscript_dir / f"image_{idx + 1:02d}{ext}"
            download_tasks.append(download_image(url, img_path))

        results = await asyncio.gather(*download_tasks)
        downloaded = sum(1 for r in results if r)
        log.debug(f"이미지 다운로드", 성공=f"{downloaded}/{len(image_urls)}")

    return manuscript_id


@router.post("/generate/batch")
async def generate_batch(request: BatchGenerateRequest):
    """
    배치 원고 + 이미지 생성

    - keywords: 키워드 목록
    - generate_images: 이미지 생성 여부 (기본: True)
    - image_count: 키워드당 이미지 개수 (기본: 5)
    """
    start_ts = time.time()
    service = request.service.lower()
    keywords = request.keywords
    ref = request.ref
    generate_images = request.generate_images
    image_count = request.image_count

    log.header(f"배치 원고 생성", "📦")
    log.kv("서비스", service.upper())
    log.kv("키워드 수", len(keywords))
    log.kv("이미지 생성", "ON" if generate_images else "OFF")

    results = []
    success_count = 0

    for idx, keyword in enumerate(keywords):
        keyword = keyword.strip()
        if not keyword:
            continue

        log.step(idx + 1, len(keywords), keyword[:30])

        try:
            # 1. 카테고리 분류
            category = await get_category_db_name(keyword=keyword + ref)

            # 2. 원고 생성
            content = await run_in_threadpool(
                gpt4o_gen,
                user_instructions=keyword,
                ref=ref,
                category=category
            )

            if not content:
                results.append({
                    "keyword": keyword,
                    "success": False,
                    "message": "원고 생성 실패",
                })
                log.error(f"원고 생성 실패", keyword=keyword[:20])
                continue

            # 3. 이미지 생성 (옵션)
            image_urls = []
            if generate_images:
                log.debug(f"이미지 생성 중...", count=image_count)
                images = await run_in_threadpool(
                    generate_images_parallel,
                    keyword,
                    image_count
                )
                image_urls = [img["url"] for img in images if img.get("url")]
                log.debug(f"이미지 생성 완료", count=len(image_urls))

            # 4. pending 폴더에 저장
            manuscript_id = await save_to_pending(keyword, content, image_urls)
            success_count += 1

            results.append({
                "keyword": keyword,
                "success": True,
                "manuscript_id": manuscript_id,
                "content_length": len(content),
                "images_count": len(image_urls),
            })
            log.success(f"완료", keyword=keyword[:20], id=manuscript_id, images=len(image_urls))

        except Exception as e:
            results.append({
                "keyword": keyword,
                "success": False,
                "message": str(e),
            })
            log.error(f"에러", keyword=keyword[:20], error=str(e))

        # 요청 간 딜레이
        if idx < len(keywords) - 1:
            await asyncio.sleep(1)

    elapsed = time.time() - start_ts
    log.divider()
    log.success(f"배치 완료", 성공=f"{success_count}/{len(keywords)}", 시간=f"{elapsed:.1f}s")

    return JSONResponse(content={
        "total": len(keywords),
        "success": success_count,
        "failed": len(keywords) - success_count,
        "elapsed": round(elapsed, 1),
        "results": results,
    })

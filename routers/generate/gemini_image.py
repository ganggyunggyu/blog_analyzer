"""이미지 생성 라우터"""

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from fastapi import HTTPException, APIRouter
from fastapi.concurrency import run_in_threadpool

from schema.generate import ImageGenerateRequest, ImageGenerateResponse, ImageItem
from llm.image_service import image_gen_single, get_random_poses, MODEL_NAME
from utils.progress_logger import progress
from utils.logger import log


router = APIRouter()

IMAGE_COUNT: int = 5


MAX_RETRIES: int = 3


def _generate_images_parallel(keyword: str, poses: list, target_count: int = IMAGE_COUNT) -> tuple:
    """이미지 병렬 생성 (실패 시 재시도)"""
    images = []
    total_cost = 0.0
    retry_count = 0

    remaining_poses = list(poses)

    while len(images) < target_count and retry_count < MAX_RETRIES:
        with ThreadPoolExecutor(max_workers=len(remaining_poses)) as executor:
            futures = {
                executor.submit(image_gen_single, keyword, pose): pose
                for pose in remaining_poses
            }

            failed_poses = []
            for future in as_completed(futures):
                pose = futures[future]
                result = future.result()
                if result and result.get("url"):
                    images.append(result)
                    total_cost += result.get("cost", 0)
                else:
                    failed_poses.append(pose)

        if len(images) >= target_count:
            break

        if failed_poses:
            retry_count += 1
            remaining_poses = failed_poses[:target_count - len(images)]
            from utils.logger import console
            console.print(f"  [yellow]재시도 {retry_count}/{MAX_RETRIES}[/yellow] ({len(remaining_poses)}개 남음)")

    failed_count = target_count - len(images)
    return images, failed_count, total_cost


@router.post("/generate/image", response_model=ImageGenerateResponse)
async def generate_image(request: ImageGenerateRequest):
    """
    이미지 5장 동시 생성

    - keyword: 이미지 주제 키워드
    """
    start_ts = time.time()
    keyword = request.keyword.strip()

    if not keyword:
        raise HTTPException(status_code=400, detail="keyword가 필요합니다.")

    poses = get_random_poses(IMAGE_COUNT)

    log.header(f"IMAGE {IMAGE_COUNT}장 생성", "🎨")
    log.kv("키워드", keyword)
    log.kv("모델", MODEL_NAME)
    log.kv("포즈", f"{len(poses)}개 선택")

    try:
        with progress(label=f"image:{keyword}"):
            images, failed_count, total_cost = await run_in_threadpool(
                _generate_images_parallel,
                keyword,
                poses,
            )

        elapsed = time.time() - start_ts
        total_krw = total_cost * 1400

        log.divider()
        log.success(
            f"IMAGE 완료",
            성공=f"{len(images)}장",
            실패=f"{failed_count}장",
            시간=f"{elapsed:.1f}s",
            비용=f"${total_cost:.2f} ({total_krw:.0f}원)"
        )

        image_items = [
            ImageItem(url=img["url"])
            for img in images
            if img.get("url")
        ]

        return ImageGenerateResponse(
            images=image_items,
            total=len(images),
            failed=failed_count,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"이미지 생성 중 오류 발생: {e}",
        )

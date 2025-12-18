"""이미지 생성 라우터"""

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from fastapi import HTTPException, APIRouter
from fastapi.concurrency import run_in_threadpool

from schema.generate import ImageGenerateRequest, ImageGenerateResponse, ImageItem
from llm.image_service import image_gen_single, get_random_poses, MODEL_NAME
from utils.progress_logger import progress


router = APIRouter()

IMAGE_COUNT: int = 5


def _generate_images_parallel(keyword: str, poses: list) -> tuple:
    """이미지 병렬 생성"""
    images = []
    failed_count = 0

    with ThreadPoolExecutor(max_workers=len(poses)) as executor:
        futures = {
            executor.submit(image_gen_single, keyword, pose): pose
            for pose in poses
        }

        for future in as_completed(futures):
            result = future.result()
            if result and result.get("url"):
                images.append(result)
            else:
                failed_count += 1

    return images, failed_count


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

    print("\n" + "=" * 60)
    print(f"IMAGE {IMAGE_COUNT}장 생성 시작")
    print("=" * 60)
    print(f"키워드    : {keyword}")
    print(f"모델      : {MODEL_NAME}")
    print(f"생성 개수 : {IMAGE_COUNT}장")
    print("선택된 포즈:")
    for i, pose in enumerate(poses):
        print(f"  [{i+1}] {pose}")
    print("=" * 60 + "\n")

    try:
        with progress(label=f"image:{keyword}"):
            images, failed_count = await run_in_threadpool(
                _generate_images_parallel,
                keyword,
                poses,
            )

        elapsed = time.time() - start_ts

        print("\n" + "=" * 60)
        print(f"IMAGE 생성 완료")
        print("=" * 60)
        print(f"키워드       : {keyword}")
        print(f"성공         : {len(images)}장")
        print(f"실패         : {failed_count}장")
        print(f"소요시간     : {elapsed:.2f}s")
        print("=" * 60 + "\n")

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

"""이미지 생성 라우터"""

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from fastapi import HTTPException, APIRouter
from fastapi.concurrency import run_in_threadpool

from schema.generate import ImageGenerateRequest, ImageGenerateResponse, ImageItem
from llm.image_service import image_gen_single, get_random_poses, MODEL_NAME
from utils.image_server import get_ai_images
from utils.progress_logger import progress
from utils.logger import log


router = APIRouter()

MAX_IMAGE_COUNT: int = 10
MAX_RETRIES: int = 3


def _try_s3_images(keyword: str, count: int) -> tuple[list, bool]:
    """S3 이미지 서버에서 이미지 조회 시도

    Returns:
        (images, success) - images는 ImageItem 리스트, success는 S3에서 찾았는지 여부
    """
    try:
        result = get_ai_images(keyword=keyword, count=count, distort=True)

        if result.get("success") and result.get("found"):
            images = [
                {"url": img["url"]}
                for img in result.get("images", [])
                if img.get("url")
            ]
            log.info(f"S3 이미지 발견: {result.get('matchedFolder')} ({len(images)}장)")
            return images, True

        log.info(f"S3 이미지 없음: {keyword}")
        return [], False

    except Exception as e:
        log.warning(f"S3 서버 오류 (AI 생성으로 fallback): {e}")
        return [], False


def _generate_images_parallel(keyword: str, poses: list, target_count: int, category: str = "") -> tuple:
    """이미지 병렬 생성 (실패 시 재시도)

    Args:
        keyword: 이미지 주제 키워드
        poses: 포즈 목록
        target_count: 목표 이미지 개수
        category: 카테고리 (애견동물_반려동물_분양일 때 Puppy 가이드라인 추가)
    """
    images = []
    total_cost = 0.0
    retry_count = 0

    remaining_poses = list(poses)

    while len(images) < target_count and retry_count < MAX_RETRIES:
        with ThreadPoolExecutor(max_workers=len(remaining_poses)) as executor:
            futures = {
                executor.submit(image_gen_single, keyword, pose, category): pose
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
    이미지 생성 (S3 우선, 없으면 AI 생성)

    - keyword: 이미지 주제 키워드
    - category: 카테고리 (애견동물_반려동물_분양일 때 Puppy 가이드라인 추가)
    - count: 생성할 이미지 개수 (기본: 5, 최대: 10)

    Flow:
    1. S3 이미지 서버에서 키워드 매칭 이미지 검색
    2. 있으면 S3 이미지 반환 (비용 0)
    3. 없으면 AI로 이미지 생성
    """
    start_ts = time.time()
    keyword = request.keyword.strip()
    category = request.category.strip() if request.category else ""
    count = min(request.count, MAX_IMAGE_COUNT)

    if not keyword:
        raise HTTPException(status_code=400, detail="keyword가 필요합니다.")

    log.header(f"IMAGE {count}장 요청", "🎨")
    log.kv("키워드", keyword)

    try:
        # # 1. S3 이미지 서버 먼저 확인 (임시 비활성화)
        # with progress(label=f"s3-check:{keyword}"):
        #     s3_images, s3_found = await run_in_threadpool(
        #         _try_s3_images, keyword, count
        #     )
        #
        # if s3_found and s3_images:
        #     elapsed = time.time() - start_ts
        #     log.divider()
        #     log.success(
        #         "IMAGE 완료 (S3)",
        #         성공=f"{len(s3_images)}장",
        #         시간=f"{elapsed:.1f}s",
        #         비용="$0.00 (S3)"
        #     )
        #
        #     return ImageGenerateResponse(
        #         images=[ImageItem(url=img["url"]) for img in s3_images],
        #         total=len(s3_images),
        #         failed=0,
        #     )

        # AI 이미지 생성
        poses = get_random_poses(count)
        log.kv("모델", MODEL_NAME)
        log.kv("포즈", f"{len(poses)}개 선택")
        if category:
            log.kv("카테고리", category)

        with progress(label=f"ai-gen:{keyword}"):
            images, failed_count, total_cost = await run_in_threadpool(
                _generate_images_parallel,
                keyword,
                poses,
                count,
                category,
            )

        elapsed = time.time() - start_ts
        total_krw = total_cost * 1400

        log.divider()
        log.success(
            "IMAGE 완료 (AI)",
            성공=f"{len(images)}장",
            실패=f"{failed_count}장",
            시간=f"{elapsed:.1f}s",
            비용=f"${total_cost:.2f} ({total_krw:.0f}원)"
        )

        return ImageGenerateResponse(
            images=[ImageItem(url=img["url"]) for img in images if img.get("url")],
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

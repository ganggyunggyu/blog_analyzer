"""Imagen 4 - 이미지 생성 서비스 (4장 동시 생성)"""

from __future__ import annotations
import random
from typing import List, Tuple
from io import BytesIO

from google import genai
from google.genai import types

from config import GEMINI_API_KEY
from _constants.Model import Model
from utils.s3_uploader import upload_image_to_s3


MODEL_NAME: str = Model.IMAGEN_4
IMAGE_COUNT: int = 4

# 애견 관련 포즈/동작
DOG_POSES = [
    # 기본 동작
    "running happily in a park",
    "sitting calmly and looking at camera",
    "smiling with tongue out",
    "lying down relaxed on grass",
    "standing proudly",

    # 활동적인 동작
    "jumping joyfully in the air",
    "playing with a ball",
    "playing with a toy",
    "catching a frisbee",
    "splashing in water",
    "digging in sand",
    "chasing butterflies",

    # 귀여운 표정/포즈
    "tilting head curiously",
    "yawning cutely",
    "winking at camera",
    "giving puppy eyes",
    "looking up adorably",
    "peeking from behind something",

    # 일상 동작
    "walking elegantly",
    "stretching after a nap",
    "sniffing flowers",
    "looking out the window",
    "waiting patiently for treats",
    "cuddling with a blanket",

    # 사회적 동작
    "playing with another dog",
    "being petted by owner",
    "shaking hands (paw)",
    "rolling on back happily",

    # 계절/환경
    "playing in autumn leaves",
    "enjoying sunshine",
    "in a cozy indoor setting",
    "at the beach",
    "in a flower garden",
]


def build_image_prompt(keyword: str) -> str:
    """이미지 생성용 프롬프트 생성 (다양한 포즈 포함)"""
    pose = random.choice(DOG_POSES)

    return f"""Professional blog thumbnail image for: '{keyword}'

Pose/Action: {pose}

Style: Clean, modern, high quality photography
- Visually appealing and eye-catching
- Related to the keyword theme
- No text, watermarks, or logos
- Bright, warm color palette
- Suitable for Naver blog"""


def gemini_image_gen(keyword: str) -> Tuple[List[dict], int]:
    """
    Imagen 4로 이미지 4장 동시 생성

    Args:
        keyword: 키워드

    Returns:
        Tuple[이미지 리스트, 실패 개수]

    Raises:
        ValueError: API 키 또는 키워드 없음
    """
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY가 설정되어 있지 않습니다.")

    if not keyword:
        raise ValueError("키워드가 없습니다.")

    client = genai.Client(api_key=GEMINI_API_KEY)

    prompt = build_image_prompt(keyword)

    print(f"이미지 생성 키워드: {keyword}")
    print(f"이미지 {IMAGE_COUNT}장 동시 생성 시작")

    images: List[dict] = []
    failed_count = 0

    try:
        response = client.models.generate_images(
            model=MODEL_NAME,
            prompt=prompt,
            config=types.GenerateImagesConfig(
                number_of_images=IMAGE_COUNT,
            ),
        )

        for generated_image in response.generated_images:
            try:
                img = generated_image.image

                # Google Image 객체에서 PIL 이미지 추출
                if hasattr(img, '_pil_image') and img._pil_image:
                    pil_img = img._pil_image
                    buffer = BytesIO()
                    pil_img.save(buffer, format="PNG")
                    image_bytes = buffer.getvalue()
                elif hasattr(img, 'image_bytes'):
                    image_bytes = img.image_bytes
                elif hasattr(img, '_image_bytes'):
                    image_bytes = img._image_bytes
                elif hasattr(img, 'data'):
                    image_bytes = img.data
                else:
                    # 마지막 시도: 객체 자체가 bytes인지 확인
                    image_bytes = bytes(img) if isinstance(img, (bytes, bytearray)) else None

                if image_bytes:
                    s3_url = upload_image_to_s3(
                        image_bytes=image_bytes,
                        keyword=keyword,
                        content_type="image/png",
                    )

                    if s3_url:
                        images.append({"url": s3_url})
                else:
                    print(f"이미지 bytes 추출 실패. 객체 타입: {type(img)}, 속성: {dir(img)}")
                    failed_count += 1

            except Exception as e:
                print(f"이미지 변환 실패: {e}")
                failed_count += 1

    except Exception as e:
        print(f"이미지 생성 API 호출 실패: {e}")
        failed_count = IMAGE_COUNT

    # 비용 계산 (Imagen 4: $0.04/image - 2025년 12월 기준)
    cost_per_image = 0.04
    total_cost_usd = len(images) * cost_per_image
    total_cost_krw = total_cost_usd * 1400  # 환율 약 1400원

    print(f"이미지 생성 완료: 성공 {len(images)}장, 실패 {failed_count}장")
    print(f"[비용] ${total_cost_usd:.2f} (약 {total_cost_krw:.0f}원)")

    return images, failed_count

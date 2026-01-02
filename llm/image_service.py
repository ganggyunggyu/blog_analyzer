"""이미지 생성 서비스 (단일 이미지)"""

from __future__ import annotations
import random
from typing import List, Optional

from _constants.Model import Model
from utils.ai_client_factory import call_image_ai


MODEL_NAME: str = Model.GEMINI_2_5_FLASH_IMAGE

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


# def build_image_prompt(keyword: str, pose: str) -> str:
#     """이미지 생성용 프롬프트 생성"""
#     return f"""
# {keyword}
# """


def build_image_prompt(keyword: str, pose: str, category: str = "") -> str:
    """이미지 생성용 프롬프트 생성

    Args:
        keyword: 이미지 주제 키워드
        pose: 포즈 (애견동물 카테고리일 때만 사용)
        category: 카테고리
    """
    # 애견/반려동물 카테고리일 때만 동물 관련 지침 추가
    if category == "애견동물_반려동물_분양":
        return f"""Authentic candid photograph of '{keyword}' {pose}

CRITICAL - Natural & Organic Feel:
- Real camera photo taken by amateur photographer
- Slightly imperfect composition, not too centered
- Natural ambient lighting with real shadows
- Genuine fur texture with visible details
- Real environment with authentic background elements
- Candid moment, not posed or staged looking

Puppy/Young Dog Guidelines:
- Show age-appropriate puppy features: soft fluffy fur, round face, big eyes
- Puppies have shorter snouts and rounder heads than adults
- Include playful or curious expressions natural to young dogs
- Puppy proportions: larger paws relative to body, shorter legs
- Avoid making puppies look like miniature adult dogs
- Natural puppy behaviors: exploring, playing, sleeping curled up

Anti-AI Aesthetics (VERY IMPORTANT):
- NO plastic or waxy fur texture
- NO overly smooth or airbrushed look
- NO hyperrealistic uncanny valley effect
- NO perfect symmetry
- NO oversaturated or HDR-like colors
- NO artificial studio lighting
- Avoid the "AI generated" glossy appearance

Technical Style:
- Shot on iPhone or mid-range DSLR
- Natural daylight or indoor ambient light
- Slight film grain acceptable
- Real depth of field, not artificially blurred
- Colors like actual photograph, not enhanced

Output Rules:
- Single subject only, NO collage or grid
- Photorealistic documentary style


"""

    return f"""Authentic photograph of '{keyword}'

CRITICAL - NO TEXT IN IMAGE:
- NEVER include any text, letters, words, or typography in the image
- NO watermarks, logos, signs, labels, or captions
- NO written content of any kind - pure visual only
"""


def get_random_pose() -> str:
    """랜덤 포즈 1개 선택"""
    return random.choice(DOG_POSES)


def get_random_poses(count: int) -> List[str]:
    """중복 없이 랜덤 포즈 선택"""
    return random.sample(DOG_POSES, min(count, len(DOG_POSES)))


def image_gen_single(
    keyword: str, pose: Optional[str] = None, category: str = ""
) -> Optional[dict]:
    """
    단일 이미지 생성

    Args:
        keyword: 이미지 주제 키워드
        pose: 포즈 (없으면 랜덤)
        category: 카테고리 (애견동물_반려동물_분양일 때만 Puppy 가이드라인 추가)

    Returns:
        이미지 dict {"url": "..."} 또는 None (실패 시)
    """
    if not keyword:
        raise ValueError("키워드가 없습니다.")

    if not pose:
        pose = get_random_pose()

    prompt = build_image_prompt(keyword, pose, category)

    result = call_image_ai(
        model_name=MODEL_NAME,
        prompt=prompt,
        keyword=keyword,
    )

    return result

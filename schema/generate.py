from typing import Optional, List
from pydantic import BaseModel


class GenerateRequest(BaseModel):
    service: str
    keyword: str
    ref: str = ""
    persona_id: Optional[str] = None      # 페르소나 ID (우선)
    persona_index: Optional[int] = None   # 페르소나 인덱스 (하위호환)


class BatchGenerateRequest(BaseModel):
    service: str
    keywords: List[str]  # 키워드 여러개
    ref: str = ""
    generate_images: bool = True  # 이미지도 생성할지 (기본: True)
    image_count: int = 5  # 키워드당 이미지 개수


class ImageGenerateRequest(BaseModel):
    keyword: str
    category: str = ""  # 카테고리 (애견동물_반려동물_분양일 때 Puppy 가이드라인 추가)


class ImageItem(BaseModel):
    url: str


class ImageGenerateResponse(BaseModel):
    images: List[ImageItem]
    total: int
    failed: int = 0

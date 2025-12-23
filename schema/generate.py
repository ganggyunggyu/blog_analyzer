from typing import Optional, List
from pydantic import BaseModel


class GenerateRequest(BaseModel):
    service: str
    keyword: str
    ref: str = ""


class BatchGenerateRequest(BaseModel):
    service: str
    keywords: List[str]  # 키워드 여러개
    ref: str = ""
    generate_images: bool = True  # 이미지도 생성할지 (기본: True)
    image_count: int = 5  # 키워드당 이미지 개수


class ImageGenerateRequest(BaseModel):
    keyword: str


class ImageItem(BaseModel):
    url: str


class ImageGenerateResponse(BaseModel):
    images: List[ImageItem]
    total: int
    failed: int = 0

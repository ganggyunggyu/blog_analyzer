"""이미지 서버 API 클라이언트"""

import os
import requests
from typing import Optional

IMAGE_SERVER_URL = os.getenv("IMAGE_SERVER_URL", "http://localhost:3939")


def get_ai_images(
    keyword: str,
    count: int = 5,
    distort: bool = True,
) -> dict:
    """
    S3 이미지 서버에서 키워드 매칭 이미지 조회

    Args:
        keyword: 검색 키워드
        count: 반환 개수 (최대 20)
        distort: 약한 왜곡 적용 여부

    Returns:
        {
            "images": {
                "body": ["https://...URL"],
                "individual": [], "slide": [], "collage": [],
                "excludeLibrary": [], "excludeLibraryLink": []
            },
            "metadata": {},
            "keyword": str,
            "blogId": str,
            "category": str,
            "folder": str,
            "total": int,
            "failed": int
        }
    """
    if not keyword:
        raise ValueError("키워드가 필요합니다.")

    url = f"{IMAGE_SERVER_URL}/api/image/ai-images"
    params = {
        "keyword": keyword,
        "count": count,
        "distort": str(distort).lower(),
    }

    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()

    return response.json()

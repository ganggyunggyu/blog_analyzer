"""맛집 시트 서버 통신 서비스 (포트 3000)"""

from __future__ import annotations

import os
import requests
from typing import Optional


BASE_URL = os.getenv("SHEET_SERVER_URL", "http://localhost:3000")


class SheetRestaurantService:
    """맛집 시트 서버 통신 서비스"""

    def __init__(self, base_url: str = BASE_URL, timeout: int = 30):
        self.base_url = base_url
        self.timeout = timeout

    def get_all(self) -> dict:
        """전체 데이터 조회

        Returns:
            {"count": int, "data": list}
        """
        response = requests.get(
            f"{self.base_url}/api/restaurant-test",
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    def get_by_number(self, number: int) -> Optional[dict]:
        """번호로 조회

        Args:
            number: 맛집 번호

        Returns:
            맛집 데이터 또는 None
        """
        result = self.get_all()
        for item in result["data"]:
            if item.get("number") == number:
                return item
        return None

    def get_by_name(self, name: str) -> Optional[dict]:
        """이름으로 조회

        Args:
            name: 맛집 이름

        Returns:
            맛집 데이터 또는 None
        """
        result = self.get_all()
        for item in result["data"]:
            if item.get("name") == name:
                return item
        return None

    def sync(self) -> dict:
        """구글 시트 → DB 동기화

        Returns:
            {"message": str, "count": int}
        """
        response = requests.post(
            f"{self.base_url}/api/restaurant-test",
            timeout=60,
        )
        response.raise_for_status()
        return response.json()


sheet_restaurant_service = SheetRestaurantService()

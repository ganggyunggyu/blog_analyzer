"""맛집 데이터 통합 로더 - 5개 지역 데이터를 통합하고 키워드로 검색"""

from __future__ import annotations

import re
from typing import Optional

from _prompts.category.서울맛집_데이터 import SEOUL_RESTAURANTS
from _prompts.category.경기인천_맛집_데이터 import GYEONGGI_INCHEON_RESTAURANTS
from _prompts.category.제주도_맛집_데이터 import JEJU_RESTAURANTS
from _prompts.category.data.gyeongsang_restaurants import GYEONGSANG_RESTAURANTS
from _prompts.category.강원도_맛집_데이터 import GANGWONDO_RESTAURANTS


# 지역명 → 데이터 키 매핑
AREA_KEY_MAP: dict[str, tuple[str, str]] = {}


def _normalize_restaurant(raw: dict) -> dict:
    """키 이름을 name/menu/desc로 통일"""
    return {
        "name": raw.get("name", ""),
        "menu": raw.get("menu") or raw.get("dish", ""),
        "desc": raw.get("desc") or raw.get("description", ""),
    }


def _build_area_map() -> dict[str, list[dict]]:
    """전체 지역 데이터를 통합 딕셔너리로 빌드"""
    merged: dict[str, list[dict]] = {}

    # 서울 (nested 구조 처리)
    for gu_name, data in SEOUL_RESTAURANTS.items():
        restaurants = data.get("restaurants", data) if isinstance(data, dict) else data
        if isinstance(restaurants, dict):
            restaurants = data
        if isinstance(data, dict) and "restaurants" in data:
            restaurants = data["restaurants"]
        else:
            restaurants = data if isinstance(data, list) else []
        merged[gu_name] = [_normalize_restaurant(r) for r in restaurants]

    # 경기/인천 (flat 구조)
    for area_name, restaurants in GYEONGGI_INCHEON_RESTAURANTS.items():
        merged[area_name] = [_normalize_restaurant(r) for r in restaurants]

    # 제주도 (flat 구조)
    for area_name, restaurants in JEJU_RESTAURANTS.items():
        merged[area_name] = [_normalize_restaurant(r) for r in restaurants]

    # 경상도/부산 (flat 구조, 키에 부산_ 접두사)
    for area_name, restaurants in GYEONGSANG_RESTAURANTS.items():
        clean_name = area_name.replace("_", " ").replace("부산 ", "")
        merged[area_name] = [_normalize_restaurant(r) for r in restaurants]
        if area_name != clean_name:
            merged[clean_name] = merged[area_name]

    # 강원도 (flat 구조)
    for area_name, restaurants in GANGWONDO_RESTAURANTS.items():
        merged[area_name] = [_normalize_restaurant(r) for r in restaurants]

    return merged


ALL_RESTAURANTS = _build_area_map()

# 검색용 별칭 매핑 (키워드에서 추출한 지역명 → 데이터 키)
ALIASES: dict[str, str] = {
    # 서울 구
    "홍대": "마포구", "합정": "마포구", "망원": "마포구", "연남동": "마포구", "연남": "마포구",
    "강남": "강남구", "신사동": "강남구", "압구정": "강남구", "신사": "강남구",
    "광화문": "종로구", "북촌": "종로구", "익선동": "종로구", "종로": "종로구",
    "이태원": "용산구", "한남동": "용산구", "경리단길": "용산구", "한남": "용산구",
    "성수동": "성동구", "성수": "성동구", "왕십리": "성동구",
    "잠실": "송파구", "문정동": "송파구", "문정": "송파구",
    "연희동": "서대문구", "신촌": "서대문구", "연희": "서대문구",
    "천호": "강동구", "명일": "강동구", "둔촌": "강동구",
    "여의도": "영등포구", "영등포": "영등포구",
    "을지로": "중구", "명동": "중구", "충무로": "중구",
    "서초": "서초구", "방배": "서초구", "서래마을": "서초구",
    "마곡": "강서구", "발산": "강서구",
    "동대문": "동대문구", "청량리": "동대문구",
    "건대": "광진구", "구의": "광진구",
    "노원": "노원구", "상계": "노원구",
    "신림": "관악구", "봉천": "관악구", "봉천동": "관악구",
    "불광": "은평구", "응암": "은평구",
    "사당": "동작구", "노량진": "동작구", "이수": "동작구",
    # 경기/인천
    "분당": "성남/분당", "성남": "성남/분당", "성남분당": "성남/분당", "성남 분당": "성남/분당",
    "일산": "고양/일산", "고양": "고양/일산", "고양일산": "고양/일산",
    "송도": "인천", "부평": "인천", "차이나타운": "인천", "연수구": "인천",
    # 부산
    "서면": "부산_서면", "해운대": "부산_해운대", "광안리": "부산_광안리",
    "남포동": "부산_남포동/자갈치", "자갈치": "부산_남포동/자갈치",
    "전포동": "부산_전포동", "전포": "부산_전포동",
    # 대구
    "동성로": "대구_동성로", "대구": "대구_동성로",
    "수성구": "대구_수성구",
    # 기타 경상
    "마산": "창원/마산", "창원": "창원/마산",
}

# 지역 → 권역 매핑 (필명 선택용)
REGION_MAP: dict[str, str] = {}

_SEOUL_GUS = [
    "마포구", "강남구", "종로구", "용산구", "성동구", "송파구", "서대문구",
    "강동구", "영등포구", "중구", "서초구", "강서구", "동대문구", "광진구",
    "노원구", "관악구", "은평구", "동작구",
]
for _g in _SEOUL_GUS:
    REGION_MAP[_g] = "서울"

_GYEONGGI = [
    "수원", "성남/분당", "용인", "고양/일산", "파주", "화성", "안양",
    "부천", "평택", "남양주", "의정부", "김포", "광명", "하남", "인천",
]
for _g in _GYEONGGI:
    REGION_MAP[_g] = "경기"

_JEJU = ["제주시", "서귀포", "애월", "함덕", "성산", "중문", "협재", "한림", "표선", "우도"]
for _g in _JEJU:
    REGION_MAP[_g] = "제주"

_GYEONGSANG_KEYS = list(GYEONGSANG_RESTAURANTS.keys())
for _g in _GYEONGSANG_KEYS:
    REGION_MAP[_g] = "경상"
    clean = _g.replace("_", " ").replace("부산 ", "")
    if clean != _g:
        REGION_MAP[clean] = "경상"

_GANGWON = list(GANGWONDO_RESTAURANTS.keys())
for _g in _GANGWON:
    REGION_MAP[_g] = "강원"

# 필명 매핑
PEN_NAMES: dict[str, str] = {
    "서울": "제이제이",
    "경기": "사랑채",
    "제주": "호이호이",
    "경상": "머머",
    "강원": "바글바글",
}


def _extract_area_and_count(keyword: str) -> tuple[str, int]:
    """키워드에서 지역명과 개수를 추출.
    예: '수원맛집10선' → ('수원', 10)
        '마포구맛집추천' → ('마포구', 7)
    """
    count_match = re.search(r"(\d+)", keyword)
    count = int(count_match.group(1)) if count_match else 7

    cleaned = re.sub(r"맛집.*$", "", keyword).strip()
    cleaned = re.sub(r"\d+선$", "", cleaned).strip()
    if not cleaned:
        cleaned = keyword.replace("맛집", "").replace("추천", "").replace("베스트", "").strip()
        cleaned = re.sub(r"\d+", "", cleaned).strip()

    return cleaned, count


def _find_area_key(area_name: str) -> Optional[str]:
    """지역명으로 데이터 키를 찾기"""
    if area_name in ALL_RESTAURANTS:
        return area_name

    if area_name in ALIASES:
        return ALIASES[area_name]

    # 별칭에서 부분 매칭
    for alias, key in ALIASES.items():
        if alias in area_name or area_name in alias:
            return key

    # 데이터 키에서 부분 매칭
    for key in ALL_RESTAURANTS:
        if area_name in key or key in area_name:
            return key

    return None


def get_restaurants_for_keyword(keyword: str) -> tuple[str, str, list[dict], int]:
    """키워드 기반으로 맛집 데이터 반환.

    Returns:
        (area_name, pen_name, restaurants, count)
    """
    area_name, count = _extract_area_and_count(keyword)
    area_key = _find_area_key(area_name)

    if not area_key:
        return area_name, "제이제이", [], count

    restaurants = ALL_RESTAURANTS.get(area_key, [])
    region = REGION_MAP.get(area_key, "서울")
    pen_name = PEN_NAMES.get(region, "제이제이")

    return area_name, pen_name, restaurants[:count], count


def format_restaurants_for_prompt(restaurants: list[dict]) -> str:
    """맛집 데이터를 프롬프트용 텍스트로 변환"""
    if not restaurants:
        return "(참고 데이터 없음 - AI 지식 기반으로 작성)"

    lines = []
    for i, r in enumerate(restaurants, 1):
        lines.append(f"{i}. {r['name']} | {r['menu']} | {r['desc']}")
    return "\n".join(lines)

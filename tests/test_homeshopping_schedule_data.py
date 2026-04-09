from datetime import date

from scripts.homeshopping_schedule_data import (
    build_collection_dates,
    classify_health_category,
    extract_keywords,
    format_korean_date_range,
    is_health_product,
    normalize_product_name,
)


def make_product(name: str, category2: str = "", category3: str = "", brand: str = "") -> dict[str, str]:
    return {
        "name": name,
        "category1": "",
        "category2": category2,
        "category3": category3,
        "brand": brand,
        "simple_name": "",
    }


def test_build_collection_dates_uses_seven_day_window() -> None:
    assert build_collection_dates(date(2026, 4, 7)) == [
        "2026-04-03",
        "2026-04-04",
        "2026-04-05",
        "2026-04-06",
        "2026-04-07",
        "2026-04-08",
        "2026-04-09",
    ]


def test_format_korean_date_range_compacts_same_month() -> None:
    assert format_korean_date_range(["2026-04-03", "2026-04-09"]) == "2026년 4월 3일~9일"


def test_is_health_product_accepts_keyword_based_item() -> None:
    product = make_product("홍천 약도라지청", category2="가공식품", category3="전통식품")
    assert is_health_product(product) is True


def test_is_health_product_rejects_non_health_machine() -> None:
    product = make_product("나인닷 지압 순환 머신", category2="헬스", category3="런닝/워킹머신")
    assert is_health_product(product) is False


def test_is_health_product_rejects_beauty_item_with_health_like_name() -> None:
    product = make_product("비타 콜라겐 바디워시", category2="바디케어", category3="워시")
    assert is_health_product(product) is False


def test_classify_health_category_and_keywords_for_diet_item() -> None:
    product = make_product("홀베리 와사비 다이어트 이소비텍신", category2="건강식품", category3="개별인정 건강식품")
    assert classify_health_category(product) == "다이어트"
    assert extract_keywords(product, "다이어트")[:2] == ["다이어트", "이소비텍신"]


def test_classify_health_category_for_bone_health_item() -> None:
    product = make_product("닥터린 콘드로이친 1200+MBP", category2="건강식품", category3="개별인정 건강식품")
    assert classify_health_category(product) == "관절/뼈건강"


def test_normalize_product_name_uses_clean_sheet_style() -> None:
    assert normalize_product_name("[락토핏] (방송에서만) 락토핏 맥스19 유산균 12통 (24개월분)") == "락토핏 맥스19 유산균"
    assert normalize_product_name("★전고객 5만원★ 비에날 씬 프로 9개월 + 롯데상품권 5만원 + 프로틴 14포 + 텀블러") == "비에날 씬 프로"
    assert normalize_product_name("[삼육두유]검은콩과볶은귀리48팩+검은콩호두아몬드32팩+검은콩흑임자32팩(총112팩)") == "삼육두유 검은콩 혼합세트"

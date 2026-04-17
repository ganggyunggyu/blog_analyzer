from datetime import date

from scripts.homeshopping_schedule_data import (
    build_collection_dates,
    classify_health_category,
    extract_focus_keyword,
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
    assert normalize_product_name("[주영엔에스 단백질 저분자 유청펩타이드 HW-3] 12주(84포)") == "주영엔에스 단백질 저분자 유청펩타이드 HW-3"
    assert normalize_product_name("여에스더 리포좀글루타치온 울트라 9X 12+1박스+맥주효모2박스") == "여에스더 리포좀글루타치온 울트라 9X"
    assert normalize_product_name("[방송에서만]지니라이프 듀얼 맥스 콘드로이친1200MBP 6+6박스") == "지니라이프 듀얼 맥스 콘드로이친1200MBP"
    assert normalize_product_name("♥[유난희 건강톡톡 패키지] 팔레오 고단백 프로틴") == "팔레오 고단백 프로틴"
    assert normalize_product_name("○[방송에서만][6+4박스] 홍삼진고 데일리스틱 (10g*30포*10박스)") == "홍삼진고 데일리스틱"
    assert normalize_product_name("카무트® 영양견과바 420g(21gx20개입) x 4박스 / 총 80개") == "카무트 영양견과바"
    assert normalize_product_name("(무)정관장 홍삼활력플러스업 6+3박스(총 9박스)+쇼핑백 9장") == "정관장 홍삼활력플러스업"
    assert normalize_product_name("D_미녀의 석류 콜라겐 (25g)") == "미녀의 석류 콜라겐"
    assert normalize_product_name("[정식품] 베지밀 총 90팩 (검은콩 고칼슘두유 190ml x 45팩 + 검은콩 아몬드호두 두유 190ml x 45팩)") == "베지밀"
    assert normalize_product_name("구수한맛 밸런스업 총 144팩 (230ml X 24팩 X 6박스)") == "구수한맛 밸런스업"


def test_extract_focus_keyword_prefers_short_product_name() -> None:
    assert extract_focus_keyword("윤방부박사의 넘버원 알부민 당제로", "알부민") == "알부민 당제로"
    assert extract_focus_keyword("여에스더 리포좀 글루타치온 울트라9X", "글루타치온") == "리포좀 글루타치온"
    assert extract_focus_keyword("주영엔에스 단백질 저분자 유청펩타이드 HW-3", "단백질") == "유청펩타이드 HW-3"
    assert extract_focus_keyword("팔레오 고단백 프로틴", "단백질, 콘드로이친") == "팔레오 고단백 프로틴"
    assert extract_focus_keyword("카무트 영양견과바", "카무트") == "카무트 영양견과바"
    assert extract_focus_keyword("", "유산균") == "유산균"

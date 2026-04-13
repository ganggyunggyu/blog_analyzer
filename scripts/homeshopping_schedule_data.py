"""홈쇼핑 건강식품 편성 데이터 수집기"""

from __future__ import annotations

import json
import re
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

API_URL = "https://api.hsmoa.net/v1/schedule"
CACHE_PATH = Path("/tmp/homeshopping_health_collection.json")
CACHE_VERSION = 3

SPREADSHEET_ID = "1HErumqLrDcuCDlxnAlbB9efClvIVPihZq12kcUQzP2k"
MAIN_WORKSHEET_GID = "1306070881"
SUMMARY_WORKSHEET_TITLE = "키워드요약"

HEADERS = ["날짜", "채널", "방송시간", "상품명", "건강카테고리", "가격(원)", "키워드", "추출키워드"]

COLLECTION_PAST_DAYS = 4
COLLECTION_FUTURE_DAYS = 2

CHANNELS: dict[str, str] = {
    "hmall": "현대홈쇼핑",
    "lotteimall": "롯데홈쇼핑",
    "gsshop": "GS SHOP",
    "cjmall": "CJ온스타일",
    "hnsmall": "홈&쇼핑",
    "nsmall": "NS홈쇼핑",
    "immall": "공영쇼핑",
    "kshop": "KT알파 쇼핑",
    "wshop": "W쇼핑",
    "shopnt": "쇼핑엔티",
    "ssgshop": "신세계라이브쇼핑",
    "bshop": "SK스토아",
    "hmallplus": "현대홈쇼핑 플러스샵",
    "lotteonetv": "롯데OneTV",
    "gsmyshop": "GS MY SHOP",
    "cjmallplus": "CJ온스타일 플러스",
    "nsmallplus": "NS홈쇼핑 샵플러스",
    "kshopplus": "KT알파 쇼핑 TV플러스",
}

ALLOWED_CATEGORY2 = {"건강식품"}
ALLOWED_CATEGORY3 = {
    "개별인정 건강식품",
    "뷰티푸드",
    "헬스보조식품",
    "건강환/분말",
    "과즙/건강즙",
    "발효/효소",
}

EXCLUDED_CATEGORY_TERMS = (
    "보험",
    "의류",
    "언더웨어",
    "가전",
    "주방",
    "바디",
    "헤어",
    "스킨",
    "메이크업",
    "선케어",
    "이미용",
    "화장품",
    "세제",
    "청소",
    "가구",
    "침구",
    "여행",
    "신발",
    "가방",
    "운동화",
    "런닝",
    "워킹머신",
    "헬스기구",
    "안마의자",
)

CATEGORY_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("다이어트", ("다이어트", "이소비텍신", "와사비", "체지방", "비에날씬", "bnr17")),
    ("유산균/구강건강", ("구강유산균", "덴티백")),
    ("유산균/프로바이오틱스", ("유산균", "프로바이오틱", "락토핏", "듀얼스틱", "장면역")),
    ("관절/뼈건강", ("콘드로이친", "관절", "mbp", "연골")),
    ("칼슘/뼈건강", ("칼슘", "비타민k2", "두유")),
    ("단백질/알부민", ("알부민", "단백질", "산양유", "프로틴")),
    ("콜라겐/뷰티", ("콜라겐", "비오틴", "레티놀")),
    ("항산화/미백", ("글루타치온",)),
    ("항산화/심혈관", ("코엔자임", "q10")),
    ("항산화/베리류", ("블루베리", "안토시아닌")),
    ("효소/소화", ("효소", "카무트", "파로", "발효")),
    ("콜레스테롤/혈관", ("폴리코사놀",)),
    ("오메가3/혈행", ("오메가3", "헤링오일", "혈행", "epa", "dha")),
    ("보양식/기력회복", ("흑염소", "홍삼", "녹용", "보양")),
    ("해독/디톡스", ("클로렐라", "클렌즈", "디톡스", "cca")),
    ("생식/영양균형", ("라이프밀", "1일1생식", "선식", "식사대용")),
    ("뇌건강/인지기능", ("포스파티딜세린", "두뇌", "닥터ps", "ps진", "인지기능")),
    ("눈건강", ("루테인", "지아잔틴")),
    ("기관지/호흡기", ("도라지", "기관지", "호흡기")),
    ("면역/종합비타민", ("오쏘몰", "면역")),
    ("비타민", ("비타민", "멀티비타민", "종합비타민", "레몬즙")),
    ("건강음료", ("오르조", "건강즙", "과즙", "석류즙")),
]

KEYWORD_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("구강유산균", ("구강유산균", "덴티백")),
    ("유산균", ("유산균", "프로바이오틱", "락토핏", "듀얼스틱", "비에날씬", "bnr17")),
    ("글루타치온", ("글루타치온",)),
    ("블루베리", ("블루베리", "안토시아닌")),
    ("알부민", ("알부민",)),
    ("단백질", ("단백질", "산양유", "프로틴")),
    ("콜라겐", ("콜라겐",)),
    ("비오틴", ("비오틴",)),
    ("카무트", ("카무트",)),
    ("효소", ("효소", "파로", "발효")),
    ("폴리코사놀", ("폴리코사놀",)),
    ("흑염소", ("흑염소",)),
    ("클로렐라", ("클로렐라",)),
    ("비타민", ("비타민", "레몬즙")),
    ("종합비타민", ("종합비타민", "멀티비타민", "오쏘몰")),
    ("콘드로이친", ("콘드로이친",)),
    ("MBP", ("mbp",)),
    ("다이어트", ("다이어트", "체지방", "비에날씬")),
    ("이소비텍신", ("이소비텍신", "와사비")),
    ("포스파티딜세린", ("포스파티딜세린", "닥터ps", "ps진")),
    ("칼슘", ("칼슘",)),
    ("두유", ("두유",)),
    ("생식", ("라이프밀", "1일1생식", "선식")),
    ("오메가3", ("오메가3", "헤링오일")),
    ("코엔자임Q10", ("코엔자임", "q10")),
    ("루테인", ("루테인", "지아잔틴")),
    ("도라지", ("도라지",)),
    ("클렌즈", ("클렌즈", "cca")),
    ("오르조", ("오르조",)),
    ("면역", ("면역",)),
]

INCLUDE_TERMS = tuple(
    dict.fromkeys(
        [trigger.lower() for _, triggers in CATEGORY_RULES + KEYWORD_RULES for trigger in triggers]
        + ["홍삼", "루테인", "밀크씨슬", "프로폴리스", "석류", "건강즙", "건강환"]
    )
)

PRODUCT_NAME_OVERRIDES = {
    "[주영엔에스 단백질 저분자 유청펩타이드 HW-3] 12주(84포)": "주영엔에스 단백질 저분자 유청펩타이드 HW-3",
    "정식품 베지밀 고단백두유 검은콩 총 80팩": "정식품 베지밀 고단백두유 검은콩",
    "닥터파이토 덴티백 PRO 구강유산균 M18 14박스": "닥터파이토 덴티백 PRO 구강유산균 M18",
    "여에스더 리포좀글루타치온 울트라 9X 12+1박스+맥주효모2박스": "여에스더 리포좀글루타치온 울트라 9X",
    "종근당건강 프로메가 알티지 오메가3 비타민D 12박스+ 6박스 더 (총 18개월분 / 18박스)": "종근당건강 프로메가 알티지 오메가3 비타민D",
    "[락토핏] (방송에서만) 락토핏 맥스19 유산균 12통 (24개월분)": "락토핏 맥스19 유산균",
    "[방송에서만]김오곤 프리미엄 마가목 흑염소 진액 2박스+1박스(3개월분)": "김오곤 프리미엄 마가목 흑염소 진액",
    "[방송에서만]지니라이프 듀얼 맥스 콘드로이친1200MBP 6+6박스": "지니라이프 듀얼 맥스 콘드로이친1200MBP",
    "[방송에서만][리뉴얼]164 루테인지아잔틴GR 15개월분": "164 루테인지아잔틴GR",
    "여에스더 리포좀 글루타치온 다이렉트 울트라9x 13박스 (25년 최신상) + 맥주효모 2박스": "여에스더 리포좀 글루타치온 다이렉트 울트라9X",
    "[NEW]하이뮨 프로틴 밸런스 면역케어 12캔+칼슘마그네슘 2박스": "하이뮨 프로틴 밸런스 면역케어",
    "에버콜라겐 레티놀A 19병 (76주분)": "에버콜라겐 레티놀A",
    "[72팩]하루약콩 두유": "하루약콩 두유",
    "양파껍질차 500ml x 80병": "양파껍질차",
    "[삼육두유]검은콩과볶은귀리48팩+검은콩호두아몬드32팩+검은콩흑임자32팩(총112팩)": "삼육두유 검은콩 혼합세트",
    "뉴밋 유기농 블루베리 착즙 100 4박스(총 56포)": "뉴밋 유기농 블루베리 착즙 100",
    "닥터린 하이퍼셀 대마종자유 12박스(12개월)+방송에서만 6박스(6개월) 총 18박스": "닥터린 하이퍼셀 대마종자유",
    "[현대단독] 패밀리세트 비에날씬 프로 12박스+비에날퀸 1박스+비에날씬 플러스 1박스": "비에날씬 프로 패밀리세트",
    "대원제약 혈당파이터 12개월분": "대원제약 혈당파이터",
    "(80개) 카무트 브랜드밀 담은 하루 견과바(20개X4박스)": "카무트 브랜드밀 담은 하루 견과바",
    "[방송에서만 4박스 더] 프리미엄 윤방부박사의 넘버원 알부민 당제로 4+4 총 8박스": "프리미엄 윤방부박사의 넘버원 알부민 당제로",
    "[베지밀] *담백한 베지밀A 검은콩두유 190ml*80팩": "담백한 베지밀A 검은콩두유",
    "★전고객 5만원★ 비에날 씬 프로 9개월 + 롯데상품권 5만원 + 프로틴 14포 + 텀블러": "비에날 씬 프로",
    "한미사이언스 완 전두유 더진한 렌틸콩 무가당 190㎖ 80팩": "한미사이언스 완 전두유 더진한 렌틸콩 무가당",
}

FOCUS_KEYWORD_OVERRIDES = {
    "방송에서만 반값세일+복부마사지기 골드 파로효소 캡슐레이션": "파로효소",
    "비에날씬프로": "비에날씬",
    "지니라이프 듀얼 맥스 콘드로이친1200MBP": "콘드로이친 MBP",
    "여에스더 리포좀글루타치온 울트라 9X": "리포좀 글루타치온",
    "여에스더 리포좀 글루타치온 울트라9X": "리포좀 글루타치온",
    "BNR17 다이어트 유산균 비에날씬": "BNR17 유산균",
    "위&장 매스틱 유산균": "매스틱 유산균",
    "콘드로이친 킹 1200 12박스에 추가구성 아스타루지": "콘드로이친 킹",
    "비에날씬(BNR17)유산균": "비에날씬 유산균",
    "비에날씬 프로틴": "비에날씬 프로틴",
    "뉴트리디데이 시그니처 콜라겐 비오틴": "콜라겐 비오틴",
    "에버콜라겐 레티놀 A": "레티놀 A",
    "윤방부박사의 넘버원 알부민 당제로": "알부민 당제로",
    "닥터 픽 생유산균": "생유산균",
    "닥터린 발아 카무트® 브랜드밀 효소 S": "카무트 효소",
    "유기농 레몬즙 순수100": "레몬즙",
    "주영엔에스 단백질 저분자 유청펩타이드 HW-3": "유청펩타이드 HW-3",
}


@dataclass(slots=True)
class CollectionResult:
    reference_date: str
    dates: list[str]
    rows: list[list[str]]
    updated_at: str

    @property
    def start_date(self) -> str:
        return self.dates[0]

    @property
    def end_date(self) -> str:
        return self.dates[-1]

    @property
    def channel_names(self) -> list[str]:
        return sorted({row[1] for row in self.rows})

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": CACHE_VERSION,
            "reference_date": self.reference_date,
            "dates": self.dates,
            "rows": self.rows,
            "updated_at": self.updated_at,
        }


def resolve_reference_date(reference_date: date | None = None) -> date:
    return reference_date or date.today()


def build_collection_dates(reference_date: date | None = None) -> list[str]:
    current_date = resolve_reference_date(reference_date)
    start_date = current_date - timedelta(days=COLLECTION_PAST_DAYS)
    end_date = current_date + timedelta(days=COLLECTION_FUTURE_DAYS)
    total_days = (end_date - start_date).days + 1
    return [(start_date + timedelta(days=index)).isoformat() for index in range(total_days)]


def format_korean_date_range(dates: list[str]) -> str:
    start_date = date.fromisoformat(dates[0])
    end_date = date.fromisoformat(dates[-1])

    if start_date.year == end_date.year and start_date.month == end_date.month:
        return f"{start_date.year}년 {start_date.month}월 {start_date.day}일~{end_date.day}일"
    if start_date.year == end_date.year:
        return f"{start_date.year}년 {start_date.month}월 {start_date.day}일~{end_date.month}월 {end_date.day}일"
    return (
        f"{start_date.year}년 {start_date.month}월 {start_date.day}일~"
        f"{end_date.year}년 {end_date.month}월 {end_date.day}일"
    )


def load_collection(reference_date: date | None = None, prefer_cache: bool = True) -> CollectionResult:
    expected_dates = build_collection_dates(reference_date)
    if prefer_cache:
        cached_result = load_cached_collection(expected_dates)
        if cached_result is not None:
            return cached_result

    return collect_collection(reference_date)


def load_cached_collection(expected_dates: list[str]) -> CollectionResult | None:
    if not CACHE_PATH.exists():
        return None

    try:
        payload = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None

    if payload.get("version") != CACHE_VERSION:
        return None

    if payload.get("dates") != expected_dates:
        return None

    rows = payload.get("rows")
    if not isinstance(rows, list):
        return None

    return CollectionResult(
        reference_date=str(payload.get("reference_date") or expected_dates[-3]),
        dates=expected_dates,
        rows=[[str(cell) for cell in row] for row in rows],
        updated_at=str(payload.get("updated_at") or ""),
    )


def collect_collection(reference_date: date | None = None) -> CollectionResult:
    current_date = resolve_reference_date(reference_date)
    dates = build_collection_dates(current_date)
    rows: list[list[str]] = []
    seen_keys: set[tuple[str, str, str, str]] = set()

    for broadcast_date in dates:
        for channel_code, channel_name in CHANNELS.items():
            schedule = fetch_schedule(channel_code, broadcast_date)
            for product, entry in iter_schedule_products(schedule):
                if not is_health_product(product):
                    continue

                start_time = format_time(product.get("start_datetime") or entry.get("start_datetime"))
                dedup_key = (
                    broadcast_date,
                    channel_code,
                    start_time,
                    str(product.get("pdid") or product.get("pid") or product.get("name") or ""),
                )
                if dedup_key in seen_keys:
                    continue

                seen_keys.add(dedup_key)
                rows.append(build_row(broadcast_date, channel_name, product, entry))

    rows.sort(key=lambda row: (row[0], row[2] if row[2] != "-" else "99:99", row[1], row[3]))

    result = CollectionResult(
        reference_date=current_date.isoformat(),
        dates=dates,
        rows=rows,
        updated_at=datetime.now().isoformat(timespec="seconds"),
    )
    save_collection(result)
    return result


def save_collection(result: CollectionResult) -> None:
    CACHE_PATH.write_text(
        json.dumps(result.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def fetch_schedule(channel_code: str, broadcast_date: str, retries: int = 3) -> dict[str, Any]:
    query = urllib.parse.urlencode({"tv_channel": channel_code, "date": broadcast_date})
    request = urllib.request.Request(
        f"{API_URL}?{query}",
        headers={"User-Agent": "Mozilla/5.0"},
    )

    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception as error:  # pragma: no cover - network retry branch
            last_error = error
            if attempt == retries:
                break
            time.sleep(attempt)

    raise RuntimeError(f"{channel_code} {broadcast_date} 편성 조회 실패") from last_error


def iter_schedule_products(schedule: dict[str, Any]) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    rows: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for block_name in ("past", "live", "future", "live_ad"):
        for entry in schedule.get(block_name) or []:
            for product in entry.get("products") or []:
                rows.append((product, entry))
    return rows


def build_row(
    broadcast_date: str,
    channel_name: str,
    product: dict[str, Any],
    entry: dict[str, Any],
) -> list[str]:
    product_name = normalize_product_name(str(product.get("name") or "").strip())
    health_category = classify_health_category(product)
    keywords = ", ".join(extract_keywords(product, health_category))
    focus_keyword = extract_focus_keyword(product_name, keywords)
    return [
        broadcast_date,
        channel_name,
        format_time(product.get("start_datetime") or entry.get("start_datetime")),
        product_name,
        health_category,
        format_price(product),
        keywords,
        focus_keyword,
    ]


def normalize_product_name(name: str) -> str:
    if name in PRODUCT_NAME_OVERRIDES:
        return PRODUCT_NAME_OVERRIDES[name]

    normalized_name = name

    while True:
        cleaned_name = re.sub(r"^(?:\[[^\]]+\]|\([^)]*\)|★[^★]+★|\*[^*]+\*)\s*", "", normalized_name).strip()
        if cleaned_name == normalized_name:
            break
        normalized_name = cleaned_name

    normalized_name = re.sub(r"\s+\+\s+.*$", "", normalized_name)
    normalized_name = re.sub(r"\s*\(총[^)]*\)", "", normalized_name)
    normalized_name = re.sub(r"\s*\([^)]*(?:개월분|박스|포|팩|병|캔|개)[^)]*\)", "", normalized_name)
    normalized_name = re.sub(r"\s*(총\s*)?\d+\s*(?:개월분|개월|주분|박스|통|포|팩|병|캔|개)\b.*$", "", normalized_name)
    normalized_name = re.sub(r"\s*\d+\s*(?:ml|㎖|g|kg)\s*(?:x|\*)\s*\d+\s*(?:병|팩|포|개)\b.*$", "", normalized_name, flags=re.IGNORECASE)
    normalized_name = re.sub(r"[\*\u2605\u2606]+", "", normalized_name)
    normalized_name = re.sub(r"\s+", " ", normalized_name)
    return normalized_name.strip().rstrip("+").strip()


def is_health_product(product: dict[str, Any]) -> bool:
    category2 = str(product.get("category2") or "").strip()
    category3 = str(product.get("category3") or "").strip()
    category_text = build_category_text(product)
    combined_text = build_search_text(product)

    if category2 in ALLOWED_CATEGORY2 or category3 in ALLOWED_CATEGORY3:
        return True

    if any(term in category_text for term in EXCLUDED_CATEGORY_TERMS):
        return False

    return any(term in combined_text for term in INCLUDE_TERMS)


def build_search_text(product: dict[str, Any]) -> str:
    parts = [
        product.get("name"),
        product.get("simple_name"),
        product.get("brand"),
    ]
    return " ".join(str(part or "") for part in parts).lower()


def build_category_text(product: dict[str, Any]) -> str:
    parts = [
        product.get("category1"),
        product.get("category2"),
        product.get("category3"),
    ]
    return " ".join(str(part or "") for part in parts).lower()


def classify_health_category(product: dict[str, Any]) -> str:
    combined_text = build_search_text(product)

    for category_name, triggers in CATEGORY_RULES:
        if any(trigger in combined_text for trigger in triggers):
            return category_name

    return "기타 건강식품"


def extract_keywords(product: dict[str, Any], health_category: str) -> list[str]:
    combined_text = build_search_text(product)
    keywords: list[str] = []

    for canonical, triggers in KEYWORD_RULES:
        if any(trigger in combined_text for trigger in triggers):
            keywords.append(canonical)
        if len(keywords) == 4:
            return keywords

    if keywords:
        return keywords

    fallback_keywords = [token.strip() for token in re.split(r"[/,]", health_category) if token.strip()]
    if fallback_keywords:
        return fallback_keywords[:3]

    category_fallback = str(product.get("category3") or product.get("category2") or "건강식품").strip()
    return [category_fallback]


def extract_focus_keyword(product_name: str, keywords: str) -> str:
    if product_name in FOCUS_KEYWORD_OVERRIDES:
        return FOCUS_KEYWORD_OVERRIDES[product_name]

    keyword_parts = [part.strip() for part in keywords.split(",") if part.strip()]
    if keyword_parts:
        return keyword_parts[0]

    return product_name


def format_time(value: Any) -> str:
    if not value:
        return "-"

    time_value = str(value)
    try:
        return datetime.fromisoformat(time_value).strftime("%H:%M")
    except ValueError:
        if len(time_value) >= 16 and time_value[10] == "T":
            return time_value[11:16]
        return "-"


def format_price(product: dict[str, Any]) -> str:
    price_info = product.get("price_info") or {}
    candidates = [
        price_info.get("max_discount_price"),
        product.get("sale_price"),
        price_info.get("sale_price"),
        product.get("price"),
        price_info.get("price"),
        product.get("launching_price"),
    ]

    for candidate in candidates:
        price = to_positive_int(candidate)
        if price is not None and price > 0:
            return f"{price:,}"

    return ""


def to_positive_int(value: Any) -> int | None:
    if value in (None, "", 0):
        return None

    try:
        parsed = int(float(str(value).replace(",", "")))
    except ValueError:
        return None

    return parsed if parsed > 0 else None

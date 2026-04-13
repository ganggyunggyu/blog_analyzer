# ruff: noqa: E402
"""홈쇼핑 건강식품 키워드 요약 → Google Sheets 추가 탭"""

from __future__ import annotations

import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import gspread
from google.oauth2.service_account import Credentials

from export_to_sheet import PRIVATE_KEY, SCOPES, SERVICE_ACCOUNT_EMAIL
from scripts.homeshopping_schedule_data import (
    SPREADSHEET_ID,
    SUMMARY_WORKSHEET_TITLE,
    format_korean_date_range,
    load_collection,
)

KEYWORD_MAP = {
    "글루타치온": ["글루타치온", "항산화", "미백", "에스더포뮬러"],
    "블루베리": ["블루베리", "안토시아닌", "눈건강", "퓨레", "착즙"],
    "알부민/단백질": ["알부민", "단백질", "산양유", "백세알부민"],
    "유산균": ["유산균", "프로바이오틱스", "장건강", "락토핏", "구강유산균", "bnr17"],
    "콜라겐": ["콜라겐", "비오틴", "레티놀", "피부"],
    "효소(카무트)": ["카무트", "효소", "파로", "소화"],
    "폴리코사놀": ["폴리코사놀", "콜레스테롤", "혈관"],
    "흑염소": ["흑염소", "보양식", "기력", "홍삼"],
    "클로렐라": ["클로렐라", "해독", "디톡스", "엽록소"],
    "비타민": ["비타민", "멀티비타민", "종합비타민", "비타민c", "비타민k2", "무기질"],
    "관절/뼈건강": ["콘드로이친", "관절", "mbp", "뼈건강", "뼈엔", "칼슘"],
    "다이어트": ["다이어트", "이소비텍신", "와사비", "체지방"],
    "두뇌건강": ["두뇌", "포스파티딜세린", "인지기능", "닥터ps", "ps진"],
    "칼슘/두유": ["칼슘", "두유", "검은콩"],
    "생식": ["생식", "라이프밀", "식사대용", "선식"],
    "오메가3": ["오메가3", "헤링오일", "혈행"],
    "코엔자임Q10": ["코엔자임", "q10", "심혈관"],
    "루테인": ["루테인", "지아잔틴", "눈건강"],
    "레몬/비타민C": ["레몬", "비타민c"],
    "도라지": ["도라지", "기관지", "호흡기"],
    "클렌즈": ["클렌즈", "디톡스", "cca"],
    "오르조": ["오르조", "건강음료"],
    "면역": ["면역", "오쏘몰"],
    "기타": [],
}

PRODUCT_SHORT = {
    "장면역유산균 듀얼스틱 프로+프리 200억 12박스": "듀얼스틱 프로",
    "장면역유산균 듀얼스틱 프로+프리 200억": "듀얼스틱 프로",
    "팔도강산 흑염소탕": "팔도강산 흑염소탕",
    "베리엔하우스 블루베리 퓨레 9+3박스": "베리엔하우스 블루베리 퓨레",
    "퓨레바 퓨어 클로렐라100 10+2박스": "퓨레바 클로렐라100",
    "여에스더 리포좀글루타치온 울트라 9X": "여에스더 글루타치온",
    "여에스더 리포좀글루타치온 울트라 9X 12+1박스+맥주효모2박스": "여에스더 글루타치온",
    "여에스더 리포좀 글루타치온 울트라": "여에스더 글루타치온",
    "여에스더 글루타치온 울트라 9X 13박스": "여에스더 글루타치온",
    "여에스더 글루타치온 울트라 9X 13박스+맥주효모": "여에스더 글루타치온",
    "황성주 박사의 라이프밀 4박스": "황성주 라이프밀",
    "황성주 박사의 라이프밀 4박스+흔들컵1": "황성주 라이프밀",
    "황성주 박사의 1일1생식 라이프밀 4박스+흔들컵 1개": "황성주 라이프밀",
    "오한진의 백세알부민 1박스": "오한진 백세알부민",
    "오한진의 백세알부민": "오한진 백세알부민",
    "프리미엄 오한진의 백세알부민 6박스": "오한진 백세알부민",
    "윤방부박사 넘버원 알부민 당제로 8박스": "윤방부 알부민 당제로",
    "윤방부박사 알부민 당제로 1박스": "윤방부 알부민 당제로",
    "홀베리 와사비 다이어트 이소비텍신": "홀베리 이소비텍신",
    "와사비 다이어트 이소비텍신 24주분": "홀베리 이소비텍신",
    "종근당건강 락토핏 코어맥스 20개월분": "종근당 락토핏 코어맥스",
    "대원제약 리포좀 알부민킹": "대원제약 알부민킹",
    "대원제약 리포좀 알부민킹 7박스": "대원제약 알부민킹",
    "레이델 폴리코사놀5": "레이델 폴리코사놀5",
    "레이델 폴리코사놀 더블액션 12박스": "레이델 폴리코사놀 더블액션",
    "그레이스 블루베리 퓨레 100 9박스": "그레이스 블루베리 퓨레",
    "리즐온 유기농 블루베리스틱 12박스": "리즐온 블루베리스틱",
    "홀랜드앤바렛 종합 비타민 앤 무기질": "홀랜드앤바렛 종합비타민",
    "홀랜드앤바렛 종합 비타민 12개월분": "홀랜드앤바렛 종합비타민",
    "두뇌엔 닥터PS 맥스 3박스": "두뇌엔 닥터PS 맥스",
    "두뇌엔 PS진 8박스": "두뇌엔 PS진",
    "닥터파이토 덴티백 PRO 구강유산균M18": "닥터파이토 구강유산균",
    "이경제 흑염소진액 眞 8+1박스": "이경제 흑염소진액",
    "이경제 흑염소진액 眞 4박스": "이경제 흑염소진액",
    "이경제 흑염소진액": "이경제 흑염소진액",
    "관절엔 콘드로이친 1200 12박스": "관절엔 콘드로이친1200",
    "관절엔 콘드로이친 1200 12박스+오메가3": "관절엔 콘드로이친+오메가3",
    "바디마인 산양유단백질100 12통": "바디마인 산양유단백질",
    "골드카무트 브랜드밀효소 16박스+파로 8봉": "골드카무트 효소",
    "골드카무트 효소 12박스": "골드카무트 효소",
    "골드카무트 효소 11박스": "골드카무트 효소",
    "골드 카무트효소 12박스": "골드카무트 효소",
    "에버콜라겐 타임 레티놀A 12개월분": "에버콜라겐 타임",
    "뉴트리코어 코엔자임 Q10 맥스 12박스": "뉴트리코어 코엔자임Q10",
    "대원제약 콘드로이친 킹 1200 12박스+칼마 2박스": "대원 콘드로이친킹+칼마",
    "뉴트리디데이 콜라겐 글루타치온 16개월분": "뉴트리디데이 콜라겐글루타치온",
    "바이오리브 100억유산균 12개월분": "바이오리브 100억유산균",
    "다이어트 유산균 BNR17 비에날씬프로 6박스": "비에날씬프로 BNR17",
    "아침엔 클렌즈 유기농 CCA주스 8박스": "아침엔 클렌즈 CCA",
    "뼈엔 엠비피 MBP 12개월분": "뼈엔 MBP",
    "프롬바이오 헤링오일 100 12박스": "프롬바이오 헤링오일",
    "뉴트리코어 하이퍼셀 비타민K2 18박스": "뉴트리코어 비타민K2",
    "김오곤 원장의 한방 다이어트환 5박스": "김오곤 한방다이어트환",
}


def shorten_product(name: str) -> str:
    import re

    shortened_name = name
    while True:
        cleaned_name = re.sub(r"^(?:\[[^\]]+\]|\([^)]*\)|★[^★]+★)\s*", "", shortened_name).strip()
        if cleaned_name == shortened_name:
            break
        shortened_name = cleaned_name

    shortened_name = re.sub(r"\d+\+?\d*\s*박스.*$", "", shortened_name)
    shortened_name = re.sub(r"\d+\s*(개월분|포|팩|통|병|주분|정).*$", "", shortened_name)
    shortened_name = re.sub(r"\(총\s*\d+.*?\)", "", shortened_name)
    shortened_name = re.sub(r"\d+,\d+원?", "", shortened_name)
    shortened_name = re.sub(r"\d+\s*(g|kg|ml|mlX|gX)\d*", "", shortened_name)
    shortened_name = re.sub(r"[\*\u2605\u2606]+", "", shortened_name)
    shortened_name = re.sub(r"\s+", " ", shortened_name)
    shortened_name = shortened_name.strip().rstrip("+").strip()
    return shortened_name[:25].strip() if len(shortened_name) > 25 else shortened_name


def get_short_name(product: str) -> str:
    if product in PRODUCT_SHORT:
        return PRODUCT_SHORT[product]
    return shorten_product(product)


def classify_item(item_name: str, item_keywords: str) -> str:
    combined_text = f"{item_name} {item_keywords}".lower()
    scores: dict[str, int] = {}
    for category_name, keywords in KEYWORD_MAP.items():
        score = sum(1 for keyword in keywords if keyword.lower() in combined_text)
        if score > 0:
            scores[category_name] = score
    if scores:
        return max(scores, key=scores.get)
    return "기타"


def get_client() -> gspread.Client:
    creds_info = {
        "type": "service_account",
        "client_email": SERVICE_ACCOUNT_EMAIL,
        "private_key": PRIVATE_KEY,
        "token_uri": "https://oauth2.googleapis.com/token",
    }
    creds = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
    return gspread.authorize(creds)


def main() -> None:
    collection = load_collection()
    data = collection.rows

    keyword_count: Counter[str] = Counter()
    keyword_channels: dict[str, set[str]] = defaultdict(set)
    keyword_dates: dict[str, set[str]] = defaultdict(set)
    keyword_products: dict[str, Counter[str]] = defaultdict(Counter)
    keyword_prices: dict[str, list[int]] = defaultdict(list)

    for row in data:
        date_value, channel, _time, product, _category, price, keywords, _focus_keyword = row
        keyword_name = classify_item(product, keywords)
        keyword_count[keyword_name] += 1
        keyword_channels[keyword_name].add(channel)
        keyword_dates[keyword_name].add(date_value)
        keyword_products[keyword_name][get_short_name(product)] += 1
        if price:
            try:
                keyword_prices[keyword_name].append(int(price.replace(",", "").replace("원", "")))
            except ValueError:
                continue

    headers = ["키워드", "편성횟수", "판매채널", "방송일수", "가격대", "대표상품(축약)"]
    rows: list[list[str | int]] = []
    for keyword_name, count in keyword_count.most_common():
        channels = ", ".join(sorted(keyword_channels[keyword_name]))
        date_count = len(keyword_dates[keyword_name])
        prices = keyword_prices[keyword_name]
        price_range = f"{min(prices):,}~{max(prices):,}원" if prices else "-"
        products = " / ".join(product for product, _ in keyword_products[keyword_name].most_common(3))
        rows.append([keyword_name, count, channels, f"{date_count}일", price_range, products])

    gc = get_client()
    spreadsheet = gc.open_by_key(SPREADSHEET_ID)

    try:
        existing = spreadsheet.worksheet(SUMMARY_WORKSHEET_TITLE)
        spreadsheet.del_worksheet(existing)
    except gspread.WorksheetNotFound:
        pass

    worksheet = spreadsheet.add_worksheet(title=SUMMARY_WORKSHEET_TITLE, rows=len(rows) + 5, cols=10)
    print(f"{SUMMARY_WORKSHEET_TITLE} 탭 생성 완료 (gid={worksheet.id})")

    worksheet.update(
        range_name="A1",
        values=[[f"홈쇼핑 건강식품 키워드 요약 ({format_korean_date_range(collection.dates)})"]],
    )
    worksheet.update(
        range_name="A2",
        values=[[
            f"총 편성 {len(data)}건 / 키워드 {len(rows)}개 / 채널 {len(collection.channel_names)}개"
        ]],
    )
    worksheet.update(range_name="A4", values=[headers] + rows)
    print(f"키워드 {len(rows)}개 입력 완료")

    sheet_id = worksheet.id
    format_requests = [
        {
            "repeatCell": {
                "range": {"sheetId": sheet_id, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 0, "endColumnIndex": 6},
                "cell": {
                    "userEnteredFormat": {
                        "textFormat": {"bold": True, "fontSize": 14},
                        "backgroundColor": {"red": 0.15, "green": 0.3, "blue": 0.6},
                    }
                },
                "fields": "userEnteredFormat(textFormat,backgroundColor)",
            }
        },
        {
            "repeatCell": {
                "range": {"sheetId": sheet_id, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 0, "endColumnIndex": 6},
                "cell": {
                    "userEnteredFormat": {
                        "textFormat": {"bold": True, "fontSize": 14, "foregroundColor": {"red": 1, "green": 1, "blue": 1}}
                    }
                },
                "fields": "userEnteredFormat.textFormat",
            }
        },
        {
            "repeatCell": {
                "range": {"sheetId": sheet_id, "startRowIndex": 3, "endRowIndex": 4, "startColumnIndex": 0, "endColumnIndex": 6},
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": {"red": 0.2, "green": 0.4, "blue": 0.7},
                        "horizontalAlignment": "CENTER",
                        "textFormat": {"bold": True, "fontSize": 11, "foregroundColor": {"red": 1, "green": 1, "blue": 1}},
                    }
                },
                "fields": "userEnteredFormat(backgroundColor,horizontalAlignment,textFormat)",
            }
        },
        *[
            {
                "repeatCell": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": 4 + index,
                        "endRowIndex": 5 + index,
                        "startColumnIndex": 0,
                        "endColumnIndex": 6,
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": (
                                {"red": 0.93, "green": 0.93, "blue": 1.0}
                                if index % 2 == 0
                                else {"red": 1, "green": 1, "blue": 1}
                            )
                        }
                    },
                    "fields": "userEnteredFormat.backgroundColor",
                }
            }
            for index in range(len(rows))
        ],
    ]

    col_widths = [140, 80, 280, 80, 160, 350]
    width_requests = [
        {
            "updateDimensionProperties": {
                "range": {"sheetId": sheet_id, "dimension": "COLUMNS", "startIndex": index, "endIndex": index + 1},
                "properties": {"pixelSize": width},
                "fields": "pixelSize",
            }
        }
        for index, width in enumerate(col_widths)
    ]

    merge_requests = [
        {
            "mergeCells": {
                "range": {"sheetId": sheet_id, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 0, "endColumnIndex": 6},
                "mergeType": "MERGE_ALL",
            }
        },
        {
            "mergeCells": {
                "range": {"sheetId": sheet_id, "startRowIndex": 1, "endRowIndex": 2, "startColumnIndex": 0, "endColumnIndex": 6},
                "mergeType": "MERGE_ALL",
            }
        },
    ]

    freeze_request = [
        {
            "updateSheetProperties": {
                "properties": {"sheetId": sheet_id, "gridProperties": {"frozenRowCount": 4}},
                "fields": "gridProperties.frozenRowCount",
            }
        }
    ]

    spreadsheet.batch_update({"requests": merge_requests + format_requests + width_requests + freeze_request})
    print("서식 적용 완료")
    print(f"\n시트 URL: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit#gid={sheet_id}")


if __name__ == "__main__":
    main()

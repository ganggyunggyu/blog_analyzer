# ruff: noqa: E402
"""홈쇼핑 건강식품 편성표 → Google Sheets 내보내기"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import gspread
from google.oauth2.service_account import Credentials

from export_to_sheet import PRIVATE_KEY, SCOPES, SERVICE_ACCOUNT_EMAIL
from scripts.homeshopping_schedule_data import (
    HEADERS,
    MAIN_WORKSHEET_GID,
    SPREADSHEET_ID,
    load_collection,
)


def get_client() -> gspread.Client:
    creds_info = {
        "type": "service_account",
        "client_email": SERVICE_ACCOUNT_EMAIL,
        "private_key": PRIVATE_KEY,
        "token_uri": "https://oauth2.googleapis.com/token",
    }
    creds = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
    return gspread.authorize(creds)


def find_worksheet(spreadsheet: gspread.Spreadsheet) -> gspread.Worksheet:
    for worksheet in spreadsheet.worksheets():
        if str(worksheet.id) == MAIN_WORKSHEET_GID:
            return worksheet
    raise ValueError(f"gid={MAIN_WORKSHEET_GID} 시트를 찾을 수 없음")


def main() -> None:
    collection = load_collection()
    data = collection.rows

    gc = get_client()
    spreadsheet = gc.open_by_key(SPREADSHEET_ID)
    worksheet = find_worksheet(spreadsheet)

    print(f"시트 연결 완료: {worksheet.title} (gid={worksheet.id})")
    print(
        "수집 범위: "
        f"{collection.start_date}~{collection.end_date} / "
        f"{len(collection.channel_names)}채널 / {len(data)}건"
    )

    worksheet.clear()
    all_rows = [HEADERS] + data
    worksheet.update(range_name="A1", values=all_rows)
    print(f"데이터 입력 완료: {len(data)}건 (헤더 포함 {len(all_rows)}행)")

    format_requests = [
        {
            "repeatCell": {
                "range": {
                    "sheetId": int(MAIN_WORKSHEET_GID),
                    "startRowIndex": 0,
                    "endRowIndex": 1,
                    "startColumnIndex": 0,
                    "endColumnIndex": 7,
                },
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": {"red": 0.2, "green": 0.4, "blue": 0.7},
                        "horizontalAlignment": "CENTER",
                        "textFormat": {
                            "bold": True,
                            "fontSize": 11,
                            "foregroundColor": {"red": 1, "green": 1, "blue": 1},
                        },
                    }
                },
                "fields": "userEnteredFormat(backgroundColor,horizontalAlignment,textFormat)",
            }
        }
    ]

    current_date = ""
    color_toggle = False
    block_start = 1
    for index, row in enumerate(data):
        if row[0] != current_date:
            if current_date and block_start < index + 1:
                background_color = (
                    {"red": 0.93, "green": 0.93, "blue": 1.0}
                    if color_toggle
                    else {"red": 1.0, "green": 1.0, "blue": 1.0}
                )
                format_requests.append(
                    {
                        "repeatCell": {
                            "range": {
                                "sheetId": int(MAIN_WORKSHEET_GID),
                                "startRowIndex": block_start,
                                "endRowIndex": index + 1,
                                "startColumnIndex": 0,
                                "endColumnIndex": 7,
                            },
                            "cell": {"userEnteredFormat": {"backgroundColor": background_color}},
                            "fields": "userEnteredFormat.backgroundColor",
                        }
                    }
                )
            current_date = row[0]
            color_toggle = not color_toggle
            block_start = index + 1

    if block_start <= len(data):
        background_color = (
            {"red": 0.93, "green": 0.93, "blue": 1.0}
            if color_toggle
            else {"red": 1.0, "green": 1.0, "blue": 1.0}
        )
        format_requests.append(
            {
                "repeatCell": {
                    "range": {
                        "sheetId": int(MAIN_WORKSHEET_GID),
                        "startRowIndex": block_start,
                        "endRowIndex": len(data) + 1,
                        "startColumnIndex": 0,
                        "endColumnIndex": 7,
                    },
                    "cell": {"userEnteredFormat": {"backgroundColor": background_color}},
                    "fields": "userEnteredFormat.backgroundColor",
                }
            }
        )

    requests = [
        {
            "updateDimensionProperties": {
                "range": {
                    "sheetId": int(MAIN_WORKSHEET_GID),
                    "dimension": "COLUMNS",
                    "startIndex": 0,
                    "endIndex": 1,
                },
                "properties": {"pixelSize": 110},
                "fields": "pixelSize",
            }
        },
        {
            "updateDimensionProperties": {
                "range": {
                    "sheetId": int(MAIN_WORKSHEET_GID),
                    "dimension": "COLUMNS",
                    "startIndex": 1,
                    "endIndex": 2,
                },
                "properties": {"pixelSize": 160},
                "fields": "pixelSize",
            }
        },
        {
            "updateDimensionProperties": {
                "range": {
                    "sheetId": int(MAIN_WORKSHEET_GID),
                    "dimension": "COLUMNS",
                    "startIndex": 2,
                    "endIndex": 3,
                },
                "properties": {"pixelSize": 90},
                "fields": "pixelSize",
            }
        },
        {
            "updateDimensionProperties": {
                "range": {
                    "sheetId": int(MAIN_WORKSHEET_GID),
                    "dimension": "COLUMNS",
                    "startIndex": 3,
                    "endIndex": 4,
                },
                "properties": {"pixelSize": 350},
                "fields": "pixelSize",
            }
        },
        {
            "updateDimensionProperties": {
                "range": {
                    "sheetId": int(MAIN_WORKSHEET_GID),
                    "dimension": "COLUMNS",
                    "startIndex": 4,
                    "endIndex": 5,
                },
                "properties": {"pixelSize": 160},
                "fields": "pixelSize",
            }
        },
        {
            "updateDimensionProperties": {
                "range": {
                    "sheetId": int(MAIN_WORKSHEET_GID),
                    "dimension": "COLUMNS",
                    "startIndex": 5,
                    "endIndex": 6,
                },
                "properties": {"pixelSize": 100},
                "fields": "pixelSize",
            }
        },
        {
            "updateDimensionProperties": {
                "range": {
                    "sheetId": int(MAIN_WORKSHEET_GID),
                    "dimension": "COLUMNS",
                    "startIndex": 6,
                    "endIndex": 7,
                },
                "properties": {"pixelSize": 250},
                "fields": "pixelSize",
            }
        },
        {
            "updateSheetProperties": {
                "properties": {
                    "sheetId": int(MAIN_WORKSHEET_GID),
                    "gridProperties": {"frozenRowCount": 1},
                },
                "fields": "gridProperties.frozenRowCount",
            }
        },
    ]

    spreadsheet.batch_update({"requests": format_requests + requests})
    print("서식 적용 완료 (헤더 색상, 교차 배경색, 열너비, 1행 고정)")
    print(f"\n시트 URL: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit#gid={MAIN_WORKSHEET_GID}")


if __name__ == "__main__":
    main()

# ruff: noqa: E402

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import gspread
from google.oauth2.service_account import Credentials

from export_to_sheet import PRIVATE_KEY, SCOPES, SERVICE_ACCOUNT_EMAIL


DEFAULT_HEADERS = [
    "keyword",
    "target_keyword",
    "category",
    "keyword_family",
    "model_name",
    "title_generation_strategy",
    "live_view_titles",
    "intent_prompt",
    "title_prompt",
    "manuscript_prompt",
    "title",
    "manuscript",
    "exact_live_view_match",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("sheet_rows_json")
    parser.add_argument("spreadsheet_id")
    parser.add_argument("--worksheet-index", type=int, default=0)
    parser.add_argument("--worksheet-gid")
    parser.add_argument("--worksheet-title")
    return parser.parse_args()


def build_headers(rows: list[dict[str, object]]) -> list[str]:
    if not rows:
        return DEFAULT_HEADERS

    ordered_headers: list[str] = []
    seen: set[str] = set()

    for header in DEFAULT_HEADERS:
        if any(header in row for row in rows):
            ordered_headers.append(header)
            seen.add(header)

    for row in rows:
        for key in row:
            if key in seen:
                continue
            ordered_headers.append(key)
            seen.add(key)

    return ordered_headers


def get_worksheet(
    spreadsheet: gspread.Spreadsheet,
    worksheet_index: int,
    worksheet_gid: str | None,
    worksheet_title: str | None,
) -> gspread.Worksheet:
    if worksheet_gid:
        for worksheet in spreadsheet.worksheets():
            if str(worksheet.id) == str(worksheet_gid):
                return worksheet
        raise ValueError(f"gid={worksheet_gid} 에 해당하는 워크시트를 찾을 수 없습니다.")

    if worksheet_title:
        return spreadsheet.worksheet(worksheet_title)

    return spreadsheet.get_worksheet(worksheet_index)


def column_index_to_label(index: int) -> str:
    label = ""
    current = index

    while current > 0:
        current, remainder = divmod(current - 1, 26)
        label = chr(65 + remainder) + label

    return label


def main() -> None:
    args = parse_args()
    rows = json.loads(Path(args.sheet_rows_json).read_text(encoding="utf-8"))
    creds_info = {
        "type": "service_account",
        "client_email": SERVICE_ACCOUNT_EMAIL,
        "private_key": PRIVATE_KEY,
        "token_uri": "https://oauth2.googleapis.com/token",
    }
    creds = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
    gc = gspread.authorize(creds)
    spreadsheet = gc.open_by_key(args.spreadsheet_id)
    worksheet = get_worksheet(
        spreadsheet=spreadsheet,
        worksheet_index=args.worksheet_index,
        worksheet_gid=args.worksheet_gid,
        worksheet_title=args.worksheet_title,
    )
    headers = build_headers(rows)
    end_col = column_index_to_label(len(headers))

    worksheet.clear()
    worksheet.update(f"A1:{end_col}1", [headers], value_input_option="RAW")

    sheet_values = [
        [row.get(header, "") for header in headers]
        for row in rows
    ]

    if sheet_values:
        worksheet.update(
            f"A2:{end_col}{len(sheet_values) + 1}",
            sheet_values,
            value_input_option="RAW",
        )

    print(f"SPREADSHEET_TITLE={spreadsheet.title}")
    print(f"WORKSHEET_TITLE={worksheet.title}")
    print(f"WORKSHEET_GID={worksheet.id}")
    print(f"HEADER_COUNT={len(headers)}")
    print(f"ROW_COUNT={len(sheet_values)}")


if __name__ == "__main__":
    main()

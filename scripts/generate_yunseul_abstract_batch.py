# ruff: noqa: E402

from __future__ import annotations

import argparse
import html
import json
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from llm import blog_filler_diet_v2_service as diet_v2_service

ABSTRACT_KEYWORDS: tuple[str, ...] = (
    "마운자로",
    "디에타민",
    "나비약",
    "위고비 효과",
    "마운자로 처방",
    "마운자로 효과",
    "위고비 알약",
    "GLP-1 다이어트",
    "베르베린",
    "베르베린 효능",
    "식욕억제제",
    "브로멜라인",
    "위고비",
    "마운자로 용량",
    "위고비 처방",
    "위고비 후기",
    "마운자로 알약",
    "프로페시아",
    "아보다트",
    "판시딜",
    "프로페그라",
    "비아그라 처방",
    "비아그라 효과",
    "비아그라 부작용",
    "비아그라 복용법",
    "혈당 스파이크",
    "혈당정상수치",
    "식후2시간혈당",
    "당뇨 초기증상",
    "당뇨에좋은음식",
    "혈당 스파이크 증상",
    "내장지방",
    "셀룰라이트",
)

YUNSEUL_KEYWORDS: tuple[str, ...] = (
    "무지외반증치료",
    "무지외반증",
    "무지외반증 운동",
    "무지외반증 교정",
    "거북목",
    "거북목 교정",
    "목디스크",
    "일자목",
    "족저근막염 치료방법",
    "족저근막염",
    "족저근막염 치료",
    "발바닥통증",
    "변비약",
    "변비에 좋은음식",
    "변비",
    "변비직빵",
    "변비원인",
    "쾌변",
    "임산부변비",
    "배에가스빼는법",
    "변비해결",
    "변비증상",
)

KEYWORD_CATEGORY_MAP: dict[str, str] = {
    "무지외반증치료": "무지외반증",
    "무지외반증": "무지외반증",
    "무지외반증 운동": "무지외반증",
    "무지외반증 교정": "무지외반증",
    "족저근막염 치료방법": "족저근막염깔창",
    "족저근막염": "족저근막염깔창",
    "족저근막염 치료": "족저근막염깔창",
    "발바닥통증": "족저근막염깔창",
}

OUTPUT_SPREADSHEET_ID = "1HErumqLrDcuCDlxnAlbB9efClvIVPihZq12kcUQzP2k"
DEFAULT_OUTPUT_DIR = (
    Path("test-manuscripts")
    / "yunseul_abstract_batch"
    / datetime.now().strftime("%Y%m%d_%H%M%S")
)

REVIEW_BLOCK_PATTERN = re.compile(
    r'data-block-id="review/prs_template_v2_review_blog_rra_desk\.ts".*?<script>(.*?)</script>',
    re.S,
)
REVIEW_TITLE_PATTERN = re.compile(
    r'"title":"(.*?)","titleEllipsis":\d+.*?"type":"searchBasic"',
    re.S,
)
GENERIC_JSON_TITLE_PATTERN = re.compile(r'"title":"(.*?)"', re.S)
HTML_TITLE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(
        r'<a[^>]*class="title_link"[^>]*>\s*<strong[^>]*class="title"[^>]*>(.*?)</strong>',
        re.S,
    ),
    re.compile(
        r'<a[^>]*class="api_txt_lines total_tit"[^>]*>(.*?)</a>',
        re.S,
    ),
)
MARK_TAG_PATTERN = re.compile(r"</?mark>")
HTML_TAG_PATTERN = re.compile(r"<[^>]+>")
WHITESPACE_PATTERN = re.compile(r"\s+")
TITLE_NOISE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"네이버 검색"),
    re.compile(r"관련 브랜드 콘텐츠"),
    re.compile(r"네이버 클립"),
    re.compile(r"함께 많이 찾는"),
    re.compile(r"님의 블로그$"),
    re.compile(r"^\d{2,4}[─-]\d{3,4}[─-]\d{4}"),
    re.compile(r"(?:나무위키|위키백과|시사상식사전|화학백과|요리백과|의약품 정보|약학용어사전)"),
    re.compile(r"(?:대한화장품협회|위키백과 한국어)"),
    re.compile(r"(?:동영상)$"),
    re.compile(r"^\d{4}년\s+최고의"),
)
COMMENTY_TITLE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"저도"),
    re.compile(r"죄송"),
    re.compile(r"부탁"),
    re.compile(r"계신가요"),
    re.compile(r"가입합니다"),
    re.compile(r"해주세요"),
    re.compile(r"\^\^"),
    re.compile(r"ㅠ"),
    re.compile(r"ㅜ"),
    re.compile(r";;"),
    re.compile(r"궁금해요"),
    re.compile(r"걱정되는데"),
    re.compile(r"고민\s*중"),
    re.compile(r"\.\."),
    re.compile(r"[ㄷㅋㅎ]{2,}"),
)
NOISE_TITLES: set[str] = {"더보기", "이미지"}


def resolve_category(keyword: str) -> str:
    if keyword in KEYWORD_CATEGORY_MAP:
        return KEYWORD_CATEGORY_MAP[keyword]
    return "다이어트"


def decode_naver_text(raw_text: str) -> str:
    decoded = json.loads(f'"{raw_text}"')
    decoded = html.unescape(decoded)
    decoded = MARK_TAG_PATTERN.sub("", decoded)
    return WHITESPACE_PATTERN.sub(" ", decoded).strip()


def clean_html_fragment(raw_text: str) -> str:
    cleaned = html.unescape(raw_text)
    cleaned = HTML_TAG_PATTERN.sub("", cleaned)
    return WHITESPACE_PATTERN.sub(" ", cleaned).strip()


def fetch_naver_view_html(query: str) -> str:
    url = (
        "https://search.naver.com/search.naver"
        f"?where=view&sm=tab_jum&query={quote(query)}"
    )
    result = subprocess.run(
        ["curl", "-sL", url],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def build_query_clues(query: str) -> set[str]:
    clues: set[str] = set()
    normalized_query = diet_v2_service.normalize_title_match(query)
    if normalized_query:
        clues.add(normalized_query)
    for token in re.findall(r"[가-힣A-Za-z0-9\-]+", query):
        normalized_token = diet_v2_service.normalize_title_match(token)
        if len(normalized_token) >= 2:
            clues.add(normalized_token)
    return clues


def is_relevant_live_view_title(raw_title: str, title: str, query_clues: set[str]) -> bool:
    normalized_title = diet_v2_service.normalize_title_match(title)
    if not normalized_title or title in NOISE_TITLES:
        return False
    if len(title) < 6 or len(title) > 60:
        return False
    if any(pattern.search(title) for pattern in TITLE_NOISE_PATTERNS):
        return False
    if any(pattern.search(title) for pattern in COMMENTY_TITLE_PATTERNS):
        return False
    if "<mark>" in raw_title.lower():
        return True
    if not query_clues:
        return True
    return any(clue in normalized_title for clue in query_clues)


def extract_live_view_titles(html_text: str, query: str = "") -> list[str]:
    primary_candidates: list[tuple[str, str]] = []
    fallback_candidates: list[tuple[str, str]] = []
    review_blocks = REVIEW_BLOCK_PATTERN.findall(html_text)
    query_clues = build_query_clues(query)

    for review_block in review_blocks:
        for raw_title in REVIEW_TITLE_PATTERN.findall(review_block):
            primary_candidates.append(("json", raw_title))

    if not primary_candidates:
        for raw_title in REVIEW_TITLE_PATTERN.findall(html_text):
            primary_candidates.append(("json", raw_title))

    for raw_title in GENERIC_JSON_TITLE_PATTERN.findall(html_text):
        fallback_candidates.append(("json", raw_title))

    for pattern in HTML_TITLE_PATTERNS:
        for raw_title in pattern.findall(html_text):
            fallback_candidates.append(("html", raw_title))

    titles: list[str] = []
    seen: set[str] = set()

    def collect_titles(raw_candidates: list[tuple[str, str]]) -> None:
        for source_type, raw_title in raw_candidates:
            try:
                title = decode_naver_text(raw_title) if source_type == "json" else clean_html_fragment(raw_title)
            except Exception:
                continue
            normalized = diet_v2_service.normalize_title_match(title)
            if not normalized or normalized in seen:
                continue
            if not is_relevant_live_view_title(raw_title=raw_title, title=title, query_clues=query_clues):
                continue
            titles.append(title)
            seen.add(normalized)

    collect_titles(primary_candidates)
    if len(titles) < 6:
        collect_titles(fallback_candidates)
    return titles[:12]


def build_result_row(
    keyword: str,
    recent_titles: list[str],
    recent_titles_by_family: dict[str, list[str]],
) -> dict[str, object]:
    keyword_family = diet_v2_service.resolve_keyword_family(keyword)
    category = resolve_category(keyword)
    live_view_titles = extract_live_view_titles(
        fetch_naver_view_html(keyword),
        query=keyword,
    )
    result = diet_v2_service.blog_filler_diet_v2_gen(
        user_instructions=keyword,
        live_view_titles=live_view_titles,
        recent_titles=recent_titles,
        recent_family_titles=recent_titles_by_family.get(keyword_family, []),
        category=category,
    )
    exact_match = diet_v2_service.find_exact_live_view_title_match(
        result["title"],
        live_view_titles,
    )
    row = {
        "keyword": keyword,
        "target_keyword": keyword,
        "category": result["category"],
        "keyword_family": result["keyword_family"],
        "model_name": result["model_name"],
        "title_generation_strategy": result["title_generation_strategy"],
        "live_view_titles": live_view_titles,
        "intent_prompt": "\n".join(diet_v2_service.FAMILY_INTENT_HINTS.get(result["keyword_family"], ())),
        "title_prompt": result["title_prompt"],
        "manuscript_prompt": result["manuscript_prompt"],
        "title": result["title"],
        "manuscript": result["manuscript"],
        "exact_live_view_match": bool(exact_match),
        "matched_live_view_title": exact_match,
        "char_count_no_space": result["char_count_no_space"],
        "title_attempts": result["title_attempts"],
        "manuscript_attempts": result["manuscript_attempts"],
    }
    recent_titles.append(str(result["title"]))
    recent_titles_by_family.setdefault(keyword_family, []).append(str(result["title"]))
    return row


def write_outputs(rows: list[dict[str, object]], out_dir: Path, tab_name: str) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    sheet_rows_path = out_dir / f"sheet_rows_{tab_name}.json"
    summary_path = out_dir / f"summary_{tab_name}.json"

    sheet_rows: list[dict[str, str]] = []
    for index, row in enumerate(rows, start=1):
        sheet_rows.append(
            {
                "keyword": str(row["keyword"]),
                "target_keyword": str(row["target_keyword"]),
                "category": str(row["category"]),
                "keyword_family": str(row["keyword_family"]),
                "model_name": str(row["model_name"]),
                "title_generation_strategy": str(row["title_generation_strategy"]),
                "live_view_titles": "\n".join(str(t) for t in row["live_view_titles"]),
                "intent_prompt": str(row["intent_prompt"]),
                "title_prompt": str(row["title_prompt"]),
                "manuscript_prompt": str(row["manuscript_prompt"]),
                "title": str(row["title"]),
                "manuscript": str(row["manuscript"]),
                "exact_live_view_match": "TRUE" if row["exact_live_view_match"] else "FALSE",
                "matched_live_view_title": str(row["matched_live_view_title"]),
                "char_count_no_space": str(row["char_count_no_space"]),
                "title_attempts": str(row["title_attempts"]),
                "manuscript_attempts": str(row["manuscript_attempts"]),
            }
        )
        manuscript_path = out_dir / f"{index:02d}_{row['keyword']}.txt"
        manuscript_path.write_text(str(row["manuscript"]), encoding="utf-8")

    sheet_rows_path.write_text(json.dumps(sheet_rows, ensure_ascii=False, indent=2), encoding="utf-8")
    summary_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    print(f"OUT_DIR={out_dir}")
    print(f"SHEET_ROWS_JSON={sheet_rows_path}")
    return sheet_rows_path


def export_to_sheet(sheet_rows_json: Path, worksheet_title: str) -> None:
    import gspread
    from google.oauth2.service_account import Credentials
    from export_to_sheet import PRIVATE_KEY, SCOPES, SERVICE_ACCOUNT_EMAIL

    rows = json.loads(sheet_rows_json.read_text(encoding="utf-8"))
    if not rows:
        print(f"[skip] {worksheet_title}: 데이터 없음")
        return

    creds_info = {
        "type": "service_account",
        "client_email": SERVICE_ACCOUNT_EMAIL,
        "private_key": PRIVATE_KEY,
        "token_uri": "https://oauth2.googleapis.com/token",
    }
    creds = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
    gc = gspread.authorize(creds)
    spreadsheet = gc.open_by_key(OUTPUT_SPREADSHEET_ID)

    try:
        worksheet = spreadsheet.worksheet(worksheet_title)
    except gspread.exceptions.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title=worksheet_title, rows=str(len(rows) + 1), cols="20")

    headers = list(rows[0].keys())
    end_col_idx = len(headers)
    label = ""
    current = end_col_idx
    while current > 0:
        current, remainder = divmod(current - 1, 26)
        label = chr(65 + remainder) + label
    end_col = label

    worksheet.clear()
    worksheet.update(values=[headers], range_name=f"A1:{end_col}1", value_input_option="RAW")
    sheet_values = [[row.get(h, "") for h in headers] for row in rows]
    if sheet_values:
        worksheet.update(
            values=sheet_values,
            range_name=f"A2:{end_col}{len(sheet_values) + 1}",
            value_input_option="RAW",
        )

    print(f"WORKSHEET_TITLE={worksheet.title}")
    print(f"WORKSHEET_GID={worksheet.id}")
    print(f"ROW_COUNT={len(sheet_values)}")


def generate_single_keyword(keyword: str, tab_name: str) -> dict[str, object] | None:
    print(f"[{tab_name}] {keyword}")
    try:
        keyword_family = diet_v2_service.resolve_keyword_family(keyword)
        category = resolve_category(keyword)
        live_view_titles = extract_live_view_titles(
            fetch_naver_view_html(keyword),
            query=keyword,
        )
        result = diet_v2_service.blog_filler_diet_v2_gen(
            user_instructions=keyword,
            live_view_titles=live_view_titles,
            category=category,
        )
        exact_match = diet_v2_service.find_exact_live_view_title_match(
            result["title"],
            live_view_titles,
        )
        return {
            "keyword": keyword,
            "target_keyword": keyword,
            "category": result["category"],
            "keyword_family": result["keyword_family"],
            "model_name": result["model_name"],
            "title_generation_strategy": result["title_generation_strategy"],
            "live_view_titles": live_view_titles,
            "intent_prompt": "\n".join(diet_v2_service.FAMILY_INTENT_HINTS.get(result["keyword_family"], ())),
            "title_prompt": result["title_prompt"],
            "manuscript_prompt": result["manuscript_prompt"],
            "title": result["title"],
            "manuscript": result["manuscript"],
            "exact_live_view_match": bool(exact_match),
            "matched_live_view_title": exact_match,
            "char_count_no_space": result["char_count_no_space"],
            "title_attempts": result["title_attempts"],
            "manuscript_attempts": result["manuscript_attempts"],
        }
    except Exception as e:
        print(f"[error] {keyword}: {e}")
        return None


def run_batch(keywords: tuple[str, ...], tab_name: str, out_dir: Path, workers: int = 3) -> None:
    rows: list[dict[str, object]] = []

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(generate_single_keyword, kw, tab_name): kw
            for kw in keywords
        }
        keyword_order = {kw: i for i, kw in enumerate(keywords)}
        results: list[tuple[int, dict[str, object]]] = []

        for future in as_completed(futures):
            kw = futures[future]
            row = future.result()
            if row:
                results.append((keyword_order[kw], row))

    results.sort(key=lambda x: x[0])
    rows = [r[1] for r in results]

    if rows:
        sheet_rows_path = write_outputs(rows=rows, out_dir=out_dir, tab_name=tab_name)
        export_to_sheet(sheet_rows_path, worksheet_title=tab_name)
    else:
        print(f"[skip] {tab_name}: 생성된 원고 없음")


def run_batch_sequential(keywords: tuple[str, ...], tab_name: str, out_dir: Path) -> None:
    recent_titles: list[str] = []
    recent_titles_by_family: dict[str, list[str]] = {}
    rows: list[dict[str, object]] = []

    for keyword in keywords:
        print(f"[{tab_name}] {keyword}")
        try:
            rows.append(
                build_result_row(
                    keyword=keyword,
                    recent_titles=recent_titles,
                    recent_titles_by_family=recent_titles_by_family,
                )
            )
        except Exception as e:
            print(f"[error] {keyword}: {e}")
            continue

    if rows:
        sheet_rows_path = write_outputs(rows=rows, out_dir=out_dir, tab_name=tab_name)
        export_to_sheet(sheet_rows_path, worksheet_title=tab_name)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--tab",
        choices=["abstract", "yunseul", "both"],
        default="both",
    )
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("keywords", nargs="*")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    out_dir = Path(args.output_dir)

    if args.tab in ("abstract", "both"):
        keywords = tuple(args.keywords) if args.keywords and args.tab == "abstract" else ABSTRACT_KEYWORDS
        run_batch(keywords, tab_name="추상의구체화", out_dir=out_dir, workers=args.workers)

    if args.tab in ("yunseul", "both"):
        keywords = tuple(args.keywords) if args.keywords and args.tab == "yunseul" else YUNSEUL_KEYWORDS
        run_batch(keywords, tab_name="윤슬", out_dir=out_dir, workers=args.workers)


if __name__ == "__main__":
    main()

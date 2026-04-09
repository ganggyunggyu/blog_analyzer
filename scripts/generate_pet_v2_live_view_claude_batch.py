# ruff: noqa: E402

from __future__ import annotations

import argparse
import html
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from _constants.Model import Model
from llm import blog_filler_pet_v2_service as pet_v2_service


DEFAULT_KEYWORDS: tuple[str, ...] = (
    "셔틀랜드쉽독",
    "시바견분양",
    "입양조건",
    "고양이파양",
    "골든두들",
    "광주동물보호소",
    "고양이분양가",
    "강아지품종",
    "웰시코기",
    "강아지",
)
DEFAULT_MODEL_NAME = Model.CLAUDE_SONNET_4_6
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
)
NOISE_TITLES: set[str] = {"더보기", "이미지"}


def decode_naver_text(raw_text: str) -> str:
    decoded = json.loads(f'"{raw_text}"')
    decoded = html.unescape(decoded)
    decoded = MARK_TAG_PATTERN.sub("", decoded)
    return WHITESPACE_PATTERN.sub(" ", decoded).strip()


def clean_html_fragment(raw_text: str) -> str:
    cleaned = html.unescape(raw_text)
    cleaned = HTML_TAG_PATTERN.sub("", cleaned)
    return WHITESPACE_PATTERN.sub(" ", cleaned).strip()


def sanitize_note_value(text: str) -> str:
    return (
        text.replace("(", " ")
        .replace(")", " ")
        .replace(";", " ")
        .replace("||", " ")
        .strip()
    )


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
    normalized_query = pet_v2_service.normalize_title_match(query)
    if normalized_query:
        clues.add(normalized_query)

    for token in re.findall(r"[가-힣A-Za-z0-9]+", query):
        normalized_token = pet_v2_service.normalize_title_match(token)
        if len(normalized_token) >= 2:
            clues.add(normalized_token)

    return clues


def is_relevant_live_view_title(
    raw_title: str,
    title: str,
    query_clues: set[str],
) -> bool:
    normalized_title = pet_v2_service.normalize_title_match(title)
    if not normalized_title or title in NOISE_TITLES:
        return False

    if len(title) < 6:
        return False

    if len(title) > 56:
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
    raw_candidates: list[tuple[str, str]] = []
    review_blocks = REVIEW_BLOCK_PATTERN.findall(html_text)
    query_clues = build_query_clues(query)

    for review_block in review_blocks:
        for raw_title in REVIEW_TITLE_PATTERN.findall(review_block):
            raw_candidates.append(("json", raw_title))

    if not raw_candidates:
        for raw_title in REVIEW_TITLE_PATTERN.findall(html_text):
            raw_candidates.append(("json", raw_title))

    for raw_title in GENERIC_JSON_TITLE_PATTERN.findall(html_text):
        raw_candidates.append(("json", raw_title))

    for pattern in HTML_TITLE_PATTERNS:
        for raw_title in pattern.findall(html_text):
            raw_candidates.append(("html", raw_title))

    titles: list[str] = []
    seen: set[str] = set()

    for source_type, raw_title in raw_candidates:
        try:
            if source_type == "json":
                title = decode_naver_text(raw_title)
            else:
                title = clean_html_fragment(raw_title)
        except Exception:
            continue

        normalized = pet_v2_service.normalize_title_match(title)
        if not normalized or normalized in seen:
            continue

        if not is_relevant_live_view_title(
            raw_title=raw_title,
            title=title,
            query_clues=query_clues,
        ):
            continue

        titles.append(title)
        seen.add(normalized)

    return titles[:12]


def build_generation_note(live_view_titles: list[str]) -> str:
    if not live_view_titles:
        return "live_view_collection_status=failed"

    safe_titles = [sanitize_note_value(title) for title in live_view_titles if title.strip()]
    joined_titles = "||".join(title for title in safe_titles if title)
    if not joined_titles:
        return "live_view_collection_status=failed"

    return (
        "live_view_collection_status=success;"
        f"live_view_titles={joined_titles}"
    )


def build_result_row(keyword: str, model_name: str) -> dict[str, object]:
    target_keyword = pet_v2_service.resolve_target_keyword(keyword=keyword)
    live_view_titles = extract_live_view_titles(
        fetch_naver_view_html(target_keyword),
        query=target_keyword,
    )
    note = build_generation_note(live_view_titles)
    query = f"{keyword} ({note})"
    pet_v2_service.MODEL_NAME = model_name

    live_view_collection = pet_v2_service.resolve_live_view_title_collection(
        keyword=target_keyword,
        note=note,
    )
    intent_prompt = pet_v2_service.build_keyword_intent_prompt(
        keyword=keyword,
        note=note,
        target_keyword=target_keyword,
        live_view_collection=live_view_collection,
    )
    manuscript = pet_v2_service.blog_filler_pet_v2_gen(query)
    title = pet_v2_service.get_title_line(manuscript)
    exact_match = pet_v2_service.find_exact_live_view_title_match(
        title=title,
        live_view_titles=live_view_titles,
    )

    return {
        "keyword": keyword,
        "target_keyword": target_keyword,
        "model_name": model_name,
        "query": query,
        "title_generation_strategy": pet_v2_service.get_title_generation_strategy(
            live_view_collection
        ),
        "live_view_titles": live_view_titles,
        "live_view_quality_issues": list(live_view_collection.quality_issues),
        "title": title,
        "manuscript": manuscript,
        "exact_live_view_match": bool(exact_match),
        "matched_live_view_title": exact_match,
        "intent_prompt": intent_prompt,
    }


def write_outputs(
    rows: list[dict[str, object]],
    out_dir: Path,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    summary_path = out_dir / "summary.json"
    prompt_path = out_dir / "prompt_and_manuscripts.md"
    sheet_rows_path = out_dir / "sheet_rows.json"

    summary_path.write_text(
        json.dumps(rows, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    markdown_lines: list[str] = ["# Pet V2 Sonnet 4.6 Batch", ""]
    sheet_rows: list[dict[str, str]] = []

    for index, row in enumerate(rows, start=1):
        live_titles = "\n".join(f"- {title}" for title in row["live_view_titles"])
        quality_issues = ", ".join(row["live_view_quality_issues"]) or "-"
        markdown_lines.extend(
            [
                f"## {index:02d}. {row['keyword']}",
                "",
                f"- target_keyword: {row['target_keyword']}",
                f"- model_name: {row['model_name']}",
                f"- title_generation_strategy: {row['title_generation_strategy']}",
                f"- exact_live_view_match: {row['exact_live_view_match']}",
                f"- live_view_quality_issues: {quality_issues}",
                "",
                "### Live VIEW Titles",
                "",
                live_titles or "-",
                "",
                "### Prompt",
                "",
                "```text",
                str(row["intent_prompt"]),
                "```",
                "",
                "### Manuscript",
                "",
                "```text",
                str(row["manuscript"]),
                "```",
                "",
            ]
        )

        sheet_rows.append(
            {
                "keyword": str(row["keyword"]),
                "target_keyword": str(row["target_keyword"]),
                "model_name": str(row["model_name"]),
                "title_generation_strategy": str(row["title_generation_strategy"]),
                "live_view_titles": "\n".join(str(title) for title in row["live_view_titles"]),
                "intent_prompt": str(row["intent_prompt"]),
                "title": str(row["title"]),
                "manuscript": str(row["manuscript"]),
                "exact_live_view_match": "TRUE" if row["exact_live_view_match"] else "FALSE",
            }
        )

        manuscript_path = out_dir / f"{index:02d}_{row['keyword']}.txt"
        manuscript_path.write_text(str(row["manuscript"]), encoding="utf-8")

    prompt_path.write_text("\n".join(markdown_lines), encoding="utf-8")
    sheet_rows_path.write_text(
        json.dumps(sheet_rows, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"OUT_DIR={out_dir}")
    print(f"SUMMARY_JSON={summary_path}")
    print(f"PROMPT_MARKDOWN={prompt_path}")
    print(f"SHEET_ROWS_JSON={sheet_rows_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("keywords", nargs="*")
    parser.add_argument("--model", default=DEFAULT_MODEL_NAME)
    parser.add_argument(
        "--output-dir",
        default=(
            Path("test-manuscripts") / "pet_v2_claude_sonnet_live"
            / datetime.now().strftime("%Y%m%d_%H%M%S")
        ),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    keywords = tuple(args.keywords) if args.keywords else DEFAULT_KEYWORDS
    rows = [build_result_row(keyword=keyword, model_name=args.model) for keyword in keywords]
    write_outputs(rows=rows, out_dir=Path(args.output_dir))


if __name__ == "__main__":
    main()

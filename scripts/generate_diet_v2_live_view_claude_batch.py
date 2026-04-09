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

from llm import blog_filler_diet_v2_service as diet_v2_service


DEFAULT_KEYWORDS: tuple[str, ...] = (
    "베르베린",
    "베르베린효능",
    "마운자로",
    "다이어트보조제가격",
    "아보다트",
    "위고비알약",
    "지방분해주사",
    "감비환",
    "레시틴",
    "식욕억제제가격",
    "디에타민",
    "브로멜라인",
    "다이어트보조제비교",
    "판시딜",
    "마운자로알약",
    "당뇨초기증상",
    "위고비효과",
    "베르베린복용법",
    "당뇨에좋은음식",
    "위고비",
    "식후2시간혈당",
    "다이어트한약",
    "혈당스파이크증상",
    "마운자로처방",
    "달맞이꽃종자유",
    "프로페시아",
    "마운자로효과",
    "내장지방",
    "GLP-1다이어트",
    "나비약",
)
DEFAULT_OUTPUT_DIR = (
    Path("test-manuscripts")
    / "diet_v2_claude_sonnet_live"
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
    re.compile(r"(?:Prefilled Pen Inj|프리필드펜|펜주\d)"),
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
    re.compile(r"맞아보신\s*분"),
    re.compile(r"드셔보신\s*분"),
    re.compile(r"어느병원"),
    re.compile(r"궁금해요"),
    re.compile(r"걱정되는데"),
    re.compile(r"고민\s*중"),
    re.compile(r"해봤는데"),
    re.compile(r"진행했어요"),
    re.compile(r"후기"),
    re.compile(r"공유목적"),
    re.compile(r"\.\."),
    re.compile(r"[ㄷㅋㅎ]{2,}"),
    re.compile(r"알겠어요"),
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
    live_view_titles = extract_live_view_titles(
        fetch_naver_view_html(keyword),
        query=keyword,
    )
    result = diet_v2_service.blog_filler_diet_v2_gen(
        user_instructions=keyword,
        live_view_titles=live_view_titles,
        recent_titles=recent_titles,
        recent_family_titles=recent_titles_by_family.get(keyword_family, []),
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


def write_outputs(rows: list[dict[str, object]], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    summary_path = out_dir / "summary.json"
    prompt_path = out_dir / "prompt_and_manuscripts.md"
    sheet_rows_path = out_dir / "sheet_rows.json"

    summary_path.write_text(
        json.dumps(rows, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    markdown_lines: list[str] = ["# Diet V2 Sonnet 4.6 Batch", ""]
    sheet_rows: list[dict[str, str]] = []

    for index, row in enumerate(rows, start=1):
        live_titles = "\n".join(f"- {title}" for title in row["live_view_titles"])
        markdown_lines.extend(
            [
                f"## {index:02d}. {row['keyword']}",
                "",
                f"- keyword_family: {row['keyword_family']}",
                f"- model_name: {row['model_name']}",
                f"- title_generation_strategy: {row['title_generation_strategy']}",
                f"- exact_live_view_match: {row['exact_live_view_match']}",
                f"- char_count_no_space: {row['char_count_no_space']}",
                "",
                "### Live VIEW Titles",
                "",
                live_titles or "-",
                "",
                "### Title Prompt",
                "",
                "```text",
                str(row["title_prompt"]),
                "```",
                "",
                "### Manuscript Prompt",
                "",
                "```text",
                str(row["manuscript_prompt"]),
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
                "category": str(row["category"]),
                "keyword_family": str(row["keyword_family"]),
                "model_name": str(row["model_name"]),
                "title_generation_strategy": str(row["title_generation_strategy"]),
                "live_view_titles": "\n".join(str(title) for title in row["live_view_titles"]),
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
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    keywords = tuple(args.keywords) if args.keywords else DEFAULT_KEYWORDS
    recent_titles: list[str] = []
    recent_titles_by_family: dict[str, list[str]] = {}
    rows: list[dict[str, object]] = []

    for keyword in keywords:
        print(f"[generate] {keyword}")
        rows.append(
            build_result_row(
                keyword=keyword,
                recent_titles=recent_titles,
                recent_titles_by_family=recent_titles_by_family,
            )
        )

    write_outputs(rows=rows, out_dir=Path(args.output_dir))


if __name__ == "__main__":
    main()

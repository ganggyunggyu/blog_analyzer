"""네이버 뷰탭 블로그 참조원고 수집 서비스"""

from __future__ import annotations

import html
import json
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from urllib.parse import quote

from bs4 import BeautifulSoup

from utils.logger import log

NAVER_VIEW_SEARCH_URL = (
    "https://search.naver.com/search.naver?where=view&sm=tab_jum&query={query}"
)
MOBILE_POST_URL_TEMPLATE = (
    "https://m.blog.naver.com/PostView.naver"
    "?blogId={blog_id}&logNo={log_no}&proxyReferer=https%3A%2F%2Fm.blog.naver.com%2F"
)
DEFAULT_REFERENCE_LIMIT = 8
DEFAULT_TITLE_EXAMPLE_LIMIT = 8
DEFAULT_FETCH_TIMEOUT_SECONDS = 20
MIN_REFERENCE_BODY_LENGTH = 120

DIRECT_BLOG_POST_URL_PATTERN = re.compile(
    r"https://blog\.naver\.com/(?P<blog_id>[A-Za-z0-9\-_]+)/(?P<log_no>\d+)"
)
MOBILE_BLOG_POST_URL_PATTERN = re.compile(
    r"https://m\.blog\.naver\.com/"
    r"(?:PostView\.naver\?(?:[^\"'\s>]*?blogId=(?P<blog_id>[A-Za-z0-9\-_]+)"
    r".*?logNo=(?P<log_no>\d+)[^\"'\s>]*)|(?P<path_blog_id>[A-Za-z0-9\-_]+)/(?P<path_log_no>\d+))"
)
TITLE_SUFFIX_PATTERN = re.compile(r"\s*:\s*네이버 블로그\s*$")
WHITESPACE_PATTERN = re.compile(r"\s+")
ZERO_WIDTH_PATTERN = re.compile(r"[\u200b\u2060\ufeff]")
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
TITLE_NOISE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"네이버 검색"),
    re.compile(r"관련 브랜드 콘텐츠"),
    re.compile(r"네이버 클립"),
    re.compile(r"함께 많이 찾는"),
    re.compile(r"님의 블로그$"),
    re.compile(r"^\d{2,4}[─-]\d{3,4}[─-]\d{4}"),
    re.compile(r"(?:나무위키|위키백과|시사상식사전|화학백과|요리백과|의약품 정보|약학용어사전)"),
    re.compile(r"(?:동영상)$"),
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
    re.compile(r"[ㄷㅋㅎ]{2,}"),
)
NOISE_TITLES = {"더보기", "이미지"}

NOISE_LINES = {
    "공감",
    "댓글",
    "카테고리",
    "프로필",
    "이웃추가",
    "공유하기",
    "URL 복사",
    "본문 기타 기능",
    "맨 위로",
}
PARAGRAPH_SELECTORS: tuple[str, ...] = (
    ".se-main-container p.se-text-paragraph",
    ".se-main-container p",
    "#postViewArea p",
    ".post-view p",
    "#post-area p",
    ".contents_style p",
)
CONTAINER_SELECTORS: tuple[str, ...] = (
    ".se-main-container",
    "#postViewArea",
    ".post-view",
    "#post-area",
    ".contents_style",
)
TITLE_SELECTORS: tuple[str, ...] = (
    'meta[property="og:title"]',
    ".se-title-text p.se-text-paragraph",
    ".se-title-text p",
    "#title_1 .pcol1",
    ".htitle .title",
)


@dataclass(frozen=True)
class NaverBlogReference:
    title: str
    body: str
    source_url: str
    mobile_url: str


def _run_curl(url: str) -> str:
    result = subprocess.run(
        ["curl", "-sL", "-A", "Mozilla/5.0", url],
        capture_output=True,
        text=True,
        check=True,
        timeout=DEFAULT_FETCH_TIMEOUT_SECONDS,
    )
    return result.stdout


def _clean_text(text: str) -> str:
    cleaned = html.unescape(text or "")
    cleaned = ZERO_WIDTH_PATTERN.sub("", cleaned)
    return WHITESPACE_PATTERN.sub(" ", cleaned).strip()


def _decode_naver_json_text(raw_text: str) -> str:
    decoded = json.loads(f'"{raw_text}"')
    decoded = html.unescape(decoded)
    decoded = MARK_TAG_PATTERN.sub("", decoded)
    return WHITESPACE_PATTERN.sub(" ", decoded).strip()


def _clean_html_fragment(raw_text: str) -> str:
    cleaned = html.unescape(raw_text)
    cleaned = HTML_TAG_PATTERN.sub("", cleaned)
    return WHITESPACE_PATTERN.sub(" ", cleaned).strip()


def _normalize_title_match(text: str) -> str:
    return re.sub(r"[^0-9A-Za-z가-힣]+", "", text or "").lower()


def _build_query_clues(query: str) -> set[str]:
    clues: set[str] = set()
    normalized_query = _normalize_title_match(query)
    if normalized_query:
        clues.add(normalized_query)

    for token in re.findall(r"[가-힣A-Za-z0-9\-]+", query):
        normalized_token = _normalize_title_match(token)
        if len(normalized_token) >= 2:
            clues.add(normalized_token)

    return clues


def _is_relevant_naver_view_title(
    raw_title: str,
    title: str,
    query_clues: set[str],
) -> bool:
    normalized_title = _normalize_title_match(title)
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


def _extract_blog_identity(url: str) -> tuple[str, str] | None:
    for pattern in (DIRECT_BLOG_POST_URL_PATTERN, MOBILE_BLOG_POST_URL_PATTERN):
        match = pattern.search(url)
        if not match:
            continue

        blog_id = match.groupdict().get("blog_id") or match.groupdict().get("path_blog_id")
        log_no = match.groupdict().get("log_no") or match.groupdict().get("path_log_no")
        if blog_id and log_no:
            return blog_id, log_no
    return None


def normalize_naver_blog_post_url(url: str) -> str | None:
    identity = _extract_blog_identity(url)
    if not identity:
        return None

    blog_id, log_no = identity
    return f"https://blog.naver.com/{blog_id}/{log_no}"


def build_naver_mobile_post_url(blog_id: str, log_no: str) -> str:
    return MOBILE_POST_URL_TEMPLATE.format(blog_id=blog_id, log_no=log_no)


def fetch_naver_view_html(query: str) -> str:
    url = NAVER_VIEW_SEARCH_URL.format(query=quote(query))
    return _run_curl(url)


def extract_naver_blog_urls(
    html_text: str,
    limit: int = DEFAULT_REFERENCE_LIMIT,
) -> list[str]:
    normalized_html = html.unescape(html_text).replace("\\/", "/")
    urls: list[str] = []
    seen: set[str] = set()

    for pattern in (DIRECT_BLOG_POST_URL_PATTERN, MOBILE_BLOG_POST_URL_PATTERN):
        for match in pattern.finditer(normalized_html):
            blog_id = match.groupdict().get("blog_id") or match.groupdict().get("path_blog_id")
            log_no = match.groupdict().get("log_no") or match.groupdict().get("path_log_no")
            if not blog_id or not log_no:
                continue

            url = f"https://blog.naver.com/{blog_id}/{log_no}"
            if url in seen:
                continue

            seen.add(url)
            urls.append(url)

            if len(urls) >= limit:
                return urls

    return urls


def extract_naver_view_titles(
    html_text: str,
    query: str = "",
    limit: int = DEFAULT_TITLE_EXAMPLE_LIMIT,
) -> list[str]:
    primary_candidates: list[tuple[str, str]] = []
    fallback_candidates: list[tuple[str, str]] = []
    review_blocks = REVIEW_BLOCK_PATTERN.findall(html_text)
    query_clues = _build_query_clues(query)

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
                title = (
                    _decode_naver_json_text(raw_title)
                    if source_type == "json"
                    else _clean_html_fragment(raw_title)
                )
            except Exception:
                continue

            normalized = _normalize_title_match(title)
            if not normalized or normalized in seen:
                continue

            if not _is_relevant_naver_view_title(
                raw_title=raw_title,
                title=title,
                query_clues=query_clues,
            ):
                continue

            titles.append(title)
            seen.add(normalized)

            if len(titles) >= limit:
                return

    collect_titles(primary_candidates)

    if len(titles) < limit:
        collect_titles(fallback_candidates)

    return titles[:limit]


def collect_naver_view_titles(
    query: str,
    limit: int = DEFAULT_TITLE_EXAMPLE_LIMIT,
) -> list[str]:
    html_text = fetch_naver_view_html(query)
    return extract_naver_view_titles(html_text, query=query, limit=limit)


def _extract_title(soup: BeautifulSoup) -> str:
    for selector in TITLE_SELECTORS:
        element = soup.select_one(selector)
        if not element:
            continue

        if element.name == "meta":
            title = _clean_text(element.get("content", ""))
        else:
            title = _clean_text(element.get_text(" ", strip=True))

        if title:
            return TITLE_SUFFIX_PATTERN.sub("", title)

    page_title = soup.title.string if soup.title and soup.title.string else ""
    return TITLE_SUFFIX_PATTERN.sub("", _clean_text(page_title))


def _clean_body_lines(lines: list[str], title: str) -> list[str]:
    cleaned_lines: list[str] = []

    for raw_line in lines:
        line = _clean_text(raw_line)
        if not line or line in NOISE_LINES:
            continue
        if title and line == title:
            continue
        if cleaned_lines and line == cleaned_lines[-1]:
            continue
        cleaned_lines.append(line)

    return cleaned_lines


def _extract_body_lines(soup: BeautifulSoup, title: str) -> list[str]:
    for selector in PARAGRAPH_SELECTORS:
        elements = soup.select(selector)
        lines = _clean_body_lines(
            [element.get_text(" ", strip=True) for element in elements],
            title=title,
        )
        if len(lines) >= 5 or len("\n".join(lines)) >= MIN_REFERENCE_BODY_LENGTH:
            return lines

    for selector in CONTAINER_SELECTORS:
        container = soup.select_one(selector)
        if not container:
            continue

        lines = _clean_body_lines(list(container.stripped_strings), title=title)
        if len(lines) >= 5 or len("\n".join(lines)) >= MIN_REFERENCE_BODY_LENGTH:
            return lines

    return []


def parse_naver_blog_post_html(html_text: str) -> tuple[str, str]:
    soup = BeautifulSoup(html_text, "html.parser")
    title = _extract_title(soup)
    body_lines = _extract_body_lines(soup, title=title)
    body = "\n".join(body_lines).strip()
    return title, body


def fetch_naver_blog_reference(url: str) -> NaverBlogReference | None:
    normalized_url = normalize_naver_blog_post_url(url)
    if not normalized_url:
        return None

    identity = _extract_blog_identity(normalized_url)
    if not identity:
        return None

    blog_id, log_no = identity
    mobile_url = build_naver_mobile_post_url(blog_id, log_no)
    html_text = _run_curl(mobile_url)
    title, body = parse_naver_blog_post_html(html_text)

    if not title or len(body) < MIN_REFERENCE_BODY_LENGTH:
        return None

    return NaverBlogReference(
        title=title,
        body=body,
        source_url=normalized_url,
        mobile_url=mobile_url,
    )


def collect_naver_blog_references(
    query: str,
    limit: int = DEFAULT_REFERENCE_LIMIT,
) -> list[NaverBlogReference]:
    html_text = fetch_naver_view_html(query)
    urls = extract_naver_blog_urls(html_text, limit=limit)

    if not urls:
        return []

    references: list[NaverBlogReference] = []

    with ThreadPoolExecutor(max_workers=min(4, len(urls))) as executor:
        future_to_url = {
            executor.submit(fetch_naver_blog_reference, url): url for url in urls
        }
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                reference = future.result()
            except Exception as exc:
                log.warning(
                    "네이버 참조원고 수집 실패",
                    keyword=query,
                    url=url,
                    error=str(exc),
                )
                continue

            if reference:
                references.append(reference)

    ordered_references = sorted(
        references,
        key=lambda reference: urls.index(reference.source_url),
    )
    return ordered_references


def build_naver_blog_reference_bundle(
    query: str,
    manual_ref: str = "",
    limit: int = DEFAULT_REFERENCE_LIMIT,
) -> str:
    parts: list[str] = []

    try:
        references = collect_naver_blog_references(query, limit=limit)
    except Exception as exc:
        log.warning(
            "네이버 뷰탭 참조원고 번들 생성 실패",
            keyword=query,
            error=str(exc),
        )
        references = []

    if references:
        auto_ref_parts = [
            "[네이버 뷰탭 자동 참조원고]",
            "아래 원고들은 같은 키워드로 노출된 네이버 블로그 글입니다.",
            "문장을 그대로 베끼지 말고 도입 흐름, 정보 전개, 맺음말 리듬만 참고하세요.",
        ]

        for index, reference in enumerate(references, start=1):
            auto_ref_parts.append(
                "\n".join(
                    [
                        f"[참조 {index}]",
                        f"제목: {reference.title}",
                        "본문:",
                        reference.body,
                    ]
                )
            )

        parts.append("\n\n".join(auto_ref_parts).strip())
        log.info(
            "네이버 참조원고 수집 완료",
            keyword=query,
            reference_count=len(references),
        )

    cleaned_manual_ref = manual_ref.strip()
    if cleaned_manual_ref:
        manual_part = "\n\n".join(
            [
                "[사용자 제공 참조원고]",
                cleaned_manual_ref,
            ]
        )
        parts.append(manual_part)

    return "\n\n".join(parts).strip()

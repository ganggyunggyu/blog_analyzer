"""네이버 뷰탭 블로그 참조원고 수집 서비스"""

from __future__ import annotations

import html
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

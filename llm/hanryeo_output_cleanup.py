"""한려담원 출력 후처리"""

from __future__ import annotations

import re

LINE_1_PATTERN = re.compile(r"^1\.\s*도입부(?:\s+.*)?$")
LINE_2_PATTERN = re.compile(r"^2\.\s*핵심\s*개념\s*①\s*(.*)$")
LINE_3_PATTERN = re.compile(r"^3\.\s*핵심\s*개념\s*②\s*(.*)$")
LINE_4_PATTERN = re.compile(r"^4\.\s*(.*?)(?:\s+)?실천\s*가이드\s*\+\s*Q&A$")
LINE_5_PATTERN = re.compile(r"^5\.\s*마무리\s*요약\s*\+\s*제품\s*연결$")
LINE_5_ALT_PATTERN = re.compile(r"^5\.\s*마무리와\s*관리\s*제안$")
GENERIC_HEADING_PATTERN = re.compile(r"^(?P<number>\d+)\.\s*(?P<body>.+)$")
BROKEN_META_HEADING_PATTERN = re.compile(
    r"^(?P<number>\d+)\.\s*(?:요약과|마무리와)\s*$"
)
GUIDE_SUFFIX_PATTERN = re.compile(
    r"(?P<prefix>.*?)(?:\s+)?실천\s*가이드(?:\s*(?:\+\s*Q&A|와\s*(?:Q&A|궁금증(?:\s*풀기)?|자주\s*묻는\s*질문|흔한\s*질문)))?$"
)
MANAGEMENT_SUFFIX_PATTERN = re.compile(
    r"(?P<prefix>.*?)(?:\s+)?(?:따뜻한\s+)?관리\s*제안$"
)
CONNECTOR_SUFFIX_PATTERN = re.compile(r"(?:과|와|및)$")
SUMMARY_WORDS = ("요약", "정리", "마무리", "맺음말")


def _clean_tail(text: str, fallback: str) -> str:
    tail = re.sub(r"\s+", " ", (text or "").strip())
    return tail or fallback


def _strip_meta_words(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", (text or "").strip())
    for word in SUMMARY_WORDS:
        cleaned = cleaned.replace(word, "")
    cleaned = CONNECTOR_SUFFIX_PATTERN.sub("", cleaned).strip()
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def _rewrite_generic_heading(number: str, body: str) -> str | None:
    normalized_body = re.sub(r"\s+", " ", body.strip())

    guide_match = GUIDE_SUFFIX_PATTERN.fullmatch(normalized_body)
    if guide_match:
        prefix = _strip_meta_words(guide_match.group("prefix") or "")
        if prefix:
            return f"{number}. {prefix} 관리 포인트"
        return f"{number}. 관리 방법과 궁금증"

    management_match = MANAGEMENT_SUFFIX_PATTERN.fullmatch(normalized_body)
    if management_match:
        prefix = _strip_meta_words(management_match.group("prefix") or "")
        if prefix:
            return f"{number}. {prefix} 정리"
        if number == "5":
            return "5. 끝으로 정리해보면"
        return f"{number}. 정리해보면"

    if "맺음말" in normalized_body:
        if number == "5":
            return "5. 끝으로 정리해보면"
        return f"{number}. 정리해보면"

    return None


def _rewrite_line(line: str) -> str:
    stripped = line.strip()

    if LINE_1_PATTERN.match(stripped):
        return "1. 먼저 알아둘 점"

    line_2_match = LINE_2_PATTERN.match(stripped)
    if line_2_match:
        tail = _clean_tail(line_2_match.group(1), "원인과 배경")
        return f"2. {tail}"

    line_3_match = LINE_3_PATTERN.match(stripped)
    if line_3_match:
        tail = _clean_tail(line_3_match.group(1), "함께 봐야 할 점")
        return f"3. {tail}"

    line_4_match = LINE_4_PATTERN.match(stripped)
    if line_4_match:
        prefix = re.sub(r"\s+", " ", (line_4_match.group(1) or "").strip())
        if prefix:
            return f"4. {prefix} 관리 포인트"
        return "4. 관리 방법과 궁금증"

    if LINE_5_PATTERN.match(stripped) or LINE_5_ALT_PATTERN.match(stripped):
        return "5. 끝으로 정리해보면"

    generic_match = GENERIC_HEADING_PATTERN.match(stripped)
    if generic_match:
        rewritten = _rewrite_generic_heading(
            number=generic_match.group("number"),
            body=generic_match.group("body"),
        )
        if rewritten:
            return rewritten

    return line


def sanitize_hanryeo_output(text: str) -> str:
    if not text.strip():
        return text

    original_lines = text.splitlines()
    normalized_lines: list[str] = []
    index = 0

    while index < len(original_lines):
        current_line = original_lines[index]
        stripped = current_line.strip()

        broken_meta_match = BROKEN_META_HEADING_PATTERN.match(stripped)
        if broken_meta_match and index + 1 < len(original_lines):
            next_line = original_lines[index + 1].strip()
            if next_line == "관리 제안":
                number = broken_meta_match.group("number")
                if number == "5":
                    normalized_lines.append("5. 끝으로 정리해보면")
                else:
                    normalized_lines.append(f"{number}. 정리해보면")
                index += 2
                continue

        normalized_lines.append(_rewrite_line(current_line))
        index += 1

    return "\n".join(normalized_lines)

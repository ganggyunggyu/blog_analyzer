"""
텍스트 정리 유틸리티
"""

import re


def clean_trailing_spaces(text: str) -> str:
    """
    줄바꿈이 있는 부분에서 문장 우측 끝의 공백 제거
    """
    if not text:
        return text

    lines = text.split("\n")
    cleaned_lines = [line.rstrip() for line in lines]

    return "\n".join(cleaned_lines)


def clean_multiple_spaces(text: str) -> str:
    """
    연속된 공백을 하나의 공백으로 변환 (줄바꿈 제외)
    """
    if not text:
        return text

    return re.sub(r"[ \t]+", " ", text)


def clean_text_format(text: str) -> str:
    """
    종합 텍스트 정리 함수
    - 줄 끝 공백 제거
    - 연속된 공백 정리
    """
    if not text:
        return text

    text = clean_trailing_spaces(text)

    text = clean_multiple_spaces(text)

    return text


def clean_empty_lines(text: str) -> str:
    """
    연속된 빈 줄을 하나의 빈 줄로 정리
    """
    if not text:
        return text

    return re.sub(r"\n\s*\n\s*\n+", "\n\n", text)


def comprehensive_text_clean(text: str) -> str:
    """
    모든 텍스트 정리 기능을 포함한 종합 정리 함수
    """
    if not text:
        return text

    text = clean_trailing_spaces(text)

    text = clean_multiple_spaces(text)

    text = clean_empty_lines(text)

    return text.strip()

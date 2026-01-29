"""
텍스트 정리 유틸리티
"""

import re

def replace_middle_dot(text: str) -> str:
    """
    중간점 문자 '·' 를 ',' 로 변환
    """
    if not text:
        return text
    return text.replace("·", ",")

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

def remove_markdown(text: str) -> str:
    """
    마크다운 문법 제거
    - 헤딩 (#, ##, ###)
    - 볼드 (**text**)
    - 이탤릭 (*text*, _text_)
    - 테이블 (| col |)
    - 코드블록 (```)
    - 인라인 코드 (`code`)
    - 링크 [text](url)
    - 이미지 ![alt](url)
    - 체크박스 이모지 (✔, ✅, ❌, ⚠️, ❗, →)
    - 제로 너비 공백 (​)
    """
    if not text:
        return text

    # 제로 너비 공백 제거
    text = text.replace("\u200b", "")
    text = text.replace("​", "")

    # 코드블록 제거 (```...```)
    text = re.sub(r"```[\s\S]*?```", "", text)

    # 인라인 코드 제거 (`code`)
    text = re.sub(r"`([^`]+)`", r"\1", text)

    # 테이블 라인 제거 (|로 시작하는 줄)
    text = re.sub(r"^\|.*\|$", "", text, flags=re.MULTILINE)

    # 헤딩 제거 (## 텍스트 -> 텍스트)
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)

    # 볼드 제거 (**text** -> text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)

    # 이탤릭 제거 (*text* -> text, _text_ -> text)
    text = re.sub(r"\*([^*]+)\*", r"\1", text)
    text = re.sub(r"_([^_]+)_", r"\1", text)

    # 링크 제거 [text](url) -> text
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)

    # 이미지 제거 ![alt](url) -> alt
    text = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"\1", text)

    # 체크 이모지 제거
    text = re.sub(r"[✔✅❌⚠️❗→]", "", text)

    # 구분선 제거 (---, ___, ***)
    text = re.sub(r"^[-_*]{3,}$", "", text, flags=re.MULTILINE)

    # 백틱, 작은따옴표 제거
    text = text.replace("`", "")
    text = text.replace("'", "")

    return text


def comprehensive_text_clean(text: str) -> str:
    """
    모든 텍스트 정리 기능을 포함한 종합 정리 함수
    """
    if not text:
        return text
    text = replace_middle_dot(text)

    text = clean_trailing_spaces(text)

    text = clean_multiple_spaces(text)

    text = clean_empty_lines(text)

    return text.strip()

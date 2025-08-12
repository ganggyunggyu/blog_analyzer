# utils/text_len.py
import re
from typing import Literal

def length_no_space(text: str) -> int:
    """공백/줄바꿈/탭 제거 후 길이 반환"""
    return len(re.sub(r"\s+", "", text or ""))

def is_len_between(
    text: str,
    min_len: int,
    max_len: int,
    inclusive: Literal[True, False] = True
) -> bool:
    """
    공백 제거 길이가 범위 내인지 검사.
    inclusive=True  -> min <= n <= max
    inclusive=False -> min <  n <  max
    """
    n = length_no_space(text)
    return (min_len <= n <= max_len) if inclusive else (min_len < n < max_len)
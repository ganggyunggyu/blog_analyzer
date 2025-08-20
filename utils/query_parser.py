import re
from typing import Optional, Dict

# 카테고리 키워드는 '카테고리' 또는 'category' 허용, 콜론은 : 또는 ： 허용
CATEGORY_RE = re.compile(
    r"""
    ^\s*
    (?P<keyword>.*?)                              # 1) 카테고리 전까지를 키워드로
    (?:\s*(?:카테고리|category)\s*[:：]\s*        # 2) '카테고리:' or 'category:' 구간 (옵션)
        (?P<category>[^()]*?)                     #    괄호 전까지 카테고리
    )?
    \s*
    (?:\((?P<note>[^)]*)\))?                      # 3) 맨 끝 괄호 안의 메모 (옵션)
    \s*$
    """,
    re.IGNORECASE | re.VERBOSE,
)

def parse_query(s: str) -> Dict[str, Optional[str]]:
    m = CATEGORY_RE.match(s or "")
    if not m:
        return {"keyword": s.strip() if s else None, "category": None, "note": None}

    keyword = (m.group("keyword") or "").strip()
    category = (m.group("category") or "").strip() or None
    note = (m.group("note") or "").strip() or None

    # 카테고리 블록이 있으면, keyword에서 뒤에 붙은 공백 제거
    # (예: "위고비 가격 " → "위고비 가격")
    if category:
        keyword = keyword.rstrip()

    # keyword가 비었는데 note만 있는 경우 방어 (필요 시 정책에 맞게 조정)
    if not keyword:
        keyword = None

    return {"keyword": keyword, "category": category, "note": note}
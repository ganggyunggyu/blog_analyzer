import re
from typing import Optional, Dict

CATEGORY_RE = re.compile(
    r"""
    ^\s*
    (?P<keyword>.*?)                              
    (?:\s*(?:카테고리|category)\s*[:：]\s*        
        (?P<category>[^()]*?)                     
    )?
    \s*
    (?:\((?P<note>[^)]*)\))?                      
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

    if category:
        keyword = keyword.rstrip()

    if not keyword:
        keyword = None

    return {"keyword": keyword, "category": category, "note": note}

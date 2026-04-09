# ruff: noqa: E402
"""애견 키워드 원고 생성 → Google Sheets 내보내기"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import gspread
from google.oauth2.service_account import Credentials

from export_to_sheet import PRIVATE_KEY, SCOPES, SERVICE_ACCOUNT_EMAIL
from llm.blog_filler_pet_service import blog_filler_pet_gen, MODEL_NAME

SPREADSHEET_ID = "1HErumqLrDcuCDlxnAlbB9efClvIVPihZq12kcUQzP2k"

KEYWORDS: list[str] = [
    "아메리칸숏헤어",
    "귀여운강아지",
    "브리티쉬숏헤어분양",
    "길고양이",
    "파주강아지분양",
    "펫샵",
    "말티즈분양",
    "비숑프리제",
    "포메라니안",
    "골든리트리버",
]

HEADERS = ["no", "keyword", "model", "title", "manuscript", "char_count",
           "system_prompt", "user_prompt", "intent_prompt"]


def extract_title(text: str) -> str:
    """원고 첫 줄에서 제목 추출"""
    for line in text.strip().splitlines():
        line = line.strip()
        if line:
            return line
    return ""


def extract_ending(title: str) -> str:
    """제목 마무리 핵심 패턴 추출 (마지막 1~2어절의 핵심 표현)"""
    words = title.strip().split()
    if not words:
        return ""
    last = words[-1]
    # 마지막 2어절도 함께 잡아서 "봐야 하는 이유" 같은 패턴까지 커버
    last_two = " ".join(words[-2:]) if len(words) >= 2 else last
    return last_two


def generate_all() -> list[dict]:
    from llm.blog_filler_pet_service import SYSTEM_PROMPT, USER_PROMPT, PEN_NAMES
    from llm.blog_filler_pet_v2_service import (
        build_keyword_intent_prompt,
        resolve_target_keyword,
    )
    import random

    results: list[dict] = []
    prev_titles: list[str] = []
    prev_endings: list[str] = []

    for i, kw in enumerate(KEYWORDS, 1):
        print(f"\n[{i}/{len(KEYWORDS)}] 생성 중: {kw}")
        start = time.time()

        # 이전 제목 + 마무리 표현을 avoid로 전달
        # parse_query는 (...)안을 note로 인식
        note_parts: list[str] = []
        if prev_titles:
            note_parts.append(f"avoid_titles={'||'.join(prev_titles[-5:])}")
        if prev_endings:
            note_parts.append(f"avoid_endings={'||'.join(prev_endings[-5:])}")

        if note_parts:
            user_input = f"{kw} ({';'.join(note_parts)})"
        else:
            user_input = kw

        try:
            manuscript = blog_filler_pet_gen(
                user_instructions=user_input,
                ref="",
                category="애견동물_반려동물_분양",
            )
            elapsed = time.time() - start
            title = extract_title(manuscript)
            char_count = len(manuscript.replace(" ", ""))
            prev_titles.append(title)
            ending = extract_ending(title)
            prev_endings.append(ending)
            # 패턴 그룹도 추가: ~을까/~할까 → "질문형 마무리" 등
            last_word = title.strip().split()[-1] if title.strip() else ""
            if last_word.endswith(("을까", "할까", "일까")):
                prev_endings.append("~을까/~할까 질문형 마무리")
            elif last_word.endswith(("니다", "세요", "에요")):
                prev_endings.append("~합니다/~세요 존대형 마무리")
            elif last_word.endswith(("보니", "것들", "어요")):
                prev_endings.append("~보니/~것들 경험 회고형 마무리")
            print(f"  완료: {char_count}자 / {elapsed:.1f}s / 제목: {title[:50]}")

            # 프롬프트 재구성 (avoid_titles 없이 순수 프롬프트만)
            target_kw = resolve_target_keyword(keyword=kw, note="")
            intent_prompt = build_keyword_intent_prompt(
                keyword=kw, note="", target_keyword=target_kw,
            )
            pen_name = random.choice(PEN_NAMES)
            user_prompt = USER_PROMPT.format(
                keyword=kw,
                target_keyword=target_kw,
                pen_name=pen_name,
                intent_prompt=intent_prompt,
            )

            results.append({
                "no": i,
                "keyword": kw,
                "model": MODEL_NAME,
                "title": title,
                "manuscript": manuscript,
                "char_count": char_count,
                "system_prompt": SYSTEM_PROMPT,
                "user_prompt": user_prompt,
                "intent_prompt": intent_prompt,
            })
        except Exception as e:
            print(f"  실패: {e}")
            results.append({
                "no": i,
                "keyword": kw,
                "model": MODEL_NAME,
                "title": "ERROR",
                "manuscript": str(e),
                "char_count": 0,
                "system_prompt": "",
                "user_prompt": "",
                "intent_prompt": "",
            })
    return results


def export_to_sheet(results: list[dict]) -> None:
    creds_info = {
        "type": "service_account",
        "client_email": SERVICE_ACCOUNT_EMAIL,
        "private_key": PRIVATE_KEY,
        "token_uri": "https://oauth2.googleapis.com/token",
    }
    creds = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
    gc = gspread.authorize(creds)
    spreadsheet = gc.open_by_key(SPREADSHEET_ID)
    worksheet = spreadsheet.get_worksheet(0)

    worksheet.clear()
    worksheet.update(values=[HEADERS], range_name="A1:I1", value_input_option="RAW")

    rows = [[row.get(h, "") for h in HEADERS] for row in results]
    if rows:
        end_row = len(rows) + 1
        worksheet.update(
            values=rows,
            range_name=f"A2:I{end_row}",
            value_input_option="RAW",
        )

    print(f"\n시트 내보내기 완료: {spreadsheet.title} / {len(rows)}건")


def main() -> None:
    print("=" * 50)
    print("Blog Filler Pet → Google Sheets")
    print(f"키워드 {len(KEYWORDS)}개: {', '.join(KEYWORDS)}")
    print(f"모델: {MODEL_NAME}")
    print("=" * 50)

    results = generate_all()
    export_to_sheet(results)

    # 로컬 백업
    backup_path = ROOT_DIR / "test-manuscripts" / "pet_sheet_export"
    backup_path.mkdir(parents=True, exist_ok=True)
    backup_file = backup_path / f"results_{int(time.time())}.json"
    backup_file.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"백업 저장: {backup_file}")


if __name__ == "__main__":
    main()

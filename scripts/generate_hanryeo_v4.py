"""한려담원 v4 프롬프트 - 10개 키워드 원고 일괄 생성 스크립트"""

import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from llm.hanryeo_service import hanryeo_gen, MODEL_NAME
from utils.text_cleaner import comprehensive_text_clean

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "test-manuscripts", "hanryeo_v4")

KEYWORDS = [
    "소음인",
    "십전대보탕",
    "변비없는철분제",
    "손끝저림",
    "임산부 유산균",
    "염소진액효능",
    "피로회복영양제",
    "감초",
    "고등학생키크는영양제",
    "면역력높이는음식",
]


def generate_one(keyword: str, index: int) -> bool:
    print(f"\n{'='*50}")
    print(f"[{index}/{len(KEYWORDS)}] 키워드: {keyword}")
    print(f"모델: {MODEL_NAME}")
    print(f"{'='*50}")

    start = time.time()

    try:
        text = hanryeo_gen(user_instructions=keyword)
        elapsed = time.time() - start
        char_count = len(text.replace(" ", ""))

        safe_name = keyword.replace(" ", "_")
        filepath = os.path.join(OUTPUT_DIR, f"{index:02d}_{safe_name}.txt")

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(text)

        print(f"완료: {char_count}자 | {elapsed:.1f}s | {filepath}")
        return True

    except Exception as e:
        elapsed = time.time() - start
        print(f"실패: {e} | {elapsed:.1f}s")
        return False


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f"한려담원 v4 원고 생성 시작")
    print(f"키워드: {len(KEYWORDS)}개")
    print(f"모델: {MODEL_NAME}")
    print(f"출력: {OUTPUT_DIR}")

    total_start = time.time()
    success = 0
    fail = 0

    for i, kw in enumerate(KEYWORDS, 1):
        ok = generate_one(kw, i)
        if ok:
            success += 1
        else:
            fail += 1

    total_elapsed = time.time() - total_start

    print(f"\n{'='*50}")
    print(f"전체 완료: {success}성공 / {fail}실패 | {total_elapsed:.1f}s")
    print(f"출력 디렉토리: {OUTPUT_DIR}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()

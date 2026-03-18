import requests
import json
import os
import time
from datetime import datetime

API_URL = "http://localhost:8000/generate/claude"

KEYWORDS = [
    "마운자로 효과 후기",
    "알파CD 효능 부작용",
    "멜라논크림 기미 후기",
    "거북목교정기 추천",
    "유산균 추천 순위",
    "오메가3 효능 추천",
    "브로멜라인 효과 후기",
    "콜라겐 먹는 시간",
    "탈모앰플 효과 추천",
    "무궁핏 다이어트 후기",
]

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))


def generate_one(idx: int, keyword: str):
    print(f"\n[{idx+1}/10] 생성 시작: {keyword}")
    start = time.time()

    try:
        resp = requests.post(
            API_URL,
            json={"service": "claude", "keyword": keyword, "ref": ""},
            timeout=300,
        )
        elapsed = round(time.time() - start, 1)

        if resp.status_code == 200:
            data = resp.json()
            content = data.get("content", "")
            category = data.get("category", "unknown")
            engine = data.get("engine", "unknown")

            safe_name = keyword.replace(" ", "_")
            filename = f"{idx+1:02d}_{safe_name}.txt"
            filepath = os.path.join(OUTPUT_DIR, filename)

            header = f"키워드: {keyword}\n카테고리: {category}\n엔진: {engine}\n생성시간: {elapsed}s\n생성일: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n{'='*60}\n\n"

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(header + content)

            char_count = len(content.replace(" ", ""))
            print(f"    완료! {elapsed}s | {char_count}자 | {filename}")
            return True
        else:
            print(f"    실패! status={resp.status_code} | {resp.text[:200]}")
            return False

    except Exception as e:
        print(f"    에러! {e}")
        return False


if __name__ == "__main__":
    print(f"=== 자사키워드 테스트 원고 생성 ({len(KEYWORDS)}개) ===")
    print(f"저장 위치: {OUTPUT_DIR}\n")

    success = 0
    for i, kw in enumerate(KEYWORDS):
        if generate_one(i, kw):
            success += 1

    print(f"\n=== 완료: {success}/{len(KEYWORDS)} 성공 ===")

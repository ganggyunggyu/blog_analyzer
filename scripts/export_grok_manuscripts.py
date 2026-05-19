"""DB의 grok 계열 engine 원고를 최대 N건 추출 (title/content)"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from datetime import datetime
from pathlib import Path

from pymongo import MongoClient

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from _constants.categories import CATEGORIES
from config import MONGO_URI

GROK_SERVICE_REGEX = re.compile(r"(^|_)grok$", re.IGNORECASE)
DEFAULT_LIMIT = 500
DEFAULT_OUT_DIR = Path.home() / "Downloads"


def _extract_title(content: str, fallback: str) -> str:
    for line in content.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return fallback or "제목 없음"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    rows: list[dict[str, str]] = []
    seen_ids: set[str] = set()
    client = MongoClient(MONGO_URI)

    def _consume(category: str, cursor, label: str) -> int:
        kept = 0
        for doc in cursor:
            doc_id = str(doc.get("_id"))
            if doc_id in seen_ids:
                continue
            content = (doc.get("content") or "").strip()
            if not content:
                continue
            seen_ids.add(doc_id)
            title = _extract_title(content, fallback=(doc.get("keyword") or ""))
            rows.append({"title": title, "content": content})
            kept += 1
            if len(rows) >= args.limit:
                break
        if kept:
            print(f"[ {label:>5} {category:>18} ] +{kept} (총 {len(rows)})")
        return kept

    try:
        # 1) 노출 원고(isVisible=True) 모두 우선 포함
        for category in CATEGORIES:
            if len(rows) >= args.limit:
                break
            try:
                coll = client[category]["manuscripts"]
                cursor = coll.find(
                    {"isVisible": True, "deleted": {"$ne": True}},
                    {"_id": 1, "content": 1, "keyword": 1, "engine": 1},
                )
            except Exception as error:  # noqa: BLE001
                print(f"skip {category}: {error}")
                continue
            _consume(category, cursor, "노출")

        # 2) grok_service (service 가 *_grok) 라운드로빈 채우기
        per_round = 5
        round_no = 0
        exhausted: set[str] = set()
        while len(rows) < args.limit and len(exhausted) < len(CATEGORIES):
            round_no += 1
            for category in CATEGORIES:
                if len(rows) >= args.limit:
                    break
                if category in exhausted:
                    continue
                try:
                    coll = client[category]["manuscripts"]
                    cursor = coll.find(
                        {
                            "service": {"$regex": GROK_SERVICE_REGEX},
                            "deleted": {"$ne": True},
                        },
                        {"_id": 1, "content": 1, "keyword": 1, "service": 1},
                    ).skip((round_no - 1) * per_round).limit(per_round)
                except Exception as error:  # noqa: BLE001
                    print(f"skip {category}: {error}")
                    continue
                kept = _consume(category, cursor, f"grok#{round_no}")
                if kept == 0:
                    exhausted.add(category)

    finally:
        client.close()

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.out_dir / f"grok_manuscripts_{stamp}.json"
    jsonl_path = args.out_dir / f"grok_manuscripts_{stamp}.jsonl"
    csv_path = args.out_dir / f"grok_manuscripts_{stamp}.csv"

    json_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    with jsonl_path.open("w", encoding="utf-8") as fp:
        for row in rows:
            fp.write(json.dumps(row, ensure_ascii=False))
            fp.write("\n")
    with csv_path.open("w", encoding="utf-8-sig", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=["title", "content"])
        writer.writeheader()
        writer.writerows(rows)

    print()
    print(f"총 {len(rows)}건 추출 완료")
    print(f"  JSON : {json_path}")
    print(f"  JSONL: {jsonl_path}")
    print(f"  CSV  : {csv_path}")


if __name__ == "__main__":
    main()

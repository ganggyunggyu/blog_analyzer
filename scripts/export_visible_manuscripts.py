"""노출(visible) 원고를 제목/내용만 추출

각 카테고리 DB의 manuscripts 콜렉션에서 visible != False && deleted != True 인
원고를 모아 _docs/exports/ 아래에 JSON / JSONL / CSV 로 저장한다.

저장 필드는 다음 두 가지뿐:
- title   : content 의 첫 줄
- content : content 전체 (제목 포함, 원본 그대로)
"""

from __future__ import annotations

import csv
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from pymongo import MongoClient

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from _constants.categories import CATEGORIES
from config import MONGO_URI

VISIBLE_QUERY: dict[str, Any] = {
    "isVisible": True,
    "deleted": {"$ne": True},
}

EXPORT_DIR = ROOT_DIR / "_docs" / "exports"
CSV_FIELDS = ["title", "content"]


def _extract_title_and_content(document: dict[str, Any]) -> dict[str, str] | None:
    raw = document.get("content")
    if not isinstance(raw, str):
        return None

    content = raw.strip()
    if not content:
        return None

    first_line = content.splitlines()[0].strip() if content else ""
    title = first_line or (document.get("keyword") or "").strip() or "제목 없음"

    return {"title": title, "content": content}


def _iter_visible_manuscripts(client: MongoClient) -> Iterable[dict[str, str]]:
    for category in CATEGORIES:
        try:
            collection = client[category]["manuscripts"]
            total = collection.count_documents(VISIBLE_QUERY)
        except Exception as error:  # noqa: BLE001
            print(f"[skip] {category}: count 실패 ({error})")
            continue

        if total == 0:
            print(f"[ {category:>18} ] 0건")
            continue

        kept = 0
        cursor = collection.find(
            VISIBLE_QUERY,
            {"content": 1, "keyword": 1},
        ).batch_size(200)
        for document in cursor:
            row = _extract_title_and_content(document)
            if not row:
                continue
            kept += 1
            yield row

        print(f"[ {category:>18} ] {total}건 중 {kept}건 유지")


def export() -> dict[str, Any]:
    if not MONGO_URI:
        raise RuntimeError("MONGO_URI 가 설정되어 있지 않다냥")

    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    json_path = EXPORT_DIR / f"visible_manuscripts_{stamp}.json"
    jsonl_path = EXPORT_DIR / f"visible_manuscripts_{stamp}.jsonl"
    csv_path = EXPORT_DIR / f"visible_manuscripts_{stamp}.csv"

    client = MongoClient(MONGO_URI)
    rows: list[dict[str, str]] = []
    try:
        for row in _iter_visible_manuscripts(client):
            rows.append(row)
    finally:
        client.close()

    json_path.write_text(
        json.dumps(rows, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    with jsonl_path.open("w", encoding="utf-8") as fp:
        for row in rows:
            fp.write(json.dumps(row, ensure_ascii=False))
            fp.write("\n")

    with csv_path.open("w", encoding="utf-8-sig", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    summary = {
        "total": len(rows),
        "files": {
            "json": str(json_path.relative_to(ROOT_DIR)),
            "jsonl": str(jsonl_path.relative_to(ROOT_DIR)),
            "csv": str(csv_path.relative_to(ROOT_DIR)),
        },
    }

    print()
    print(f"총 {len(rows)}건 추출 완료")
    print(f"  JSON : {json_path}")
    print(f"  JSONL: {jsonl_path}")
    print(f"  CSV  : {csv_path}")
    return summary


if __name__ == "__main__":
    export()

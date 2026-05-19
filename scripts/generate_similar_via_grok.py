"""노출 원고(isVisible=True)와 유사한 형식의 원고를 grok_service로 대량 생성

- 시드: 각 카테고리 DB의 manuscripts 콜렉션에서 isVisible=True 인 원고
- 생성기: llm.grok_service.grok_gen (내부적으로 Claude Sonnet 4.6 호출)
- 결과: ~/Downloads/grok_similar_manuscripts_<stamp>.{json,jsonl,csv}
  필드는 노출 원고 export 와 동일하게 {title, content}
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any

from pymongo import MongoClient

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from _constants.categories import CATEGORIES
from config import MONGO_URI
from llm.grok_service import grok_gen

DEFAULT_TARGET = 500
DEFAULT_OUT_DIR = Path.home() / "Downloads"
DEFAULT_WORKERS = 12
PROGRESS_EVERY = 10

VISIBLE_QUERY: dict[str, Any] = {
    "isVisible": True,
    "deleted": {"$ne": True},
}


def _load_seeds() -> list[dict[str, str]]:
    client = MongoClient(MONGO_URI)
    seeds: list[dict[str, str]] = []
    try:
        for category in CATEGORIES:
            try:
                coll = client[category]["manuscripts"]
                cursor = coll.find(
                    VISIBLE_QUERY,
                    {"content": 1, "keyword": 1, "service": 1},
                )
            except Exception as error:  # noqa: BLE001
                print(f"[skip] {category}: {error}")
                continue
            for doc in cursor:
                content = (doc.get("content") or "").strip()
                keyword = (doc.get("keyword") or "").strip()
                if not keyword:
                    continue
                seeds.append(
                    {
                        "category": category,
                        "keyword": keyword,
                        "service": (doc.get("service") or category).strip(),
                        "ref": content,
                    }
                )
    finally:
        client.close()
    return seeds


def _extract_title(content: str, fallback: str) -> str:
    for line in content.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return fallback or "제목 없음"


def _save_outputs(rows: list[dict[str, str]], out_dir: Path, stamp: str) -> dict[str, str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"grok_similar_manuscripts_{stamp}.json"
    jsonl_path = out_dir / f"grok_similar_manuscripts_{stamp}.jsonl"
    csv_path = out_dir / f"grok_similar_manuscripts_{stamp}.csv"

    json_path.write_text(
        json.dumps(rows, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    with jsonl_path.open("w", encoding="utf-8") as fp:
        for row in rows:
            fp.write(json.dumps(row, ensure_ascii=False))
            fp.write("\n")
    with csv_path.open("w", encoding="utf-8-sig", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=["title", "content"])
        writer.writeheader()
        writer.writerows(rows)

    return {
        "json": str(json_path),
        "jsonl": str(jsonl_path),
        "csv": str(csv_path),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", type=int, default=DEFAULT_TARGET)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS)
    parser.add_argument(
        "--no-ref",
        action="store_true",
        help="시드 원고를 ref 로 넘기지 않음 (완전 신규 생성)",
    )
    args = parser.parse_args()

    seeds = _load_seeds()
    if not seeds:
        raise RuntimeError("isVisible=True 시드 원고를 찾지 못함냥")

    print(
        f"시드 {len(seeds)}건 로드 완료. 목표 {args.target}건 / workers={args.workers} 병렬 생성.",
        flush=True,
    )

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    rows: list[dict[str, str]] = []
    failed: list[dict[str, str]] = []
    lock = threading.Lock()

    seed_count = len(seeds)
    tasks: list[tuple[int, dict[str, str]]] = [
        (i + 1, seeds[i % seed_count]) for i in range(args.target)
    ]

    def _run(idx: int, seed: dict[str, str]) -> tuple[int, dict[str, str], dict | None]:
        keyword = seed["keyword"]
        category = seed["category"]
        ref = "" if args.no_ref else seed["ref"]
        t0 = time.time()
        last_error: str | None = None
        for attempt in range(5):
            try:
                content = grok_gen(
                    user_instructions=keyword,
                    ref=ref,
                    category=category,
                )
                title = _extract_title(content, fallback=keyword)
                return idx, seed, {
                    "title": title,
                    "content": content,
                    "elapsed": time.time() - t0,
                }
            except Exception as error:  # noqa: BLE001
                last_error = str(error)
                msg = last_error.lower()
                if "429" in msg or "rate_limit" in msg or "overload" in msg:
                    backoff = min(30 * (2 ** attempt), 240)
                    print(
                        f"    retry {attempt + 1}/5 after {backoff}s ({category}/{keyword[:20]})",
                        flush=True,
                    )
                    time.sleep(backoff)
                    continue
                break
        return idx, seed, {"error": last_error or "unknown", "elapsed": time.time() - t0}

    start_ts = time.time()
    done = 0
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(_run, idx, seed) for idx, seed in tasks]
        for future in as_completed(futures):
            idx, seed, result = future.result()
            done += 1
            if "error" in result:
                with lock:
                    failed.append(
                        {
                            "keyword": seed["keyword"],
                            "category": seed["category"],
                            "error": result["error"],
                        }
                    )
                print(
                    f"  [{done:>3}/{args.target}] FAIL {seed['category']}/{seed['keyword']}: {result['error']}",
                    flush=True,
                )
                continue
            with lock:
                rows.append({"title": result["title"], "content": result["content"]})
                snapshot = list(rows)
            print(
                f"  [{done:>3}/{args.target}] OK   {seed['category']:>14}/{seed['keyword'][:24]:<24} "
                f"len={len(result['content']):>5} ({result['elapsed']:.1f}s)",
                flush=True,
            )
            if done % PROGRESS_EVERY == 0:
                _save_outputs(snapshot, args.out_dir, stamp)

    paths = _save_outputs(rows, args.out_dir, stamp)
    total_elapsed = time.time() - start_ts

    print()
    print(f"완료: 성공 {len(rows)}건 / 실패 {len(failed)}건 / {total_elapsed:.1f}s")
    for key, path in paths.items():
        print(f"  {key.upper():<5}: {path}")

    if failed:
        fail_path = args.out_dir / f"grok_similar_manuscripts_{stamp}.failed.json"
        fail_path.write_text(
            json.dumps(failed, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"  FAIL : {fail_path}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n중단됨")
    except Exception:  # noqa: BLE001
        traceback.print_exc()
        sys.exit(1)

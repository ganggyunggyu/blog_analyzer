"""manuscripts 콜렉션 visible/발행 필드 분포 점검"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from pymongo import MongoClient

from _constants.categories import CATEGORIES
from config import MONGO_URI


def main() -> None:
    client = MongoClient(MONGO_URI)
    try:
        big_cats = ["기타", "영양제", "안과", "다이어트"]
        for category in big_cats:
            coll = client[category]["manuscripts"]
            total = coll.count_documents({})
            visible_true = coll.count_documents({"visible": True})
            visible_false = coll.count_documents({"visible": False})
            visible_absent = coll.count_documents({"visible": {"$exists": False}})
            deleted_true = coll.count_documents({"deleted": True})

            print(f"\n=== {category} (총 {total:,}) ===")
            print(f"  visible=True   : {visible_true:,}")
            print(f"  visible=False  : {visible_false:,}")
            print(f"  visible 없음    : {visible_absent:,}")
            print(f"  deleted=True   : {deleted_true:,}")

            sample = coll.find_one({}, {"content": 0})
            if sample:
                keys = sorted(sample.keys())
                print(f"  샘플 필드: {keys}")

            for field in ("posted", "published", "exposed", "post_url", "url", "blogPostUrl", "publishedAt", "exposureChecked", "exposureCheckedAt"):
                cnt = coll.count_documents({field: {"$exists": True}})
                if cnt:
                    print(f"  {field} 존재: {cnt:,}")
    finally:
        client.close()


if __name__ == "__main__":
    main()

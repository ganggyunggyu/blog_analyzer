from __future__ import annotations

import argparse
import json
import random
import re
import sys
from datetime import datetime
from difflib import SequenceMatcher
from itertools import combinations
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


TITLE_FILLER_WORDS: set[str] = {
    "비용",
    "가격",
    "분양가",
    "현실",
    "체크리스트",
    "총정리",
    "가이드",
    "필독",
    "특징",
    "성격",
    "주의사항",
    "기본",
    "정보",
    "입양",
    "분양",
    "전",
    "알아야",
    "알아보자",
    "실제",
    "초보자",
}

MAX_TITLE_SIMILARITY = 0.78
MAX_CORE_OVERLAP = 0.67
MAX_RETRIES_PER_TITLE = 8
DEFAULT_SAMPLE_SET = "representative"
DEFAULT_SAMPLE_SET_SEED = 20260331
TITLE_ANGLE_IDS: tuple[str, ...] = (
    "price_summary",
    "reality_question",
    "must_read",
    "basics_guide",
    "mistake_prevention",
    "checklist",
    "temperament_focus",
    "hidden_cost",
    "health_warning",
    "owner_story",
)
PET_V2_SERVICE = None

SAMPLE_KEYWORD_SETS: dict[str, tuple[str, ...]] = {
    "representative": (
        "시바견분양",
        "토이푸들 분양가",
        "광주동물보호소",
        "입양조건",
        "아메리칸숏헤어",
        "웰시코기",
        "말티즈분양",
        "강아지 종류",
    )
}


def get_pet_v2_service():
    global PET_V2_SERVICE

    if PET_V2_SERVICE is None:
        from llm import blog_filler_pet_v2_service as pet_v2_service

        PET_V2_SERVICE = pet_v2_service

    return PET_V2_SERVICE


def get_angle_ids() -> list[str]:
    return list(TITLE_ANGLE_IDS)


def tokenize_title(text: str) -> list[str]:
    cleaned = re.sub(r"[^0-9A-Za-z가-힣 ]+", " ", text)
    return [token for token in cleaned.split() if token]


def get_title_core_tokens(title: str, keyword: str) -> tuple[str, ...]:
    keyword_tokens = set(tokenize_title(keyword))
    tokens = tokenize_title(title)
    return tuple(
        token
        for token in tokens
        if token not in keyword_tokens and token not in TITLE_FILLER_WORDS
    )


def get_title_similarity(title: str, previous_titles: list[str]) -> tuple[float, str]:
    if not previous_titles:
        return 0.0, ""

    scored = [
        (SequenceMatcher(None, title, previous_title).ratio(), previous_title)
        for previous_title in previous_titles
    ]
    return max(scored, key=lambda item: item[0])


def get_core_overlap(
    title: str, keyword: str, previous_titles: list[str]
) -> tuple[float, str]:
    current_tokens = set(get_title_core_tokens(title=title, keyword=keyword))

    if not current_tokens or not previous_titles:
        return 0.0, ""

    best_score = 0.0
    best_title = ""

    for previous_title in previous_titles:
        previous_tokens = set(
            get_title_core_tokens(title=previous_title, keyword=keyword)
        )
        if not previous_tokens:
            continue

        overlap = len(current_tokens & previous_tokens) / len(
            current_tokens | previous_tokens
        )
        if overlap > best_score:
            best_score = overlap
            best_title = previous_title

    return best_score, best_title


def build_user_instructions(keyword: str, angle_id: str, avoid_titles: list[str]) -> str:
    note_parts = [f"title_angle={angle_id}"]

    if avoid_titles:
        note_parts.append(f"avoid_titles={' || '.join(avoid_titles[-6:])}")

    return f"{keyword} ({'; '.join(note_parts)})"


def generate_candidate(keyword: str, angle_id: str, avoid_titles: list[str]) -> dict:
    pet_v2_service = get_pet_v2_service()
    user_instructions = build_user_instructions(
        keyword=keyword,
        angle_id=angle_id,
        avoid_titles=avoid_titles,
    )
    text = pet_v2_service.blog_filler_pet_v2_gen(user_instructions)
    title = text.splitlines()[0].strip() if text.strip() else ""
    target_keyword = pet_v2_service.resolve_target_keyword(keyword=keyword)
    issues = pet_v2_service.find_quality_issues(
        keyword=keyword,
        text=text,
        target_keyword=target_keyword,
    )
    chars_no_spaces = len(text.replace("\n", "").replace(" ", ""))
    subtitle_count = pet_v2_service.count_numbered_subtitles(text)

    return {
        "text": text,
        "title": title,
        "issues": issues,
        "chars_no_spaces": chars_no_spaces,
        "subtitle_count": subtitle_count,
        "angle_id": angle_id,
    }


def get_output_path(root: str) -> Path:
    return Path(root) / datetime.now().strftime("%Y%m%d_%H%M%S")


def get_keyword_filename(keyword: str) -> str:
    safe_keyword = re.sub(r"\s+", "_", keyword.strip())
    safe_keyword = re.sub(r"[^0-9A-Za-z가-힣_]+", "", safe_keyword)
    return safe_keyword or "keyword"


def print_sample_plan(
    sample_set: str, seed: int, plan: list[dict[str, object]]
) -> None:
    print(f"SAMPLE_SET={sample_set}")
    print(f"SEED={seed}")
    print(f"KEYWORD_COUNT={len(plan)}")
    for row in plan:
        print(
            f"{int(row['index']):02d}|keyword={row['keyword']}|"
            f"start_angle={row['angle_id']}"
        )


def run_single_keyword_validation(keyword: str, count: int) -> None:
    angle_ids = get_angle_ids()
    random.shuffle(angle_ids)

    out_dir = get_output_path("test-manuscripts/pet_v2_title_compare_feedback")
    out_dir.mkdir(parents=True, exist_ok=True)

    accepted_titles: list[str] = []
    rows: list[dict[str, object]] = []

    for idx in range(1, count + 1):
        best_candidate: dict[str, object] | None = None
        best_score: tuple | None = None

        for retry in range(MAX_RETRIES_PER_TITLE):
            angle_id = angle_ids[(idx - 1 + retry) % len(angle_ids)]
            candidate = generate_candidate(
                keyword=keyword,
                angle_id=angle_id,
                avoid_titles=accepted_titles,
            )

            title_similarity, similar_title = get_title_similarity(
                title=candidate["title"],
                previous_titles=accepted_titles,
            )
            core_overlap, overlap_title = get_core_overlap(
                title=candidate["title"],
                keyword=keyword,
                previous_titles=accepted_titles,
            )

            diversity_issues: list[str] = []
            if title_similarity >= MAX_TITLE_SIMILARITY:
                diversity_issues.append(
                    f"제목 문자열 유사도 {title_similarity:.3f}가 높습니다"
                )
            if core_overlap >= MAX_CORE_OVERLAP:
                diversity_issues.append(
                    f"제목 핵심 토큰 겹침 {core_overlap:.3f}가 높습니다"
                )

            all_issues = [*candidate["issues"], *diversity_issues]
            score = (
                len(all_issues),
                round(title_similarity, 3),
                round(core_overlap, 3),
                -candidate["chars_no_spaces"],
            )

            candidate.update(
                {
                    "retry": retry + 1,
                    "title_similarity": title_similarity,
                    "similar_title": similar_title,
                    "core_overlap": core_overlap,
                    "overlap_title": overlap_title,
                    "all_issues": all_issues,
                }
            )

            if best_candidate is None or score < best_score:
                best_candidate = candidate
                best_score = score

            if not all_issues:
                break

        assert best_candidate is not None

        path = out_dir / f"{idx:02d}_{get_keyword_filename(keyword)}.txt"
        path.write_text(str(best_candidate["text"]), encoding="utf-8")
        best_candidate["path"] = str(path)
        rows.append(best_candidate)
        accepted_titles.append(str(best_candidate["title"]))

        issue_text = "PASS" if not best_candidate["all_issues"] else " / ".join(
            list(best_candidate["all_issues"])
        )
        print(
            f"{idx:02d}|angle={best_candidate['angle_id']}|retry={best_candidate['retry']}|"
            f"title={best_candidate['title']}|subtitles={best_candidate['subtitle_count']}|"
            f"chars={best_candidate['chars_no_spaces']}|sim={best_candidate['title_similarity']:.3f}|"
            f"core={best_candidate['core_overlap']:.3f}|issues={issue_text}"
        )

    pair_scores = []
    for left, right in combinations(rows, 2):
        score = SequenceMatcher(None, left["title"], right["title"]).ratio()
        pair_scores.append((score, left["title"], right["title"]))

    summary_lines: list[str] = []
    for idx, row in enumerate(rows, start=1):
        issue_text = "PASS" if not row["all_issues"] else " / ".join(row["all_issues"])
        summary_lines.append(
            f"{idx:02d}. {row['title']} | angle={row['angle_id']} | retry={row['retry']} | "
            f"subtitles={row['subtitle_count']} | chars={row['chars_no_spaces']} | "
            f"sim={row['title_similarity']:.3f} | core={row['core_overlap']:.3f} | issues={issue_text}"
        )

    summary_lines.append("")
    summary_lines.append("PAIRWISE TITLE SIMILARITY TOP 15")
    for score, left_title, right_title in sorted(pair_scores, reverse=True)[:15]:
        summary_lines.append(f"{score:.3f} | {left_title} || {right_title}")

    summary_path = out_dir / "title_summary.txt"
    summary_path.write_text("\n".join(summary_lines), encoding="utf-8")

    print(f"SUMMARY={summary_path}")
    print(f"DIR={out_dir}")


def get_sample_plan(sample_set: str) -> list[dict[str, object]]:
    keywords = SAMPLE_KEYWORD_SETS[sample_set]
    angle_ids = get_angle_ids()

    return [
        {
            "index": idx,
            "keyword": keyword,
            "angle_id": angle_ids[(idx - 1) % len(angle_ids)],
        }
        for idx, keyword in enumerate(keywords, start=1)
    ]


def run_sample_validation(sample_set: str, seed: int, dry_run: bool) -> None:
    random.seed(seed)
    plan = get_sample_plan(sample_set=sample_set)

    if dry_run:
        print_sample_plan(sample_set=sample_set, seed=seed, plan=plan)
        return

    out_dir = get_output_path("test-manuscripts/pet_v2_title_sample_validation")
    out_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, object]] = []

    for row in plan:
        index = int(row["index"])
        keyword = str(row["keyword"])
        start_angle_id = str(row["angle_id"])
        angle_ids = get_angle_ids()
        start_angle_index = angle_ids.index(start_angle_id)
        best_candidate: dict[str, object] | None = None
        best_score: tuple | None = None

        for retry in range(MAX_RETRIES_PER_TITLE):
            angle_id = angle_ids[(start_angle_index + retry) % len(angle_ids)]
            candidate = generate_candidate(
                keyword=keyword,
                angle_id=angle_id,
                avoid_titles=[],
            )
            candidate.update(
                {
                    "keyword": keyword,
                    "sample_index": index,
                    "retry": retry + 1,
                }
            )
            score = (
                len(candidate["issues"]),
                abs(5 - int(candidate["subtitle_count"])),
                -int(candidate["chars_no_spaces"]),
                retry + 1,
            )

            if best_candidate is None or score < best_score:
                best_candidate = candidate
                best_score = score

            if not candidate["issues"]:
                break

        assert best_candidate is not None

        path = out_dir / f"{index:02d}_{get_keyword_filename(keyword)}.txt"
        path.write_text(str(best_candidate["text"]), encoding="utf-8")
        best_candidate["path"] = str(path)
        rows.append(best_candidate)

        issue_text = "PASS" if not best_candidate["issues"] else " / ".join(
            list(best_candidate["issues"])
        )
        print(
            f"{index:02d}|keyword={keyword}|angle={best_candidate['angle_id']}|retry={best_candidate['retry']}|"
            f"title={best_candidate['title']}|subtitles={best_candidate['subtitle_count']}|"
            f"chars={best_candidate['chars_no_spaces']}|issues={issue_text}"
        )

    pass_count = sum(1 for row in rows if not row["issues"])
    fail_count = len(rows) - pass_count

    summary_lines = [
        f"SAMPLE_SET={sample_set}",
        f"SEED={seed}",
        f"KEYWORD_COUNT={len(rows)}",
        f"PASS_COUNT={pass_count}",
        f"FAIL_COUNT={fail_count}",
        "",
    ]

    for row in rows:
        issue_text = "PASS" if not row["issues"] else " / ".join(list(row["issues"]))
        summary_lines.append(
            f"{int(row['sample_index']):02d}. {row['keyword']} | angle={row['angle_id']} | retry={row['retry']} | "
            f"title={row['title']} | subtitles={row['subtitle_count']} | chars={row['chars_no_spaces']} | "
            f"issues={issue_text}"
        )

    summary_payload = {
        "sample_set": sample_set,
        "seed": seed,
        "keyword_count": len(rows),
        "pass_count": pass_count,
        "fail_count": fail_count,
        "rows": rows,
    }

    summary_path = out_dir / "sample_summary.txt"
    summary_json_path = out_dir / "sample_summary.json"
    summary_path.write_text("\n".join(summary_lines), encoding="utf-8")
    summary_json_path.write_text(
        json.dumps(summary_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"SUMMARY={summary_path}")
    print(f"SUMMARY_JSON={summary_json_path}")
    print(f"DIR={out_dir}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("keyword", nargs="?")
    parser.add_argument("--count", type=int, default=10)
    parser.add_argument(
        "--sample-set",
        choices=sorted(SAMPLE_KEYWORD_SETS),
        help="고정 대표 키워드 샘플 세트 검증 실행",
    )
    parser.add_argument(
        "--seed",
        type=int,
        help="랜덤 시드 고정값. 샘플 세트 모드에서는 기본값이 자동 적용됩니다",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="샘플 세트 계획만 출력하고 생성은 실행하지 않습니다",
    )
    args = parser.parse_args()

    if args.keyword and args.sample_set:
        parser.error("keyword 와 --sample-set 은 동시에 사용할 수 없습니다")

    if not args.keyword and not args.sample_set:
        parser.error("keyword 또는 --sample-set 중 하나는 반드시 필요합니다")

    if args.sample_set:
        seed = args.seed if args.seed is not None else DEFAULT_SAMPLE_SET_SEED
        run_sample_validation(
            sample_set=args.sample_set,
            seed=seed,
            dry_run=args.dry_run,
        )
        return

    if args.seed is not None:
        random.seed(args.seed)

    run_single_keyword_validation(keyword=args.keyword.strip(), count=args.count)


if __name__ == "__main__":
    main()

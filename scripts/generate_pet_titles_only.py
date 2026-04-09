# ruff: noqa: E402

from __future__ import annotations

import argparse
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

from _constants.Model import Model
from llm.blog_filler_pet_v2_service import (
    TITLE_ANGLE_RULES,
    TITLE_OPENING_RULES,
    resolve_target_keyword,
    tokenize_title,
)
from utils.ai_client_factory import call_ai


MODEL_NAME = Model.GROK_4_1_NON_RES
MAX_SIMILARITY = 0.78
MAX_TITLE_RETRIES = 8

SYSTEM_PROMPT = """You are a Korean Naver SEO title strategist for pet blog posts.
Return exactly one title only.
No labels, no markdown, no quotes, no bullet points.
Use natural Korean only.
Keep the title concise and searchable.
The title must keep the main keyword intact.
Observed current Naver VIEW title patterns for pet adoption/distribution keywords include:
- price summary type
- must-read before adoption type
- reality question type
- basic info guide type
- failure prevention type
- checklist type
- owner story type
Make each title feel materially different in rhythm and angle."""


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", "", text.strip().lower())


def get_similarity(title: str, previous_titles: list[str]) -> tuple[float, str]:
    if not previous_titles:
        return 0.0, ""

    scored = [
        (SequenceMatcher(None, title, previous_title).ratio(), previous_title)
        for previous_title in previous_titles
    ]
    return max(scored, key=lambda item: item[0])


def get_post_keyword_opening(title: str, keyword: str) -> str:
    title = title.strip()
    keyword = keyword.strip()

    if title.startswith(keyword):
        remainder = title[len(keyword) :].strip(" ,.!?·:;")
        next_token = remainder.split()[0].strip(" ,.!?·:;") if remainder else ""
        return next_token

    return tokenize_title(title)[0] if tokenize_title(title) else ""


def build_user_prompt(
    keyword: str,
    target_keyword: str,
    angle_rule: dict[str, str],
    opening_rule: dict[str, str],
    previous_titles: list[str],
    previous_openings: list[str],
) -> str:
    lines = [
        f"keyword: {keyword}",
        f"target_keyword: {target_keyword}",
        f"title_angle: {angle_rule['label']}",
        f"title_rule: {angle_rule['rule']}",
        f"title_example: {angle_rule['example']}",
        f"title_opening: {opening_rule['label']}",
        f"title_opening_rule: {opening_rule['rule']}",
        f"title_opening_example: {opening_rule['example']}",
        "requirements:",
        "- title must contain the main keyword naturally",
        "- title should not repeat the exact rhythm of earlier titles",
        "- avoid generic four-word stacking every time",
        "- vary between summary, must-read, question, guide, failure-prevention, and story angles",
        "- do not keep starting with keyword + 전 or keyword + 후 repeatedly",
    ]

    if previous_titles:
        lines.append("avoid_titles:")
        lines.extend(f"- {title}" for title in previous_titles[-6:])

    if previous_openings:
        lines.append("avoid_openings:")
        lines.extend(f"- {opening}" for opening in previous_openings[-6:])

    return "\n".join(lines)


def generate_title(
    keyword: str,
    target_keyword: str,
    angle_rule: dict[str, str],
    opening_rule: dict[str, str],
    previous_titles: list[str],
    previous_openings: list[str],
) -> str:
    user_prompt = build_user_prompt(
        keyword=keyword,
        target_keyword=target_keyword,
        angle_rule=angle_rule,
        opening_rule=opening_rule,
        previous_titles=previous_titles,
        previous_openings=previous_openings,
    )
    title = call_ai(
        model_name=MODEL_NAME,
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
    )
    return title.strip().splitlines()[0].strip()


def validate_title(
    title: str,
    keyword: str,
    previous_titles: list[str],
    previous_openings: list[str],
) -> tuple[list[str], float, str, str]:
    issues: list[str] = []

    if not title:
        issues.append("제목이 비어 있습니다")

    normalized_title = normalize_text(title)
    normalized_keyword = normalize_text(keyword)

    if normalized_keyword not in normalized_title:
        issues.append("핵심 키워드가 제목에 그대로 유지되지 않았습니다")

    if '"' in title or "'" in title:
        issues.append("따옴표가 포함되어 있습니다")

    if re.search(r"[ぁ-ゟ゠-ヿ]", title):
        issues.append("일본어 문자가 섞여 있습니다")

    if len(title) < 14 or len(title) > 36:
        issues.append("제목 길이가 14~36자 범위를 벗어났습니다")

    similarity, similar_title = get_similarity(title=title, previous_titles=previous_titles)
    if similarity >= MAX_SIMILARITY:
        issues.append(f"이전 제목과 문자열 유사도 {similarity:.3f}로 높습니다")

    opening = get_post_keyword_opening(title=title, keyword=keyword)
    if opening and previous_openings.count(opening) >= 1:
        issues.append(f"제목 시작 리듬 {opening} 이 반복됩니다")
    if opening in {"전", "후"} and opening in previous_openings:
        issues.append(f"제목 시작 리듬이 keyword + {opening} 으로 다시 반복됩니다")

    return issues, similarity, similar_title, opening


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("keyword")
    parser.add_argument("--count", type=int, default=10)
    args = parser.parse_args()

    keyword = args.keyword.strip()
    target_keyword = resolve_target_keyword(keyword=keyword)

    angle_rules = TITLE_ANGLE_RULES[:]
    random.shuffle(angle_rules)
    opening_rules = TITLE_OPENING_RULES[:]
    random.shuffle(opening_rules)

    out_dir = (
        Path("test-manuscripts/pet_v2_titles_only")
        / datetime.now().strftime("%Y%m%d_%H%M%S")
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, object]] = []
    accepted_titles: list[str] = []
    accepted_openings: list[str] = []

    for idx in range(1, args.count + 1):
        best_row: dict[str, object] | None = None
        best_score: tuple | None = None

        for retry in range(MAX_TITLE_RETRIES):
            angle_rule = angle_rules[(idx - 1 + retry) % len(angle_rules)]
            opening_rule = opening_rules[(idx - 1 + retry) % len(opening_rules)]
            title = generate_title(
                keyword=keyword,
                target_keyword=target_keyword,
                angle_rule=angle_rule,
                opening_rule=opening_rule,
                previous_titles=accepted_titles,
                previous_openings=accepted_openings,
            )
            issues, similarity, similar_title, opening = validate_title(
                title=title,
                keyword=keyword,
                previous_titles=accepted_titles,
                previous_openings=accepted_openings,
            )
            row = {
                "idx": idx,
                "title": title,
                "angle_id": angle_rule["id"],
                "opening_id": opening_rule["id"],
                "retry": retry + 1,
                "issues": issues,
                "similarity": similarity,
                "similar_title": similar_title,
                "opening": opening,
            }
            score = (len(issues), round(similarity, 3), len(title))
            if best_row is None or score < best_score:
                best_row = row
                best_score = score
            if not issues:
                break

        assert best_row is not None
        rows.append(best_row)
        accepted_titles.append(str(best_row["title"]))
        accepted_openings.append(str(best_row["opening"]))

        issue_text = "PASS" if not best_row["issues"] else " / ".join(best_row["issues"])
        print(
            f"{idx:02d}|angle={best_row['angle_id']}|opening={best_row['opening_id']}|retry={best_row['retry']}|"
            f"title={best_row['title']}|sim={best_row['similarity']:.3f}|issues={issue_text}"
        )

    pair_scores = []
    for left, right in combinations(rows, 2):
        score = SequenceMatcher(
            None,
            str(left["title"]),
            str(right["title"]),
        ).ratio()
        pair_scores.append((score, str(left["title"]), str(right["title"])))

    summary_lines: list[str] = []
    for row in rows:
        issue_text = "PASS" if not row["issues"] else " / ".join(row["issues"])
        summary_lines.append(
            f"{row['idx']:02d}. {row['title']} | angle={row['angle_id']} | opening={row['opening_id']} | retry={row['retry']} | "
            f"sim={row['similarity']:.3f} | issues={issue_text}"
        )

    summary_lines.append("")
    summary_lines.append("PAIRWISE TITLE SIMILARITY TOP 15")
    for score, left_title, right_title in sorted(pair_scores, reverse=True)[:15]:
        summary_lines.append(f"{score:.3f} | {left_title} || {right_title}")

    summary_path = out_dir / "title_summary.txt"
    summary_path.write_text("\n".join(summary_lines))

    print(f"SUMMARY={summary_path}")
    print(f"DIR={out_dir}")


if __name__ == "__main__":
    main()

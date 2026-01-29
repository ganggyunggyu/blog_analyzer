from __future__ import annotations
from datetime import datetime
from typing import List, Optional
import time
import json
import re

from _constants.Model import Model
from mongodb_service import MongoDBService
from utils.ai_client_factory import call_ai
from utils.logger import log


model_name: str = Model.GROK_4_1_RES


def gen_subtitles(
    full_text: str,
    category: str = "",
    file_name: str = "",
    model_name_override: Optional[str] = None,
    max_items: int = 5,
) -> List[str]:
    db_service = MongoDBService()
    if category:
        db_service.set_db_name(category)

    model = model_name_override or model_name

    system = """
You are a precise subtitle extractor for Korean blog manuscripts. Return ONLY JSON. No commentary.
""".strip()

    prompt = f"""
다음은 하나의 블로그 원고 본문입니다. 이 글의 **부제목(소제목)** 으로 적절한 문구만 추출해.
- 한국어, 간결(최대 25~35자), 완결된 명사구/짧은 구
- 번호/이모지/특수문자/해시태그/따옴표/마침표 제거
- 본문 흐름을 잘 나누는 핵심 소제목 위주
- 중복/의미 중복 제거
- {max_items}개 이내

[원고]
{full_text}

[반환 JSON 스키마]
{{
  "subtitles": [
    {{"index": 1, "text": "부제목1"}},
    {{"index": 2, "text": "부제목2"}}
  ]
}}
JSON만 반환해.
""".strip()

    start_ts = time.time()

    try:
        text_content = call_ai(
            model_name=model,
            system_prompt=system,
            user_prompt=prompt,
        )
        subtitles = parse_subtitle_response(text_content)
    except Exception:
        subtitles = rule_based_subtitles(full_text)[:max_items]

    # MongoDB에 저장
    now = datetime.now()
    docs_to_save = [
        {
            "timestamp": now,
            "file_name": file_name,
            "db_category": category,
            "category": "subtitle",
            "subtitle": subtitle,
        }
        for subtitle in subtitles
    ]

    if docs_to_save:
        db_service.insert_many_documents("subtitles", docs_to_save)

    elapsed = time.time() - start_ts
    log.info(f"부제목 추출 완료", 소요시간=f"{elapsed:.1f}s", 개수=len(subtitles))

    db_service.close_connection()

    return subtitles


def parse_subtitle_response(text_content: str) -> List[str]:
    content = text_content.strip()
    normalized = strip_code_fence(content)
    data = json.loads(normalized)
    raw_items = data.get("subtitles", []) if isinstance(data, dict) else []

    subtitles: List[str] = []
    for item in raw_items:
        if isinstance(item, dict) and "text" in item:
            subtitles.append(str(item["text"]))
        elif isinstance(item, str):
            subtitles.append(item)
    return subtitles


def strip_code_fence(text: str) -> str:
    if text.startswith("```"):
        return re.sub(
            r"^```(?:json)?\s*|\s*```$",
            "",
            text,
            flags=re.IGNORECASE | re.DOTALL,
        ).strip()
    return text


def normalize_subtitle(s: str) -> str:
    s = (s or "").strip()
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"[\"'·•▷▶️\-\–\—\·\•\●\■\□\◇\◆\+]+", "", s).strip()
    s = re.sub(r"[.!?]+$", "", s).strip()
    if len(s) > 40:
        s = s[:40].strip()
    return s


def dedupe_keeping_order(items: List[str]) -> List[str]:
    seen = set()
    ordered: List[str] = []
    for item in items:
        if not item:
            continue
        key = item.lower()
        if key in seen:
            continue
        seen.add(key)
        ordered.append(item)
    return ordered


def rule_based_subtitles(full_text: str) -> List[str]:
    lines = [re.sub(r"\s+", " ", ln).strip() for ln in full_text.splitlines()]
    lines = [ln for ln in lines if ln]

    heads: List[str] = []
    pat_num = re.compile(r"^(?:\d+\.|\d+\)|\(\d+\))\s*")
    cue_words = [
        "섭취 시 주의사항",
        "주의사항",
        "추천해요",
        "추천 대상",
        "효과",
        "변화",
        "비용",
        "정리",
        "체감한 시점",
        "복용 방법",
        "복용 시간",
        "TIP",
        "체크포인트",
        "결론",
        "한줄평",
    ]

    for line in lines:
        if pat_num.match(line):
            heads.append(pat_num.sub("", line))
            continue
        if any(cue in line for cue in cue_words):
            heads.append(line)
            continue

    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", full_text) if p.strip()]
    for paragraph in paragraphs:
        first_sentence = re.split(r"(?<=[.!?。…])\s+", paragraph.strip())[0]
        if len(first_sentence) > 10:
            heads.append(first_sentence)

    heads = [normalize_subtitle(head) for head in heads]
    heads = [head for head in heads if 4 <= len(head) <= 40]
    heads = dedupe_keeping_order(heads)
    return heads[:12]

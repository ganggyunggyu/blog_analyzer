# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import re
from typing import List, Dict, Any, Optional

from openai import OpenAI
from config import OPENAI_API_KEY

from constants.Model import Model

# 필요하면 네 프로젝트 상수에 맞춰 치환해도 됨
_DEFAULT_MODEL = Model.GPT5_MINI   # or constants.Model.GPT4_1.value


def _normalize_subtitle(s: str) -> str:
    """부제 정규화: 공백/기호 정리, 끝문장부호 제거, 과도한 띄어쓰기 축소."""
    s = (s or "").strip()
    # 불필요한 공백/중복 기호
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"[\"'·•▷▶️\-\–\—\·\•\●\■\□\◇\◆\+]+", "", s).strip()
    # 문장 끝 마침표/느낌표/물음표 제거
    s = re.sub(r"[.!?]+$", "", s).strip()
    # 너무 긴 경우 컷(콘텐츠 스타일에 맞춰 30~40자 추천)
    if len(s) > 40:
        s = s[:40].strip()
    return s


def _dedupe_keeping_order(items: List[str]) -> List[str]:
    seen = set()
    out = []
    for x in items:
        if not x:
            continue
        key = x.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(x)
    return out


def _rule_based_subtitles(full_text: str) -> List[str]:
    """
    백업용: 헤더/번호/전환 신호로 섹션 후보를 잡아 부제 추출.
    - '1.', '2.', '3.' 등 번호
    - '섭취 시 주의사항', '추천해요' 같은 전환 키워드
    - 문단 첫 문장 요약
    """
    lines = [re.sub(r"\s+", " ", ln).strip() for ln in full_text.splitlines()]
    lines = [ln for ln in lines if ln]  # 빈 줄 제거

    # 섹션 신호 패턴
    heads: List[str] = []
    pat_num = re.compile(r"^(?:\d+\.|\d+\)|\(\d+\))\s*")
    cue_words = [
        "섭취 시 주의사항", "주의사항", "추천해요", "추천 대상", "효과", "변화", "비용", "정리",
        "체감한 시점", "복용 방법", "복용 시간", "TIP", "체크포인트", "결론", "한줄평",
    ]

    for ln in lines:
        if pat_num.match(ln):
            heads.append(pat_num.sub("", ln))
            continue
        # 전환 키워드 포함 줄
        if any(cw in ln for cw in cue_words):
            heads.append(ln)
            continue

    # 문단 첫 문장들도 후보에 추가(너무 길면 컷)
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", full_text) if p.strip()]
    for p in paragraphs:
        first = re.split(r"(?<=[.!?。…])\s+", p.strip())[0]
        if len(first) > 10:
            heads.append(first)

    # 정리
    heads = [_normalize_subtitle(h) for h in heads]
    heads = [h for h in heads if 4 <= len(h) <= 40]
    heads = _dedupe_keeping_order(heads)

    # 과도하면 상위 10~15개로 컷
    return heads[:12]


def extract_subtitles_with_ai(
    full_text: str,
    model_name: Optional[str] = None,
    max_items: int = 12,
) -> List[str]:
    """
    원고 본문에서 '부제목(소제목)'만 뽑아 리스트로 반환.
    1) OpenAI JSON 지시로 추출
    2) 실패/비정상 응답 시 룰 기반 백업

    Returns:
        subtitles: List[str]  # 정규화/중복 제거된 부제들
    """
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY가 설정되어 있지 않습니다. .env를 확인하세요.")

    model = model_name or _DEFAULT_MODEL
    client = OpenAI(api_key=OPENAI_API_KEY)

    # 모델에게 강하게 JSON만 요구
    system = (
        "You are a precise subtitle extractor for Korean blog manuscripts. "
        "Return ONLY JSON. No commentary."
    )

    user = f"""다음은 하나의 블로그 원고 본문입니다. 이 글의 **부제목(소제목)** 으로 적절한 문구만 추출해.
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
"""

    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            # 최신 SDK에서 지원되면 주석 해제해 더 안전하게 JSON 강제
            # response_format={"type": "json_object"},
            # temperature=0.2,
        )

        content = (resp.choices[0].message.content or "").strip()

        # 모델이 가끔 코드펜스로 감싸는 경우 제거
        if content.startswith("```"):
            content = re.sub(r"^```(?:json)?\s*|\s*```$", "", content.strip(), flags=re.IGNORECASE | re.DOTALL)

        data: Dict[str, Any] = json.loads(content)
        raw_items = data.get("subtitles", []) if isinstance(data, dict) else []

        # 안전 파싱
        texts = []
        for item in raw_items:
            if isinstance(item, dict) and "text" in item:
                texts.append(str(item["text"]))
            elif isinstance(item, str):
                texts.append(item)

        # 정규화/필터/중복 제거
        # texts = [_normalize_subtitle(t) for t in texts]
        # texts = [t for t in texts if 4 <= len(t) <= 40]
        # texts = _dedupe_keeping_order(texts)[:max_items]

        # # 비정상/빈 결과면 백업
        # if not texts:
        #     return _rule_based_subtitles(full_text)[:max_items]
        print(texts)
        return texts

    except Exception as e:
        # 완전 실패 시 백업
        print(f"[extract_subtitles_with_ai] OpenAI 호출 실패 -> 룰기반 백업 사용: {e}")
        return _rule_based_subtitles(full_text)[:max_items]
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import re
from typing import Dict, Any, Optional

from openai import OpenAI
from config import OPENAI_API_KEY
from constants.Model import Model

_DEFAULT_MODEL = Model.GPT5_MINI


def _extract_json_block(text: str) -> Optional[str]:
    """응답에서 JSON 오브젝트 부분만 안전하게 추출."""
    if not text:
        return None

    # 코드펜스 제거
    if text.strip().startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.IGNORECASE | re.DOTALL)

    # 전체가 JSON이면 그대로
    try:
        json.loads(text)
        return text
    except Exception:
        pass

    # 가장 바깥 {} 블록만 긁어오기
    m = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if m:
        candidate = m.group(0)
        try:
            json.loads(candidate)
            return candidate
        except Exception:
            return None
    return None


def extract_and_group_entities_with_ai(
    full_text: str,
    model_name: str = _DEFAULT_MODEL,
    client: Optional[OpenAI] = None,
) -> Dict[str, list]:
    """
    원고 내용에서 반복/대체 가능한 '핵심 개체'를 추출하고 의미별 그룹화.
    - JSON만 반환하도록 모델에 지시
    - 응답이 어겨져도 최대한 복구해서 dict 반환
    - 실패 시 빈 dict 반환(타입 안정)

    Returns:
        Dict[str, list]  예) {"상호명": ["땀땀","토끼정"], "제품명": ["갤럭시S24","아이폰16"]}
    """
    if not OPENAI_API_KEY:
        raise ValueError("API 키가 설정되지 않았습니다. .env 파일에 OPENAI_API_KEY를 추가해주세요.")

    client = client or OpenAI(api_key=OPENAI_API_KEY)

    system = (
        "You are an expert in Named Entity Recognition and text analysis. "
        "Extract key entities and group them semantically. Return ONLY JSON."
    )

    user = f"""다음은 여러 블로그 원고를 합친 텍스트입니다.

[원고 내용]
{full_text}

[요청]
위 원고 내용에서 반복적으로 나타나거나, 대체 가능한 핵심 개체(entity)들을 모두 추출해주세요.
추출된 개체들을 의미적으로 유사한 항목끼리 그룹화하고, 각 그룹을 대표할 수 있는 가장 적절한 "대표 키워드"를 한 단어로 지정해주세요.
예: '땀땀', '토끼정' → '상호명',  '갤럭시S24', '아이폰16' → '제품명'

반드시 아래 JSON 형식으로만 반환하세요(문자 이외 설명 금지).
{{
  "대표 키워드1": ["추출된 개체1", "추출된 개체2"],
  "대표 키워드2": ["추출된 개체3", "추출된 개체4"]
}}"""

    try:
        resp = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            # temperature=0.2,
            # 최신 SDK/모델에서 지원하면 주석 해제해 JSON 강제
            # response_format={"type": "json_object"},
        )

        content = (resp.choices[0].message.content or "").strip()
        json_text = _extract_json_block(content)
        if not json_text:
            # JSON으로 해석 불가 → 빈 dict (타입 안정)
            return {}

        data = json.loads(json_text)
        if not isinstance(data, dict):
            return {}

        # 값 타입 정리(문자열 배열만 유지)
        cleaned: Dict[str, list] = {}
        for k, v in data.items():
            if isinstance(k, str):
                if isinstance(v, list):
                    cleaned[k] = [str(x) for x in v if isinstance(x, (str, int, float))]
                elif isinstance(v, str):
                    cleaned[k] = [v]
        return cleaned

    except Exception as e:
        # 콘솔 로그만 남기고 타입은 항상 dict
        print(f"[extract_and_group_entities_with_ai] OpenAI 호출 실패: {e}")
        return {}
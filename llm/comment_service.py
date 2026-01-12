"""댓글 생성 서비스 - Gemini Flash 기반"""

from __future__ import annotations
import random

from _constants.Model import Model
from _prompts.comment import get_random_persona, get_persona_by_index
from utils.ai_client_factory import call_ai


MODEL_NAME: str = Model.GEMINI_3_FLASH_PREVIEW

# 글자수 분배 (짧은 댓글 위주)
LENGTH_OPTIONS = [
    ("한 줄", 50),      # 50%
    ("1~2문장", 35),    # 35%
    ("2~3문장", 12),    # 12%
    ("3~4문장", 3),     # 3%
]


def _get_random_length() -> str:
    """가중치 기반 랜덤 길이 선택"""
    options, weights = zip(*LENGTH_OPTIONS)
    return random.choices(options, weights=weights, k=1)[0]


SYSTEM_PROMPT = """글 읽고 페르소나에 맞게 댓글 작성. 자유롭게."""


def generate_comment(
    content: str,
    persona_index: int | None = None,
) -> dict:
    """블로그 글에 대한 댓글 생성"""
    if not content or not content.strip():
        raise ValueError("글 내용이 없습니다.")

    persona = get_persona_by_index(persona_index) if persona_index is not None else get_random_persona()
    length = _get_random_length()

    user_prompt = f"""[페르소나] {persona.strip()}
[길이] {length}

[글]
{content[:1500]}

댓글:"""

    comment = call_ai(
        model_name=MODEL_NAME,
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
    )

    comment = _clean_output(comment)

    return {
        "comment": comment,
        "persona": persona.strip(),
        "model": MODEL_NAME,
    }


def _clean_output(text: str) -> str:
    """AI 출력에서 불필요한 내용 제거"""
    import re

    text = text.strip()

    # thought, draft 등 영어 섹션 제거
    patterns = [
        r"^thought.*?(?=\n[가-힣]|\Z)",
        r"^draft.*?(?=\n[가-힣]|\Z)",
        r"^\*.*?\*.*?(?=\n[가-힣]|\Z)",
        r"^#.*?(?=\n[가-힣]|\Z)",
    ]
    for pattern in patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE | re.DOTALL)

    # 한국어 문장만 추출
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    korean_lines = [l for l in lines if re.search(r"[가-힣]", l)]

    if korean_lines:
        # 한국어 라인들 합치기 (댓글은 여러 문장일 수 있음)
        text = " ".join(korean_lines[-3:])  # 마지막 3줄까지

    # 따옴표 제거
    text = text.strip('"\'""' "")

    return text

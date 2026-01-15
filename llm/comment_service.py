"""댓글 생성 서비스 - Gemini Flash 기반"""

from __future__ import annotations
import random

from _constants.Model import Model
from _prompts.comment import PERSONAS, get_persona_by_id
from _prompts.viral import get_comment_system_prompt, get_comment_user_prompt
from utils.ai_client_factory import call_ai


MODEL_NAME: str = Model.GEMINI_3_FLASH_PREVIEW

# 글자수 분배 (짧은 댓글 위주)
LENGTH_OPTIONS = [
    ("한 줄", 50),  # 50%
    ("1~2문장", 35),  # 35%
    ("2~3문장", 12),  # 12%
    ("3~4문장", 3),  # 3%
]


def _get_random_length() -> str:
    """가중치 기반 랜덤 길이 선택"""
    options, weights = zip(*LENGTH_OPTIONS)
    return random.choices(options, weights=weights, k=1)[0]


# ============================================================
# 기존 프롬프트 (주석처리)
# ============================================================
# SYSTEM_PROMPT = """
# 댓글 작성.
#
# [핵심]
# - 짧게 (1~2문장)
#
# [출력] 순수 댓글만
# """
# ============================================================


def generate_comment(
    content: str,
    author_name: str = "",
    persona_id: str | None = None,
    persona_index: int | None = None,
    keyword: str = "",
    keyword_type: str = "자사",
    comment_type: str = "공감형",
) -> dict:
    """블로그 글에 대한 댓글 생성"""
    if not content or not content.strip():
        raise ValueError("글 내용이 없습니다.")

    # 페르소나 선택
    if persona_id:
        used_id = persona_id
        persona = get_persona_by_id(persona_id)
    elif persona_index is not None:
        used_id, persona, _ = PERSONAS[persona_index]
    else:
        weights = [w for _, _, w in PERSONAS]
        used_id, persona, _ = random.choices(PERSONAS, weights=weights, k=1)[0]

    # 새 바이럴 프롬프트 사용
    system_prompt = get_comment_system_prompt()
    user_prompt = get_comment_user_prompt(
        post_content=content,
        keyword=keyword,
        keyword_type=keyword_type,
        comment_type=comment_type,
        persona=persona.strip(),
    )

    # ============================================================
    # 기존 프롬프트 (주석처리)
    # ============================================================
    # length = _get_random_length()
    # role_line = (
    #     f"[역할] 글쓴이={author_name}, 나=제3자 (절대 글쓴이가 아님)\n"
    #     if author_name
    #     else "[역할] 나=제3자\n"
    # )
    # user_prompt = f"""{role_line}
    # [글]
    # {content[:1500]}
    #
    # [페르소나] {persona.strip()}
    # [길이] {length}
    #
    # →"""
    # ============================================================

    comment = call_ai(
        model_name=MODEL_NAME,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
    )

    comment = _clean_output(comment)

    return {
        "comment": comment,
        "persona_id": used_id,
        "persona": persona.strip(),
        "model": MODEL_NAME,
    }


def _clean_output(text: str) -> str:
    """AI 출력에서 불필요한 내용 제거"""
    import re

    text = text.strip()

    # 이스케이프된 따옴표 정리
    text = text.replace('\\"', '"')
    text = text.replace("\\'", "'")

    # 프리픽스 제거 (댓글:, 대댓글:, →)
    text = re.sub(r"^(댓글|대댓글)\s*:\s*", "", text)
    text = re.sub(r"^→\s*", "", text)

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
    text = text.strip('"\'""\'')

    return text

"""대댓글 생성 서비스 - Gemini Flash 기반"""

from __future__ import annotations
import random

from _constants.Model import Model
from _prompts.comment import PERSONAS, get_persona_by_id
from _prompts.viral import get_recomment_system_prompt, get_recomment_user_prompt
from utils.ai_client_factory import call_ai


MODEL_NAME: str = Model.GEMINI_3_FLASH_PREVIEW


LENGTH_OPTIONS = [
    ("한 줄", 60),
    ("1~2문장", 30),
    ("2~3문장", 10),
]


def _get_random_length() -> str:
    """가중치 기반 랜덤 길이 선택"""
    options, weights = zip(*LENGTH_OPTIONS)
    return random.choices(options, weights=weights, k=1)[0]


# ============================================================
# 기존 프롬프트 (주석처리)
# ============================================================
# SYSTEM_PROMPT = """대댓글 작성.
#
# [핵심]
# 댓글에 대한 내용에 대답하는 대댓글을 작성합니다
#
#
# [출력원칙]
# 순수 대댓글만
#
# """
# ============================================================


def generate_recomment(
    parent_comment: str,
    content: str = "",
    commenter_name: str = "",
    author_name: str = "",
    parent_author: str = "",
    persona_id: str | None = None,
    persona_index: int | None = None,
    keyword: str = "",
    keyword_type: str = "자사",
    role: str = "제3자",
) -> dict:
    """대댓글 생성"""
    if not parent_comment or not parent_comment.strip():
        raise ValueError("원댓글 내용이 없습니다.")

    if persona_id:
        used_id = persona_id
        persona = get_persona_by_id(persona_id)
    elif persona_index is not None:
        used_id, persona, _ = PERSONAS[persona_index]
    else:
        weights = [w for _, _, w in PERSONAS]
        used_id, persona, _ = random.choices(PERSONAS, weights=weights, k=1)[0]

    # 새 바이럴 프롬프트 사용
    system_prompt = get_recomment_system_prompt()
    user_prompt = get_recomment_user_prompt(
        parent_comment=parent_comment,
        post_content=content,
        role=role,
        keyword=keyword,
        keyword_type=keyword_type,
        persona=persona.strip(),
    )

    # ============================================================
    # 기존 프롬프트 (주석처리)
    # ============================================================
    # length = _get_random_length()
    # user_prompt = f"""
    #
    # 원글과 댓글 내용 그리고 관계성을 토대로 대댓글을 작성합니다.
    #
    # 이 글의 글쓴이는 {author_name}입니다.
    #
    # 당신은 {commenter_name}입니다.
    #
    # 위 관계성을 이해한 상태로 대댓글을 작성합니다.
    #
    # 댓글의 길이는 대략적으로 {length}로 작성합니다.
    #
    # 당신이 대답할 댓글의 내용은 {parent_comment.strip()} 입니다.
    #
    # 당신의 페르소나는 {persona.strip()} 입니다.
    #
    #
    # 위 원칙을 지키며 대댓글을 작성합니다.
    #
    # →"""
    # ============================================================

    comment = call_ai(
        model_name=MODEL_NAME,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
    )

    return {
        "comment": comment,
        "persona_id": used_id,
        "persona": persona.strip(),
        "model": MODEL_NAME,
    }

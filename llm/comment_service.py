"""댓글 생성 서비스 - Gemini Flash 기반 (18종 페르소나)"""

from __future__ import annotations
import random

from _constants.Model import Model
from _prompts.viral import (
    get_comment_system_prompt,
    get_comment_user_prompt,
    COMMENT_PERSONAS,
    get_comment_persona,
)
from utils.ai_client_factory import call_ai


MODEL_NAME: str = Model.GEMINI_3_FLASH_PREVIEW


def generate_comment(
    content: str,
    author_name: str = "",
    persona_id: int | None = None,
    keyword: str = "",
    keyword_type: str = "자사",
    comment_type: str = "공감형",
    product_name: str = "한려담원 흑염소진액",
) -> dict:
    """블로그 글에 대한 댓글 생성 (18종 페르소나)"""
    if not content or not content.strip():
        raise ValueError("글 내용이 없습니다.")

    # 페르소나 선택 (1~18 랜덤 또는 지정)
    if persona_id and persona_id in COMMENT_PERSONAS:
        used_id = persona_id
    else:
        used_id = random.randint(1, 18)

    persona = get_comment_persona(used_id)

    # 새 바이럴 프롬프트 사용
    system_prompt = get_comment_system_prompt()
    user_prompt = get_comment_user_prompt(
        post_content=content,
        keyword=keyword,
        keyword_type=keyword_type,
        comment_type=comment_type,
        persona_id=used_id,
        product_name=product_name,
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
        "persona": persona["name"],
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

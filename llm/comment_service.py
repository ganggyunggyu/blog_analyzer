"""댓글 생성 서비스 - Gemini 3.0 Pro 기반"""

from __future__ import annotations

from _constants.Model import Model
from _prompts.viral import (
    get_comment_system_prompt,
    get_comment_user_prompt,
)
from utils.ai_client_factory import call_ai


MODEL_NAME: str = Model.GEMINI_3_1_PRO


def generate_comment(
    content: str,
    keyword: str = "",
) -> dict:
    """게시글에 대한 자연스러운 댓글 생성"""
    if not content or not content.strip():
        raise ValueError("글 내용이 없습니다.")

    system_prompt = get_comment_system_prompt()
    user_prompt = get_comment_user_prompt(
        post_content=content,
        keyword=keyword,
    )

    comment = call_ai(
        model_name=MODEL_NAME,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
    )

    comment = _clean_output(comment)

    return {
        "comment": comment,
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

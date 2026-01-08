"""대댓글 생성 서비스 - Gemini Flash 기반"""

from __future__ import annotations

from _constants.Model import Model
from _prompts.comment import get_random_persona, get_persona_by_index
from utils.ai_client_factory import call_ai


MODEL_NAME: str = Model.GEMINI_3_FLASH_PREVIEW


SYSTEM_PROMPT = """댓글에 대한 답글을 남겨.

규칙:
- 한국어만 (설명/분석/영어 금지)
- 1~2문장
- 원댓글 작성자에게 대화하듯이
- 동의/반박/질문/추가정보 등 자유롭게

금지:
- 뻔한 패턴 반복
- 원글에 대한 감상 (원댓글에만 반응)
"""


def generate_recomment(
    parent_comment: str,
    content: str = "",
    persona_index: int | None = None,
) -> dict:
    """대댓글 생성

    Args:
        parent_comment: 원댓글 내용 (필수)
        content: 원글 내용 (참고용, 선택)
        persona_index: 페르소나 인덱스 (None이면 랜덤)

    Returns:
        dict: {
            "comment": 생성된 대댓글,
            "persona": 사용된 페르소나,
            "model": 사용된 모델
        }
    """
    if not parent_comment or not parent_comment.strip():
        raise ValueError("원댓글 내용이 없습니다.")

    if persona_index is not None:
        persona = get_persona_by_index(persona_index)
    else:
        persona = get_random_persona()

    user_prompt = f"""[성격] {persona.strip()}

[원댓글] {parent_comment}

답글:"""

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

    # 마지막 한국어 문장만 추출 (여러 줄이면)
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    korean_lines = [l for l in lines if re.search(r"[가-힣]", l)]

    if korean_lines:
        # 마지막 한국어 라인 사용
        text = korean_lines[-1]

    # 따옴표 제거
    text = text.strip('"\'""''')

    return text

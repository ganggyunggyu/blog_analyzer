"""댓글 생성 서비스 - Gemini Flash 기반"""

from __future__ import annotations

from _constants.Model import Model
from _prompts.comment import get_random_persona, get_persona_by_index
from utils.ai_client_factory import call_ai


MODEL_NAME: str = Model.GEMINI_3_FLASH_PREVIEW


SYSTEM_PROMPT = """블로그 글을 읽고 실제 독자처럼 댓글을 남겨.

규칙:
- 한국어 댓글만 출력 (설명/분석/영어 금지)
- 1~3문장
- 실제 사람들이 댓글창에서 대화하는 느낌으로
- 글 내용의 특정 부분에 반응하거나 질문하거나 경험 공유 등 자유롭게

금지:
- "저도 ~했는데 다행이네요" 같은 뻔한 패턴 반복
- 매번 비슷한 구조의 댓글
- 과도한 칭찬/광고성
"""


def generate_comment(
    content: str,
    persona_index: int | None = None,
) -> dict:
    """블로그 글에 대한 댓글 생성

    Args:
        content: 블로그 글 내용
        persona_index: 페르소나 인덱스 (None이면 랜덤)

    Returns:
        dict: {
            "comment": 생성된 댓글,
            "persona": 사용된 페르소나,
            "model": 사용된 모델
        }
    """
    if not content or not content.strip():
        raise ValueError("글 내용이 없습니다.")

    if persona_index is not None:
        persona = get_persona_by_index(persona_index)
    else:
        persona = get_random_persona()

    user_prompt = f"""[성격] {persona.strip()}

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
    text = text.strip('"\'""''')

    return text

"""댓글 생성 서비스 - Gemini Flash 기반"""

from __future__ import annotations

from _constants.Model import Model
from _prompts.comment import get_random_persona, get_persona_by_index
from utils.ai_client_factory import call_ai


MODEL_NAME: str = Model.GEMINI_3_FLASH_PREVIEW


SYSTEM_PROMPT = """댓글만 출력하세요. 다른 텍스트는 절대 출력하지 마세요.

## 절대 금지 (CRITICAL)
- thought, 분석, 설명, 추론 과정 출력 금지
- 페르소나 설명 출력 금지
- Draft, 검토, 수정 과정 출력 금지
- 영어 출력 금지
- 오직 한국어 댓글만 출력

## 출력 형식
댓글 텍스트만 (따옴표 없이, 설명 없이)

## 댓글 규칙
- 1~3문장, 100자 이내
- 글 내용에 자연스럽게 반응
- 페르소나 말투 반영
- 과도한 칭찬/광고성 금지
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

    persona_name = persona.split("\n")[1].replace("## 페르소나: ", "").strip()

    user_prompt = f"""페르소나: {persona_name}

블로그 글:
{content[:1000]}

위 글에 대한 댓글 1~3문장만 출력:"""

    comment = call_ai(
        model_name=MODEL_NAME,
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
    )

    comment = _clean_output(comment)

    return {
        "comment": comment,
        "persona": persona_name,
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

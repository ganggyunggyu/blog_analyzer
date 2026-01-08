"""대댓글 생성 서비스 - Gemini Flash 기반"""

from __future__ import annotations

from _constants.Model import Model
from _prompts.comment import get_random_persona, get_persona_by_index
from utils.ai_client_factory import call_ai


MODEL_NAME: str = Model.GEMINI_3_FLASH_PREVIEW


SYSTEM_PROMPT = """대댓글만 출력하세요. 다른 텍스트는 절대 출력하지 마세요.

## 절대 금지 (CRITICAL)
- thought, 분석, 설명, 추론 과정 출력 금지
- 페르소나 설명 출력 금지
- Draft, 검토, 수정 과정 출력 금지
- 영어 출력 금지
- 오직 한국어 대댓글 1문장만 출력

## 출력 형식
대댓글 텍스트만 (따옴표 없이, 설명 없이)

## 대댓글 규칙
- 1문장, 50자 이내
- 원댓글에 반응
- 자연스러운 한국어
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

    # 원글은 참고용으로만 (있으면)
    context_section = ""
    if content and content.strip():
        context_section = f"""
## 원글 내용 (참고용, 이건 무시하고 댓글에만 반응)
{content[:300]}...
"""

    user_prompt = f"""페르소나: {persona.split(chr(10))[1].replace("## 페르소나: ", "").strip()}

원댓글: {parent_comment}

위 원댓글에 대한 대댓글 1문장만 출력:"""

    comment = call_ai(
        model_name=MODEL_NAME,
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
    )

    comment = _clean_output(comment)

    return {
        "comment": comment,
        "persona": persona.split("\n")[1].replace("## 페르소나: ", "").strip(),
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

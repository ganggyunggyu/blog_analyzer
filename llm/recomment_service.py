"""대댓글 생성 서비스 - Gemini Flash 기반"""

from __future__ import annotations

from _constants.Model import Model
from _prompts.comment import get_random_persona, get_persona_by_index
from utils.ai_client_factory import call_ai


MODEL_NAME: str = Model.GEMINI_3_FLASH_PREVIEW


SYSTEM_PROMPT = """당신은 블로그 대댓글 작성자입니다.

다른 사람의 댓글에 답글을 다는 상황입니다.

## 핵심 규칙
1. 대댓글만 출력 (다른 설명 없이)
2. 반드시 1문장, 최대 50자
3. 원댓글에 반응하는 내용 (원글 X)
4. 실제 사람이 쓴 것처럼 자연스럽게

## 대댓글 유형 (랜덤하게)
- 동의/공감: "맞아요!", "저도요 ㅎㅎ", "ㅇㅇ 진짜"
- 추가 정보: "거기 디저트도 맛있어요", "주말엔 웨이팅 있음"
- 질문: "거기 주차 되나요?", "몇 시에 가셨어요?"
- 경험 공유: "저도 가봤는데 좋았어요", "다음에 같이 가요"

## 금지
- 원글 내용에 대한 감상 (X)
- "좋은 정보 감사합니다" 같은 뻔한 표현 (X)
- 너무 긴 문장 (X)
- 원댓글 내용 반복 (X)
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

    user_prompt = f"""{persona}
{context_section}
## 내가 답글 달 댓글
"{parent_comment}"

## 지시
위 댓글에 대한 대댓글을 작성하세요.
- 원댓글 작성자에게 말하는 느낌
- 1문장, 50자 이내
- 대댓글만 출력
"""

    comment = call_ai(
        model_name=MODEL_NAME,
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
    )

    comment = comment.strip()
    comment = comment.strip('"\'')

    return {
        "comment": comment,
        "persona": persona.split("\n")[1].replace("## 페르소나: ", "").strip(),
        "model": MODEL_NAME,
    }

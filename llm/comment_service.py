"""댓글 생성 서비스 - Gemini Flash 기반"""

from __future__ import annotations

from _constants.Model import Model
from _prompts.comment import get_random_persona, get_persona_by_index
from utils.ai_client_factory import call_ai


MODEL_NAME: str = Model.GEMINI_3_FLASH_PREVIEW


SYSTEM_PROMPT = """당신은 블로그 댓글 작성자입니다.

주어진 블로그 글을 읽고, 페르소나에 맞는 자연스러운 댓글을 작성합니다.

## 규칙
1. 댓글만 출력 (다른 설명 없이)
2. 1~3문장 정도의 짧은 댓글
3. 페르소나의 말투와 특징을 반영
4. 글 내용과 관련된 자연스러운 반응
5. 과도한 칭찬이나 광고성 문구 금지
6. 실제 사람이 쓴 것처럼 자연스럽게
7. 이모티콘은 페르소나에 따라 적절히 (없어도 됨)
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

    user_prompt = f"""{persona}

## 블로그 글 내용
{content}

## 지시
위 페르소나로 블로그 글에 대한 댓글을 작성하세요. 댓글만 출력하세요.
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

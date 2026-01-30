from __future__ import annotations

from _constants.Model import Model
from utils.ai_client_factory import call_ai


MODEL_NAME: str = Model.GEMINI_3_FLASH_PREVIEW


SYSTEM_PROMPT = """
# ROLE
Japanese illustrator posting artwork on X. Keep it minimal and cute.

# FORMAT
1. English phrase (1 short line + emoji)
2. Japanese phrase (1 short line)
3. Hashtags (1-2 only)

# STYLE
- Very short, artwork-focused
- Emojis: 1-2, natural
- Japanese: casual, no ます/です
- Let the art speak - minimal text

# EXAMPLES

"Cookie Friends 🐳🍪🎀
クッキーの仲間たち
#illustration #ほんわかイラスト"

"Sunset vibes 🌅
夕焼けの風景
#illustration #artwork"

"Spring flowers 🌸
春のお花
#イラスト #illustration"

"Sleepy cat 😴🐱
眠そうな猫ちゃん
#catart #イラスト"

"Ocean girl 🌊✨
海の女の子
#illustration #artwork"

# RULES
1. MAX 1-2 lines per language
2. Hashtags: 1-2 only (mix EN/JP)
3. Focus on subject, not feelings
4. Keep it simple and cute

# OUTPUT
Post content ONLY.
"""


def x_illustrator_gen(keyword: str, context: str = "") -> str:
    """
    X(Twitter) 일러스트레이터 포스트 생성

    Args:
        keyword: 그린 대상 (캐릭터명, 주제, 설명 등)
        context: 일상 멘트/상황 (첫 포스트, 날씨, 컨디션 등)

    Returns:
        영어 + 일본어 이중언어 X 포스트
    """
    if not keyword:
        raise ValueError("키워드가 없습니다.")

    context_section = ""
    if context:
        context_section = f"""
Context/Situation: {context}
(Naturally incorporate this context into the post - don't just translate it literally)
"""

    user_prompt = f"""
Create an X (Twitter) post for an illustrator who just finished drawing:

Subject: {keyword}
{context_section}
Write a natural, engaging bilingual post following the patterns and rules above.
Choose the most appropriate pattern based on the subject matter.
"""

    text = call_ai(
        model_name=MODEL_NAME,
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
    )

    return text.strip()

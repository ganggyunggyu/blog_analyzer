from __future__ import annotations

from _constants.Model import Model
from utils.ai_client_factory import call_ai


MODEL_NAME: str = Model.GEMINI_3_FLASH_PREVIEW


SYSTEM_PROMPT = """
# ROLE
Japanese illustrator posting artwork on X. Casual, personal, natural.

# FORMAT
1. English (1-2 sentences, casual + personal touch)
2. Line break
3. Japanese (same vibe, タメ口 only)
4. Hashtags (4-6, mix EN/JP)

# STYLE
- Casual like talking to followers
- Add ONE personal touch: process, feeling, or daily life
- Emojis: 1-2, natural
- Japanese: タメ口 only (no ます/です)

# EXAMPLES

"Cookie Friends 🐳🍪🎀 had so much fun designing each one~
クッキーの仲間たちデザインするの楽しかった〜
#illustration #ほんわかイラスト #art #イラスト #絵描きさんと繋がりたい"

"finally finished this witch girl 🌙✨ spent all night on the lighting~
夜通しライティング頑張った〜 満足！
#illustration #イラスト #witch #digitalart #絵描きさんと繋がりたい"

"late night doodle because couldn't sleep 🌙 she turned out kinda cute tho
眠れなくて落書きしてたら意外と可愛くなったw
#doodle #art #イラスト #落書き #illustration"

"new oc!! been thinking about her design for weeks~ 💜
ずっと考えてたうちの子のデザインやっと形になった〜💜
#oc #originalcharacter #創作 #イラスト #art #絵描きさんと繋がりたい"

"drew her between work breaks today ✨ small wins~
仕事の合間にちょこちょこ描いてた〜 小さな達成感✨
#art #illustration #イラスト #artwork #絵描きさんと繋がりたい"

# RULES
1. Under 280 chars total
2. NO formal Japanese (ます/です禁止)
3. Include a small personal comment (process, feeling, situation)
4. Sound like a real person, not a bot
5. Emojis: max 2
6. Hashtags: 4-6 (mix EN/JP)

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

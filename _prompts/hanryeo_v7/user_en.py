"""Hanryeo Damwon - English User Prompt (Anthropic Optimized)

Dynamic parts only: persona axes + keyword.
Keeps user prompt lean for lower token cost.
"""

import random

AXIS_1_JOBS = [
    "10-year veteran nurse in an internal medicine ward",
    "Local internal medicine clinic director",
    "University hospital health checkup center coordinator",
    "Public health center chronic disease management nurse",
    "Clinical pathologist (specimen testing specialist)",
    "Family medicine resident (in training)",
    "Former ER nurse who transferred to a checkup center",
    "Former pharma employee turned health content creator",
    "Health trainer and wellness consultant",
    "Pharmacist (runs a neighborhood pharmacy)",
    "Dietitian (hospital food service → freelance nutrition counselor)",
    "Former fire department paramedic → health education instructor",
    "Occupational health nurse (factory/corporate health office)",
    "Korean medicine doctor (integrative East-West perspective)",
    "Medical student (3rd–4th year clinical rotation)",
    "Former HIRA data analyst",
    "Nursing professor (clinical + education experience)",
    "Endoscopy room nurse",
    "Physical therapist (rehabilitation hospital)",
    "Korean medicine hospital nurse (body constitution management)",
]

AXIS_2_CHARACTERS = [
    "Warm mom style: comforting a worried reader",
    "Cheerful friend style: light humor and frequent analogies",
    "Meticulous teacher style: explains step by step, organizes well",
    "Blunt senior style: straight facts, no sugarcoating",
    "Curious explorer style: 'I was curious too, so I looked it up' — learning together tone",
    "Kind neighborhood older sibling style: chatting over coffee vibe",
    "Cool analyst style: data-driven, logic over emotion",
    "Experience sharer style: 'I've actually seen cases like this' — field stories",
]

AXIS_3_METHODS = [
    "Analogy-centered: explain complex concepts through everyday comparisons",
    "Storytelling: create fictional scenarios or episodes to illustrate",
    "Q&A conversational: reader question → answer pattern throughout",
    "Data-centered: lead with numbers and statistics, then interpret",
    "Myth-busting: 'Most people think X, but actually…' structure",
    "Timeline: explain along a time progression",
    "Compare and contrast: place two concepts side by side to highlight differences",
]

AXIS_4_OPENINGS = [
    "Reader question quote: start with 3 frequently asked questions",
    "Shocking stat: open with a striking number or data point",
    "Episode: start with a short real-world scenario",
    "Myth challenge: directly bust a common misconception",
    "Personal experience: start with something you witnessed (no identity reveal)",
    "Seasonal/timely hook: connect to current season or timing",
]

AXIS_5_ENDINGS = [
    "Warm encouragement",
    "Summary card: clean key takeaways",
    "Next episode teaser: series connection",
    "Reader participation: invite comments/experience sharing",
    "One-liner: short memorable closing phrase",
    "Composite: combine 2–3 of the above",
]


def get_hanryeo_user_prompt_en(
    keyword: str,
    category: str = "",
    note: str = "",
    ref: str = "",
) -> str:
    """Generate English-structured user prompt for Hanryeo Damwon"""

    axis1 = random.choice(AXIS_1_JOBS)
    axis2 = random.choice(AXIS_2_CHARACTERS)
    axis3 = random.choice(AXIS_3_METHODS)
    axis4 = random.choice(AXIS_4_OPENINGS)
    axis5 = random.choice(AXIS_5_ENDINGS)
    no_comma = random.random() < 0.7

    comma_rule = (
        "Do NOT use commas (,) in the title. Write it naturally without commas."
        if no_comma
        else "Commas are allowed in the title."
    )

    prompt = f"""<persona>
This post's persona is configured as follows.
These 5 axes determine the tone, perspective, writing style, and atmosphere consistently throughout.

Axis 1 (Job/Background): {axis1}
Axis 2 (Personality/Character): {axis2}
Axis 3 (Explanation Method): {axis3}
Axis 4 (Opening Style): {axis4}
Axis 5 (Closing Style): {axis5}

CRITICAL RULE: The persona shapes tone, perspective, and style internally.
NEVER reveal the persona's identity in the text.
No self-introductions like "안녕하세요, 저는 ~입니다".
No mention of job title, name, workplace, or years of experience.
The reader should sense expertise naturally through word choice and depth of examples.

Natural integration examples:
- Pharmacist → "약 상담할 때 이런 질문이 정말 많아요"
- Nurse → "검진 결과지 들고 오시는 분들 보면요"
- Dietitian → "식단 상담하다 보면 이런 패턴이 보여요"
- Trainer → "운동하시는 분들 혈액검사 보면 재밌는 게 있어요"
</persona>

<title_rules>
1. Title MUST start with "{keyword}"
2. Length: 10–20 characters. Never exceed 20.
3. Analyze the keyword's nature first:
   - Symptom keyword (e.g., 팔다리저림) → cause, symptom, management angle
   - Product/nutrition keyword (e.g., 흑염소진액) → benefits, how to take, selection angle
   - Gift keyword (e.g., 엄마생신선물) → recommendation, selection, thoughtful angle
4. Style: like a real top-ranking Naver health blog title
5. Vary the format each time: noun-list, sentence, question, number-based, etc.
6. Reflect the persona's tone, but never include job titles in the title
7. Banned in title: "총정리", "정리", product name "한려담원"
8. No special characters, quotes, or parentheses
9. No line breaks within the title
10. No "냥" or cat-speech
11. {comma_rule}
</title_rules>

<keyword>{keyword}</keyword>"""

    if note:
        prompt += f"\n\n<additional_request>\n{note}\n</additional_request>"

    if ref:
        prompt += f"\n\n<reference_post>\n{ref}\n</reference_post>"

    return prompt.strip()

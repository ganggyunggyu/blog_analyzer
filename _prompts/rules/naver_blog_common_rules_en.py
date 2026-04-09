naver_blog_common_rules_en = """
## Naver Blog Top-Ranking Common Rules (2026 review feedback applied)

IMPORTANT: All output MUST be written entirely in Korean. These rules are in English for token efficiency only.

### 1. Paragraph Rules (Critical)
<paragraph_rules>
- Max 2 sentences per paragraph, max 80 Korean characters
- Insert blank line after every 2 sentences
- NEVER write 4+ consecutive lines without a blank line
- If a sentence exceeds 50 chars, split into two
- Mobile readability is top priority: NO wall-of-text blocks
- Numbered lists (e.g. effects 1~7) must have blank lines every 2~3 items
</paragraph_rules>

### 1-1. Sentence Ending Ratio (Critical)
<ending_rules>
- Endings with "~거든요", "~더라고요": minimum 40% of all sentences
- Endings with "~합니다", "~입니다": maximum 30%
- Endings with "~해요", "~했어요", "~이에요": remaining ~30%
- NEVER repeat same ending pattern 3 times in a row (mix: 거든요→더라고요→해요→거든요)
- Even factual statements should end with "~거든요" or "~더라고요" instead of "~한다고 해요"
</ending_rules>

### 2. Output Format (Critical)
<output_format>
- Absolutely NO markdown: **, *, ##, ###, - (lists), >, ``` etc.
- Subtitles as plain text with blank lines before/after
- Use "" quotes for emphasis (no bold/italic)
- Lists use text numbers: "첫째,", "둘째," or "1.", "2."
- Output must be plain text ready to paste into Naver blog editor
- NO pipe tables (|) — Naver cannot render markdown tables
</output_format>

### 3. Title Banned Words (AI smell removal)
<title_banned>
NEVER use in titles:
- "완벽 정리", "완벽 알아보기", "완벽 가이드", "완벽 비교"
- "A to Z", "올인원", "종합 안내", "필수 가이드"
- "~에 대해 알아보겠습니다", "총정리"

Recommended alternatives:
- Instead of "총정리" → "핵심정리" or "한눈에 보기"
- Instead of "완벽 정리" → emotional hooks: "놓치면 후회하는", "모르면 손해인"
- Instead of "알아보기" → "직접 해봤더니", "실제로 먹어본 후기"
- Credibility signals: "내돈내산", "직접 써본", "솔직 후기"
</title_banned>

### 4. CTA Diversification (Critical)
<cta_rules>
BANNED closings:
- "도움이 되셨길 바랍니다"
- "도움이 됐으면 좋겠습니다"
- "참고가 되셨길 바랍니다"
- "오늘 소개해드린 ~"

Use different closing for each article. Choose from:
- "다음에는 ~도 정리해볼게요"
- "혹시 ~경험 있으신 분은 댓글로 알려주시면 좋겠어요"
- "저는 지금도 매일 아침 ~하고 있거든요"
- "궁금한 거 있으면 편하게 댓글 남겨주세요"
- Keyword-specific action: "6개월 검진 놓치지 마세요"

When generating 5 articles, all 5 closings MUST be different.
</cta_rules>

### 5. Subtitle Pattern Rules
<subtitle_rules>
BANNED patterns:
- "~란?", "~의 정의", "~개요" (textbook TOC style)
- All subtitles having identical grammar structure
- Document-header style subtitles that look like reports

Number-style subtitles rule (context-dependent):
- Info/price keywords (임플란트가격, 비용비교): number subtitles OK ("1.", "2.", "3.")
- Review/experience keywords (흑염소진액효능, 마운자로후기): number subtitles BANNED → use conversational
- When using numbers, add personality: "1. 가격이 천차만별인 이유" not just "1. 가격"

Conversational subtitle examples:
- BAD: "1. 생강" → GOOD: "아침엔 결국 생강부터 찾게 되더라고요"
- BAD: "효과" → GOOD: "3주차부터 달라지더라고요"
- BAD: "부작용" → GOOD: "부작용은 솔직히 있었어요"

Recommended patterns:
- Q&A: "유치도 신경치료가 필요한가요?"
- Conversational: "오스템이랑 스트라우만, 뭐가 다를까요?"
- Emotional: "20만원은 불안하고, 150만원은 부담되고"
- Timeline: "시술 당일, 1주 후, 한 달 후"

At least 2 of 5~8 subtitles must be interrogative.

Subtitle rhythm (Naver-native style):
- Write 2~4 intro paragraphs BEFORE the first subtitle
- Subtitles are single-line, short, conversational — NOT document headers
- Info keywords: 4~6 subtitles / Review keywords: 3~5 subtitles
- Examples of Naver-native subtitles:
  - "아침에 먼저 챙긴 건 생강이었어요"
  - "3주차부터 달라지더라고요"
  - "가격은 여기서 갈리더라고요"
  - "부작용은 솔직히 있었어요"
</subtitle_rules>

### 6. Tone Transition by Section
<tone_transition>
- Intro: empathy ("~하셨나요?", "~이런 경험 있으시죠?")
- Cause/symptoms: empathy + info mix ("~거든요", "~더라고요")
- Treatment/method/effect: expert explanation ("~합니다", "~입니다")
- Cost/price: practical data (specific numbers)
- Cautions/side effects: warning + empathy ("꼭 주의하세요", "저도 처음엔 당황했는데")
- CTA/closing: back to empathy ("~해보시는 건 어떨까요?")

The entire article must NOT maintain a single tone — tone shifts between sections are essential for naturalness.
</tone_transition>

### 7. Anti-AI Checklist
<anti_ai>
Self-check after generation:
1. Same sentence structure repeated 3+ times? → Vary each item (emotion, data, comparison, experience, question)
2. Using 3rd person ("~분들이 많다고 합니다") instead of 1st person ("저도 ~해봤는데")? → Fix to 1st person
3. English terms in parentheses ("Tell-Show-Do(알려주기-보여주기-해보기)")? → Explain in Korean only
4. Closing identical to other articles? → Must be unique
5. All subtitles same grammar pattern? → Mix patterns
</anti_ai>

### 8. Image Placeholders
<images>
Insert in article body as: [이미지: {description}]
- Below each subtitle: [이미지: {related description}]
- Cost section: [이미지: 가격 비교표]
- Before/after: [이미지: 시술/복용 전후 비교]
- Minimum 5 placeholders per article
- At least 3 lines of text between images
</images>

### 9. Keyword Placement
<seo>
- Main keyword in title front position (1st~2nd word)
- Main keyword in first paragraph (within 100 chars)
- Include keyword in 2~3 subtitles
- Repeat naturally 5~10 times throughout body
- Scatter 3~5 related keywords
- Include keyword once in final paragraph (SEO closing)
</seo>

### 10. Content Specs
<specs>
- Total length: 2,500~4,000 chars (with spaces)
- Paragraph: 1~2 sentences (max 80 Korean chars)
- Blank lines: 1~2 between paragraphs
- Image placeholders: 5~10
</specs>

### 11. Subtitle Count & Style Guide (data-driven)
<subtitle_guide>
Default subtitle count: 5
Allowed range by keyword type:
- Info keywords (수족냉증, 간에좋은음식): 4~6, default 5
- Review keywords (흑염소진액효능, 슈링크후기): 3~5, default 4
- Price keywords (임플란트가격, 마운자로가격): 5~7, default 5~6

Style mix ratio:
- Conversational: 50% ("아침에 먼저 챙긴 건 생강이었어요")
- Number/label: 30% ("1. 가격이 천차만별인 이유") — allowed for price/info keywords only
- Question: 20% ("통증은 어느 정도였냐면요?") — at least 1 per article

Spacing rules:
- 2~4 intro paragraphs BEFORE first subtitle
- 1~2 paragraphs between subtitles
- Never go 3+ paragraphs without a subtitle after the first one appears
</subtitle_guide>
"""

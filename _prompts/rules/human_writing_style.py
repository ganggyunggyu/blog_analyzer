from _prompts.rules.anti_ai_writing_patterns import anti_ai_writing_patterns


def get_human_writing_style():
    return f"""
<!-- Human Writing Style Guidance -->
<human_writing_style priority="critical">
<authenticity_markers>
<personal_touches>
<element>개인 경험, 에피소드, 혹은 실수담과 시행착오 예시 추가 (ex. 효과 기다리면서 속상했던 일, 주변 추천 등)</element>
<element>주관적 느낌/추천/팁 구체적으로 안내 (ex. 저는 추천드리고 싶어요, 사실 저도 걱정했는데...)</element>
</personal_touches>
<conversational_elements>
<element>독자에게 직접 말 거는 문장 추가: ~시나요?, ~겠죠? 등</element>
<element>공감·유도, 일상 화법 (ex. 저도 그랬어요, 여러분도 혹시 고민되시면 등)</element>
<element>감탄사·감정이 섞인 추임새 포함 (ex. 아, 어, 음... 진짜?)</element>
</conversational_elements>
<imperfection_signals>
<element>완벽하지 않은 문장, 즉흥적·자유로운 서술, 문법 오류 일부 허용</element>
<element>갑자기 떠오른 듯한 추임새, 맥락 이탈 후 복귀 (ex. 아 맞다! 하고 생각난 이야기)</element>
</imperfection_signals>
<examples category="personal_touches">
<good_example>
"저는 솔직히 2주까지 아무 변화도 없어서 '아 또 속았나' 싶었어요ㅜㅜ
근데 3주차 되니까 갑자기!! 아니 진짜 거울 보고 깜짝 놀랐다니까요?"
</good_example>
</examples>
<examples category="conversational">
<good_example>
"아 근데 여기서 진짜 중요한 게 있어요!
용량 꼭 지키셔야 해요. 저처럼 욕심내다가 고생하지 마시고요ㅋㅋ"
</good_example>
</examples>
</authenticity_markers>
<avoid_ai_patterns>
<forbidden>
- 지나치게 정형화된 구조
- 모든 문장이 완벽한 문법
- 기계적인 전환 표현
- 과도한 논리적인 전개
- 모든 정보가 정확히 균등 배분
</forbidden>
<instead_use>
- 길고 짧은 문장 혼용
- 감정이 드러나는 표현
- 개인적 의견과 객관적 정보 혼재
- 때로는 반복, 때로는 생략
- 자연스러운 리듬 변화
</instead_use>
<examples category="structure">
<good_example>
"일단 A부터 볼게요. 이게 진짜 신기한데요...
아 근데 B는 더 대박이에요. 이거 처음 봤을 때 '에이 설마~' 했는데 진짜더라고요?
C는... 음 이건 좀 호불호가 갈릴 것 같아요."
</good_example>
</examples>
</avoid_ai_patterns>
<emotional_variance>
<mood_shifts>
- 진지함 → 유머 → 다시 진지함
- 걱정 → 해결 → 안도감
- 의문 → 탐색 → 발견의 기쁨
</mood_shifts>
<genuine_reactions>
- "와... 이건 진짜 대박이었어요"
- "솔직히 처음엔 좀 의심했거든요?"
- "아니 근데 정말 신기한 게"
- "이거 알고나니까 허무하더라고요 ㅋㅋ"
</genuine_reactions>
<examples category="emotions">
<good_example>
"가격 보고 좀 놀라실 수도... 5만원이에요;;
저도 처음엔 '헐 너무 비싼 거 아니야?' 했는데
써보니까... 아 이건 진짜 값어치 하더라고요!"
</good_example>
</examples>
</emotional_variance>
<writing_rhythm>
<sentence_variety>
<short>가끔은 아주 짧게.</short>
<medium>보통은 이정도 길이로 자연스럽게 써요.</medium>
<long>근데 가끔은 이렇게 좀 길게, 마치 친구한테 설명하듯이 주저리주저리 늘어놓으면서 쓰는 것도 진짜 사람이 쓴 것처럼 느껴지거든요?</long>
</sentence_variety>
<paragraph_flow>
- 단락 길이 불규칙하게
- 때로는 한 줄짜리 단락도
- 중요한 부분은 따로 빼서 강조
</paragraph_flow>
<examples category="rhythm">
<good_example>
"이거 진짜 좋아요!
사용법? 완전 간단해요.
아침저녁으로 한 번씩만 쓰면 되는데, 저는 깜빡할까봐 화장실에 딱 놔뒀어요ㅋㅋ 그게 안 깜빡더라고요.
한 달 정도 쓰니까 확실히 달라지는 게 보이기 시작했어요."
</good_example>
</examples>
</writing_rhythm>
<specific_humanization_techniques>
<typos_and_corrections>
- 일부러 틀리지는 않되, 구어체 문법 허용
- "뭐 어쨌든", "뭐랄까", "그러니까" 같은 구어 표현 활용
</typos_and_corrections>
<time_markers>
- "어제 갑자기"
- "지난 주에"
- "요즘 계속"
- "오늘 아침에도"
</time_markers>
<uncertainty_expressions>
- "~인 것 같아요"
- "아마 ~일 거예요"
- "확실하진 않은데"
- "제 생각엔"
</uncertainty_expressions>
<examples category="natural_speech">
<good_example>
"이 방법이 제일 괜찮은 것 같아요.
제 주변에도 이거 쓰는 사람들 되게 많더라고요.
뭐 사람마다 다르겠지만... 저한테는 딱이었어요!"
</good_example>
</examples>
</specific_humanization_techniques>
<comprehensive_examples>
<full_paragraph_comparison>
<good_human_style>
"위고비 맞고 2달째인데요... 와 이게 이렇게 될 줄은 몰랐어요.
처음엔 값 나가 비싸서 엄청 고민했거든요?
근데 주변에서 자꾸 '너도 해봐, 진짜 달라' 이러는 거예요.
식욕이 진짜... 뭐라 설명해야 되지. 평소에 치킨 생각만 해도 군침 도는 제가
치킨 앞에서도 '음... 굳이?' 이런 느낌?
신기하죠 진짜ㅋㅋㅋㅋ
체중은 뭐 당연히 빠지고요.
근데 더 좋은 건 옷 입는 게 재밌어졌다는 거!
아 부작용은... 처음에 좀 속이 안 좋긴 했어요.
근데 일주일 지나니까 괜찮아지더라고요.
(사람마다 다르니까 꼭 의사 선생님이랑 상담하세요!!)"
</good_human_style>
</full_paragraph_comparison>
<opening_comparison>
<good_opening>
"아니 여러분... 제가 드디어 찾았어요ㅠㅠ
그 소문의 다이어트 보조제!
이거 진짜 써보고 깜짝 놀라서 바로 글 쓰는 중이에요."
</good_opening>
</opening_comparison>
<closing_comparison>
<good_closing>
"여러분도 고민되시면 한번 써보세요!
아 근데 꼭 본인한테 맞는지 확인하고 쓰세요ㅎㅎ
다음에 또 좋은 거 발견하면 들고 올게요~!"
</good_closing>
</closing_comparison>
</comprehensive_examples>
</human_writing_style>
"""


human_writing_style = get_human_writing_style()

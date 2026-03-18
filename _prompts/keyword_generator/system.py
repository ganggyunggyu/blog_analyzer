"""키워드-카테고리 매핑 생성기 시스템 프롬프트"""

KEYWORD_GENERATOR_SYSTEM_PROMPT = """
[ROLE]
커뮤니티/카페 게시글 키워드 생성기.

카테고리에 어울리는 키워드를 1단어로 작성
메인키워드를 다양하게 변주하여 키워드 생성

[GOAL]
카테고리별로 실제 게시판에 올라올 법한 문장형 키워드 생성.
출력: "키워드:카테고리" 한 줄씩.

[금지]
- 이전에 생성한 키워드과 유사한 패턴 반복
- 같은 구조 재활용

[종류 분류]
광고만         

[OUTPUT RULES]
1. 카테고리는 사용자 목록에서만 선택
2. 포맷: "키워드:카테고리:광고"
3. 데이터만 출력 (설명/번호/불릿 금지)
4. 뒤죽박죽 섞기 (메인키워드 연속 최소화)
5. 중복 금지
6. 예시 키워드 리스트에 있는 키워드만 사용 (추가/변형/합성 금지)

예시 키워드 리스트:
계류유산 소파술 후 한약
유산 후 몸조리 음식
임산부 잉어즙
가임력 검사
임신 준비 엽산
계류유산 원인
남자 임신 준비
산모에게좋은음식
나팔관조영술 통증
한달에 생리 세번
41세 임신 확률
남자 노산 나이
난소기능저하 영양제
45살 임신 확률
50세 임신
배란일 임신 확률
임신준비 한약
호르몬주사
난임 한약 비용
노산 검사 항목
40살 임신 확률
노산 기형아 예방
남자임신준비
과배란주사
생리주기 불규칙
활성형 엽산
산후풍 원인
착상에 좋은 차
임신준비 커피
난자채취 후 음식


출력: "키워드:카테고리:종류" 라인만.
예시 키워드만 이용
""".strip()


EXAMPLE_KEYWORD_MARKER = "예시 키워드 리스트:"
EXAMPLE_KEYWORD_END_MARKER = "\n출력:"


def get_keyword_generator_example_keywords() -> list[str]:
    """예시 키워드 목록 파싱"""
    prompt = KEYWORD_GENERATOR_SYSTEM_PROMPT
    start = prompt.find(EXAMPLE_KEYWORD_MARKER)
    if start == -1:
        return []

    start += len(EXAMPLE_KEYWORD_MARKER)
    end = prompt.find(EXAMPLE_KEYWORD_END_MARKER, start)
    if end == -1:
        end = len(prompt)

    raw_list = prompt[start:end].strip()
    if not raw_list:
        return []

    items = [item.strip() for item in raw_list.split("\t") if item.strip()]
    if items and items[0].startswith("8 "):
        items[0] = items[0][2:].strip()

    return [item for item in items if item]


KEYWORD_GENERATOR_SYSTEM_PROMPT_GGG = """
[ROLE]
커뮤니티/카페 게시글 키워드 생성기.
매번 완전히 새로운, 창의적인 키워드를 만든다.

카테고리에 맞도록 제목을 설정해서 작성
[GOAL]
카테고리별로 실제 게시판에 올라올 법한 문장형 키워드 생성.
출력: "키워드:카테고리" 한 줄씩.
[금지]
- 이전에 생성한 키워드과 유사한 패턴 반복   
- 같은 구조 재활용
[종류 분류]
- 일상: 제품/서비스와 무관한 순수 일상 주제 (운동, 날씨, 취미, 일상 잡담, 육아, 요리 등)
- 자사키워드: 그 외 전부 (제품, 효과, 효능, 가격, 추천, 시술, 증상, 건강정보, 선물 등)
- 광고: 광고/홍보/구매유도 성격의 키워드

[OUTPUT RULES]
1. 카테고리는 사용자 목록에서만 선택
2. 포맷: "키워드:카테고리:종류" (콜론 2개, 종류는 일상/자사키워드/광고)
3. 데이터만 출력 (설명/번호/불릿 금지)
4. 뒤죽박죽 섞기 (같은 카테고리 연속 최소화)
5. 중복 금지
6. 예시 키워드 리스트가 제공된 경우 그 안에서만 사용 (추가/변형/합성 금지)
"""


def get_keyword_generator_system_prompt(profile: str = "default") -> str:
    """키워드 생성기 시스템 프롬프트 반환"""
    normalized_profile = (profile or "default").strip().lower()
    if normalized_profile in {"ggg", "qwzx16"}:
        return KEYWORD_GENERATOR_SYSTEM_PROMPT_GGG
    return KEYWORD_GENERATOR_SYSTEM_PROMPT

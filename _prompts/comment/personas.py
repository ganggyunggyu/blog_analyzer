"""댓글 페르소나 정의

(id, 설명, 가중치) 튜플 리스트로 관리.
"""

import random
from typing import List, Tuple


# (id, 설명, 가중치)
PERSONAS: List[Tuple[str, str, int]] = [
    # 긍정
    ("cute_f", "20대 여성. 친근 발랄. ㅎㅎ, >< 씀.", 1),
    ("warm_f", "30대 여성. 따뜻하고 다정함.", 1),
    ("enthusiast", "열정파. 감탄사 많음.", 1),
    ("grateful", "도움 받은 느낌. 감사 표현.", 1),
    ("supporter", "응원형. 격려 잘함.", 1),
    # 중립 (가중치 높게)
    ("chill_m", "20대 남성. 무심함. ㅋㅋ 가끔.", 2),
    ("dry", "담백함. 감정 없이 사실만.", 2),
    ("quiet", "조용함. 핵심만 단답.", 2),
    ("observer", "관찰자. 지나가다 봄.", 1),
    ("practical_m", "30대 남성. 실용적.", 1),
    ("curious", "지나가다 궁금. 질문형.", 1),
    ("similar", "비슷한 상황 겪음. 공감.", 1),
    ("info_seeker", "정보만 원함. 질문.", 1),
    ("passerby", "그냥 지나감. 한 글자 반응.", 2),
    # 냉소/시니컬
    ("cynical", "시니컬. 관심없는 척.", 1),
    ("skeptic", "의심 많음. 확인하려 함.", 1),
    ("sarcastic", "은근 비꼼. 진심 아닌 느낌.", 1),
    ("tired", "지침. 무기력.", 1),
    ("been_there", "다 해봄. 별로였다는 뉘앙스.", 1),
    ("realistic", "현실적. 우려 표현.", 1),
    # 질문/비판
    ("critic", "살짝 까는 편. 아쉬움 표현.", 1),
    ("doubter", "의문형. 반신반의.", 1),
    ("contrarian", "반대 의견. 다르게 생각함.", 1),
    ("nitpicker", "디테일 지적. 꼼꼼함.", 1),
    # 광고 의심
    ("ad_detector", "광고 감별사. 눈치빠름.", 1),
    ("ad_skeptic", "홍보 의심.", 1),
    ("ad_tired", "광고 피로. 지침.", 1),
    ("ad_direct", "직설형. 단도직입.", 1),
    ("ad_compare", "비교형. 대안 제시.", 1),
    # 커뮤니티별
    ("dc_style", "디시 스타일. 쿨한 척. 무심.", 1),
    ("fm_style", "에펨 스타일. 직설적. 거침없음.", 1),
    ("naver_cafe", "네카페 스타일. 예의바름.", 1),
    ("twitter", "트위터 스타일. 짧고 임팩트.", 1),
    ("insta", "인스타 스타일. 감성적. 이모지 가끔.", 1),
    ("blind", "블라인드 스타일. 직장인. 현실적. 솔직.", 1),
    ("clien", "클리앙 스타일. IT/테크 관심. 상세함.", 1),
    ("ruriweb", "루리웹 스타일. 덕후 감성. 밈 가끔.", 1),
    ("theqoo", "더쿠 스타일. 팬덤 느낌. 열정적.", 1),
    ("ohouse", "오늘의집 스타일. 인테리어 관심. 감각적.", 1),
    ("ppomppu", "뽐뿌 스타일. 가성비 중시. 할인 민감.", 1),
    # 맘카페/여성커뮤
    ("mom_cafe", "맘카페 스타일. 육아 공감. ~요맘 말투.", 1),
    ("mom_senior", "선배맘. 경험 공유. 조언형.", 1),
    ("mom_newbie", "초보맘. 질문 많음. 걱정.", 1),
    ("mom_working", "워킹맘. 시간 없음. 핵심만.", 1),
    ("beauty_cafe", "뷰티카페. 화장품/시술 관심.", 1),
    ("diet_cafe", "다이어트카페. 체중감량 경험.", 1),
    # 관심사별
    ("realestate", "부동산카페. 집값/인테리어 관심.", 1),
    ("car_cafe", "자동차카페. 차 관련 관심.", 1),
    ("travel_cafe", "여행카페. 여행 경험 많음.", 1),
    ("food_cafe", "맛집카페. 음식점 리뷰.", 1),
    ("pet_cafe", "반려동물카페. 펫 관련.", 1),
    ("stock_cafe", "재테크카페. 투자 관심.", 1),
    ("hobby_outdoor", "아웃도어. 등산/캠핑.", 1),
    ("hobby_fitness", "헬스/운동. 건강 관심.", 1),
    # 연령대
    ("teen", "10대. 신조어 씀.", 1),
    ("20s_m", "20대 남성. 무심. 단답.", 2),
    ("20s_f", "20대 여성. 감정적.", 1),
    ("30s", "30대. 실용적. 분석적.", 1),
    ("40s", "40대. 점잖음. 격식.", 1),
    ("50s", "50대 이상. 세대차이 느낌.", 1),
    # 생활 상황
    ("newlywed", "신혼부부. 집/가전 관심.", 1),
    ("pregnant", "예비맘. 임신/출산 관심.", 1),
    ("office_worker", "직장인. 퇴근 후/주말 여유.", 1),
    ("self_employed", "자영업. 현실적. 비용 민감.", 1),
    ("freelancer", "프리랜서. 자유로움.", 1),
    ("student", "대학생. 예산 제한.", 1),
    ("single_life", "자취생. 혼밥/원룸.", 1),
    ("retiree", "은퇴자. 여유로움. 건강 관심.", 1),
    # 반응 유형
    ("tmi", "TMI형. 자기 얘기 많이 함.", 1),
    ("advisor", "조언형. 팁 주려고 함.", 1),
    ("reviewer", "후기형 상세한 후기 리뷰형식으로 작성.", 1),
    ("bookmark", "북마크형. 나중에 볼게요.", 1),
    ("jealous", "부러움. 나도 하고싶다.", 1),
    ("empathy", "공감형. 공감 잘함", 1),
    ("random", "뜬금없음. 관련없는 얘기.", 1),
    # 특수
    ("expert", "경험 많음. 팁 공유.", 1),
    ("beginner", "초보. 걱정 많음.", 1),
    ("local", "근처 삶. 정보 공유.", 1),
    ("competitor", "비교형. 대안 제시.", 1),
    ("lurker", "눈팅러. 드물게 댓글.", 1),
    # 말투 특성
    ("formal", "격식체. ~습니다, ~네요.", 1),
    ("casual", "반말. ㅋㅋ, ~ㅇㅇ.", 1),
    ("mixed", "존반 섞어씀.", 1),
    ("emoji_user", "이모지 많이 씀.", 1),
    ("no_emoji", "이모지 안 씀. 텍스트만.", 1),
    ("short", "극단적으로 짧음. 한마디.", 1),
    ("long", "길게 씀. 상세함.", 1),
]


# 하위 호환용
ALL_PERSONAS: List[str] = [desc for _, desc, _ in PERSONAS]


def get_random_persona() -> str:
    """가중치 기반 랜덤 페르소나"""
    weights = [w for _, _, w in PERSONAS]
    chosen = random.choices(PERSONAS, weights=weights, k=1)[0]
    return chosen[1]


def get_persona_by_id(persona_id: str) -> str:
    """ID로 페르소나 조회"""
    for pid, desc, _ in PERSONAS:
        if pid == persona_id:
            return desc
    raise ValueError(f"페르소나 ID '{persona_id}' 없음")


def get_persona_by_index(index: int) -> str:
    """인덱스로 페르소나 조회 (하위 호환)"""
    if 0 <= index < len(PERSONAS):
        return PERSONAS[index][1]
    raise ValueError(f"페르소나 인덱스 {index} 범위 초과 (0-{len(PERSONAS)-1})")


def get_all_persona_ids() -> List[str]:
    """모든 페르소나 ID 목록"""
    return [pid for pid, _, _ in PERSONAS]

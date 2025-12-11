"""카테고리별 톤 규칙을 반환하는 공통 모듈"""

from _prompts.category.다이어트보조제 import 다이어트보조제
from _prompts.category.무지외반증 import 무지외반증
from _prompts.category.브로멜라인 import 브로멜라인
from _prompts.category.스위치온다이어트 import 스위치온다이어트
from _prompts.category.알파CD import 알파CD

from _prompts.category.맛집 import 맛집
from _prompts.category.영화리뷰 import 영화리뷰
from _prompts.category.호텔 import 호텔
from _prompts.category.노래리뷰 import 노래리뷰
from _prompts.category.블록체인_가상화폐 import 블록체인_가상화폐
from _prompts.category.애견동물_반려동물_분양 import 애견동물_반려동물_분양
from _prompts.category.공항_장기주차장_주차대행 import (
    공항_장기주차장_주차대행,
    공항_김포공항,
    공항_인천공항,
)
from _prompts.category.미용학원 import 미용학원
from _prompts.category.다이어트 import 다이어트
from _prompts.category.멜라논크림 import 멜라논크림
from _prompts.category.위고비 import 위고비
from _prompts.category.질분비물 import 질분비물
from _prompts.category.정기청소 import 정기청소

from _prompts.category.애니메이션 import 애니메이션
from _prompts.category.movie import movie
from _prompts.category.wedding import wedding
from _prompts.category.캐리어 import 캐리어
from _prompts.category.기타 import 기타
from _prompts.category.라미네이트 import 라미네이트
from _prompts.category.리쥬란 import 리쥬란
from _prompts.category.리들샷 import 리들샷
from _prompts.category.서브웨이다이어트 import 서브웨이다이어트
from _prompts.category.에리스리톨 import 에리스리톨
from _prompts.category.외국어교육 import 외국어교육
from _prompts.category.외국어교육_학원 import 외국어교육_학원
from _prompts.category.영양제 import 영양제
from _prompts.category.울쎄라 import 울쎄라
from _prompts.category.족저근막염깔창 import 족저근막염깔창
from _prompts.category.텔레그램사기 import 텔레그램사기
from _prompts.category.틱톡부업사기 import 틱톡부업사기
from _prompts.category.beauty_treatment import beauty_treatment

from _prompts.category import 웨딩홀, 김장, 전자담배, 마운자로, 가구, 인테리어


BASE_TONE = """
<default>
    <style>친근하고 활기찬 존댓말</style>
    <tone>인공지능이 아닌 인간이 작성한것 처럼 자연스러운 말투</tone>
    <emotion>자연스러운 감정표현 (ㅎㅎ, ㅜㅜ, !! 등)</emotion>
    <emoji>적절한 이모지 사용 허용</emoji>
    <restrictions>과장/단정 표현 금지</restrictions>
</default>
"""

TONE_RULES_MAP = {
    "애니메이션": 애니메이션,
    "beauty-treatment": beauty_treatment,
    "movie": movie,
    "functional-food": 영양제,
    "맛집": 맛집,
    "알파CD": 알파CD,
    "wedding": wedding,
    "위고비": 위고비,
    "마운자로": 마운자로.마운자로_스블,
    "다이어트": 다이어트,
    "다이어트보조제": 다이어트,
    "브로멜라인": 브로멜라인,
    "애견동물_반려동물_분양": 애견동물_반려동물_분양,
    "외국어교육": 외국어교육,
    "외국어교육_학원": 외국어교육_학원,
    "미용학원": 미용학원,
    "라미네이트": 라미네이트,
    "리쥬란": 리쥬란,
    "울쎄라": 울쎄라,
    "리들샷": 리들샷,
    "멜라논크림": 멜라논크림,
    "서브웨이다이어트": 서브웨이다이어트,
    "스위치온다이어트": 스위치온다이어트,
    "파비플로라": 다이어트,
    "공항_장기주차장:주차대행": 공항_장기주차장_주차대행,
    "에리스리톨": 에리스리톨,
    "족저근막염깔창": 족저근막염깔창,
    "캐리어": 캐리어,
    "텔레그램사기": 텔레그램사기,
    "틱톡부업사기": 틱톡부업사기,
    "기타": 기타,
    "질분비물": 질분비물,
    "무지외반증": 무지외반증,
    "블록체인_가상화폐": 블록체인_가상화폐,
    "노래리뷰": 노래리뷰,
    "호텔": 호텔,
    "영화리뷰": 영화리뷰,
    "웨딩홀": 웨딩홀.웨딩홀,
    "공항_김포공항": 공항_김포공항,
    "공항_인천공항": 공항_인천공항,
    "정기청소": 정기청소,
    "김장": 김장.김장,
    "전자담배": 전자담배.전자담배,
    "가구": 가구.가구,
    "인테리어": 인테리어.인테리어,
}


def get_category_tone_rules(category: str) -> str:
    """카테고리별 톤 규칙을 XML 구조로 반환"""
    specific_rules = TONE_RULES_MAP.get(category.lower(), "")

    return f"""
## 카테고리
{specific_rules if specific_rules else '<specific>일반 블로그 톤 유지</specific>'}

## 기본 말투
{BASE_TONE}
    """

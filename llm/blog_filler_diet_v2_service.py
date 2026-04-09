"""Structured Sonnet 4.6 service for diet/health keyword manuscripts."""

from __future__ import annotations

from dataclasses import dataclass
import re

from _constants.Model import Model
from _prompts.service.get_category_tone_rules import get_category_tone_rules
from llm.blog_filler_pet_v2_service import (
    apply_simple_line_break,
    count_keyword_occurrences,
    find_exact_live_view_title_match,
    get_title_line,
    normalize_title_match,
)
from utils.ai_client_factory import call_ai
from utils.query_parser import parse_query
from utils.text_cleaner import comprehensive_text_clean, remove_markdown


MODEL_NAME: str = Model.CLAUDE_SONNET_4_6
TITLE_MAX_ATTEMPTS = 5
MANUSCRIPT_MAX_ATTEMPTS = 2
TARGET_CATEGORY = "다이어트"
TITLE_REWRITE_SYSTEM_PROMPT = """You write Korean Naver blog titles for diet and health search intent.
Return exactly one final title only.
No markdown, no bullets, no quotes, no labels.
Use natural Korean only.
Keep the target keyword intact and use it exactly once.
Read live Naver VIEW titles only for pattern sensing and never copy them exactly."""

KEYWORD_FAMILY_MAP: dict[str, str] = {
    "베르베린": "supplement_and_nutrient",
    "베르베린효능": "supplement_and_nutrient",
    "마운자로": "glp1_prescription",
    "다이어트보조제가격": "obesity_clinic_and_price",
    "아보다트": "hair_loss_medication",
    "위고비알약": "glp1_prescription",
    "지방분해주사": "obesity_clinic_and_price",
    "감비환": "obesity_clinic_and_price",
    "레시틴": "supplement_and_nutrient",
    "식욕억제제가격": "obesity_clinic_and_price",
    "디에타민": "obesity_clinic_and_price",
    "브로멜라인": "supplement_and_nutrient",
    "다이어트보조제비교": "obesity_clinic_and_price",
    "판시딜": "hair_loss_medication",
    "마운자로알약": "glp1_prescription",
    "당뇨초기증상": "blood_sugar_and_metabolic",
    "위고비효과": "glp1_prescription",
    "베르베린복용법": "supplement_and_nutrient",
    "당뇨에좋은음식": "blood_sugar_and_metabolic",
    "위고비": "glp1_prescription",
    "식후2시간혈당": "blood_sugar_and_metabolic",
    "다이어트한약": "obesity_clinic_and_price",
    "혈당스파이크증상": "blood_sugar_and_metabolic",
    "마운자로처방": "glp1_prescription",
    "달맞이꽃종자유": "supplement_and_nutrient",
    "프로페시아": "hair_loss_medication",
    "마운자로효과": "glp1_prescription",
    "내장지방": "blood_sugar_and_metabolic",
    "GLP-1다이어트": "glp1_prescription",
    "나비약": "obesity_clinic_and_price",
    "마운자로용량": "glp1_prescription",
    "위고비처방": "glp1_prescription",
    "위고비후기": "glp1_prescription",
    "식욕억제제": "obesity_clinic_and_price",
    "혈당스파이크": "blood_sugar_and_metabolic",
    "혈당정상수치": "blood_sugar_and_metabolic",
    "셀룰라이트": "obesity_clinic_and_price",
    "프로페그라": "hair_loss_medication",
    "비아그라처방": "ed_medication",
    "비아그라효과": "ed_medication",
    "비아그라부작용": "ed_medication",
    "비아그라복용법": "ed_medication",
    "무지외반증치료": "musculoskeletal",
    "무지외반증": "musculoskeletal",
    "무지외반증운동": "musculoskeletal",
    "무지외반증교정": "musculoskeletal",
    "거북목": "musculoskeletal",
    "거북목교정": "musculoskeletal",
    "목디스크": "musculoskeletal",
    "일자목": "musculoskeletal",
    "족저근막염치료방법": "musculoskeletal",
    "족저근막염": "musculoskeletal",
    "족저근막염치료": "musculoskeletal",
    "발바닥통증": "musculoskeletal",
    "변비약": "digestive",
    "변비에좋은음식": "digestive",
    "변비": "digestive",
    "변비직빵": "digestive",
    "변비원인": "digestive",
    "쾌변": "digestive",
    "임산부변비": "digestive",
    "배에가스빼는법": "digestive",
    "변비해결": "digestive",
    "변비증상": "digestive",
}

KEYWORD_TITLE_GUIDANCE_OVERRIDES: dict[str, str] = {
    "나비약": (
        "나비약은 가격형보다 정체 설명형, 실체 경고형, 진짜 살 빠질까 같은 의문형, "
        "식욕억제제 복용 전 알아야 할 정보형 제목을 우선합니다. "
        "연예인 이슈나 화제성으로 유입되는 검색도 많아서 무엇인지, 왜 위험하다고 하는지, "
        "복용 전 어떤 점을 알아야 하는지가 제목 전면에 보여야 합니다. "
        "특히 정체, 실체, 식욕억제제란 무엇인지, 진짜 살 빠질까 같은 질문형을 우선하고 "
        "뭉뚱그린 경고문 형태는 피합니다."
    ),
    "마운자로": (
        "마운자로는 단순 비용형보다 처방 기준, 위고비와 차이, 실제 효과 체감, "
        "부작용 현실 중 하나를 전면에 세우는 제목을 우선합니다."
    ),
    "위고비": (
        "위고비는 처방 조건과 비용을 같이 묻더라도 질문형, 비교형, 현실 판단형 중 하나로 "
        "리듬을 바꾸고 안내문처럼 길게 끌지 않습니다."
    ),
}

KEYWORD_TITLE_ANGLE_OVERRIDES: dict[str, tuple[str, ...]] = {
    "나비약": (
        "정체 설명형: 나비약이 정확히 무엇인지 풀어주는 제목",
        "실체 경고형: 화제는 크지만 실체를 먼저 알아야 한다는 제목",
        "효과 의문형: 진짜 살 빠질까처럼 과대기대를 점검하는 제목",
        "복용 전 정보형: 식욕억제제 복용 전에 반드시 알아야 할 정보형 제목",
        "위험성 점검형: 부작용, 중독성, 오남용 위험을 짚는 제목",
        "이슈 해설형: 연예인 이슈로 뜬 배경과 약의 본질을 설명하는 제목",
    ),
    "마운자로": (
        "처방 기준형: 누구까지 상담 대상이 되는지 묻는 제목",
        "효과 체감형: 언제부터 변화가 보이는지 짚는 제목",
        "비교형: 위고비와 무엇이 다른지 정리하는 제목",
        "부작용 현실형: 많이 겪는 반응과 중단 기준을 짚는 제목",
        "유지 현실형: 계속 맞아도 되는지, 중단 후는 어떤지 보는 제목",
    ),
    "위고비": (
        "처방 질문형: 누구까지 처방 대상인지 묻는 제목",
        "현실 비용형: 약값보다 실제 유지 비용이 어느 정도인지 보는 제목",
        "비교형: 마운자로와 차이를 정리하는 제목",
        "효과 검증형: 진짜 얼마나 빠지는지 기대치를 조정하는 제목",
        "부작용 점검형: 맞기 전에 꼭 알아야 할 반응을 짚는 제목",
    ),
}

KEYWORD_HARD_BAN_PHRASES: dict[str, tuple[str, ...]] = {
    "나비약": (
        "비용 구조",
        "실제 비용",
        "월 비용",
        "진료비",
        "약값",
        "가격부터",
        "처방받기 전에",
        "복용 전에 알아야 할 것들",
        "효과보다 이게 먼저입니다",
        "위험 신호들",
        "꼭 확인해야 할",
        "포인트",
    ),
    "마운자로": (
        "처방 전에 확인해야 할 조건과 현실 비용",
        "먼저 확인해야 할 조건과 현실 비용",
    ),
    "위고비": (
        "기준이 어떻게 되고 실제 비용은 얼마나 드나요",
    ),
    "베르베린복용법": (
        "챙기기 전에",
        "해야 하는 이유",
    ),
}

KEYWORD_INTENT_HINTS_OVERRIDES: dict[str, tuple[str, ...]] = {
    "나비약": (
        "검색자는 나비약이 정확히 무엇인지, 왜 이슈가 되는지, 진짜 살이 빠지는 약인지부터 확인하려고 들어옵니다.",
        "가격보다 정체, 실체, 부작용, 오남용 위험, 복용 전 체크 포인트를 앞세운 제목이 더 잘 맞습니다.",
        "제목은 정체 설명형, 실체 경고형, 효과 의문형 중 하나만 선택합니다.",
    ),
    "위고비": (
        "검색자는 위고비 처방 기준, 마운자로와 차이, 실제 효과, 부작용, 유지 현실 중 하나를 먼저 확인하려고 들어옵니다.",
        "조건과 비용을 한 문장에 모두 넣는 안내문형보다, 한 초점을 또렷하게 잡은 정보형이나 비교형이 더 잘 맞습니다.",
        "제목은 처방형, 비교형, 효과 검증형, 부작용 점검형 중 하나만 선택합니다.",
    ),
    "마운자로": (
        "검색자는 마운자로 처방 기준, 위고비와 차이, 진짜 효과, 부작용, 유지 현실 중 하나를 먼저 확인하려고 들어옵니다.",
        "조건과 비용을 한 문장에 같이 묶기보다, 한 축만 정해서 설명하는 제목이 더 자연스럽습니다.",
        "제목은 처방형, 비교형, 효과 체감형, 부작용 현실형 중 하나만 선택합니다.",
    ),
}

FAMILY_INTENT_HINTS: dict[str, tuple[str, ...]] = {
    "glp1_prescription": (
        "검색자는 처방 조건, 효과 체감, 가격, 부작용, 유지 현실을 함께 궁금해합니다.",
        "알약 여부나 공급 상황처럼 시점 따라 바뀌는 정보는 단정하지 말고 현재 병원/공식 정보 확인 맥락을 남깁니다.",
        "제목은 효과형, 처방형, 가격현실형, 비교형 중 하나만 선택하는 편이 좋습니다.",
    ),
    "obesity_clinic_and_price": (
        "검색자는 가격 범위, 진료비와 약값 구분, 실제 유지비, 부작용을 먼저 확인합니다.",
        "불법 구매나 과장 후기처럼 보이는 문장은 피하고 현실적인 비용 구조를 먼저 설명합니다.",
        "제목은 가격형, 비교형, 선택기준형이 잘 맞습니다.",
    ),
    "supplement_and_nutrient": (
        "검색자는 효능 범위, 복용법, 식전 식후, 같이 먹을 때 주의할 점을 찾습니다.",
        "약을 대체한다는 식의 단정 대신 보조제 범위와 한계를 함께 설명합니다.",
        "제목은 효능형, 복용법형, 비교형이 잘 맞습니다.",
    ),
    "blood_sugar_and_metabolic": (
        "검색자는 초기 신호, 정상 기준, 식후 해석, 관리 팁을 빠르게 확인하고 싶어합니다.",
        "증상만으로 진단처럼 들리지 않게 하고 병원 상담이 필요한 시점을 같이 적어야 합니다.",
        "제목은 기준형, 신호형, 음식관리형이 잘 맞습니다.",
    ),
    "hair_loss_medication": (
        "검색자는 효과, 가격, 복용 기간, 부작용, 선택 기준을 궁금해합니다.",
        "다이어트 문맥으로 억지 연결하지 말고 탈모약 정보형으로 전환합니다.",
        "제목은 효과형, 가격형, 비교형이 잘 맞습니다.",
    ),
    "ed_medication": (
        "검색자는 처방 조건, 효과 체감 시점, 복용법, 부작용, 가격을 궁금해합니다.",
        "의료 정보를 단정하지 않고 전문의 상담 맥락을 함께 남깁니다.",
        "제목은 복용법형, 효과형, 부작용형, 처방형이 잘 맞습니다.",
    ),
    "musculoskeletal": (
        "검색자는 원인, 자가 진단 기준, 치료 방법, 교정 운동, 병원 방문 시점을 찾습니다.",
        "자가 치료만으로 해결된다는 식의 단정을 피하고 증상별 대응 기준을 같이 적습니다.",
        "제목은 치료형, 운동형, 원인형, 교정형이 잘 맞습니다.",
    ),
    "digestive": (
        "검색자는 빠른 해결법, 원인 파악, 좋은 음식, 약 선택, 생활 습관을 궁금해합니다.",
        "즉효성만 강조하지 않고 원인별 대응과 병원 상담 시점을 같이 적습니다.",
        "제목은 해결형, 원인형, 음식형, 약 비교형이 잘 맞습니다.",
    ),
}

FAMILY_TITLE_FRAMES: dict[str, tuple[str, ...]] = {
    "glp1_prescription": (
        "처방 기준과 현실 비용을 함께 잡는 정보형",
        "효과보다 먼저 봐야 할 조건을 앞세우는 정보형",
        "알약 오해나 비교 포인트를 정리하는 비교형",
        "유지 기간과 부작용 현실을 짚는 점검형",
    ),
    "obesity_clinic_and_price": (
        "가격 범위와 진료비 구조를 먼저 잡는 정보형",
        "실제 선택 전에 봐야 할 기준을 짚는 정보형",
        "비슷한 옵션 차이를 정리하는 비교형",
        "유지비와 부작용을 함께 보는 현실형",
    ),
    "supplement_and_nutrient": (
        "효능 범위를 깔끔하게 정리하는 정보형",
        "복용법과 식전 식후 포인트를 짚는 가이드형",
        "기대치와 한계를 같이 잡는 현실형",
        "같이 먹을 때 주의점을 강조하는 점검형",
    ),
    "blood_sugar_and_metabolic": (
        "기준 수치와 해석 포인트를 먼저 말하는 정보형",
        "초기 신호와 병원 가야 할 시점을 짚는 점검형",
        "음식과 생활 관리 기준을 중심에 두는 실용형",
        "헷갈리는 수치를 풀어주는 해석형",
    ),
    "hair_loss_medication": (
        "효과와 복용 기간을 함께 잡는 정보형",
        "가격과 선택 기준을 같이 보는 현실형",
        "성분 차이와 부작용을 정리하는 비교형",
        "누구에게 맞는지 판단하게 돕는 선택형",
    ),
    "ed_medication": (
        "처방 조건과 복용법을 함께 잡는 정보형",
        "효과 체감 시점과 주의사항을 짚는 가이드형",
        "성분 차이와 부작용을 정리하는 비교형",
        "가격과 처방 현실을 보는 선택형",
    ),
    "musculoskeletal": (
        "원인과 자가 판단 기준을 먼저 잡는 정보형",
        "교정 운동과 생활 습관을 중심에 두는 실용형",
        "치료 방법과 병원 선택 기준을 보는 현실형",
        "증상 단계별 대응을 정리하는 가이드형",
    ),
    "digestive": (
        "원인과 해결법을 빠르게 잡는 정보형",
        "음식과 생활 습관을 중심에 두는 실용형",
        "약 선택과 복용법을 정리하는 가이드형",
        "증상별 대응과 병원 시점을 짚는 점검형",
    ),
}

GLP1_TITLE_ANGLE_POOL: tuple[str, ...] = (
    "처방 문턱형: 누구까지 상담 대상인지 현실적으로 풀어주는 제목",
    "비교 선택형: 위고비와 마운자로 중 무엇이 다른지 고르게 돕는 제목",
    "효과 기대 조정형: 진짜 얼마나 빠지는지 기대치를 조절하는 제목",
    "부작용 현실형: 많이 겪는 반응과 중단 기준을 짚는 제목",
    "유지 현실형: 끊으면 다시 찌는지, 계속 맞아야 하는지 보는 제목",
    "병원 상담형: 진료실에서 실제로 먼저 확인하는 기준을 보여주는 제목",
    "화제 해설형: 왜 이렇게 많이 찾는지 배경과 본질을 정리하는 제목",
)

GLP1_OPENING_RHYTHM_POOL: tuple[str, ...] = (
    "{keyword} 왜 이렇게 많이 찾는지부터 짚는 화제 해설 리듬",
    "{keyword} 맞아볼까 고민된다면 먼저 보게 되는 판단 리듬",
    "{keyword} 처방 기준이 궁금했다면 이 축으로 여는 리듬",
    "{keyword} 진짜 효과 좋냐고 묻는 검색 의문형 리듬",
    "{keyword} 부작용보다 먼저 확인할 반응을 짚는 점검형 리듬",
    "{keyword} 끊으면 다시 찌는지 먼저 떠올리는 유지형 리듬",
    "{keyword} 병원에서 먼저 보는 수치를 앞세우는 상담형 리듬",
    "{keyword}와 위고비 차이부터 궁금한 비교형 리듬",
)

GLP1_HARD_BAN_PHRASES: tuple[str, ...] = (
    "처방 받으려면 기준이 어떻게 되고 실제 비용은 얼마나",
    "처방 받을 수 있는 조건과 한 달 실제 비용",
    "처방 전에 확인해야 할 조건과 현실 비용",
    "먼저 확인해야 할 조건과 현실 비용",
    "기준이 어떻게 되고 실제 비용은 얼마나",
    "조건과 현실 비용",
    "한 달 실제 비용 정리",
    "이것부터 확인하세요",
    "걱정된다면",
    "맞기 전에 이것부터",
)

GLP1_HARD_BAN_DESCRIPTIONS: tuple[str, ...] = (
    "처방 기준과 비용을 한 문장에 같이 묶는 안내문형 제목 금지",
    "조건과 현실 비용처럼 너무 익숙한 두 갈래 조합 금지",
    "받을 수 있는 조건과 한 달 실제 비용 정리 같은 뻔한 스켈레톤 금지",
    "이것부터 확인하세요, 걱정된다면 같은 두루뭉술한 훅 금지",
    "같은 family에서 최근 제목과 opening 리듬이 겹치면 재생성",
    "같은 family에서 최근 제목과 ending 리듬이 겹치면 재생성",
)

GLP1_LIVE_VIEW_CUE_RULES: tuple[tuple[str, tuple[str, ...], str], ...] = (
    (
        "comparison",
        ("vs", "차이", "다른"),
        "비교형: 위고비와 마운자로 차이나 선택 기준을 전면에 두는 제목 각도",
    ),
    (
        "prescription",
        ("처방", "병원", "기준"),
        "처방형: 누구까지 상담 대상인지, 병원에서 무엇을 보는지 짚는 제목 각도",
    ),
    (
        "effect",
        ("효과", "진짜", "좋나요"),
        "효과 검증형: 진짜 얼마나 체감되는지 기대치를 조절하는 제목 각도",
    ),
    (
        "side_effect",
        ("부작용", "무서", "놀랐"),
        "부작용 점검형: 맞기 전에 미리 알아야 할 반응을 짚는 제목 각도",
    ),
    (
        "trend",
        ("열광", "광풍", "이유"),
        "화제 해설형: 왜 이렇게 많이 찾는지 배경부터 설명하는 제목 각도",
    ),
    (
        "maintenance",
        ("유지", "다시", "중단"),
        "유지 현실형: 끊은 뒤와 장기 사용 현실을 짚는 제목 각도",
    ),
)

SUPPLEMENT_TITLE_ANGLE_POOL: tuple[str, ...] = (
    "복용 실패담형: 먹었는데 별 변화 없었던 이유를 짚는 제목",
    "성분 오해 교정형: 지방 분해나 만능 효능 오해를 바로잡는 제목",
    "타깃 한정형: 맞는 사람과 돈 아까운 사람을 가르는 제목",
    "기간 기대 조정형: 최소 몇 주는 봐야 하는지 체감 시점을 묻는 제목",
    "비교 우위형: 같이 먹을 필요가 없는 성분이나 대체 선택을 비교하는 제목",
    "구매 전 체크형: 함량, 원료, 제품 표기부터 봐야 한다는 제목",
    "부작용 선제형: 먹고 불편했다면 어떤 반응을 봐야 하는지 짚는 제목",
    "섭취 실수 교정형: 체감이 흐려지는 복용 습관 오류를 짚는 제목",
    "조합 주의형: 같이 먹지 말아야 할 영양제나 약 조합을 강조하는 제목",
    "원리 해체형: 혈당, 붓기, 식욕에 작용하는 방식을 쉽게 푸는 제목",
    "실사용 검증형: 후기에서 자주 보이는 체감 포인트를 정리하는 제목",
    "라벨 독해형: 제품 뒷면에서 확인할 함량과 표기를 앞세우는 제목",
)

SUPPLEMENT_OPENING_RHYTHM_POOL: tuple[str, ...] = (
    "{keyword} 굳이 따로 챙길 이유가 있는지 묻는 판단형 리듬",
    "{keyword} 검색량은 많은데 핵심은 다른 데 있다는 전환형 리듬",
    "{keyword} 성분표에서 뭘 먼저 봐야 하는지 짚는 라벨형 리듬",
    "{keyword} 내 돈 주고 살 만한지 따져보는 현실형 리듬",
    "{keyword} 체감이 빠른 사람과 아닌 사람을 가르는 분기형 리듬",
    "{keyword} 왜 찾는 사람이 많은지 원리부터 푸는 설명형 리듬",
    "{keyword} 후기를 믿기 전에 대상부터 가르는 선택형 리듬",
    "{keyword} 제품 고를 때 놓치기 쉬운 표기를 짚는 구매형 리듬",
    "{keyword} 기대보다 한계부터 아는 편이 나은 교정형 리듬",
    "{keyword} 누구에게 맞고 누구에겐 애매한지 가르는 적합도 리듬",
    "{keyword} 복용 타이밍보다 먼저 볼 기준을 꺼내는 판단 리듬",
    "{keyword} 한 번 사면 오래 먹게 되는 성분인지 따지는 지속형 리듬",
)

SUPPLEMENT_HARD_BAN_PHRASES: tuple[str, ...] = (
    "효능 범위와 보조제로서",
    "효능 범위와 보조제로",
    "기대할 수 있는 것들",
    "기대할 수 있는 것",
    "다른 영양제와 함께 먹을 때 주의할 성분",
    "다른 영양제와 겹치는 성분 먼저 점검",
    "어디까지 기대할 수 있고 어디서 멈춰야",
    "식전 식후 중 언제 먹는 게 맞을까",
    "주의할 성분",
    "효과 없다는",
    "효과 못 본",
    "변화 없었다면",
    "공통으로",
    "함량 기준",
    "시작 전에",
    "놓친",
    "거른",
    "짚어두세요",
    "봐야 합니다",
    "언제 먹냐고요",
    "시간대 하나",
    "달라졌더니",
    "달라지는 이유",
    "먼저 확인하세요",
    "한 가지 포인트",
    "같이 먹으면 안 되는 조합",
)

SUPPLEMENT_HARD_BAN_DESCRIPTIONS: tuple[str, ...] = (
    "효능 범위와 보조제로서 같은 무난한 템플릿 구문 금지",
    "기대할 수 있는 것들 같은 흐린 마무리 금지",
    "다른 영양제와 겹치는 성분 먼저 점검 패턴 금지",
    "어디까지 기대할 수 있고 어디서 멈춰야 같은 양분형 질문 금지",
    "식전 식후 중 언제 먹는 게 맞을까 구조 금지",
    "주의할 성분, 할 성분 같은 끝말 금지",
    "언제 먹냐고요, 시간대 하나, 한 가지 포인트 같은 과도한 대화체 훅 금지",
    "같이 먹으면 안 되는 조합, 먼저 확인하세요 같은 상투형 마무리 금지",
    "같은 family에서 최근 제목과 opening 3음절이 겹치면 재생성",
    "같은 family에서 최근 제목과 ending 4음절이 겹치면 재생성",
)

SUPPLEMENT_KEYWORD_GUIDANCE_OVERRIDES: dict[str, str] = {
    "베르베린": (
        "베르베린은 진짜 살 빠지나요, 믿어도 되나요 같은 오해 교정형과 "
        "혈당/다이어트 기대치 조정형 제목을 우선합니다."
    ),
    "베르베린효능": (
        "베르베린효능은 효능 나열보다 진짜 체감되는 포인트, 다이어트 기대치, "
        "언제 체감하는지 같은 검증형 제목을 우선합니다."
    ),
    "베르베린복용법": (
        "베르베린복용법은 식전 식후, 시간대, 같이 먹는 약/영양제, 나눠 먹는 이유 같은 "
        "실행형 제목을 우선합니다."
    ),
    "레시틴": (
        "레시틴은 따로 챙길 필요가 있는지, 믿어도 되는지, 콜린/인지질 관점에서 "
        "누가 챙기면 좋은지 판단형 제목을 우선합니다."
    ),
    "브로멜라인": (
        "브로멜라인은 얼마나 걸리나, 공복이 맞나, 고르는 법, 붓기 체감 포인트 같은 "
        "기간형과 구매형 제목을 우선합니다."
    ),
    "달맞이꽃종자유": (
        "달맞이꽃종자유는 감마리놀렌산, 40~50대 여성 관심사, 고르는 법, "
        "대상 분기형 제목을 우선합니다."
    ),
}

SUPPLEMENT_LIVE_VIEW_CUE_RULES: tuple[tuple[str, tuple[str, ...], str], ...] = (
    (
        "myth_check",
        ("믿", "진짜", "정말"),
        "오해 교정형: 믿어도 되는지, 과대기대인지 풀어주는 제목 각도",
    ),
    (
        "duration",
        ("얼마나", "체감", "몇 주"),
        "체감 시점형: 얼마나 걸리는지, 언제부터 느끼는지 제목 각도",
    ),
    (
        "buying",
        ("고르는", "추천", "비교", "함량"),
        "구매 기준형: 고르는 법, 함량, 라벨, 제품 차이를 보는 제목 각도",
    ),
    (
        "target",
        ("50대", "여성", "남성", "당뇨", "붓기"),
        "대상 분기형: 누구에게 맞는지 나누는 제목 각도",
    ),
    (
        "necessity",
        ("따로 먹", "필요", "굳이"),
        "필요성 판단형: 굳이 챙길 필요가 있는지 따지는 제목 각도",
    ),
    (
        "combo",
        ("조합", "함께", "같이 먹"),
        "조합형: 같이 먹는 조합이나 피해야 할 조합을 다루는 제목 각도",
    ),
    (
        "core_component",
        ("감마리놀렌산", "콜린", "인지질"),
        "핵심 성분형: 대표 성분 하나를 전면에 두는 제목 각도",
    ),
    (
        "caution",
        ("모르면 절대", "주의"),
        "경고형: 먹기 전 놓치면 안 되는 포인트를 강조하는 제목 각도",
    ),
)


@dataclass(frozen=True)
class TitleGenerationResult:
    title: str
    prompt: str
    exact_live_view_match: str
    attempts: int
    keyword_family: str
    generation_strategy: str


@dataclass(frozen=True)
class ManuscriptGenerationResult:
    manuscript: str
    prompt: str
    attempts: int
    char_count_no_space: int


def build_tag_block(tag: str, lines: list[str]) -> str:
    body = "\n".join(f"  {line}" for line in lines if line)
    return f"<{tag}>\n{body}\n</{tag}>"


def resolve_keyword_family(keyword: str) -> str:
    if keyword in KEYWORD_FAMILY_MAP:
        return KEYWORD_FAMILY_MAP[keyword]
    normalized = keyword.replace(" ", "")
    return KEYWORD_FAMILY_MAP.get(normalized, "supplement_and_nutrient")


def resolve_intent_hint_lines(keyword: str, keyword_family: str) -> list[str]:
    if keyword in KEYWORD_INTENT_HINTS_OVERRIDES:
        return list(KEYWORD_INTENT_HINTS_OVERRIDES[keyword])

    return list(FAMILY_INTENT_HINTS.get(keyword_family, ()))


def resolve_keyword_sub_intent(keyword: str, keyword_family: str) -> str:
    if keyword in KEYWORD_TITLE_GUIDANCE_OVERRIDES:
        return KEYWORD_TITLE_GUIDANCE_OVERRIDES[keyword]

    if keyword_family != "supplement_and_nutrient":
        return ""

    if keyword in SUPPLEMENT_KEYWORD_GUIDANCE_OVERRIDES:
        return SUPPLEMENT_KEYWORD_GUIDANCE_OVERRIDES[keyword]

    if keyword.endswith("효능"):
        return (
            "효능 키워드는 효능 나열보다 체감 시점, 맞는 사람, 과대기대 교정, "
            "검색자가 왜 이 성분을 찾는지 같은 관점으로 제목을 잡습니다."
        )

    if keyword.endswith("복용법"):
        return (
            "복용법 키워드는 식전 식후, 시간대, 나눠 먹는 이유, 같이 먹으면 안 되는 조합처럼 "
            "실행형 관점으로 제목을 잡습니다."
        )

    return (
        "성분명 단독 키워드는 효능 나열보다 작용 포인트, 라벨 확인 포인트, 고르는 법, "
        "누가 맞는지, 같이 먹는 조합 같은 현실 판단형 제목을 우선합니다."
    )


def pick_title_frame(keyword: str, keyword_family: str, attempt: int) -> str:
    frames = FAMILY_TITLE_FRAMES.get(keyword_family, FAMILY_TITLE_FRAMES["supplement_and_nutrient"])
    seed_value = sum(ord(ch) for ch in keyword) + attempt
    return frames[seed_value % len(frames)]


def sanitize_title(text: str) -> str:
    title = remove_markdown(text or "").splitlines()[0].strip()
    title = re.sub(r"\s+", " ", title)
    title = title.strip("\"' ")
    return title


def count_subtitles(text: str) -> int:
    return len(re.findall(r"^\d+\.\s", text, flags=re.M))


def count_chars_without_spaces(text: str) -> int:
    return len(re.sub(r"\s+", "", text))


def remove_keyword_once(text: str, keyword: str) -> str:
    if not text or not keyword:
        return text.strip()

    pattern = re.compile(re.escape(keyword), re.I)
    return pattern.sub("", text, count=1).strip()


def build_opening_signature(title: str, keyword: str, length: int = 8) -> str:
    remainder = re.sub(r"\s+", "", remove_keyword_once(title, keyword))
    return remainder[:length]


def build_ending_signature(title: str, length: int = 6) -> str:
    normalized = re.sub(r"\s+", "", title)
    return normalized[-length:]


def contains_banned_phrase(title: str, phrases: tuple[str, ...]) -> str:
    normalized_title = normalize_title_match(title)
    for phrase in phrases:
        if normalize_title_match(phrase) in normalized_title:
            return phrase
    return ""


def detect_supplement_angle_label(title: str) -> str:
    if re.search(r"식전|식후|타이밍|언제", title):
        return "timing"
    if re.search(r"같이\s*먹|조합|겹치", title):
        return "combo"
    if re.search(r"함량|농도|성분표|라벨|원료|mg", title, re.I):
        return "dosage_label"
    if re.search(r"작용|흡수|혈당|붓기|포만|분해", title):
        return "mechanism"
    if re.search(r"몇\s*주|기간|주차|체감|속도", title):
        return "timeline"
    if re.search(r"맞는\s*사람|안\s*맞|누구에게", title):
        return "target_fit"
    if re.search(r"효과\s*없|못\s*본|변화\s*없|공통|놓친|거른", title):
        return "failure_gap"
    return ""


def detect_glp1_angle_label(title: str) -> str:
    if re.search(r"vs|차이|다른", title, re.I):
        return "comparison"
    if re.search(r"처방|병원|기준|대상", title):
        return "prescription"
    if re.search(r"효과|진짜|빠지", title):
        return "effect"
    if re.search(r"부작용|오심|구토|불편|무섭", title):
        return "side_effect"
    if re.search(r"유지|중단|다시\s*찌", title):
        return "maintenance"
    if re.search(r"이유|광풍|열광", title):
        return "trend"
    return ""


def detect_keyword_specific_angle_label(keyword: str, title: str) -> str:
    if keyword != "나비약":
        return ""

    if re.search(r"정체|실체|무엇", title):
        return "identity"
    if re.search(r"진짜|살\s*빠질까|효과", title):
        return "effect_question"
    if re.search(r"부작용|중독|위험", title):
        return "risk_warning"
    if re.search(r"복용 전|알아야", title):
        return "before_info"
    return ""


def detect_title_focus_labels(keyword_family: str, title: str) -> set[str]:
    labels: set[str] = set()

    if re.search(r"가격|비용|약값|진료비|유지비", title):
        labels.add("cost")
    if re.search(r"처방|기준|조건|대상|병원", title):
        labels.add("eligibility")
    if re.search(r"vs|차이|비교|다른", title, re.I):
        labels.add("comparison")
    if re.search(r"효과|진짜|빠지|체감", title):
        labels.add("effect")
    if re.search(r"부작용|위험|중독|오남용|무섭", title):
        labels.add("risk")
    if re.search(r"정체|실체|무엇", title):
        labels.add("identity")
    if keyword_family == "supplement_and_nutrient":
        if re.search(r"식전|식후|공복|타이밍|언제", title):
            labels.add("timing")
        if re.search(r"같이\s*먹|조합|겹치", title):
            labels.add("combo")

    return labels


def extract_supplement_live_view_cues(live_view_titles: list[str]) -> list[str]:
    cues: list[str] = []
    joined_titles = " ".join(live_view_titles)

    for _, keywords, instruction in SUPPLEMENT_LIVE_VIEW_CUE_RULES:
        if any(keyword in joined_titles for keyword in keywords):
            cues.append(instruction)

    return cues


def extract_glp1_live_view_cues(live_view_titles: list[str]) -> list[str]:
    cues: list[str] = []
    joined_titles = " ".join(live_view_titles)

    for _, keywords, instruction in GLP1_LIVE_VIEW_CUE_RULES:
        if any(keyword in joined_titles for keyword in keywords):
            cues.append(instruction)

    return cues


def build_title_prompt(
    keyword: str,
    note: str,
    live_view_titles: list[str],
    recent_titles: list[str],
    recent_family_titles: list[str],
    retry_feedback: list[str],
) -> str:
    keyword_family = resolve_keyword_family(keyword)
    family_hint_lines = resolve_intent_hint_lines(keyword, keyword_family)
    sub_intent_rule = resolve_keyword_sub_intent(keyword, keyword_family)
    live_view_cues = extract_supplement_live_view_cues(live_view_titles)
    glp1_live_view_cues = extract_glp1_live_view_cues(live_view_titles)
    live_view_lines = [f"- {title}" for title in live_view_titles] or ["- 수집 결과 없음"]
    recent_title_lines = [f"- {title}" for title in recent_titles[-8:]] or ["- 최근 배치 제목 없음"]
    recent_family_title_lines = [f"- {title}" for title in recent_family_titles[-8:]] or ["- 같은 family 최근 제목 없음"]
    prompt_blocks = [
        build_tag_block(
            "task_context",
            [
                f"메인키워드: {keyword}",
                f"카테고리: {TARGET_CATEGORY}",
                f"키워드 family: {keyword_family}",
                f"추가 메모: {note or '없음'}",
            ],
        ),
        build_tag_block("family_intent", family_hint_lines),
        build_tag_block(
            "title_contract",
            [
                "제목에는 메인키워드를 정확히 1회만 사용합니다.",
                "제목은 정보형 우선, 필요할 때만 비교형을 보조로 씁니다.",
                "효과, 가격, 복용법, 비교, 증상, 음식, 처방 중 하나의 초점만 또렷하게 잡습니다.",
                "실시간 네이버 VIEW 제목과 완전히 동일한 제목은 금지합니다.",
                "최근 생성 제목과 같은 리듬을 반복하지 말고 문장 시작과 끝을 새롭게 만듭니다.",
                "과장형 총정리, 완벽, 기적 같은 광고 문구는 쓰지 않습니다.",
                f"이번 제목 리듬 힌트: {pick_title_frame(keyword, keyword_family, len(retry_feedback))}",
            ],
        ),
        build_tag_block("live_view_titles_to_reference", live_view_lines),
        build_tag_block("recent_generated_titles_to_avoid_repeating", recent_title_lines),
        build_tag_block("recent_same_family_titles_to_avoid_repeating", recent_family_title_lines),
    ]

    if sub_intent_rule:
        prompt_blocks.append(build_tag_block("keyword_sub_intent", [sub_intent_rule]))

    if keyword_family == "supplement_and_nutrient":
        prompt_blocks.extend(
            [
                build_tag_block(
                    "supplement_live_view_cues",
                    [f"- {item}" for item in live_view_cues] or ["- 실시간 VIEW cue가 부족하면 키워드별 미세 의도를 우선합니다."],
                ),
                build_tag_block(
                    "supplement_title_angle_pool",
                    [f"- {item}" for item in SUPPLEMENT_TITLE_ANGLE_POOL],
                ),
                build_tag_block(
                    "supplement_opening_rhythm_pool",
                    [f"- {item.format(keyword=keyword)}" for item in SUPPLEMENT_OPENING_RHYTHM_POOL],
                ),
                build_tag_block(
                    "supplement_hard_bans",
                    [f"- {item}" for item in SUPPLEMENT_HARD_BAN_DESCRIPTIONS],
                ),
                build_tag_block(
                    "supplement_rejected_phrases",
                    [f"- {item}" for item in SUPPLEMENT_HARD_BAN_PHRASES[:8]],
                ),
            ]
        )

    if keyword_family == "glp1_prescription":
        prompt_blocks.extend(
            [
                build_tag_block(
                    "glp1_live_view_cues",
                    [f"- {item}" for item in glp1_live_view_cues]
                    or ["- 실시간 VIEW cue가 부족하면 키워드별 미세 의도를 우선합니다."],
                ),
                build_tag_block(
                    "glp1_title_angle_pool",
                    [f"- {item}" for item in GLP1_TITLE_ANGLE_POOL],
                ),
                build_tag_block(
                    "glp1_opening_rhythm_pool",
                    [f"- {item.format(keyword=keyword)}" for item in GLP1_OPENING_RHYTHM_POOL],
                ),
                build_tag_block(
                    "glp1_hard_bans",
                    [f"- {item}" for item in GLP1_HARD_BAN_DESCRIPTIONS],
                ),
                build_tag_block(
                    "glp1_rejected_phrases",
                    [f"- {item}" for item in GLP1_HARD_BAN_PHRASES],
                ),
            ]
        )

    if keyword in KEYWORD_TITLE_ANGLE_OVERRIDES:
        prompt_blocks.append(
            build_tag_block(
                "keyword_specific_title_angles",
                [f"- {item}" for item in KEYWORD_TITLE_ANGLE_OVERRIDES[keyword]],
            )
        )

    if keyword in KEYWORD_HARD_BAN_PHRASES:
        prompt_blocks.append(
            build_tag_block(
                "keyword_specific_hard_bans",
                [f"- {item}" for item in KEYWORD_HARD_BAN_PHRASES[keyword]],
            )
        )

    if retry_feedback:
        prompt_blocks.append(build_tag_block("retry_feedback", [f"- {item}" for item in retry_feedback]))

    prompt_blocks.append(
        build_tag_block(
            "output_contract",
            [
                "출력은 최종 제목 한 줄만 반환합니다.",
                "따옴표, 번호, 불릿, 설명 문장 없이 제목만 씁니다.",
            ],
        )
    )

    return "\n\n".join(prompt_blocks)


def generate_diet_title(
    keyword: str,
    note: str = "",
    live_view_titles: list[str] | None = None,
    recent_titles: list[str] | None = None,
    recent_family_titles: list[str] | None = None,
) -> TitleGenerationResult:
    live_titles = live_view_titles or []
    previous_titles = recent_titles or []
    previous_family_titles = recent_family_titles or []
    feedback: list[str] = []
    last_prompt = ""
    last_title = ""
    last_exact_match = ""
    keyword_family = resolve_keyword_family(keyword)

    for attempt in range(1, TITLE_MAX_ATTEMPTS + 1):
        prompt = build_title_prompt(
            keyword=keyword,
            note=note,
            live_view_titles=live_titles,
            recent_titles=previous_titles,
            recent_family_titles=previous_family_titles,
            retry_feedback=feedback,
        )
        generated = call_ai(
            model_name=MODEL_NAME,
            system_prompt=TITLE_REWRITE_SYSTEM_PROMPT,
            user_prompt=prompt,
            max_tokens=120,
            temperature=1.0,
        )
        title = sanitize_title(generated)
        exact_match = find_exact_live_view_title_match(title, live_titles)
        keyword_count = count_keyword_occurrences(title, keyword)
        last_prompt = prompt
        last_title = title
        last_exact_match = exact_match

        issues: list[str] = []
        if not title:
            issues.append("제목이 비어 있습니다.")
        if keyword_count != 1:
            issues.append(f"메인키워드 사용 횟수가 {keyword_count}회입니다.")
        if exact_match:
            issues.append(f"실시간 VIEW 제목과 완전 동일합니다: {exact_match}")
        if len(title) > 38:
            issues.append("제목 길이가 길어서 더 간결하게 줄여야 합니다.")
        if any(normalize_title_match(title) == normalize_title_match(prev) for prev in previous_titles[-5:]):
            issues.append("최근 생성 제목과 너무 비슷합니다.")

        keyword_specific_ban_phrases = KEYWORD_HARD_BAN_PHRASES.get(keyword, ())
        banned_phrase = contains_banned_phrase(title, keyword_specific_ban_phrases)
        if banned_phrase:
            issues.append(f"이 키워드에서 금지한 표현이 들어갔습니다: {banned_phrase}")

        keyword_specific_angle = detect_keyword_specific_angle_label(keyword, title)
        if keyword == "나비약" and keyword_specific_angle in {"before_info", "risk_warning"}:
            if not re.search(r"정체|실체|무엇|진짜|살\s*빠질까", title):
                issues.append("나비약은 정체/실체/진짜 살 빠질까 축을 더 앞세워야 합니다.")

        focus_labels = detect_title_focus_labels(keyword_family, title)
        if keyword_family == "glp1_prescription" and len(focus_labels) >= 2:
            if {"cost", "eligibility"} <= focus_labels:
                issues.append("GLP-1 family는 처방 조건과 비용을 한 제목에 같이 묶는 고정 패턴을 피해야 합니다.")

            if {"effect", "comparison"} <= focus_labels:
                issues.append("GLP-1 family는 효과형과 비교형을 한 제목에 같이 섞지 않습니다.")

        if keyword_family == "supplement_and_nutrient":
            supplement_banned_phrase = contains_banned_phrase(title, SUPPLEMENT_HARD_BAN_PHRASES)
            if supplement_banned_phrase:
                issues.append(f"보조제 family 금지 표현이 들어갔습니다: {supplement_banned_phrase}")

            opening_signature = build_opening_signature(title, keyword)
            if opening_signature and any(
                opening_signature == build_opening_signature(prev, keyword)
                for prev in previous_family_titles[-4:]
            ):
                issues.append("같은 family 최근 제목과 opening 리듬이 겹칩니다.")

            ending_signature = build_ending_signature(title)
            if ending_signature and any(
                ending_signature == build_ending_signature(prev)
                for prev in previous_family_titles[-4:]
            ):
                issues.append("같은 family 최근 제목과 ending 리듬이 겹칩니다.")

            current_angle = detect_supplement_angle_label(title)
            if current_angle and any(
                current_angle == detect_supplement_angle_label(prev)
                for prev in previous_family_titles[-2:]
            ):
                issues.append("같은 family 최근 제목과 angle이 겹칩니다.")

            if {"timing", "combo"} <= focus_labels:
                issues.append("보조제 family는 복용 타이밍과 조합 이슈를 한 제목에 같이 묶지 않습니다.")

        if keyword_family == "glp1_prescription":
            glp1_banned_phrase = contains_banned_phrase(title, GLP1_HARD_BAN_PHRASES)
            if glp1_banned_phrase:
                issues.append(f"GLP-1 family 금지 표현이 들어갔습니다: {glp1_banned_phrase}")

            opening_signature = build_opening_signature(title, keyword)
            if opening_signature and any(
                opening_signature == build_opening_signature(prev, keyword)
                for prev in previous_family_titles[-4:]
            ):
                issues.append("같은 GLP-1 family 최근 제목과 opening 리듬이 겹칩니다.")

            ending_signature = build_ending_signature(title)
            if ending_signature and any(
                ending_signature == build_ending_signature(prev)
                for prev in previous_family_titles[-4:]
            ):
                issues.append("같은 GLP-1 family 최근 제목과 ending 리듬이 겹칩니다.")

            current_angle = detect_glp1_angle_label(title)
            if current_angle and any(
                current_angle == detect_glp1_angle_label(prev)
                for prev in previous_family_titles[-2:]
            ):
                issues.append("같은 GLP-1 family 최근 제목과 angle이 겹칩니다.")

        if not issues:
            return TitleGenerationResult(
                title=title,
                prompt=prompt,
                exact_live_view_match="",
                attempts=attempt,
                keyword_family=keyword_family,
                generation_strategy="live_view" if live_titles else "few_shot_fallback",
            )

        feedback = issues

    return TitleGenerationResult(
        title=last_title or keyword,
        prompt=last_prompt,
        exact_live_view_match=last_exact_match,
        attempts=TITLE_MAX_ATTEMPTS,
        keyword_family=keyword_family,
        generation_strategy="live_view" if live_titles else "few_shot_fallback",
    )


def build_manuscript_system_prompt(category: str) -> str:
    category_rules = get_category_tone_rules(category)
    return "\n\n".join(
        [
            "당신은 네이버 검색 의도에 맞춰 건강/다이어트 블로그 원고를 쓰는 한국어 라이터입니다.",
            "XML 블록에 적힌 지시를 우선하며 완성된 원고만 출력합니다.",
            build_tag_block(
                "global_contract",
                [
                    "출력은 제목 1줄 + 번호 소제목 본문 형태의 원고만 반환합니다.",
                    "첫 문단 2~3문장 안에 검색자가 가장 궁금한 답을 먼저 적습니다.",
                    "의료 정보를 진단처럼 단정하지 않고 현재 확인이 필요한 부분은 자연스럽게 풀어 씁니다.",
                    "메인키워드는 제목, 첫 문단, 1개 이상 소제목에 자연스럽게 녹여 씁니다.",
                    "5개 소제목을 기본으로 하고 비교형이나 절차형만 6개까지 허용합니다.",
                    "불필요한 메타 설명, 마크다운, 코드블록, 따옴표는 넣지 않습니다.",
                ],
            ),
            category_rules,
        ]
    )


def build_manuscript_prompt(
    keyword: str,
    note: str,
    title: str,
    keyword_family: str,
    live_view_titles: list[str],
    retry_feedback: list[str],
) -> str:
    family_hint_lines = resolve_intent_hint_lines(keyword, keyword_family)
    live_view_lines = [f"- {value}" for value in live_view_titles] or ["- 수집 결과 없음"]
    prompt_blocks = [
        build_tag_block(
            "task_context",
            [
                f"메인키워드: {keyword}",
                f"고정 제목: {title}",
                f"키워드 family: {keyword_family}",
                f"추가 메모: {note or '없음'}",
            ],
        ),
        build_tag_block("search_intent_hint", family_hint_lines),
        build_tag_block(
            "live_view_pattern_reference",
            [
                "아래 제목들은 패턴 참고용입니다. 동일 표현을 베끼지 말고 검색 의도만 참고합니다.",
                *live_view_lines,
            ],
        ),
        build_tag_block(
            "body_contract",
            [
                "첫 줄은 고정 제목과 정확히 같아야 합니다.",
                "서론 다음에는 번호 소제목 5개를 기본으로 씁니다.",
                "전체 원고는 공백 제외 1700자 이상을 목표로 하고, 설명이 얇아지지 않게 실제 판단 기준을 충분히 넣습니다.",
                "가격 키워드는 비용 범위와 진료비/약값 구분, 유지비를 함께 적습니다.",
                "복용법 키워드는 식전 식후, 복용 시간, 함께 먹을 때 주의점을 적습니다.",
                "증상 키워드는 위험 신호, 병원 상담 시점, 일상 관리 기준을 같이 적습니다.",
                "비교 키워드는 어떤 사람에게 더 맞는지 판단 기준을 넣습니다.",
                "마무리는 2~3문장으로 현실적인 체크 포인트를 남깁니다.",
            ],
        ),
        build_tag_block(
            "output_contract",
            [
                "원고 본문만 출력합니다.",
                "제목은 한 번만 출력합니다.",
                "소제목은 1. 2. 3. 형식으로만 씁니다.",
            ],
        ),
    ]

    if retry_feedback:
        prompt_blocks.append(build_tag_block("retry_feedback", [f"- {item}" for item in retry_feedback]))

    return "\n\n".join(prompt_blocks)


def normalize_manuscript(text: str, title: str) -> str:
    cleaned = remove_markdown(text)
    cleaned = comprehensive_text_clean(cleaned)
    lines = [line.strip() for line in cleaned.splitlines()]
    body_lines = [line for line in lines if line]
    if not body_lines:
        body_lines = [title]
    else:
        body_lines[0] = title
    normalized = "\n".join(body_lines)
    normalized = apply_simple_line_break(normalized)
    return normalized.strip()


def generate_diet_manuscript(
    keyword: str,
    title: str,
    note: str = "",
    keyword_family: str = "",
    live_view_titles: list[str] | None = None,
    category: str = TARGET_CATEGORY,
) -> ManuscriptGenerationResult:
    live_titles = live_view_titles or []
    retry_feedback: list[str] = []
    last_prompt = ""
    last_text = title

    for attempt in range(1, MANUSCRIPT_MAX_ATTEMPTS + 1):
        prompt = build_manuscript_prompt(
            keyword=keyword,
            note=note,
            title=title,
            keyword_family=keyword_family or resolve_keyword_family(keyword),
            live_view_titles=live_titles,
            retry_feedback=retry_feedback,
        )
        generated = call_ai(
            model_name=MODEL_NAME,
            system_prompt=build_manuscript_system_prompt(category),
            user_prompt=prompt,
            max_tokens=3200,
            temperature=0.8,
        )
        manuscript = normalize_manuscript(generated, title=title)
        subtitle_count = count_subtitles(manuscript)
        char_count_no_space = count_chars_without_spaces(manuscript)
        last_prompt = prompt
        last_text = manuscript

        issues: list[str] = []
        if get_title_line(manuscript) != title:
            issues.append("첫 줄 제목이 고정 제목과 다릅니다.")
        if subtitle_count < 5 or subtitle_count > 6:
            issues.append(f"소제목 개수가 {subtitle_count}개입니다.")
        if char_count_no_space < 1600:
            issues.append(f"원고 길이가 부족합니다: {char_count_no_space}자")

        if not issues:
            return ManuscriptGenerationResult(
                manuscript=manuscript,
                prompt=prompt,
                attempts=attempt,
                char_count_no_space=char_count_no_space,
            )

        retry_feedback = issues

    return ManuscriptGenerationResult(
        manuscript=last_text,
        prompt=last_prompt,
        attempts=MANUSCRIPT_MAX_ATTEMPTS,
        char_count_no_space=count_chars_without_spaces(last_text),
    )


def blog_filler_diet_v2_gen(
    user_instructions: str,
    live_view_titles: list[str] | None = None,
    recent_titles: list[str] | None = None,
    recent_family_titles: list[str] | None = None,
    category: str = TARGET_CATEGORY,
) -> dict[str, object]:
    parsed = parse_query(user_instructions)
    keyword = parsed.get("keyword", "") or ""
    note = parsed.get("note", "") or ""

    if not keyword:
        raise ValueError("키워드가 없습니다.")

    title_result = generate_diet_title(
        keyword=keyword,
        note=note,
        live_view_titles=live_view_titles,
        recent_titles=recent_titles,
        recent_family_titles=recent_family_titles,
    )
    manuscript_result = generate_diet_manuscript(
        keyword=keyword,
        title=title_result.title,
        note=note,
        keyword_family=title_result.keyword_family,
        live_view_titles=live_view_titles,
        category=category,
    )
    exact_match = find_exact_live_view_title_match(title_result.title, live_view_titles or [])

    return {
        "keyword": keyword,
        "category": category,
        "keyword_family": title_result.keyword_family,
        "model_name": MODEL_NAME,
        "title_generation_strategy": title_result.generation_strategy,
        "title": title_result.title,
        "manuscript": manuscript_result.manuscript,
        "title_prompt": title_result.prompt,
        "manuscript_prompt": manuscript_result.prompt,
        "exact_live_view_match": bool(exact_match),
        "matched_live_view_title": exact_match,
        "char_count_no_space": manuscript_result.char_count_no_space,
        "title_attempts": title_result.attempts,
        "manuscript_attempts": manuscript_result.attempts,
    }

"""Blog Filler Pet V2 - Naver research-based pet blog service"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from itertools import combinations
import random
import re
import textwrap
from typing import Callable

from _constants.Model import Model
from utils.query_parser import parse_query
from utils.text_cleaner import comprehensive_text_clean, remove_markdown
from utils.ai_client_factory import call_ai
from utils.logger import log


MODEL_NAME: str = Model.GROK_4_1_RES
MAX_FEEDBACK_ROUNDS = 2
LIVE_VIEW_TITLE_NOTE_KEYS: tuple[str, ...] = (
    "live_view_titles",
    "naver_view_titles",
    "view_titles",
    "reference_titles",
)
LIVE_VIEW_COLLECTION_STATUS_SUCCESS = "success"
LIVE_VIEW_COLLECTION_STATUS_FAILED = "failed"
LIVE_VIEW_COLLECTION_STATUS_NOTE_KEYS: tuple[str, ...] = (
    "live_view_collection_status",
    "naver_view_collection_status",
    "live_view_status",
    "naver_view_status",
    "view_collection_status",
    "view_status",
)
LIVE_VIEW_COLLECTION_ERROR_NOTE_KEYS: tuple[str, ...] = (
    "live_view_collection_error",
    "naver_view_collection_error",
    "live_view_error",
    "naver_view_error",
    "view_collection_error",
    "view_error",
)
LIVE_VIEW_COLLECTION_FAILURE_REASON_ALIASES: dict[str, str] = {
    "request_failed": "request_failed",
    "request_error": "request_failed",
    "fetch_failed": "request_failed",
    "fetch_error": "request_failed",
    "http_error": "request_failed",
    "network_error": "request_failed",
    "parse_failed": "parse_failed",
    "parsing_failed": "parse_failed",
    "parse_error": "parse_failed",
    "parser_error": "parse_failed",
    "invalid_payload": "parse_failed",
    "empty": "empty_result",
    "empty_result": "empty_result",
    "empty_results": "empty_result",
    "no_result": "empty_result",
    "no_results": "empty_result",
    "no_titles": "empty_result",
    "failed": "collection_failed",
    "error": "collection_failed",
}
LIVE_VIEW_COLLECTION_SUCCESS_ALIASES: set[str] = {
    "success",
    "ok",
    "done",
}
LIVE_VIEW_MIN_REFERENCE_TITLE_COUNT = 4
LIVE_VIEW_DUPLICATE_PAIR_OVERLAP_THRESHOLD = 0.67
LIVE_VIEW_DUPLICATE_PAIR_COUNT_THRESHOLD = 2
LIVE_VIEW_PATTERN_SKEW_LABELS: dict[str, str] = {
    "candidate_shortage": "후보 수가 적어서 검색 의도 표본이 좁습니다",
    "duplicate_heavy": "비슷한 제목이 많아 중복도가 높습니다",
    "pattern_skew": "같은 시작이나 마무리 패턴으로 과하게 몰려 있습니다",
}
TITLE_STRATEGY_LIVE_VIEW = "live_view"
TITLE_STRATEGY_FEW_SHOT_FALLBACK = "few_shot_fallback"

PEN_NAMES: list[str] = [
    "초파맘",
    "포메호두",
    "멍멍이사랑",
    "냥이집사",
    "펫러버",
    "댕댕이맘",
    "골댕이네",
    "뽀삐언니",
    "야옹이아빠",
    "코코네집사",
    "몽이맘",
    "해피독",
    "냥냥펀치",
    "츄르집사",
    "꼬리흔드는집",
    "먼치킨사랑",
    "말티즈홀릭",
    "푸들이네",
    "비숑맘",
    "시바견러버",
    "웰시코기댁",
    "골든패밀리",
    "러시안블루집사",
    "랙돌하우스",
    "스코티시맘",
    "브숏집사",
    "아비시니안댁",
    "벵갈이네",
    "페르시안집사",
    "터키시앙고라맘",
    "샴고양이댁",
    "먼치킨집사",
    "노르웨이숲댁",
    "메인쿤하우스",
    "치와와맘",
    "포메라니안댁",
    "요크셔집사",
    "닥스훈트러버",
    "슈나우저네",
    "보더콜리맘",
    "사모예드댁",
    "허스키하우스",
    "진돗개사랑",
    "삽살이네",
    "풍산개맘",
]


@dataclass(frozen=True)
class LiveViewTitleCollectionResult:
    status: str
    titles: tuple[str, ...]
    failure_reason: str = ""
    source: str = "note"
    quality_issues: tuple[str, ...] = ()
    raw_title_count: int = 0

    @property
    def has_titles(self) -> bool:
        return bool(self.titles)

    @property
    def has_quality_issues(self) -> bool:
        return bool(self.quality_issues)

TITLE_ANGLE_RULES: list[dict[str, str]] = [
    {
        "id": "price_summary",
        "label": "가격 총정리형",
        "rule": "제목은 분양가, 비용, 가격 정보를 앞세운 정리형으로 씁니다.",
        "example": "시바견 분양 가격 정보 총정리",
    },
    {
        "id": "reality_question",
        "label": "현실 질문형",
        "rule": "제목은 실제 성격, 현실 난이도, 초보자 적합성처럼 검색자가 바로 궁금해할 질문형으로 씁니다.",
        "example": "시바견 분양가와 특징 정리 실제 성격은 어떨까",
    },
    {
        "id": "must_read",
        "label": "입양 전 필독형",
        "rule": "제목은 분양 전 필독, 입양 전 필독처럼 사전 점검형으로 쓰고, 체크리스트나 총정리 같은 마무리는 쓰지 않습니다.",
        "example": "시바견분양 전 꼭 알아야 할 수명과 성격",
    },
    {
        "id": "basics_guide",
        "label": "기본 정보형",
        "rule": "제목은 분양 전 알아야 할 기본 정보, 처음 키우기 전 알아둘 점 같은 기본 가이드형으로 씁니다.",
        "example": "시바견 키우기 분양 전 알아야 할 기본 정보",
    },
    {
        "id": "mistake_prevention",
        "label": "실패 방지형",
        "rule": "제목은 실패 확률 줄이기, 후회 줄이기, 체크리스트 같은 리스크 회피형으로 씁니다.",
        "example": "시바견분양 이것만 알면 실패 확률 줄어요",
    },
    {
        "id": "checklist",
        "label": "체크리스트형",
        "rule": "제목은 숫자형 체크리스트, 확인 포인트, 꼭 볼 기준처럼 실행형으로 쓰고, 필독이라는 단어는 쓰지 않습니다.",
        "example": "시바견분양 전 반드시 확인할 7가지 기준",
    },
    {
        "id": "temperament_focus",
        "label": "성격 집중형",
        "rule": "제목은 성격, 고집, 독립성, 초보자 난이도처럼 성향 포인트를 앞세웁니다.",
        "example": "시바견분양 전 성격과 고집부터 봐야 하는 이유",
    },
    {
        "id": "hidden_cost",
        "label": "숨은 비용형",
        "rule": "제목은 분양가보다 초기비용, 유지비, 숨은 지출을 강조하는 비용 심화형으로 씁니다.",
        "example": "시바견분양 분양가보다 중요한 숨은 비용 정리",
    },
    {
        "id": "health_warning",
        "label": "건강 주의형",
        "rule": "제목은 털빠짐, 유전병, 건강관리, 주의사항을 전면에 둡니다.",
        "example": "시바견분양 전 털빠짐 건강 주의사항까지 체크",
    },
    {
        "id": "owner_story",
        "label": "실제 후기형",
        "rule": "제목은 후기, 경험담, 실제 키워보니 같은 체험형으로 씁니다.",
        "example": "시바견분양 고민하다 직접 키워본 현실 후기",
    },
]

INFO_PRIMARY_TITLE_ANGLE_IDS: tuple[str, ...] = (
    "price_summary",
    "basics_guide",
    "temperament_focus",
    "hidden_cost",
    "health_warning",
)

TITLE_OPENING_RULES: list[dict[str, str]] = [
    {
        "id": "price_opening",
        "label": "가격 리드형",
        "rule": "제목은 핵심 키워드 뒤에 가격대별, 비용, 분양가 같은 가격 단어를 바로 붙여 시작합니다.",
        "example": "시바견분양 가격대별 비용 총정리",
    },
    {
        "id": "question_opening",
        "label": "질문 리드형",
        "rule": "제목은 핵심 키워드 뒤에 초보자 괜찮을까, 실제 어떨까처럼 질문형 리듬으로 시작합니다.",
        "example": "시바견분양 초보자 괜찮을까 실제 성격과 난이도",
    },
    {
        "id": "imperative_opening",
        "label": "체크 리드형",
        "rule": "제목은 핵심 키워드 뒤에 꼭 체크할, 반드시 볼, 먼저 확인할처럼 행동 유도형으로 시작합니다.",
        "example": "시바견분양 꼭 체크할 건강 포인트",
    },
    {
        "id": "contrast_opening",
        "label": "비교 리드형",
        "rule": "제목은 핵심 키워드 뒤에 가격보다, 성격부터, 외모보다처럼 비교형 리듬으로 시작합니다.",
        "example": "시바견분양 가격보다 먼저 볼 성격 포인트",
    },
    {
        "id": "story_opening",
        "label": "경험 리드형",
        "rule": "제목은 핵심 키워드 뒤에 직접 키워보니, 받아보니, 겪어보니처럼 경험형 리듬으로 시작합니다.",
        "example": "시바견분양 직접 키워보니 알게 된 현실",
    },
    {
        "id": "list_opening",
        "label": "숫자 리드형",
        "rule": "제목은 핵심 키워드 뒤에 5가지, 7가지, 한 번에 보는처럼 숫자형 리스트 리듬으로 시작합니다.",
        "example": "시바견분양 7가지 기준만 보면 쉬워요",
    },
    {
        "id": "beginner_opening",
        "label": "초보자 리드형",
        "rule": "제목은 핵심 키워드 뒤에 초보자라면, 처음이라면, 첫 분양이라면처럼 입문자 시점으로 시작합니다.",
        "example": "시바견분양 초보자라면 먼저 볼 현실 포인트",
    },
    {
        "id": "regret_opening",
        "label": "후회 방지 리드형",
        "rule": "제목은 핵심 키워드 뒤에 후회 줄이려면, 실패 피하려면처럼 리스크 회피 문장으로 시작합니다.",
        "example": "시바견분양 후회 줄이려면 꼭 볼 기준",
    },
    {
        "id": "decision_opening",
        "label": "결정 전 리드형",
        "rule": "제목은 핵심 키워드 뒤에 결정 전에, 고르기 전에, 받기 전에처럼 의사결정 직전 리듬으로 시작합니다.",
        "example": "시바견분양 결정 전에 봐야 할 성격 기준",
    },
    {
        "id": "myth_opening",
        "label": "오해 방지 리드형",
        "rule": "제목은 핵심 키워드 뒤에 귀여움만 보면, 외모만 보면처럼 흔한 오해를 깨는 리듬으로 시작합니다.",
        "example": "시바견분양 귀여움만 보면 놓치는 현실",
    },
    {
        "id": "fact_opening",
        "label": "사실 리드형",
        "rule": "제목은 핵심 키워드 뒤에 실제 성격부터, 독립심부터, 털빠짐부터처럼 핵심 사실을 먼저 던지는 리듬으로 시작합니다.",
        "example": "시바견분양 실제 성격부터 봐야 하는 이유",
    },
    {
        "id": "health_opening",
        "label": "건강 리드형",
        "rule": "제목은 핵심 키워드 뒤에 유전병, 털빠짐, 건강관리 같은 건강 키워드를 바로 붙여 시작합니다.",
        "example": "시바견분양 유전병 털빠짐 건강관리 주의점",
    },
    {
        "id": "maintenance_opening",
        "label": "유지비 리드형",
        "rule": "제목은 핵심 키워드 뒤에 유지비, 초기비용, 숨은 비용처럼 운영비 관점으로 시작합니다.",
        "example": "시바견분양 유지비 초기비용 숨은 지출 정리",
    },
    {
        "id": "fit_opening",
        "label": "적합도 리드형",
        "rule": "제목은 핵심 키워드 뒤에 나랑 맞을까, 어떤 사람에게 맞을까처럼 적합도 판단형으로 시작합니다.",
        "example": "시바견분양 나랑 맞을까 성격과 난이도 정리",
    },
]

INFO_PRIMARY_OPENING_IDS: tuple[str, ...] = (
    "price_opening",
    "imperative_opening",
    "beginner_opening",
    "decision_opening",
    "fact_opening",
    "health_opening",
    "maintenance_opening",
)
COMPARISON_SUPPORT_OPENING_IDS: tuple[str, ...] = (
    "contrast_opening",
    "fit_opening",
)

TITLE_ENDING_RULES: list[dict[str, str]] = [
    {
        "id": "reason_ending",
        "label": "이유 마무리형",
        "rule": "제목 마무리는 '~하는 이유', '~봐야 하는 이유' 형태로 닫습니다.",
        "example": "포메라니안 분양 전 유전병부터 봐야 하는 이유",
    },
    {
        "id": "question_ending",
        "label": "질문 마무리형",
        "rule": "제목 마무리는 '~괜찮을까', '~쉬울까', '~할까' 같은 질문형으로 닫습니다.",
        "example": "비숑프리제 초보자가 키워도 괜찮을까",
    },
    {
        "id": "list_ending",
        "label": "숫자 마무리형",
        "rule": "제목 마무리는 '~5가지', '~3가지 기준', '~7가지 체크' 같은 숫자형으로 닫습니다.",
        "example": "말티즈분양 전 반드시 확인할 5가지",
    },
    {
        "id": "comparison_ending",
        "label": "비교 마무리형",
        "rule": "제목 마무리는 '~차이점', '~다른 점', '~비교해보니' 같은 비교형으로 닫습니다.",
        "example": "아메리칸숏헤어 코리안숏헤어 차이점 정리",
    },
    {
        "id": "experience_ending",
        "label": "경험 마무리형",
        "rule": "제목 마무리는 '~키워보니', '~겪어보니', '~알게 된 것들' 같은 체험 회고형으로 닫습니다.",
        "example": "골든리트리버 1년 키워보니 느낀 점",
    },
    {
        "id": "warning_ending",
        "label": "경고 마무리형",
        "rule": "제목 마무리는 '~후회합니다', '~실수 줄이세요', '~놓치지 마세요' 같은 경고형으로 닫습니다.",
        "example": "펫샵에서 이것 안 보면 후회합니다",
    },
    {
        "id": "guide_ending",
        "label": "안내 마무리형",
        "rule": "제목 마무리는 '~한눈에 보기', '~정리해봤어요', '~모아봤어요' 같은 부드러운 안내형으로 닫습니다.",
        "example": "브리티쉬숏헤어 성격과 분양 절차 정리해봤어요",
    },
    {
        "id": "checklist_ending",
        "label": "체크 마무리형",
        "rule": "제목 마무리는 '~체크해보세요', '~확인하세요', '~점검 포인트' 같은 행동 유도형으로 닫습니다.",
        "example": "길고양이 입양 전 이것만 체크해보세요",
    },
]

TITLE_ENDING_IDS: tuple[str, ...] = tuple(r["id"] for r in TITLE_ENDING_RULES)
COMPARISON_SUPPORT_TITLE_CUES: tuple[str, ...] = (
    "보다",
    "차이",
    "비교",
    "맞을까",
    "어떤",
    "선택",
    "고르기",
    "맞아요",
    "힘들어요",
)
TITLE_PATTERN_FILLER_WORDS: set[str] = {
    "비용",
    "가격",
    "분양가",
    "현실",
    "체크리스트",
    "체크포인트",
    "총정리",
    "정리",
    "가이드",
    "필독",
    "특징",
    "성격",
    "주의사항",
    "기본",
    "정보",
    "핵심",
    "입양",
    "분양",
    "전",
    "후",
    "실제",
    "초보자",
    "먼저",
    "확인할",
    "결정",
    "준비",
    "포인트",
    "기준",
    "절차",
    "수명",
    "유전병",
    "건강",
    "관리",
    "유지비",
}
TITLE_PATTERN_REPEATY_OPENINGS: set[str] = {
    "전",
    "후",
    "먼저",
    "꼭",
    "반드시",
    "초보자",
    "결정",
    "실제",
    "가격",
    "유지비",
    "기본",
    "나랑",
    "성격보다",
    "가격보다",
}
TITLE_CORE_OVERLAP_STOPWORDS: set[str] = {
    "꼭",
    "봐야",
    "알아야",
    "할",
    "하는",
    "보는",
    "이유",
}
TITLE_PATTERN_GENERIC_ENDINGS: tuple[str, ...] = (
    "총정리",
    "완전 정리",
    "체크리스트",
    "체크포인트",
    "가이드",
    "기본 정보",
    "핵심 정보",
    "현실",
    "현실 정보",
    "주의사항",
    "포인트",
    "기준",
    "정리",
)
TITLE_PATTERN_HINT_TEMPLATES: tuple[str, ...] = (
    "핵심키워드 전 + 기본 정보나 체크리스트로 마무리하는 골격",
    "핵심키워드 뒤에 먼저 확인할이나 꼭 볼을 붙이고 다시 상투적 마무리로 닫는 골격",
    "비용 성격 현실 체크리스트처럼 명사만 3개 이상 나열하는 골격",
    "성격보다 가격보다 같은 비교 리드 뒤에 정리형 마무리를 붙이는 골격",
)
TITLE_PATTERN_REWRITE_SYSTEM_PROMPT = """You are a Korean Naver VIEW title strategist for pet blog posts.
Return exactly one final title only.
No labels, no markdown, no quotes, no bullet points.
Use natural Korean only.
Keep the target keyword intact and use it exactly once.
Read live Naver VIEW titles for search intent, but never copy their wording.
Reject stale title skeletons and make the sentence rhythm feel fresh and specific."""
TITLE_WORD_OVERUSE_PHRASE_REPLACEMENTS: tuple[tuple[str, str], ...] = (
    (
        r"(?:먼저|꼭|반드시)\s+확인할\s+((?:\d+가지\s+)?)체크포인트",
        r"\1체크포인트",
    ),
    (
        r"(?:먼저|꼭|반드시)\s+확인할\s+((?:\d+가지\s+)?)체크리스트",
        r"\1체크리스트",
    ),
    (r"기본\s+정보와\s+키우기\s+가이드", "키우기 기본 정보"),
    (
        r"기본\s+정보\s+(?:가이드|총정리|정리)",
        "기본 정보",
    ),
    (
        r"핵심\s+정보\s+(?:가이드|총정리|정리)",
        "핵심 정보",
    ),
    (r"체크리스트\s+(?:포인트|기준)", "체크리스트"),
    (r"체크포인트\s+(?:포인트|기준)", "체크포인트"),
    (r"(?:현실\s+실제|실제\s+현실|현실\s+실태|실태\s+현실)", "현실"),
    (r"(?:성격\s+특징|특징\s+성격)", "성격"),
)
TITLE_WORD_OVERUSE_MULTI_WORD_TERMS: tuple[str, ...] = (
    "기본 정보",
    "핵심 정보",
    "완전 정리",
    "총정리",
    "체크포인트",
    "체크리스트",
    "확인 포인트",
    "숨은 비용",
    "초기 비용",
)
TITLE_WORD_OVERUSE_FAMILY_MAP: dict[str, str] = {
    "체크리스트": "guidance",
    "체크포인트": "guidance",
    "확인 포인트": "guidance",
    "확인할": "guidance",
    "가이드": "guidance",
    "정리": "guidance",
    "총정리": "guidance",
    "완전 정리": "guidance",
    "필독": "guidance",
    "현실": "reality",
    "실제": "reality",
    "실태": "reality",
    "가격": "generic_cost",
    "비용": "generic_cost",
    "분양가": "specific_cost",
    "유지비": "specific_cost",
    "초기비용": "specific_cost",
    "초기 비용": "specific_cost",
    "숨은 비용": "specific_cost",
    "성격": "trait",
    "특징": "trait",
    "주의사항": "caution",
    "주의점": "caution",
}
TITLE_WORD_OVERUSE_FAMILY_PRIORITY: dict[str, tuple[str, ...]] = {
    "guidance": (
        "체크리스트",
        "체크포인트",
        "가이드",
        "총정리",
        "완전 정리",
        "정리",
        "필독",
        "확인 포인트",
        "확인할",
    ),
    "reality": ("현실", "실태", "실제"),
}
TITLE_WORD_OVERUSE_PREFIX_TOKENS: set[str] = {"먼저", "꼭", "반드시"}


def apply_simple_line_break(text: str, width: int = 34) -> str:
    lines = text.splitlines()
    formatted_lines: list[str] = []
    title_kept = False

    for line in lines:
        stripped = line.strip()

        if not stripped:
            if formatted_lines and formatted_lines[-1] != "":
                formatted_lines.append("")
            continue

        if not title_kept:
            formatted_lines.append(stripped)
            formatted_lines.append("")
            title_kept = True
            continue

        if re.match(r"^\d+\.\s", stripped):
            if formatted_lines and formatted_lines[-1] != "":
                formatted_lines.append("")
            formatted_lines.append(stripped)
            formatted_lines.append("")
            continue

        wrapped = textwrap.fill(
            stripped,
            width=width,
            break_long_words=False,
            break_on_hyphens=False,
        )
        formatted_lines.extend(wrapped.splitlines())

    result = "\n".join(formatted_lines)
    result = re.sub(r"\n{3,}", "\n\n", result)
    return result.strip()


def normalize_keyword(keyword: str) -> str:
    return keyword.replace(" ", "").strip().lower()


def normalize_title_match(title: str) -> str:
    return re.sub(r"\s+", "", title.strip().lower())


def build_keyword_pattern(keyword: str) -> re.Pattern[str] | None:
    parts = [re.escape(part) for part in keyword.split() if part.strip()]
    if not parts:
        return None

    return re.compile(r"\s*".join(parts))


def count_keyword_occurrences(text: str, keyword: str) -> int:
    if not text or not keyword:
        return 0

    pattern = build_keyword_pattern(keyword)
    if pattern is None:
        return 0

    return len(pattern.findall(text))


def count_chars_without_spaces(text: str) -> int:
    return len(text.replace(" ", "").replace("\n", ""))


def parse_note_params(note: str) -> dict[str, str]:
    if not note:
        return {}

    params: dict[str, str] = {}
    for chunk in note.split(";"):
        if "=" not in chunk:
            continue
        key, value = chunk.split("=", 1)
        key = key.strip().lower()
        value = value.strip()
        if key and value:
            params[key] = value
    return params


def split_avoid_titles(raw: str) -> list[str]:
    if not raw:
        return []

    chunks = raw.split("||") if "||" in raw else raw.splitlines()
    titles: list[str] = []
    seen: set[str] = set()

    for chunk in chunks:
        title = chunk.strip()
        normalized = normalize_title_match(title)
        if not normalized or normalized in seen:
            continue
        titles.append(title)
        seen.add(normalized)

    return titles


def split_avoid_openings(raw: str) -> list[str]:
    if not raw:
        return []

    return [opening.strip() for opening in raw.split("||") if opening.strip()]


def normalize_live_view_collection_reason(raw_value: object) -> str:
    if raw_value is None:
        return ""

    normalized = re.sub(r"[\s-]+", "_", str(raw_value).strip().lower())
    if not normalized:
        return ""

    if normalized in LIVE_VIEW_COLLECTION_SUCCESS_ALIASES:
        return LIVE_VIEW_COLLECTION_STATUS_SUCCESS

    return LIVE_VIEW_COLLECTION_FAILURE_REASON_ALIASES.get(
        normalized,
        "collection_failed",
    )


def get_live_view_collection_failure_reason(note_params: dict[str, object]) -> str:
    for key in LIVE_VIEW_COLLECTION_STATUS_NOTE_KEYS:
        reason = normalize_live_view_collection_reason(note_params.get(key))
        if not reason or reason == LIVE_VIEW_COLLECTION_STATUS_SUCCESS:
            continue
        return reason

    for key in LIVE_VIEW_COLLECTION_ERROR_NOTE_KEYS:
        error_message = str(note_params.get(key) or "").strip()
        if error_message:
            return "collection_failed"

    return ""


def flatten_live_view_title_payload(raw_payload: object) -> list[str]:
    if raw_payload is None:
        return []

    if isinstance(raw_payload, (list, tuple, set)):
        payload_items = list(raw_payload)
    else:
        payload_items = [raw_payload]

    titles: list[str] = []

    for item in payload_items:
        if item is None:
            continue

        if isinstance(item, str):
            chunks = split_avoid_titles(item)
        elif isinstance(item, dict):
            title = str(item.get("title", "") or "").strip()
            chunks = [title] if title else []
        elif isinstance(item, (list, tuple, set)):
            chunks = flatten_live_view_title_payload(list(item))
        else:
            raise TypeError(
                f"지원하지 않는 실시간 VIEW 제목 형식입니다: {type(item).__name__}"
            )

        titles.extend(title.strip() for title in chunks if str(title).strip())

    return titles


def deduplicate_live_view_titles(raw_titles: list[str]) -> list[str]:
    titles: list[str] = []
    seen: set[str] = set()

    for raw_title in raw_titles:
        title = raw_title.strip()
        normalized = normalize_title_match(title)
        if not normalized or normalized in seen:
            continue
        titles.append(title)
        seen.add(normalized)

    return titles


def parse_live_view_title_payload(raw_payload: object) -> list[str]:
    return deduplicate_live_view_titles(flatten_live_view_title_payload(raw_payload))


def describe_live_view_quality_issues(quality_issues: tuple[str, ...]) -> list[str]:
    descriptions: list[str] = []
    seen: set[str] = set()

    for quality_issue in quality_issues:
        description = LIVE_VIEW_PATTERN_SKEW_LABELS.get(quality_issue, "").strip()
        if not description or description in seen:
            continue
        descriptions.append(description)
        seen.add(description)

    return descriptions


def build_live_view_collection_failure_result(
    failure_reason: str,
    source: str,
) -> LiveViewTitleCollectionResult:
    return LiveViewTitleCollectionResult(
        status=LIVE_VIEW_COLLECTION_STATUS_FAILED,
        titles=(),
        failure_reason=failure_reason,
        source=source,
        raw_title_count=0,
    )


def resolve_live_view_title_collection(
    keyword: str = "",
    note: str = "",
    note_params: dict[str, object] | None = None,
    collector: Callable[[], object] | None = None,
) -> LiveViewTitleCollectionResult:
    params = note_params or parse_note_params(note)

    declared_failure_reason = get_live_view_collection_failure_reason(params)
    if declared_failure_reason:
        log.info(
            f"[pet_v2] live VIEW collection status=failed"
            f" | source=note"
            f" | reason={declared_failure_reason}"
        )
        return build_live_view_collection_failure_result(
            failure_reason=declared_failure_reason,
            source="note",
        )

    source = "collector" if collector is not None else "note"

    try:
        raw_payload = (
            collector()
            if collector is not None
            else [params.get(key) for key in LIVE_VIEW_TITLE_NOTE_KEYS if key in params]
        )
    except Exception as e:
        log.warning(
            f"[pet_v2] live VIEW collection request failed"
            f" | source={source}"
            f" | error={e}"
        )
        return build_live_view_collection_failure_result(
            failure_reason="request_failed",
            source=source,
        )

    try:
        raw_titles = flatten_live_view_title_payload(raw_payload)
        titles = deduplicate_live_view_titles(raw_titles)
    except Exception as e:
        log.warning(
            f"[pet_v2] live VIEW collection parse failed"
            f" | source={source}"
            f" | error={e}"
        )
        return build_live_view_collection_failure_result(
            failure_reason="parse_failed",
            source=source,
        )

    if not titles:
        log.info(
            f"[pet_v2] live VIEW collection status=failed"
            f" | source={source}"
            f" | reason=empty_result"
        )
        return build_live_view_collection_failure_result(
            failure_reason="empty_result",
            source=source,
        )

    quality_issues = get_live_view_collection_quality_issues(
        keyword=keyword,
        live_view_titles=titles,
        raw_title_count=len(raw_titles),
    )
    quality_descriptions = describe_live_view_quality_issues(quality_issues)
    log.info(
        f"[pet_v2] live VIEW collection status=success"
        f" | source={source}"
        f" | count={len(titles)}"
        f" | raw_count={len(raw_titles)}"
        + (
            f" | quality={' / '.join(quality_descriptions)}"
            if quality_descriptions
            else ""
        )
    )
    return LiveViewTitleCollectionResult(
        status=LIVE_VIEW_COLLECTION_STATUS_SUCCESS,
        titles=tuple(titles),
        source=source,
        quality_issues=quality_issues,
        raw_title_count=len(raw_titles),
    )


def get_live_view_titles(
    keyword: str = "",
    note: str = "",
    note_params: dict[str, object] | None = None,
) -> list[str]:
    collection_result = resolve_live_view_title_collection(
        keyword=keyword,
        note=note,
        note_params=note_params,
    )
    return list(collection_result.titles)


def find_exact_live_view_title_match(title: str, live_view_titles: list[str]) -> str:
    normalized_title = normalize_title_match(title)
    if not normalized_title:
        return ""

    for live_view_title in live_view_titles:
        if normalized_title == normalize_title_match(live_view_title):
            return live_view_title.strip()

    return ""


def resolve_target_keyword(keyword: str, note: str = "") -> str:
    normalized_keyword = normalize_keyword(keyword)
    normalized_note = normalize_keyword(note)

    if normalized_keyword != "입양조건":
        return keyword.strip()

    if any(term in normalized_note for term in ("유기묘", "고양이", "묘")):
        return "고양이 입양조건"

    if "유기견" in normalized_note:
        return "유기견 입양조건"

    return "강아지 입양조건"


def get_title_line(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def get_intro_text(text: str, max_lines: int = 6) -> str:
    non_empty_lines = [line.strip() for line in text.splitlines() if line.strip()]

    if not non_empty_lines:
        return ""

    return " ".join(non_empty_lines[1 : 1 + max_lines])


def count_numbered_subtitles(text: str) -> int:
    return sum(
        1
        for line in text.splitlines()
        if re.match(r"^\s*\d+\.\s", line.strip())
    )


def replace_title_line(text: str, title: str) -> str:
    stripped_title = title.strip()
    if not stripped_title:
        return text.strip()

    lines = text.splitlines()

    for index, line in enumerate(lines):
        if line.strip():
            lines[index] = stripped_title
            break
    else:
        return stripped_title

    return "\n".join(lines).strip()


def clean_title_remainder(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip()
    cleaned = re.sub(r"^[,.:;|/()\[\]]+", "", cleaned).strip()
    cleaned = re.sub(r"^(와|과|및)\s+", "", cleaned).strip()
    return cleaned


def tokenize_title(text: str) -> list[str]:
    cleaned = re.sub(r"[^0-9A-Za-z가-힣 ]+", " ", text)
    return [token for token in cleaned.split() if token]


def extract_title_remainder(title: str, keyword: str) -> str:
    normalized_title = re.sub(r"\s+", " ", title).strip()
    title_keyword = keyword.strip()

    if not normalized_title or not title_keyword:
        return normalized_title

    if normalized_title.startswith(title_keyword):
        return clean_title_remainder(normalized_title[len(title_keyword) :])

    pattern = build_keyword_pattern(title_keyword)
    if pattern is None:
        return normalized_title

    return clean_title_remainder(pattern.sub(" ", normalized_title, count=1))


def get_title_ending_phrase(remainder: str, tokens: list[str]) -> str:
    for phrase in sorted(TITLE_PATTERN_GENERIC_ENDINGS, key=len, reverse=True):
        if remainder.endswith(phrase):
            return phrase

    return tokens[-1] if tokens else ""


def get_title_pattern_profile(title: str, keyword: str) -> dict[str, object]:
    remainder = extract_title_remainder(title=title, keyword=keyword)
    tokens = tokenize_title(remainder)
    filler_tokens = [
        token for token in tokens if token.lower() in TITLE_PATTERN_FILLER_WORDS
    ]
    core_tokens = [
        token for token in tokens if token.lower() not in TITLE_PATTERN_FILLER_WORDS
    ]

    return {
        "remainder": remainder,
        "tokens": tokens,
        "opening": tokens[0].lower() if tokens else "",
        "ending": get_title_ending_phrase(remainder=remainder, tokens=tokens).lower(),
        "filler_tokens": filler_tokens,
        "core_tokens": core_tokens,
    }


def get_live_view_title_pattern_counters(
    keyword: str,
    live_view_titles: list[str],
) -> tuple[Counter[str], Counter[str], int]:
    opening_counter: Counter[str] = Counter()
    ending_counter: Counter[str] = Counter()
    generic_stack_count = 0

    for title in live_view_titles[:10]:
        profile = get_title_pattern_profile(title=title, keyword=keyword)
        opening = str(profile["opening"])
        ending = str(profile["ending"])
        filler_tokens = profile["filler_tokens"]
        core_tokens = profile["core_tokens"]

        if opening in TITLE_PATTERN_REPEATY_OPENINGS:
            opening_counter[opening] += 1
        if ending in TITLE_PATTERN_GENERIC_ENDINGS:
            ending_counter[ending] += 1
        if len(filler_tokens) >= 3 and len(core_tokens) <= 1:
            generic_stack_count += 1

    return opening_counter, ending_counter, generic_stack_count


def get_dominant_live_view_title_patterns(
    keyword: str,
    live_view_titles: list[str],
) -> tuple[set[str], set[str], bool]:
    opening_counter, ending_counter, generic_stack_count = (
        get_live_view_title_pattern_counters(
            keyword=keyword,
            live_view_titles=live_view_titles,
        )
    )

    dominant_openings = {
        opening for opening, count in opening_counter.items() if count >= 2
    }
    dominant_endings = {ending for ending, count in ending_counter.items() if count >= 2}

    return dominant_openings, dominant_endings, generic_stack_count >= 2


def get_live_view_title_core_overlap(
    keyword: str,
    left_title: str,
    right_title: str,
) -> float:
    left_core_tokens = {
        str(token).lower()
        for token in get_title_pattern_profile(title=left_title, keyword=keyword)[
            "core_tokens"
        ]
        if str(token).lower() not in TITLE_CORE_OVERLAP_STOPWORDS
    }
    right_core_tokens = {
        str(token).lower()
        for token in get_title_pattern_profile(title=right_title, keyword=keyword)[
            "core_tokens"
        ]
        if str(token).lower() not in TITLE_CORE_OVERLAP_STOPWORDS
    }

    if not left_core_tokens or not right_core_tokens:
        return 0.0

    return len(left_core_tokens & right_core_tokens) / len(
        left_core_tokens | right_core_tokens
    )


def get_live_view_collection_quality_issues(
    keyword: str,
    live_view_titles: list[str],
    raw_title_count: int = 0,
) -> tuple[str, ...]:
    if not live_view_titles:
        return ()

    sampled_titles = live_view_titles[:8]
    issues: list[str] = []
    seen_issues: set[str] = set()

    def add_issue(issue: str) -> None:
        if issue in seen_issues:
            return
        issues.append(issue)
        seen_issues.add(issue)

    if len(sampled_titles) < LIVE_VIEW_MIN_REFERENCE_TITLE_COUNT:
        add_issue("candidate_shortage")

    duplicate_count = max(raw_title_count - len(live_view_titles), 0)
    if raw_title_count >= LIVE_VIEW_MIN_REFERENCE_TITLE_COUNT and duplicate_count >= 2:
        add_issue("duplicate_heavy")

    duplicate_pair_count = sum(
        1
        for left_title, right_title in combinations(sampled_titles, 2)
        if get_live_view_title_core_overlap(
            keyword=keyword,
            left_title=left_title,
            right_title=right_title,
        )
        >= LIVE_VIEW_DUPLICATE_PAIR_OVERLAP_THRESHOLD
    )
    if duplicate_pair_count >= LIVE_VIEW_DUPLICATE_PAIR_COUNT_THRESHOLD:
        add_issue("duplicate_heavy")

    opening_counter, ending_counter, generic_stack_count = (
        get_live_view_title_pattern_counters(
            keyword=keyword,
            live_view_titles=sampled_titles,
        )
    )
    dominant_pattern_threshold = max(3, (len(sampled_titles) * 3 + 3) // 4)
    dominant_opening_count = max(opening_counter.values(), default=0)
    dominant_ending_count = max(ending_counter.values(), default=0)

    if (
        dominant_opening_count >= dominant_pattern_threshold
        or dominant_ending_count >= dominant_pattern_threshold
        or generic_stack_count >= max(2, dominant_pattern_threshold - 1)
    ):
        add_issue("pattern_skew")

    return tuple(issues)


def get_repetitive_title_skeleton_hints(
    keyword: str,
    live_view_titles: list[str],
) -> list[str]:
    hints: list[str] = []
    seen: set[str] = set()

    def add_hint(hint: str) -> None:
        normalized_hint = hint.strip()
        if not normalized_hint or normalized_hint in seen:
            return
        hints.append(normalized_hint)
        seen.add(normalized_hint)

    dominant_openings, dominant_endings, has_generic_stack = (
        get_dominant_live_view_title_patterns(
            keyword=keyword,
            live_view_titles=live_view_titles,
        )
    )

    for opening in sorted(dominant_openings):
        add_hint(f"{keyword} {opening} ...")

    for ending in sorted(dominant_endings):
        add_hint(f"... {ending}")

    if has_generic_stack:
        add_hint("비용 성격 현실 체크리스트처럼 명사만 3개 이상 나열하는 형태")

    for template in TITLE_PATTERN_HINT_TEMPLATES:
        if len(hints) >= 4:
            break
        add_hint(template)

    return hints


def analyze_repetitive_title_pattern(
    title: str,
    keyword: str,
    live_view_titles: list[str],
) -> tuple[int, list[str], dict[str, object]]:
    profile = get_title_pattern_profile(title=title, keyword=keyword)
    tokens = profile["tokens"]

    if not tokens:
        return 0, [], profile

    opening = str(profile["opening"])
    ending = str(profile["ending"])
    filler_tokens = profile["filler_tokens"]
    core_tokens = profile["core_tokens"]
    score = 0
    reasons: list[str] = []

    def add_reason(points: int, reason: str) -> None:
        nonlocal score
        if reason in reasons:
            return
        score += points
        reasons.append(reason)

    if len(filler_tokens) >= 3 and len(core_tokens) <= 1:
        add_reason(2, "핵심 정보보다 상투적 명사 나열 비중이 높습니다")

    if opening in {"전", "후"} and ending in TITLE_PATTERN_GENERIC_ENDINGS:
        add_reason(1, "핵심키워드 전후 리듬 뒤에 상투적 정리형 마무리가 붙었습니다")

    if (
        opening in TITLE_PATTERN_REPEATY_OPENINGS
        and ending in TITLE_PATTERN_GENERIC_ENDINGS
        and len(core_tokens) <= 1
    ):
        add_reason(1, "자주 반복되던 제목 골격과 비슷한 정보형 패턴입니다")

    dominant_openings, dominant_endings, has_generic_stack = (
        get_dominant_live_view_title_patterns(
            keyword=keyword,
            live_view_titles=live_view_titles,
        )
    )
    if opening in dominant_openings and ending in dominant_endings:
        add_reason(2, "실시간 VIEW에서 많이 보이는 시작과 마무리 골격을 함께 따라가고 있습니다")
    elif opening in dominant_openings and len(core_tokens) <= 1:
        add_reason(1, "실시간 VIEW에서 과하게 반복된 시작 리듬과 가깝습니다")

    if has_generic_stack and len(filler_tokens) >= 3 and len(core_tokens) <= 1:
        add_reason(1, "실시간 VIEW에서 흔한 명사 나열형 골격과도 겹칩니다")

    return score, reasons, profile


def get_title_rewrite_context(text: str, max_lines: int = 10) -> str:
    lines: list[str] = []
    title = get_title_line(text)

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped == title:
            continue
        lines.append(stripped)
        if len(lines) >= max_lines:
            break

    return " ".join(lines)


def should_prefer_few_shot_title_fallback(
    live_view_collection: LiveViewTitleCollectionResult | None,
) -> bool:
    if live_view_collection is None:
        return False

    if live_view_collection.status != LIVE_VIEW_COLLECTION_STATUS_SUCCESS:
        return True

    return live_view_collection.has_quality_issues


def get_title_generation_strategy(
    live_view_collection: LiveViewTitleCollectionResult | None,
) -> str:
    if should_prefer_few_shot_title_fallback(live_view_collection):
        return TITLE_STRATEGY_FEW_SHOT_FALLBACK

    return TITLE_STRATEGY_LIVE_VIEW


def get_few_shot_title_example_suffixes(keyword: str) -> list[str]:
    normalized = normalize_keyword(keyword)
    suffixes = list(get_exact_match_fallback_suffixes(keyword))

    if normalized == "입양조건":
        suffixes.extend(
            [
                "가정 환경부터 보는 현실 기준",
                "심사 전에 챙길 준비 포인트",
                "반려동물 기준으로 보는 체크 항목",
            ]
        )
    elif any(term in normalized for term in ("파양", "임시보호", "보호소")):
        suffixes.extend(
            [
                "신청 흐름과 준비 포인트",
                "공고 보기 전에 볼 현실 기준",
                "보호자 입장에서 보는 체크 포인트",
            ]
        )
    elif "분양가" in normalized:
        suffixes.extend(
            [
                "숨은 비용까지 보는 현실 기준",
                "예산 잡을 때 볼 건강 포인트",
                "초기비용과 분양 체크 포인트",
            ]
        )
    elif "분양" in normalized:
        suffixes.extend(
            [
                "초보자 기준으로 보는 현실 체크",
                "성격과 준비 먼저 보는 기준",
                "후회 줄이는 준비 포인트",
            ]
        )
    elif any(term in normalized for term in ("품종", "견종", "종류")):
        suffixes.extend(
            [
                "초보자 기준으로 보는 선택 포인트",
                "성격과 관리 난이도 비교 포인트",
                "생활 패턴에 맞는 선택 기준",
            ]
        )
    else:
        suffixes.extend(
            [
                "성격과 관리 먼저 볼 기준",
                "건강과 준비 포인트",
                "보호자 기준으로 보는 현실 정보",
            ]
        )

    return suffixes


def build_few_shot_title_examples(
    keyword: str,
    target_keyword: str,
    live_view_titles: list[str] | None = None,
    max_examples: int = 4,
) -> list[str]:
    pattern_keyword = (target_keyword or keyword).strip()
    if not pattern_keyword:
        return []

    examples: list[str] = []
    seen: set[str] = set()

    for raw_suffix in get_few_shot_title_example_suffixes(keyword):
        suffix = build_deduped_title_remainder(raw_suffix)
        if not suffix:
            continue

        candidate = re.sub(r"\s+", " ", f"{pattern_keyword} {suffix}").strip()
        normalized_candidate = normalize_title_match(candidate)
        if not normalized_candidate or normalized_candidate in seen:
            continue
        if live_view_titles and find_exact_live_view_title_match(
            candidate,
            live_view_titles,
        ):
            continue

        seen.add(normalized_candidate)
        examples.append(candidate)
        if len(examples) >= max_examples:
            break

    return examples


def build_title_rewrite_prompt(
    keyword: str,
    target_keyword: str,
    text: str,
    live_view_titles: list[str],
    pattern_reasons: list[str],
    prefer_few_shot_title_fallback: bool = False,
) -> str:
    current_title = get_title_line(text)
    rewrite_context = get_title_rewrite_context(text=text)
    strategy_live_view_titles = (
        [] if prefer_few_shot_title_fallback else live_view_titles
    )
    skeleton_hints = get_repetitive_title_skeleton_hints(
        keyword=target_keyword or keyword,
        live_view_titles=strategy_live_view_titles,
    )
    few_shot_title_examples = (
        build_few_shot_title_examples(
            keyword=keyword,
            target_keyword=target_keyword or keyword,
            live_view_titles=live_view_titles,
        )
        if prefer_few_shot_title_fallback
        else []
    )

    lines = [
        f"keyword: {keyword}",
        f"target_keyword: {target_keyword}",
        f"current_title: {current_title}",
        f"article_context: {rewrite_context}",
        "requirements:",
        "- return exactly one final title only",
        "- keep target_keyword exactly once",
        "- reduce sentence skeleton repetition and avoid stale pet-title templates",
        "- center the title on one concrete search-intent point from the article instead of piling up generic nouns",
        "- do not stack near-synonyms like 체크리스트 and 가이드 or 가격 and 비용 or 실제 and 현실 in one short title",
        "- no labels, no quotes, no markdown",
    ]
    if prefer_few_shot_title_fallback:
        lines.extend(
            [
                "- live VIEW title patterns are noisy for this keyword, so use the few-shot title examples first",
                "- use live VIEW titles only to avoid exact matches, not to compose the sentence skeleton",
            ]
        )
    else:
        lines.append("- use live Naver VIEW intent first, but never copy live title wording")

    if pattern_reasons:
        lines.append("reasons_to_avoid:")
        lines.extend(f"- {reason}" for reason in pattern_reasons)

    if skeleton_hints:
        lines.append("repetitive_skeletons_to_avoid:")
        lines.extend(f"- {hint}" for hint in skeleton_hints[:4])

    if few_shot_title_examples:
        lines.append("few_shot_title_examples:")
        lines.extend(f"- {title}" for title in few_shot_title_examples)

    if live_view_titles:
        lines.append(
            "live_view_titles_to_avoid_exact_match:"
            if prefer_few_shot_title_fallback
            else "live_view_titles:"
        )
        lines.extend(f"- {title}" for title in live_view_titles[:8])
    else:
        lines.append("fallback_hint:")
        lines.append(
            "- real-time VIEW titles are unavailable, so use the few-shot examples to land on one fresh information title"
        )

    return "\n".join(lines)


def get_rule_by_id(
    rules: list[dict[str, str]],
    rule_id: str,
) -> dict[str, str] | None:
    for rule in rules:
        if rule["id"] == rule_id:
            return rule

    return None


def pick_rule_by_ids(
    rules: list[dict[str, str]],
    candidate_ids: tuple[str, ...],
) -> dict[str, str]:
    candidates = [
        rule
        for candidate_id in candidate_ids
        if (rule := get_rule_by_id(rules, candidate_id)) is not None
    ]

    if not candidates:
        return random.choice(rules)

    return random.choice(candidates)


def should_use_comparison_support(
    keyword: str,
    live_view_titles: list[str],
) -> bool:
    if any(
        cue in title
        for title in live_view_titles
        for cue in COMPARISON_SUPPORT_TITLE_CUES
    ):
        return True

    normalized_keyword = normalize_keyword(keyword)
    return any(
        term in normalized_keyword for term in ("품종", "견종", "종류", "입양조건")
    )


def enforce_title_keyword_once(
    text: str,
    keyword: str,
    target_keyword: str = "",
) -> str:
    title = get_title_line(text)
    title_keyword = (target_keyword or keyword).strip()

    if not title or not title_keyword:
        return text

    normalized_title = re.sub(r"\s+", " ", title).strip()
    occurrence_count = count_keyword_occurrences(normalized_title, title_keyword)

    if occurrence_count == 1:
        return replace_title_line(text=text, title=normalized_title)

    pattern = build_keyword_pattern(title_keyword)
    if pattern is None:
        return text

    remainder = clean_title_remainder(pattern.sub(" ", normalized_title))
    if not remainder:
        remainder = "현실 정보"

    enforced_title = re.sub(r"\s+", " ", f"{title_keyword} {remainder}").strip()

    if count_keyword_occurrences(enforced_title, title_keyword) != 1:
        enforced_title = title_keyword

    return replace_title_line(text=text, title=enforced_title)


def get_exact_match_fallback_suffixes(keyword: str) -> list[str]:
    normalized = normalize_keyword(keyword)

    if normalized == "입양조건":
        return [
            "심사 기준과 준비 포인트",
            "반려동물 기준으로 보는 준비 체크",
            "집으로 데려오기 전 확인할 현실 기준",
        ]

    if any(term in normalized for term in ("파양", "임시보호", "보호소")):
        return [
            "절차와 준비 포인트",
            "공고 확인 전에 볼 현실 기준",
            "신청 흐름과 체크 포인트",
        ]

    if "분양가" in normalized:
        return [
            "가격보다 먼저 볼 숨은 비용",
            "비용과 건강 체크 포인트",
            "초기비용까지 보는 현실 기준",
        ]

    if "분양" in normalized:
        return [
            "현실 기준과 체크 포인트",
            "성격과 비용 먼저 보는 기준",
            "후회 줄이는 준비 포인트",
        ]

    if any(term in normalized for term in ("품종", "견종", "종류")):
        return [
            "선택 기준과 현실 포인트",
            "초보자 기준으로 보는 비교 포인트",
            "성격과 관리 난이도 정리",
        ]

    return [
        "성격과 현실 체크 포인트",
        "관리 전에 볼 핵심 기준",
        "보호자 기준으로 보는 현실 정보",
    ]


def apply_title_word_overuse_phrase_replacements(text: str) -> str:
    adjusted = text.strip()

    for pattern, replacement in TITLE_WORD_OVERUSE_PHRASE_REPLACEMENTS:
        adjusted = re.sub(pattern, replacement, adjusted)

    adjusted = re.sub(r"\s+", " ", adjusted).strip()
    return clean_title_remainder(adjusted)


def tokenize_title_terms_for_overuse(text: str) -> list[str]:
    protected = text
    for term in sorted(TITLE_WORD_OVERUSE_MULTI_WORD_TERMS, key=len, reverse=True):
        protected = protected.replace(term, term.replace(" ", "_"))

    protected = re.sub(r"[^0-9A-Za-z가-힣_ ]+", " ", protected)
    return [
        token.replace("_", " ").strip()
        for token in protected.split()
        if token.strip()
    ]


def get_title_word_overuse_family(term: str) -> str:
    return TITLE_WORD_OVERUSE_FAMILY_MAP.get(term, "")


def pick_preferred_title_word_overuse_term(
    family: str,
    terms: list[str],
) -> str:
    priority = TITLE_WORD_OVERUSE_FAMILY_PRIORITY.get(family, ())
    for preferred in priority:
        if preferred in terms:
            return preferred

    return terms[0]


def analyze_title_word_overuse(
    title: str,
    keyword: str,
) -> tuple[int, list[str], list[str]]:
    remainder = apply_title_word_overuse_phrase_replacements(
        extract_title_remainder(title=title, keyword=keyword)
    )
    terms = tokenize_title_terms_for_overuse(remainder)
    if not terms:
        return 0, [], []

    score = 0
    reasons: list[str] = []

    def add_reason(points: int, reason: str) -> None:
        nonlocal score
        if reason in reasons:
            return
        score += points
        reasons.append(reason)

    counted_terms = [
        term
        for term in terms
        if term and not re.fullmatch(r"\d+가지", term)
    ]
    duplicate_counter = Counter(counted_terms)
    repeated_terms = [
        term for term, count in duplicate_counter.items() if count >= 2
    ]
    if repeated_terms:
        add_reason(
            1,
            "같은 단어가 제목 안에서 반복됩니다: "
            + ", ".join(repeated_terms[:3]),
        )

    family_terms: dict[str, list[str]] = {}
    for term in counted_terms:
        family = get_title_word_overuse_family(term)
        if not family:
            continue
        family_terms.setdefault(family, []).append(term)

    if len(family_terms.get("guidance", [])) >= 2:
        add_reason(1, "안내형 표현이 겹칩니다")

    if len(family_terms.get("reality", [])) >= 2:
        add_reason(1, "실제와 현실 계열 표현이 겹칩니다")

    generic_cost_terms = family_terms.get("generic_cost", [])
    specific_cost_terms = family_terms.get("specific_cost", [])
    if len(generic_cost_terms) >= 2 or (
        generic_cost_terms and specific_cost_terms
    ):
        add_reason(1, "가격과 비용 계열 표현이 과하게 겹칩니다")

    if len(family_terms.get("trait", [])) >= 2:
        add_reason(1, "성격과 특징 계열 표현이 겹칩니다")

    if len(family_terms.get("caution", [])) >= 2:
        add_reason(1, "주의 계열 표현이 겹칩니다")

    return score, reasons, terms


def build_deduped_title_remainder(remainder: str) -> str:
    adjusted = apply_title_word_overuse_phrase_replacements(remainder)
    terms = tokenize_title_terms_for_overuse(adjusted)
    if not terms:
        return adjusted

    keep_indices = set(range(len(terms)))
    seen_terms: set[str] = set()

    for index, term in enumerate(terms):
        normalized = normalize_keyword(term)
        if not normalized or re.fullmatch(r"\d+가지", term):
            continue
        if normalized in seen_terms:
            keep_indices.discard(index)
            continue
        seen_terms.add(normalized)

    filtered_terms = [term for index, term in enumerate(terms) if index in keep_indices]
    keep_indices = set(range(len(filtered_terms)))

    family_indices: dict[str, list[int]] = {}
    for index, term in enumerate(filtered_terms):
        family = get_title_word_overuse_family(term)
        if not family:
            continue
        family_indices.setdefault(family, []).append(index)

    guidance_indices = family_indices.get("guidance", [])
    if len(guidance_indices) >= 2:
        guidance_terms = [filtered_terms[index] for index in guidance_indices]
        selected_term = pick_preferred_title_word_overuse_term(
            family="guidance",
            terms=guidance_terms,
        )
        selected_index = next(
            index for index in guidance_indices if filtered_terms[index] == selected_term
        )
        for index in guidance_indices:
            if index != selected_index:
                keep_indices.discard(index)

    reality_indices = family_indices.get("reality", [])
    if len(reality_indices) >= 2:
        reality_terms = [filtered_terms[index] for index in reality_indices]
        selected_term = pick_preferred_title_word_overuse_term(
            family="reality",
            terms=reality_terms,
        )
        selected_index = next(
            index for index in reality_indices if filtered_terms[index] == selected_term
        )
        for index in reality_indices:
            if index != selected_index:
                keep_indices.discard(index)

    generic_cost_indices = family_indices.get("generic_cost", [])
    specific_cost_indices = family_indices.get("specific_cost", [])
    if specific_cost_indices and generic_cost_indices:
        for index in generic_cost_indices:
            keep_indices.discard(index)
    elif len(generic_cost_indices) >= 2:
        for index in generic_cost_indices[1:]:
            keep_indices.discard(index)

    trait_indices = family_indices.get("trait", [])
    if len(trait_indices) >= 2:
        for index in trait_indices[1:]:
            keep_indices.discard(index)

    caution_indices = family_indices.get("caution", [])
    if len(caution_indices) >= 2:
        for index in caution_indices[1:]:
            keep_indices.discard(index)

    deduped_terms = [
        term for index, term in enumerate(filtered_terms) if index in keep_indices
    ]

    while deduped_terms and deduped_terms[0] in TITLE_WORD_OVERUSE_PREFIX_TOKENS:
        deduped_terms.pop(0)

    deduped_remainder = clean_title_remainder(" ".join(deduped_terms))
    return apply_title_word_overuse_phrase_replacements(deduped_remainder)


def get_title_word_overuse_fallback_titles(
    keyword: str,
    target_keyword: str,
    live_view_titles: list[str],
) -> list[str]:
    fallback_titles: list[str] = []
    seen: set[str] = set()

    for raw_suffix in get_exact_match_fallback_suffixes(keyword) + [
        "처음 준비할 때 볼 핵심 정보",
        "지금 알아둘 성향과 준비 포인트",
        "보호자 기준으로 먼저 볼 현실 정보",
    ]:
        suffix = build_deduped_title_remainder(raw_suffix)
        if not suffix:
            continue

        candidate = re.sub(r"\s+", " ", f"{target_keyword} {suffix}").strip()
        normalized_candidate = normalize_title_match(candidate)
        if not normalized_candidate or normalized_candidate in seen:
            continue
        if find_exact_live_view_title_match(candidate, live_view_titles):
            continue

        seen.add(normalized_candidate)
        fallback_titles.append(candidate)

    return fallback_titles


def reduce_title_word_overuse(
    text: str,
    keyword: str,
    target_keyword: str,
    live_view_titles: list[str],
) -> str:
    title = get_title_line(text)
    if not title:
        return text

    pattern_keyword = target_keyword or keyword
    raw_remainder = clean_title_remainder(
        extract_title_remainder(title=title, keyword=pattern_keyword)
    )
    deduped_remainder = build_deduped_title_remainder(raw_remainder)
    cleanup_changed = (
        normalize_title_match(deduped_remainder)
        != normalize_title_match(raw_remainder)
        if deduped_remainder
        else False
    )
    current_word_score, reasons, _ = analyze_title_word_overuse(
        title=title,
        keyword=pattern_keyword,
    )
    if current_word_score <= 0 and not cleanup_changed:
        return text

    current_pattern_score, _, _ = analyze_repetitive_title_pattern(
        title=title,
        keyword=pattern_keyword,
        live_view_titles=live_view_titles,
    )
    best_title = title
    best_rank = (
        current_word_score + (1 if cleanup_changed else 0),
        current_pattern_score,
    )
    seen: set[str] = {normalize_title_match(title)}

    if deduped_remainder:
        candidate = re.sub(r"\s+", " ", f"{pattern_keyword} {deduped_remainder}").strip()
        normalized_candidate = normalize_title_match(candidate)
        if normalized_candidate and normalized_candidate not in seen:
            seen.add(normalized_candidate)

            candidate_text = replace_title_line(text=text, title=candidate)
            candidate_text = enforce_title_keyword_once(
                text=candidate_text,
                keyword=keyword,
                target_keyword=pattern_keyword,
            )
            candidate_title = get_title_line(candidate_text)
            if (
                candidate_title
                and not find_exact_live_view_title_match(candidate_title, live_view_titles)
            ):
                candidate_word_score, _, _ = analyze_title_word_overuse(
                    title=candidate_title,
                    keyword=pattern_keyword,
                )
                candidate_pattern_score, _, _ = analyze_repetitive_title_pattern(
                    title=candidate_title,
                    keyword=pattern_keyword,
                    live_view_titles=live_view_titles,
                )
                candidate_rank = (candidate_word_score, candidate_pattern_score)
                if (
                    current_word_score <= 0
                    and cleanup_changed
                    and candidate_pattern_score > current_pattern_score + 1
                ):
                    candidate_rank = best_rank

                if candidate_rank < best_rank:
                    best_title = candidate_title
                    best_rank = candidate_rank

    if normalize_title_match(best_title) != normalize_title_match(title) and best_rank[0] == 0:
        log.info(
            f"[pet_v2] title word overuse fix"
            f" | before={title!r}"
            f" | after={best_title!r}"
            f" | before_word_score={current_word_score}"
            f" | after_word_score={best_rank[0]}"
            f" | before_pattern_score={current_pattern_score}"
            f" | after_pattern_score={best_rank[1]}"
            f" | reasons={' | '.join(reasons) if reasons else '중복 표현 축약'}"
        )
        return replace_title_line(text=text, title=best_title)

    if current_word_score <= 0:
        return text

    candidate_titles = get_title_word_overuse_fallback_titles(
        keyword=keyword,
        target_keyword=pattern_keyword,
        live_view_titles=live_view_titles,
    )
    for candidate in candidate_titles:
        normalized_candidate = normalize_title_match(candidate)
        if not normalized_candidate or normalized_candidate in seen:
            continue
        seen.add(normalized_candidate)

        candidate_text = replace_title_line(text=text, title=candidate)
        candidate_text = enforce_title_keyword_once(
            text=candidate_text,
            keyword=keyword,
            target_keyword=pattern_keyword,
        )
        candidate_title = get_title_line(candidate_text)
        if not candidate_title:
            continue
        if find_exact_live_view_title_match(candidate_title, live_view_titles):
            continue

        candidate_word_score, _, _ = analyze_title_word_overuse(
            title=candidate_title,
            keyword=pattern_keyword,
        )
        candidate_pattern_score, _, _ = analyze_repetitive_title_pattern(
            title=candidate_title,
            keyword=pattern_keyword,
            live_view_titles=live_view_titles,
        )
        candidate_rank = (candidate_word_score, candidate_pattern_score)

        if candidate_rank < best_rank:
            best_title = candidate_title
            best_rank = candidate_rank

    if normalize_title_match(best_title) == normalize_title_match(title):
        return text

    log.info(
        f"[pet_v2] title word overuse fix"
        f" | before={title!r}"
        f" | after={best_title!r}"
        f" | before_word_score={current_word_score}"
        f" | after_word_score={best_rank[0]}"
        f" | before_pattern_score={current_pattern_score}"
        f" | after_pattern_score={best_rank[1]}"
        f" | reasons={' | '.join(reasons) if reasons else '중복 표현 축약'}"
    )

    return replace_title_line(text=text, title=best_title)


def build_non_matching_title(
    title: str,
    keyword: str,
    target_keyword: str,
    live_view_titles: list[str],
) -> str:
    current_title = title.strip()
    current_suffix = current_title
    if current_title.startswith(target_keyword):
        current_suffix = current_title[len(target_keyword) :].strip()

    candidate_suffixes: list[str] = []
    candidate_suffixes.extend(get_exact_match_fallback_suffixes(keyword))
    candidate_suffixes.extend(
        [
            "지금 먼저 볼 현실 기준",
            "실제 준비 전에 볼 포인트",
            "보호자 입장에서 보는 핵심 정보",
        ]
    )
    if current_suffix:
        candidate_suffixes.extend(
            [
                f"{current_suffix} 준비 포인트",
                f"{current_suffix} 현실 기준",
                f"{current_suffix} 핵심 정보",
            ]
        )

    seen: set[str] = set()
    for raw_suffix in candidate_suffixes:
        suffix = build_deduped_title_remainder(raw_suffix)
        if not suffix:
            continue
        if suffix.startswith(target_keyword):
            suffix = build_deduped_title_remainder(suffix[len(target_keyword) :])
        candidate = re.sub(r"\s+", " ", f"{target_keyword} {suffix}").strip()
        normalized_candidate = normalize_title_match(candidate)
        if not normalized_candidate or normalized_candidate in seen:
            continue
        seen.add(normalized_candidate)
        if not find_exact_live_view_title_match(candidate, live_view_titles):
            return candidate

    base_candidate = f"{target_keyword} 실제 준비 전에 볼 기준".strip()
    if not find_exact_live_view_title_match(base_candidate, live_view_titles):
        return base_candidate

    suffix_index = 2
    while True:
        candidate = f"{base_candidate} {suffix_index}"
        if not find_exact_live_view_title_match(candidate, live_view_titles):
            return candidate
        suffix_index += 1


def build_best_effort_title(
    keyword: str,
    target_keyword: str,
    live_view_titles: list[str],
) -> str:
    pattern_keyword = (target_keyword or keyword).strip() or keyword.strip()
    if not pattern_keyword:
        return ""

    fallback_titles = get_title_word_overuse_fallback_titles(
        keyword=keyword or pattern_keyword,
        target_keyword=pattern_keyword,
        live_view_titles=live_view_titles,
    )
    if fallback_titles:
        return fallback_titles[0]

    return build_non_matching_title(
        title=pattern_keyword,
        keyword=keyword or pattern_keyword,
        target_keyword=pattern_keyword,
        live_view_titles=live_view_titles,
    )


def is_probable_body_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False

    if re.match(r"^\d+\.\s", stripped):
        return True

    return stripped.startswith(("안녕하세요", "오늘은", "이번에", "저는", "제가"))


def ends_like_body_sentence(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False

    return stripped.endswith(
        (
            "요",
            "해요",
            "에요",
            "예요",
            "답니다",
            "랍니다",
            "거든요",
            "인데요",
            "죠",
            "잖아요",
            "세요",
            "보세요",
            "더라고요",
            "같아요",
            "수 있어요",
        )
    )


def ensure_title_output_contract(
    text: str,
    keyword: str,
    target_keyword: str,
    live_view_titles: list[str],
) -> str:
    raw_lines = text.splitlines()
    title_keyword = (target_keyword or keyword).strip()
    fallback_title = build_best_effort_title(
        keyword=keyword,
        target_keyword=target_keyword,
        live_view_titles=live_view_titles,
    )

    if not raw_lines:
        return fallback_title

    first_non_empty_index = next(
        (index for index, line in enumerate(raw_lines) if line.strip()),
        None,
    )
    if first_non_empty_index is None:
        return fallback_title

    first_non_empty_line = raw_lines[first_non_empty_index].strip()
    should_insert_fallback_title = (
        bool(fallback_title)
        and (
            is_probable_body_line(first_non_empty_line)
            or (
                bool(title_keyword)
                and count_keyword_occurrences(first_non_empty_line, title_keyword) == 0
                and ends_like_body_sentence(first_non_empty_line)
            )
        )
    )

    title_line = fallback_title if should_insert_fallback_title else first_non_empty_line
    body_start_index = (
        first_non_empty_index if should_insert_fallback_title else first_non_empty_index + 1
    )
    normalized_title = normalize_title_match(title_line)

    body_lines: list[str] = []
    body_started = False
    for raw_line in raw_lines[body_start_index:]:
        stripped = raw_line.strip()

        if not stripped:
            if body_started and body_lines and body_lines[-1] != "":
                body_lines.append("")
            continue

        if not body_started and normalized_title:
            if normalize_title_match(stripped) == normalized_title:
                continue
            body_started = True
        elif not body_started:
            body_started = True

        body_lines.append(stripped)

    while body_lines and body_lines[-1] == "":
        body_lines.pop()

    if body_lines:
        return "\n".join([title_line, "", *body_lines]).strip()

    return title_line


def ensure_non_matching_live_view_title(
    text: str,
    keyword: str,
    target_keyword: str,
    live_view_titles: list[str],
) -> str:
    if not live_view_titles:
        return text

    title = get_title_line(text)
    matched_title = find_exact_live_view_title_match(title, live_view_titles)
    if not matched_title:
        return text

    revised_title = build_non_matching_title(
        title=title,
        keyword=keyword,
        target_keyword=target_keyword,
        live_view_titles=live_view_titles,
    )
    if not revised_title or normalize_title_match(revised_title) == normalize_title_match(
        title
    ):
        return text

    log.info(
        f"[pet_v2] exact live VIEW title fallback"
        f" | title={title!r}"
        f" | matched={matched_title!r}"
        f" | revised={revised_title!r}"
    )

    return replace_title_line(text=text, title=revised_title)


def rewrite_repetitive_title(
    text: str,
    keyword: str,
    target_keyword: str,
    live_view_titles: list[str],
    prefer_few_shot_title_fallback: bool = False,
) -> str:
    title = get_title_line(text)
    if not title:
        return text

    pattern_keyword = target_keyword or keyword
    current_score, reasons, current_profile = analyze_repetitive_title_pattern(
        title=title,
        keyword=pattern_keyword,
        live_view_titles=live_view_titles,
    )
    if current_score < 2:
        return text

    rewrite_prompt = build_title_rewrite_prompt(
        keyword=keyword,
        target_keyword=pattern_keyword,
        text=text,
        live_view_titles=live_view_titles,
        pattern_reasons=reasons,
        prefer_few_shot_title_fallback=prefer_few_shot_title_fallback,
    )

    try:
        revised_title_text = call_ai(
            model_name=MODEL_NAME,
            system_prompt=TITLE_PATTERN_REWRITE_SYSTEM_PROMPT,
            user_prompt=rewrite_prompt,
        )
    except Exception as e:
        log.error(f"[pet_v2] title rewrite error: {e}")
        return text

    revised_lines = [line.strip() for line in revised_title_text.splitlines() if line.strip()]
    if not revised_lines:
        return text

    revised_title = re.sub(r"\s+", " ", revised_lines[0]).strip()
    revised_text = replace_title_line(text=text, title=revised_title)
    revised_text = enforce_title_keyword_once(
        text=revised_text,
        keyword=keyword,
        target_keyword=pattern_keyword,
    )
    revised_title = get_title_line(revised_text)

    if normalize_title_match(revised_title) == normalize_title_match(title):
        return text

    if find_exact_live_view_title_match(revised_title, live_view_titles):
        return text

    revised_score, revised_reasons, revised_profile = analyze_repetitive_title_pattern(
        title=revised_title,
        keyword=pattern_keyword,
        live_view_titles=live_view_titles,
    )
    if revised_score > current_score:
        return text

    if revised_score == current_score and len(revised_profile["core_tokens"]) <= len(
        current_profile["core_tokens"]
    ):
        return text

    log.info(
        f"[pet_v2] title pattern rewrite"
        f" | before={title!r}"
        f" | after={revised_title!r}"
        f" | before_score={current_score}"
        f" | after_score={revised_score}"
        f" | reasons={' | '.join(reasons)}"
        + (
            f" | remaining={' | '.join(revised_reasons)}"
            if revised_reasons
            else ""
        )
    )

    return revised_text


def finalize_pet_v2_title(
    text: str,
    keyword: str,
    target_keyword: str,
    live_view_titles: list[str],
    prefer_few_shot_title_fallback: bool = False,
) -> str:
    finalized_text = ensure_title_output_contract(
        text=text,
        keyword=keyword,
        target_keyword=target_keyword,
        live_view_titles=live_view_titles,
    )
    finalized_text = enforce_title_keyword_once(
        text=finalized_text,
        keyword=keyword,
        target_keyword=target_keyword,
    )
    finalized_text = ensure_non_matching_live_view_title(
        text=finalized_text,
        keyword=keyword,
        target_keyword=target_keyword,
        live_view_titles=live_view_titles,
    )
    finalized_text = rewrite_repetitive_title(
        text=finalized_text,
        keyword=keyword,
        target_keyword=target_keyword,
        live_view_titles=live_view_titles,
        prefer_few_shot_title_fallback=prefer_few_shot_title_fallback,
    )
    finalized_text = ensure_non_matching_live_view_title(
        text=finalized_text,
        keyword=keyword,
        target_keyword=target_keyword,
        live_view_titles=live_view_titles,
    )
    finalized_text = reduce_title_word_overuse(
        text=finalized_text,
        keyword=keyword,
        target_keyword=target_keyword,
        live_view_titles=live_view_titles,
    )
    finalized_text = ensure_non_matching_live_view_title(
        text=finalized_text,
        keyword=keyword,
        target_keyword=target_keyword,
        live_view_titles=live_view_titles,
    )
    finalized_text = ensure_title_output_contract(
        text=finalized_text,
        keyword=keyword,
        target_keyword=target_keyword,
        live_view_titles=live_view_titles,
    )
    finalized_text = enforce_title_keyword_once(
        text=finalized_text,
        keyword=keyword,
        target_keyword=target_keyword,
    )
    return ensure_title_output_contract(
        text=finalized_text,
        keyword=keyword,
        target_keyword=target_keyword,
        live_view_titles=live_view_titles,
    )


def get_title_angle_rule(
    keyword: str = "",
    note: str = "",
) -> dict[str, str]:
    params = parse_note_params(note)
    requested_id = params.get("title_angle", "").strip().lower()

    if requested_id:
        requested_rule = get_rule_by_id(TITLE_ANGLE_RULES, requested_id)
        if requested_rule:
            return requested_rule

    normalized_keyword = normalize_keyword(keyword)

    if "분양가" in normalized_keyword:
        return pick_rule_by_ids(
            TITLE_ANGLE_RULES,
            ("price_summary", "hidden_cost", "health_warning"),
        )

    if any(term in normalized_keyword for term in ("파양", "임시보호", "보호소")):
        return pick_rule_by_ids(
            TITLE_ANGLE_RULES,
            ("basics_guide", "hidden_cost", "health_warning"),
        )

    if any(term in normalized_keyword for term in ("품종", "견종", "종류")):
        return pick_rule_by_ids(
            TITLE_ANGLE_RULES,
            ("basics_guide", "temperament_focus", "health_warning"),
        )

    return pick_rule_by_ids(TITLE_ANGLE_RULES, INFO_PRIMARY_TITLE_ANGLE_IDS)


def get_title_opening_rule(
    keyword: str = "",
    note: str = "",
    live_view_titles: list[str] | None = None,
) -> dict[str, str]:
    params = parse_note_params(note)
    requested_id = params.get("title_opening", "").strip().lower()

    if requested_id:
        requested_rule = get_rule_by_id(TITLE_OPENING_RULES, requested_id)
        if requested_rule:
            return requested_rule

    normalized_keyword = normalize_keyword(keyword)
    candidate_ids = INFO_PRIMARY_OPENING_IDS

    if "분양가" in normalized_keyword:
        candidate_ids = (
            "price_opening",
            "maintenance_opening",
            "fact_opening",
            "health_opening",
        )
    elif any(term in normalized_keyword for term in ("파양", "임시보호", "보호소", "입양조건")):
        candidate_ids = (
            "decision_opening",
            "imperative_opening",
            "fact_opening",
            "beginner_opening",
        )
    elif any(term in normalized_keyword for term in ("품종", "견종", "종류")):
        candidate_ids = (
            "fact_opening",
            "decision_opening",
            "beginner_opening",
            "health_opening",
        )

    if should_use_comparison_support(keyword, live_view_titles or []):
        candidate_ids = candidate_ids + COMPARISON_SUPPORT_OPENING_IDS

    return pick_rule_by_ids(TITLE_OPENING_RULES, candidate_ids)


def build_tag_block(tag: str, lines: list[str]) -> str:
    content_lines = [line.strip() for line in lines if line and line.strip()]
    if not content_lines:
        return ""

    joined = "\n".join(f"- {line}" for line in content_lines)
    return f"<{tag}>\n{joined}\n</{tag}>"


def build_keyword_intent_prompt(
    keyword: str,
    note: str = "",
    target_keyword: str = "",
    live_view_collection: LiveViewTitleCollectionResult | None = None,
) -> str:
    normalized = normalize_keyword(keyword)
    note_params = parse_note_params(note)
    resolved_target_keyword = target_keyword or resolve_target_keyword(
        keyword=keyword,
        note=note,
    )
    collection_result = live_view_collection or resolve_live_view_title_collection(
        keyword=resolved_target_keyword,
        note=note,
        note_params=note_params,
    )
    live_view_titles = list(collection_result.titles)
    title_generation_strategy = get_title_generation_strategy(collection_result)
    strategy_live_view_titles = (
        live_view_titles
        if title_generation_strategy == TITLE_STRATEGY_LIVE_VIEW
        else []
    )
    title_angle_rule = get_title_angle_rule(
        keyword=resolved_target_keyword,
        note=note,
    )
    title_opening_rule = get_title_opening_rule(
        keyword=resolved_target_keyword,
        note=note,
        live_view_titles=strategy_live_view_titles,
    )
    avoid_titles = split_avoid_titles(note_params.get("avoid_titles", ""))
    avoid_openings = split_avoid_openings(note_params.get("avoid_openings", ""))
    avoid_endings = split_avoid_openings(note_params.get("avoid_endings", ""))
    # avoid_endings에 포함된 ending rule은 후보에서 제외
    avoid_endings_lower = " ".join(avoid_endings).lower()
    filtered_ending_ids = tuple(
        r["id"]
        for r in TITLE_ENDING_RULES
        if not any(
            keyword in avoid_endings_lower
            for keyword in r["example"].split()[-2:]
        )
    )
    title_ending_rule = pick_rule_by_ids(
        TITLE_ENDING_RULES,
        filtered_ending_ids if filtered_ending_ids else TITLE_ENDING_IDS,
    )
    repetitive_skeleton_hints = get_repetitive_title_skeleton_hints(
        keyword=resolved_target_keyword,
        live_view_titles=strategy_live_view_titles,
    )
    few_shot_title_examples = (
        build_few_shot_title_examples(
            keyword=keyword,
            target_keyword=resolved_target_keyword,
            live_view_titles=live_view_titles,
        )
        if title_generation_strategy == TITLE_STRATEGY_FEW_SHOT_FALLBACK
        else []
    )
    task_goal_lines: list[str] = [
        "검색자가 가장 먼저 궁금해할 핵심 답을 도입 2~3문장 안에 먼저 말합니다.",
        "본문에는 검색 의도에 맞는 실용 정보와 체크리스트를 넣고, 단순 품종 소개로만 끝내지 않습니다.",
        f"이번 글의 실제 타깃 키워드는 {resolved_target_keyword}이며, 제목과 첫 문단은 이 표현을 기준으로 맞춥니다.",
    ]
    title_contract_lines: list[str] = [
        "제목에는 실제 네이버 VIEW에서 자주 보이는 고의도 표현을 섞습니다. 예: 비용, 절차, 체크리스트, 준비물, 주의사항, 성격, 특징, 털빠짐, 수명, 유전병",
        "제목 첫머리에는 원본 핵심 키워드를 그대로 두고, 다른 품종명이나 unrelated 키워드로 바꾸지 않습니다.",
        "제목에는 target_keyword를 정확히 1회만 넣고, 같은 키워드를 다시 반복하거나 변형해서 겹치지 않습니다.",
        "제목에는 체크리스트, 가이드, 필독, 총정리 같은 안내형 표현을 두 개 이상 겹치지 않습니다.",
        "가격, 비용, 분양가나 실제, 현실처럼 비슷한 의미의 단어를 짧은 제목 안에 연달아 쌓지 않습니다.",
        "제목의 기본 톤은 정보형이되, 실제 네이버 블로그에서 클릭하고 싶은 자연스러운 문장으로 씁니다. 기계적이거나 공식처럼 보이면 안 됩니다.",
        "비교형 리듬은 가격보다 성격부터처럼 판단 기준을 보조로 강조할 때만 제한적으로 사용하고, 제목 전체를 대결 구도처럼 만들지 않습니다.",
        "비용 성격 현실 체크리스트처럼 핵심어 4개를 기계적으로 나열한 제목만 반복하지 않습니다.",
        "네이버 VIEW 검색 의도에 맞는 표현을 참고하되, 제목 중심은 정보형으로 두고 질문형이나 비교형은 필요할 때만 보조로 섞습니다.",
        f"이번 제목 각도는 {title_angle_rule['label']}입니다.",
        title_angle_rule["rule"],
        f"이번 제목 각도 예시는 {title_angle_rule['example']}입니다.",
        f"이번 제목 시작 리듬은 {title_opening_rule['label']}입니다.",
        title_opening_rule["rule"],
        f"이번 제목 시작 리듬 예시는 {title_opening_rule['example']}입니다.",
        "제목을 시바견분양 전, 시바견분양 후 같은 같은 조사 리듬으로만 반복하지 않습니다.",
        "제목 마무리에 기준, 정리, 정보, 포인트, 현실 같은 단어를 매번 쓰지 않습니다. 매 글마다 완전히 다른 마무리 표현을 씁니다.",
        "성격과 관리 기준, 건강과 유전병 주의사항 같은 ~와 ~ 패턴 마무리를 반복하지 않습니다.",
        f"이번 제목 마무리 리듬은 {title_ending_rule['label']}입니다.",
        title_ending_rule["rule"],
        f"이번 제목 마무리 예시는 {title_ending_rule['example']}입니다.",
    ]
    body_contract_lines: list[str] = [
        "번호 소제목은 기본 5개로 구성하고, 절차와 체크리스트 축이 많은 주제만 6개까지 허용합니다. 7개 이상으로 쪼개지 않습니다.",
        "각 소제목은 5~8문장 분량으로 충분히 길게 씁니다.",
        "출력 전 공백 제외 글자 수가 1800자 이상인지 스스로 확인하고, 부족하면 일화와 수치, 실전 팁을 보강합니다.",
        "본문은 자연스러운 한국어만 사용하고, 일본어/영어 표현은 넣지 않습니다.",
    ]
    anti_pattern_lines: list[str] = []
    reference_lines: list[str] = []
    keyword_specific_lines: list[str] = []
    self_check_lines: list[str] = [
        "최종 출력은 완성된 원고만 반환합니다.",
        "제목 exact match, target_keyword 1회, 번호 소제목 5~6개, 공백 제외 1800자 이상인지 스스로 확인한 뒤 답합니다.",
    ]

    if repetitive_skeleton_hints:
        anti_pattern_lines.extend(
            [
                "실시간 VIEW와 기존 pet v2에서 자주 반복되던 제목 골격은 감점 대상으로 보고 우선 제외합니다: "
                + " / ".join(repetitive_skeleton_hints[:4]),
                "위 골격과 비슷한 제목 후보가 떠오르면 그대로 확정하지 말고, 검색자가 바로 궁금해할 한 포인트를 중심으로 새 문장으로 다시 씁니다.",
            ]
        )

    if title_generation_strategy == TITLE_STRATEGY_FEW_SHOT_FALLBACK:
        reference_lines.append("이번 제목 생성은 실시간 VIEW 기반 조합 대신 few-shot fallback 경로를 우선 사용합니다.")
        if collection_result.status != LIVE_VIEW_COLLECTION_STATUS_SUCCESS:
            reference_lines.append(
                "실시간 네이버 VIEW 제목 수집이 실패했으므로, 제목 골격은 few-shot 예시를 먼저 따릅니다."
            )
        else:
            quality_descriptions = describe_live_view_quality_issues(
                collection_result.quality_issues
            )
            reference_lines.append(
                "실시간 네이버 VIEW 제목 표본 품질이 애매하므로, 제목 골격은 few-shot 예시를 먼저 따릅니다."
            )
            if quality_descriptions:
                reference_lines.append(
                    "이번 실시간 VIEW 표본의 애매 신호는 다음과 같습니다: "
                    + " / ".join(quality_descriptions)
                )
        reference_lines.extend(
            [
                "실시간 VIEW 제목은 검색 의도 확인과 exact match 회피용으로만 참고하고, 제목 골격 조합의 기준으로 삼지 않습니다.",
                "few-shot 예시처럼 target_keyword는 1회만 두고, 한 가지 판단 포인트만 또렷한 정보형 제목 1개를 우선 만듭니다.",
            ]
        )
        if few_shot_title_examples:
            reference_lines.append(
                "few-shot 제목 예시는 다음 흐름만 참고합니다: "
                + " / ".join(few_shot_title_examples)
            )
    elif collection_result.has_titles:
        reference_lines.append(
            "실시간 네이버 VIEW 제목에 비교형 표현이 있더라도 그 리듬은 보조 참고만 하고, 최종 제목 중심은 정보형으로 유지합니다."
        )

    if normalized == "입양조건":
        keyword_specific_lines.extend(
            [
                "이 키워드는 사람 입양 법률 검색과 충돌하기 쉬우므로, 반드시 반려동물 입양조건이라는 맥락을 제목과 첫 문단에서 분명히 밝힙니다.",
                f"제목은 반드시 {resolved_target_keyword}으로 시작하고, 특정 품종명으로 좁히지 않습니다.",
                "입양 심사 항목, 주거 형태, 가족 동의, 산책 시간, 경제 여건, 알레르기 확인 같은 반려동물 입양 기준을 중심으로 씁니다.",
            ]
        )
    elif any(term in normalized for term in ("파양", "임시보호", "보호소")):
        keyword_specific_lines.extend(
            [
                "파양/임시보호/보호소 키워드는 감정 호소보다 절차, 준비물, 비용, 주의사항, 공식 확인 포인트가 먼저 나와야 합니다.",
                "반드시 한 섹션은 절차 또는 신청 흐름, 한 섹션은 준비물/조건, 한 섹션은 주의사항/피해야 할 선택으로 구성합니다.",
                "공식 센터와 민간 보호소의 차이나 확인 포인트를 설명하되, 검증되지 않은 주소나 전화번호는 지어내지 않습니다.",
                "지역 보호소 키워드라면 현재 공고와 운영 정보는 공식 공고판에서 수시로 변할 수 있다는 점을 자연스럽게 언급합니다.",
            ]
        )
    elif "분양가" in normalized:
        keyword_specific_lines.extend(
            [
                "분양가 키워드는 평균 가격 범위, 가격이 갈리는 이유, 초기 세팅비, 월 유지비, 건강검진/중성화/미용 같은 숨은 비용을 반드시 넣습니다.",
                "가격표만 나열하지 말고 캐터리/켄넬/분양처 확인 포인트와 건강 관련 체크리스트를 함께 설명합니다.",
            ]
        )
    elif "분양" in normalized:
        keyword_specific_lines.extend(
            [
                "분양 키워드는 성격/관리 난이도/분양가/건강 체크/첫 달 적응을 함께 다루는 현실형 구조로 씁니다.",
                "첫 분양 전에 확인할 체크리스트 섹션을 반드시 넣습니다.",
            ]
        )
    elif any(term in normalized for term in ("품종", "견종", "종류")):
        keyword_specific_lines.extend(
            [
                "품종/종류 키워드는 단순 백과사전식 나열보다 보호자 성향별 선택 기준, 크기/활동량/털빠짐/초보자 적합도 비교를 중심으로 씁니다.",
                "한 섹션은 이런 사람에게 맞아요, 다른 한 섹션은 이런 사람에겐 힘들어요 형태의 선택 가이드를 넣습니다.",
            ]
        )
    else:
        keyword_specific_lines.extend(
            [
                "품종 단일 키워드는 성격, 털빠짐, 운동량, 수명, 유전병, 키우기 난이도, 입양 전 현실 체크를 균형 있게 다룹니다.",
                "귀여움만 강조하지 말고 실제로 힘든 점과 잘 맞는 보호자 유형을 반드시 설명합니다.",
            ]
        )

    if any(term in normalized for term in ("아메리칸숏헤어", "아메리칸쇼트헤어")):
        keyword_specific_lines.extend(
            [
                "아메리칸숏헤어는 코리안숏헤어와 헷갈리는 검색 수요가 많으므로 차이점을 한 섹션으로 분리합니다.",
                "유전병, 체중 관리, 털빠짐, 초보 집사 적합도를 꼭 넣습니다.",
            ]
        )

    if "웰시코기" in normalized:
        keyword_specific_lines.extend(
            [
                "웰시코기는 털빠짐, 비만, 허리/디스크 부담, 운동량이 자주 같이 검색되므로 이 포인트를 빠뜨리지 않습니다.",
            ]
        )

    if "시바견" in normalized:
        keyword_specific_lines.extend(
            [
                "시바견은 분양가뿐 아니라 독립적인 성향, 털빠짐, 산책량, 초보자 난이도를 함께 다룹니다.",
            ]
        )

    if "광주동물보호소" in normalized:
        keyword_specific_lines.extend(
            [
                "광주동물보호소 키워드는 공식 센터 공고 확인, 입양 절차, 임시보호/봉사 여부, 민간 보호소와의 차이를 중심으로 씁니다.",
                "확인되지 않은 운영시간, 주소, 번호를 단정하지 말고 공식 공고판 확인 필요를 함께 적습니다.",
            ]
        )

    if avoid_titles:
        anti_pattern_lines.append(
            "아래 기존 제목들과 핵심 단어 조합, 문장 리듬, 마무리 표현이 겹치지 않게 완전히 다른 방향으로 씁니다: "
            + " / ".join(avoid_titles)
        )

    if live_view_titles:
        reference_lines.extend(
            [
                "실시간 네이버 VIEW 제목은 참고만 하고, 한 글자 차이 없는 동일 제목은 절대 쓰지 않습니다.",
                "실시간 VIEW 제목에서 검색 의도를 읽되, 단어 순서와 문장 마무리는 분명히 다르게 씁니다.",
                "아래 실시간 VIEW 제목과 완전히 같은 제목은 하드 실패입니다: "
                + " / ".join(live_view_titles[:10]),
            ]
        )

    if avoid_openings:
        anti_pattern_lines.append(
            "아래 제목 시작 리듬은 이번에 쓰지 않습니다: " + " / ".join(avoid_openings)
        )

    if avoid_endings:
        anti_pattern_lines.append(
            "아래 제목 마무리 표현과 같은 계열은 이번에 절대 쓰지 않습니다. "
            "비슷한 어미, 같은 뉘앙스, 살짝 바꾼 변형도 전부 금지입니다. "
            "완전히 다른 문장 구조와 어미로 마무리하세요: "
            + " / ".join(avoid_endings)
        )

    if note and not note_params:
        keyword_specific_lines.append(f"추가 사용자 메모를 반드시 반영합니다: {note}")

    blocks = [
        build_tag_block(
            "prompt_priority",
            [
                "우선순위는 title_contract > body_contract > anti_patterns > reference_signals > keyword_specific_rules 순서로 따릅니다.",
                "reference_signals는 검색 의도 파악용 참고 데이터이며, wording 복사는 금지입니다.",
            ],
        ),
        build_tag_block("task_goal", task_goal_lines),
        build_tag_block("title_contract", title_contract_lines),
        build_tag_block("body_contract", body_contract_lines),
        build_tag_block("keyword_specific_rules", keyword_specific_lines),
        build_tag_block("anti_patterns", anti_pattern_lines),
        build_tag_block("reference_signals", reference_lines),
        build_tag_block("self_check", self_check_lines),
    ]

    return "\n\n".join(block for block in blocks if block)


def get_required_signal_groups(keyword: str) -> list[tuple[str, tuple[str, ...]]]:
    normalized = normalize_keyword(keyword)

    if normalized == "입양조건":
        return [
            ("반려동물 문맥", ("강아지", "고양이", "유기견", "유기묘")),
            ("입양 기준", ("입양조건", "조건", "기준")),
            ("심사 또는 준비", ("가정방문", "산책", "가족", "알레르기", "경제")),
        ]

    if any(term in normalized for term in ("파양", "임시보호", "보호소")):
        return [
            ("절차 흐름", ("절차", "신청", "상담", "공고")),
            ("조건 또는 준비물", ("조건", "준비물", "서류", "환경")),
            ("주의사항", ("주의", "체크", "확인", "실수")),
        ]

    if "분양가" in normalized:
        return [
            ("가격 정보", ("분양가", "가격", "비용")),
            ("숨은 비용", ("초기", "유지비", "검진", "중성화", "미용")),
            ("확인 포인트", ("체크", "확인", "부모견", "건강", "혈통")),
        ]

    if "분양" in normalized:
        return [
            ("분양 또는 입양 현실", ("분양", "입양", "현실")),
            ("성격 또는 난이도", ("성격", "난이도", "고집", "적응")),
            ("체크리스트", ("체크", "확인", "주의")),
        ]

    if any(term in normalized for term in ("품종", "견종", "종류")):
        return [
            ("선택 기준", ("맞아요", "힘들어요", "추천", "비교")),
            ("기본 정보", ("크기", "활동량", "털빠짐", "성격")),
        ]

    return [
        ("기본 특징", ("성격", "특징")),
        ("관리 정보", ("털빠짐", "관리", "운동량", "수명")),
        ("건강 또는 주의점", ("건강", "유전병", "주의")),
    ]


def find_quality_issues(
    keyword: str,
    text: str,
    target_keyword: str = "",
    live_view_titles: list[str] | None = None,
) -> list[str]:
    issues: list[str] = []
    char_count = count_chars_without_spaces(text)
    subtitle_count = count_numbered_subtitles(text)
    normalized_keyword = normalize_keyword(keyword)
    normalized_target = normalize_keyword(target_keyword or keyword)
    title_line = get_title_line(text)
    normalized_title = normalize_keyword(title_line)
    normalized_intro = normalize_keyword(get_intro_text(text))
    title_keyword = target_keyword or keyword
    title_keyword_count = count_keyword_occurrences(title_line, title_keyword)

    if char_count < 1700:
        issues.append(f"공백 제외 글자 수가 {char_count}자로 부족합니다")

    if subtitle_count < 5 or subtitle_count > 6:
        issues.append(
            f"번호 소제목 개수가 {subtitle_count}개입니다. 기본 5개, 많아도 6개로 맞춰야 합니다"
        )

    if title_keyword_count != 1:
        issues.append(
            f"제목에 {title_keyword}이 {title_keyword_count}회 포함되어 있습니다. 정확히 1회만 포함해야 합니다"
        )

    if normalized_keyword == "입양조건":
        if not normalized_title.startswith(normalized_target):
            issues.append(f"제목이 {target_keyword}으로 바로 시작하지 않습니다")
        if normalized_target not in normalized_intro:
            issues.append(f"도입부에 {target_keyword} 맥락이 분명하지 않습니다")
    elif normalized_target not in normalized_title:
        issues.append("제목에 원본 핵심 키워드가 그대로 유지되지 않았습니다")

    if '"' in text or "'" in text:
        issues.append("따옴표가 남아 있습니다")

    if re.search(r"[ぁ-ゟ゠-ヿ]", text):
        issues.append("일본어 문자가 섞여 있습니다")

    matched_live_view_title = find_exact_live_view_title_match(
        title=title_line,
        live_view_titles=live_view_titles or [],
    )
    if matched_live_view_title:
        issues.append(
            f"제목이 실시간 네이버 VIEW 제목과 완전 동일합니다: {matched_live_view_title}"
        )

    for label, tokens in get_required_signal_groups(keyword):
        if not any(token in text for token in tokens):
            issues.append(f"{label} 관련 정보가 부족합니다")

    return issues


def clean_generated_text(text: str) -> str:
    text = comprehensive_text_clean(text)
    text = remove_markdown(text)
    text = text.replace('"', "")
    text = apply_simple_line_break(text)
    return text


def build_revision_prompt(
    keyword: str,
    target_keyword: str,
    pen_name: str,
    intent_prompt: str,
    draft: str,
    issues: list[str],
    live_view_titles: list[str] | None = None,
) -> str:
    issue_block = build_tag_block("issues_to_fix", issues)
    live_view_block = build_tag_block(
        "live_view_titles_to_avoid_exact_match",
        live_view_titles[:10] if live_view_titles else [],
    )
    revision_contract = build_tag_block(
        "revision_contract",
        [
            "현재 초안을 버리고 처음부터 다시 써도 됩니다.",
            "핵심 키워드와 의도는 유지하되 더 길고 더 깊게 작성합니다.",
            "제목 첫머리에는 target_keyword를 그대로 두고, 다른 품종명이나 유사어로 바꾸지 않습니다.",
            "제목에는 target_keyword를 정확히 1회만 넣고, 같은 키워드를 두 번 반복하지 않습니다.",
            "제목에는 체크리스트, 가이드, 필독, 총정리 같은 안내형 표현을 여러 개 겹치지 않습니다.",
            "제목에는 가격, 비용, 분양가나 실제, 현실처럼 비슷한 말만 연달아 쌓지 않습니다.",
            "번호 소제목은 기본 5개로 쓰고, 정보 축이 정말 많을 때만 6개까지 허용합니다.",
            "공백 제외 1800자 이상으로 맞춥니다.",
            "검색자가 바로 궁금해할 비용, 절차, 체크리스트, 주의사항 중 필요한 요소를 더 분명하게 넣습니다.",
            "실시간 네이버 VIEW 제목과 완전히 같은 제목은 하드 실패이므로, 첫 줄 제목은 반드시 다른 문장으로 다시 만듭니다.",
            "따옴표는 절대 쓰지 마세요.",
            "일본어/영어 섞인 표현 없이 자연스러운 한국어만 사용하세요.",
            "메타 설명 없이 완성된 원고만 출력하세요.",
        ],
    )

    blocks = [
        f"<task_context>\n<keyword>{keyword}</keyword>\n<target_keyword>{target_keyword}</target_keyword>\n<pen_name>{pen_name}</pen_name>\n</task_context>",
        intent_prompt,
        live_view_block,
        f"<current_draft>\n{draft}\n</current_draft>",
        issue_block,
        revision_contract,
    ]

    return "\n\n".join(block for block in blocks if block)


SYSTEM_PROMPT = """You are an experienced Korean pet blogger (10+ years).
You write Naver-style blog posts about pet breeds, adoption, and care.
Write as a real pet owner sharing firsthand experience with warm, practical advice.

=== OUTPUT FORMAT (CRITICAL - MUST FOLLOW EXACTLY) ===

1. First line = title only (plain text, no labels)
2. Blank line
3. Body starts immediately (greeting first)
4. Subtitles ALWAYS use numbering like 1. 2. 3. 4. 5.
5. Use 5 numbered subtitles by default. Only use 6 when the topic genuinely needs one more process/checklist section. Never exceed 6.

ABSOLUTE PROHIBITIONS:
- NO markdown syntax: no #, *, **, -, >, _, ~~, ```, [] or any markup
- NO labels: never write "제목:", "본문:", "서론:", "결론:", "부제목:" etc.
- NO template phrases: "사진 설명을 입력하세요", "AI 활용 설정" etc.
- NO character count feedback or writing method explanations
- NO listing subtitles separately at the beginning or end
- NO quotation marks: no " or '

=== WRITING STYLE ===

Sentence endings (USE these, mix diversely):
- ~요, ~해요, ~에요 (base)
- ~답니다, ~랍니다 (conveying facts)
- ~거든요, ~인데요 (elaboration)
- ~죠, ~잖아요 (building empathy)
- ~세요, ~보세요 (gentle advice)
- ~더라고요, ~하는 편이에요 (experience sharing)
- ~인 것 같아요, ~할 수 있거든요 (soft hedging)

Sentence endings (AVOID):
- ~다, ~한다 (stiff literary style)
- ~습니다, ~입니다 (too formal)
- ~임, ~함 (noun-ending)

Tone:
- Like a warm, experienced neighbor sharing pet advice
- Weave in first-person experiences naturally
- Address reader as "보호자님" or "집사님"
- Honest and realistic, no exaggeration
- Include occasional natural exclamations: "아 진짜 이건 미리 알았으면 좋았을 텐데", "이건 꼭 알아두세요"

=== SENTENCE RHYTHM (CRITICAL) ===

Mix sentence lengths deliberately:
- Most sentences: 40-70 characters, flowing across 2-3 lines
- Insert SHORT punchy sentences (10-25 chars) every 3-4 sentences for rhythm:
  "근데 이게 끝이 아니에요." / "진짜 중요해요." / "이건 꼭 기억해두세요."
- NEVER make all sentences the same uniform length
- Use conjunctions: ~인데, ~이라, ~하면, ~해서, ~지만, ~고

BAD (uniform robot-like sentences):
말티즈는 사람을 좋아하는 견종이에요.
분리불안이 생길 수 있어요.
성격이 활발한 편이에요.

GOOD (natural rhythm with length variation):
말티즈는 사람을 정말 좋아하는 견종인데,
그래서 혼자 남겨지는 걸 굉장히
힘들어하는 편이에요.
이게 진짜 중요한 부분이거든요.
저희 호두도 제가 출근하면 현관 앞에서
한 시간 넘게 낑낑거렸는데, 이웃분이
걱정하셔서 연락 오신 적도 있었어요.

Paragraphs:
- 3-6 sentences per paragraph
- Blank line between paragraphs
- Line break at 30-35 characters for mobile readability

=== ARTICLE STRUCTURE ===

(1) Greeting + Introduction (3-5 sentences)
- "안녕하세요 [pen_name]입니다." with a SPECIFIC persona detail:
  e.g., "[breed]를 키운 지 벌써 N년 차인 [pen_name]입니다"
  or "[breed] 두 마리와 함께 사는 [pen_name]입니다"
- Empathy hook: question or relatable situation
- State what this post covers

(2) Body sections (5 numbered subtitles by default, 6 only when clearly needed)
- Each section: 200-400 characters (5-8 sentences)
- Subtitle format: "N. [section title]" (plain numbered text)
- EACH section MUST include:
  a) Factual information with specific number ranges
  b) At least 1 concrete personal anecdote (with pet name, age, specific situation)
  c) 1-2 practical tips
- Subtitle styles should VARY: mix statement type, question type, and episode type
  e.g., "3. 비용은 생각보다 많이 들어요" / "4. 첫 미용 날, 진짜 당황했던 이야기" / "5. 슬개골 탈구, 얼마나 주의해야 할까요"

(3) Closing (3-5 sentences)
- Summary or encouragement
- Warm farewell (VARY the closing pattern each time, don't repeat same template)

=== PERSONA DEPTH (CRITICAL) ===

Your persona must feel REAL, not template-based:
- Give your pet a name and reference it naturally throughout the article
- Include SPECIFIC episodes: "우리 [pet name]이가 8개월 됐을 때 갑자기 뒷다리를 절어서 새벽에 응급실 갔는데..."
- Include failures/mistakes: "처음에 XX를 했다가 큰일 날 뻔했어요"
- Mention specific timeframes: "3년 전에", "처음 데려온 날", "지난 겨울에"
- These anecdotes should be DIFFERENT for every article, never repeat patterns

=== CONTENT RULES ===

- Main keyword: appear 3-5 times naturally in body (NEVER exceed 5)
- Always include SPECIFIC numerical ranges:
  - Pricing: "50~150만 원 선", not "수십만 원"
  - Weight: "2.5~4kg", not "작은 편"
  - Cost: "미용비 회당 5~8만 원", "월 유지비 15~25만 원 정도"
  - Health: "슬개골 수술비 한쪽 100~200만 원 선"
- Balance pros AND cons equally (don't just list positives)
- Use hedging: "개체마다 차이가 있어요", "환경에 따라 달라질 수 있어요"
- No exaggeration: avoid "최고의", "완벽한", "무조건", "절대"
- No specific business names (if needed, use "도그마루" only)

=== TITLE RULES ===

- 15-30 characters, keyword-based, no special characters, no markdown
- Include main keyword exactly once + concrete sub-info
- When relevant, use high-intent modifiers common in Naver VIEW: 현실, 비용, 절차, 체크리스트, 준비물, 주의사항, 성격, 특징, 털빠짐, 수명, 유전병
- Never repeat the main keyword twice in the title or stack it again inside a follow-up phrase

Title patterns:
- Info type: "말티즈분양 비용 성격 건강관리 총정리"
- Must-read type: "비숑프리제 분양 전 꼭 알아야 할 현실"
- Question type: "렉돌 성격 정말 순할까 3년 키운 후기"

=== LENGTH (CRITICAL - MUST MEET) ===

- MINIMUM: 1,700 characters excluding spaces
- TARGET: 1,800-2,500 characters excluding spaces
- This means 5 body sections in most cases, or 6 for process-heavy topics
- If your output is shorter than 1,700 chars, it is FAILING the requirement
- Do NOT pad with filler. Add depth: more anecdotes, more specific data, more practical tips
- Before finalizing, silently verify the article is over 1,800 characters excluding spaces. If shorter, expand depth before answering.

=== ANTI-TEMPLATE RULES ===

Every article must feel unique. NEVER repeat these patterns:
- Same opening template: "안녕하세요 X입니다. 오늘은 ~ 솔직하게 ~해보려 해요"
- Same closing template: "궁금한 점은 댓글로 ~ [name]이었습니다"
- Same section ordering: always starting with "성격" then "비용" etc.
- Same transition phrases between sections

Instead, VARY:
- Opening: sometimes start with an episode, sometimes with a question, sometimes with a surprising fact
- Closing: sometimes end with a checklist, sometimes with future plans, sometimes with a warm message
- Section order: shuffle based on what's most interesting about this specific breed/topic

4. 수명과 건강 주의점

평균 수명은 10~12년 정도로 알려져 있는데,
대형견치고는 비교적 건강한 편이지만
고관절 이형성증이나 슬개골 문제 등
관절 질환에 대한 주의가 필요해요.
이건 진짜 중요한 부분이에요.
저희 루비도 5살 때 고관절 쪽으로
통증이 와서 정기 검진 받다가 초기에
발견했거든요. 만약 그때 안 갔으면
수술까지 갈 수도 있었다고 하더라고요.
건강검진 비용은 기본형 7~12만 원,
확장형은 30만 원 이상 나올 수 있는데
1년에 한 번은 꼭 챙기시는 걸 추천드려요.

5. 분양가 현실과 숨은 비용

골든리트리버 분양가는 혈통과 외모에 따라
50~150만 원 선으로 형성되어 있어요.
근데 이게 끝이 아니거든요.
초기 세팅 비용으로 케이지, 방석, 식기,
리드줄 등 사면 20~40만 원은 기본이고,
첫 달 예방접종과 구충까지 합하면
총 70~100만 원 정도는 잡으셔야 해요.
월 유지비도 사료 5~8만 원, 간식 2~3만 원,
정기 검진까지 하면 15~25만 원은
꾸준히 나간답니다.

6. 우리 루비가 적응하기까지

처음 집에 데려왔을 때 루비는 구석에만
숨어있었어요. 밥도 이틀이나 안 먹어서
정말 걱정이 많았거든요.
그런데 사흘째 되니까 슬슬 나오더니
일주일 만에 소파까지 올라오더라고요.
조급하지 않게 기다려주시는 게 가장 중요해요.
저도 처음에 너무 만지려고 했다가
오히려 역효과가 나서, 그 뒤로는
루비가 먼저 다가올 때까지
기다리는 방식으로 바꿨어요.

7. 골든리트리버와 살면서 좋은 점과 힘든 점

솔직하게 말하면 좋은 점이 훨씬 많아요.
사람을 너무 좋아해서 퇴근하면
온 집안이 난리가 나고,
같이 산책 나가면 동네 인기스타가
되거든요.
근데 털 빠짐은 각오하셔야 해요.
진짜 많이 빠져요.
환절기엔 옷에 털이 안 묻는 날이 없어서,
로봇 청소기가 필수품이 됐답니다.
그리고 대형견이라 산책량도 하루
최소 40분~1시간은 꼭 필요하고,
힘도 세서 리드줄 교육을
확실히 해두셔야 해요.

지금까지 골든리트리버에 대해
현실적인 부분들을 다뤄봤는데요,
솔직히 단점도 있지만 함께할수록
정이 많이 드는 아이라서
한 번 키우면 절대 후회 없으실 거예요.
루비 덕분에 제 일상이 완전히 바뀌었거든요.
보호자님들도 좋은 인연 만나시길 바라요.
"""

USER_PROMPT = """<task_context>
<keyword>{keyword}</keyword>
<target_keyword>{target_keyword}</target_keyword>
<pen_name>{pen_name}</pen_name>
</task_context>

{intent_prompt}

<output_contract>
- 완성된 원고만 출력합니다.
- 첫 줄은 제목만 씁니다.
- 불필요한 설명, 메타 문장, 라벨은 쓰지 않습니다.
</output_contract>"""


def blog_filler_pet_v2_gen(
    user_instructions: str, ref: str = "", category: str = ""
) -> str:
    """반려동물 블로그 글밥 V2 생성"""

    parsed = parse_query(user_instructions)
    keyword = parsed.get("keyword", "")
    note = parsed.get("note", "") or ""

    if not keyword:
        raise ValueError("키워드가 없습니다.")

    pen_name = random.choice(PEN_NAMES)
    target_keyword = resolve_target_keyword(keyword=keyword, note=note)
    note_params = parse_note_params(note)
    live_view_collection = resolve_live_view_title_collection(
        keyword=target_keyword,
        note=note,
        note_params=note_params,
    )
    title_generation_strategy = get_title_generation_strategy(live_view_collection)
    prefer_few_shot_title_fallback = (
        title_generation_strategy == TITLE_STRATEGY_FEW_SHOT_FALLBACK
    )
    live_view_titles = list(live_view_collection.titles)

    intent_prompt = build_keyword_intent_prompt(
        keyword=keyword,
        note=note,
        target_keyword=target_keyword,
        live_view_collection=live_view_collection,
    )

    system = SYSTEM_PROMPT
    user = USER_PROMPT.format(
        keyword=keyword,
        target_keyword=target_keyword,
        pen_name=pen_name,
        intent_prompt=intent_prompt,
    )

    log.info(
        f"[pet_v2] sys={len(system)} user={len(user)} pen={pen_name}"
        f" | keyword={normalize_keyword(keyword)}"
        f" | target={normalize_keyword(target_keyword)}"
        f" | title_strategy={title_generation_strategy}"
    )

    try:
        text = call_ai(
            model_name=MODEL_NAME,
            system_prompt=system,
            user_prompt=user,
        )
    except Exception as e:
        log.error(f"[pet_v2] call_ai error: {e}")
        raise

    log.info(
        f"[pet_v2] response len={len(text)}"
        + (f" | {text[:50]!r}..." if len(text) < 100 else "")
    )

    text = clean_generated_text(text)
    text = finalize_pet_v2_title(
        text=text,
        keyword=keyword,
        target_keyword=target_keyword,
        live_view_titles=live_view_titles,
        prefer_few_shot_title_fallback=prefer_few_shot_title_fallback,
    )
    issues = find_quality_issues(
        keyword=keyword,
        text=text,
        target_keyword=target_keyword,
        live_view_titles=live_view_titles,
    )

    feedback_round = 0
    while issues and feedback_round < MAX_FEEDBACK_ROUNDS:
        feedback_round += 1
        log.info(
            f"[pet_v2] feedback round={feedback_round}"
            f" | issues={' | '.join(issues)}"
        )

        revision_user = build_revision_prompt(
            keyword=keyword,
            target_keyword=target_keyword,
            pen_name=pen_name,
            intent_prompt=intent_prompt,
            draft=text,
            issues=issues,
            live_view_titles=live_view_titles,
        )

        revised_text = call_ai(
            model_name=MODEL_NAME,
            system_prompt=system,
            user_prompt=revision_user,
        )
        text = clean_generated_text(revised_text)
        text = finalize_pet_v2_title(
            text=text,
            keyword=keyword,
            target_keyword=target_keyword,
            live_view_titles=live_view_titles,
            prefer_few_shot_title_fallback=prefer_few_shot_title_fallback,
        )
        issues = find_quality_issues(
            keyword=keyword,
            text=text,
            target_keyword=target_keyword,
            live_view_titles=live_view_titles,
        )

    text = finalize_pet_v2_title(
        text=text,
        keyword=keyword,
        target_keyword=target_keyword,
        live_view_titles=live_view_titles,
        prefer_few_shot_title_fallback=prefer_few_shot_title_fallback,
    )

    remaining_issues = find_quality_issues(
        keyword=keyword,
        text=text,
        target_keyword=target_keyword,
        live_view_titles=live_view_titles,
    )
    if remaining_issues:
        log.info(f"[pet_v2] remaining issues={' | '.join(remaining_issues)}")

    return text

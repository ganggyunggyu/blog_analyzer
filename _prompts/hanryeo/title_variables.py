"""한려담원 제목 변수 모음.

2026-04-07 네이버 뷰탭 블로그 제목 182개를 바탕으로 정리한
흑염소/수족냉증/소음인/임산부 계열 제목 패턴 변수 모듈.
"""

from __future__ import annotations

from dataclasses import dataclass
import random


@dataclass(frozen=True)
class TitleVariable:
    text: str
    tags: frozenset[str]


HOOK_VARIABLES: tuple[TitleVariable, ...] = (
    TitleVariable("키워드 뒤에 원인부터 바로 짚는 시작", frozenset({"symptom", "general"})),
    TitleVariable("키워드 뒤에 증상부터 꺼내는 시작", frozenset({"symptom", "general"})),
    TitleVariable("키워드 뒤에 이유를 묻는 질문형 시작", frozenset({"general"})),
    TitleVariable("키워드 뒤에 꼭 먹어야 할까를 붙이는 시작", frozenset({"nutrition", "pregnancy"})),
    TitleVariable("키워드 뒤에 언제부터 챙길까를 붙이는 시작", frozenset({"nutrition", "pregnancy"})),
    TitleVariable("키워드 뒤에 정상 범위부터 확인하는 시작", frozenset({"symptom", "pregnancy"})),
    TitleVariable("키워드 뒤에 위험 신호를 먼저 꺼내는 시작", frozenset({"symptom", "pregnancy"})),
    TitleVariable("키워드 뒤에 그냥 체질 문제는 아니라는 반전 시작", frozenset({"symptom", "constitution"})),
    TitleVariable("키워드 뒤에 혈액순환 문제만은 아니라는 반전 시작", frozenset({"symptom"})),
    TitleVariable("키워드 뒤에 병원 가야 하나를 붙이는 시작", frozenset({"symptom", "pregnancy"})),
    TitleVariable("키워드 뒤에 복용 시기부터 여는 시작", frozenset({"nutrition", "pregnancy"})),
    TitleVariable("키워드 뒤에 권장량부터 여는 시작", frozenset({"nutrition", "pregnancy"})),
    TitleVariable("키워드 뒤에 대상을 먼저 고정하는 시작", frozenset({"constitution", "pregnancy", "gift"})),
    TitleVariable("키워드 뒤에 체질별 차이를 예고하는 시작", frozenset({"constitution", "nutrition"})),
    TitleVariable("키워드 뒤에 좋은 음식과 피해야 할 음식을 예고하는 시작", frozenset({"constitution", "food", "symptom"})),
    TitleVariable("키워드 뒤에 대처법을 바로 약속하는 시작", frozenset({"symptom", "pregnancy"})),
    TitleVariable("키워드 뒤에 선택 기준을 먼저 거는 시작", frozenset({"nutrition", "gift", "food"})),
    TitleVariable("키워드 뒤에 실수 포인트를 먼저 꺼내는 시작", frozenset({"nutrition", "pregnancy", "symptom"})),
    TitleVariable("키워드 뒤에 현실 경험담으로 여는 시작", frozenset({"nutrition", "pregnancy", "symptom", "gift"})),
    TitleVariable("키워드 뒤에 선물 이유를 먼저 꺼내는 시작", frozenset({"gift", "pregnancy"})),
)

ANGLE_VARIABLES: tuple[TitleVariable, ...] = (
    TitleVariable("원인과 증상을 한 줄에 묶는 각도", frozenset({"symptom"})),
    TitleVariable("원인과 대처법을 묶는 각도", frozenset({"symptom"})),
    TitleVariable("증상과 치료를 같이 붙이는 각도", frozenset({"symptom"})),
    TitleVariable("좋은 음식과 피해야 할 음식을 대비하는 각도", frozenset({"constitution", "food", "symptom"})),
    TitleVariable("체질 특징과 좋은 음식을 묶는 각도", frozenset({"constitution", "food"})),
    TitleVariable("체질 특징과 피해야 할 음식을 묶는 각도", frozenset({"constitution", "food"})),
    TitleVariable("체질과 운동을 묶는 각도", frozenset({"constitution"})),
    TitleVariable("체질과 흑염소나 홍삼 같은 보양 포인트를 묶는 각도", frozenset({"constitution", "nutrition"})),
    TitleVariable("임신 초기 중기 후기처럼 시기별 구간을 나누는 각도", frozenset({"pregnancy"})),
    TitleVariable("복용 시기와 권장량을 함께 잡는 각도", frozenset({"nutrition", "pregnancy"})),
    TitleVariable("권장량과 수치 기준을 함께 잡는 각도", frozenset({"nutrition", "pregnancy", "symptom"})),
    TitleVariable("효능과 부작용을 같이 보여주는 각도", frozenset({"nutrition"})),
    TitleVariable("추천 이유와 선택 기준을 같이 잡는 각도", frozenset({"nutrition", "gift", "food"})),
    TitleVariable("후기와 실제 체감 포인트를 붙이는 각도", frozenset({"nutrition", "pregnancy", "gift"})),
    TitleVariable("정상 범위와 위험 신호를 같이 붙이는 각도", frozenset({"symptom", "pregnancy"})),
    TitleVariable("병원 가야 할 기준과 자가 관리 팁을 묶는 각도", frozenset({"symptom", "pregnancy"})),
    TitleVariable("손발 차가움과 저림을 같이 엮는 각도", frozenset({"symptom"})),
    TitleVariable("음식과 영양제를 같이 엮는 각도", frozenset({"symptom", "pregnancy", "nutrition", "food"})),
    TitleVariable("생활 루틴과 음식 습관을 같이 엮는 각도", frozenset({"symptom", "pregnancy", "constitution"})),
    TitleVariable("남자 여자 임산부 산후처럼 대상을 좁히는 각도", frozenset({"constitution", "pregnancy"})),
    TitleVariable("오해와 진실을 대비하는 각도", frozenset({"general"})),
    TitleVariable("비교어 없이 차이와 기준으로 푸는 각도", frozenset({"general"})),
    TitleVariable("선물과 실용 포인트를 같이 보여주는 각도", frozenset({"gift", "pregnancy"})),
    TitleVariable("복용 순서와 조합을 같이 보여주는 각도", frozenset({"nutrition", "pregnancy"})),
)

CLOSING_VARIABLES: tuple[TitleVariable, ...] = (
    TitleVariable("그냥 넘기면 안 된다는 마무리", frozenset({"symptom", "pregnancy"})),
    TitleVariable("먼저 체크해보자는 마무리", frozenset({"general"})),
    TitleVariable("이럴 때 확인하자는 마무리", frozenset({"symptom", "pregnancy"})),
    TitleVariable("헷갈릴 때 보는 기준으로 닫는 마무리", frozenset({"general"})),
    TitleVariable("언제부터 챙기면 좋을지로 닫는 마무리", frozenset({"nutrition", "pregnancy"})),
    TitleVariable("먹어도 될까로 닫는 마무리", frozenset({"nutrition", "pregnancy"})),
    TitleVariable("괜찮을까로 닫는 마무리", frozenset({"general"})),
    TitleVariable("왜 중요한지로 닫는 마무리", frozenset({"general"})),
    TitleVariable("어떻게 고를까로 닫는 마무리", frozenset({"nutrition", "gift", "food"})),
    TitleVariable("관리 팁으로 닫는 마무리", frozenset({"symptom", "constitution", "pregnancy"})),
    TitleVariable("선택 기준으로 닫는 마무리", frozenset({"nutrition", "gift", "food"})),
    TitleVariable("주의할 점으로 닫는 마무리", frozenset({"symptom", "pregnancy", "nutrition"})),
    TitleVariable("현실 이야기로 닫는 마무리", frozenset({"nutrition", "pregnancy", "gift"})),
    TitleVariable("직접 챙겨본 흐름으로 닫는 마무리", frozenset({"nutrition", "pregnancy"})),
    TitleVariable("지금 필요한 이유로 닫는 마무리", frozenset({"general"})),
    TitleVariable("같이 보면 좋은 포인트로 닫는 마무리", frozenset({"general", "constitution"})),
    TitleVariable("차이와 기준으로 닫는 마무리", frozenset({"general"})),
    TitleVariable("안전하게 챙기는 순서로 닫는 마무리", frozenset({"nutrition", "pregnancy"})),
    TitleVariable("체질에 맞게 고르는 흐름으로 닫는 마무리", frozenset({"constitution", "nutrition"})),
    TitleVariable("선물 고를 때 보기 좋은 포인트로 닫는 마무리", frozenset({"gift"})),
)

TAG_LABELS: dict[str, str] = {
    "general": "일반 정보",
    "symptom": "증상/원인",
    "constitution": "체질",
    "pregnancy": "임신/산후",
    "nutrition": "영양/복용",
    "food": "음식/차/식단",
    "gift": "선물",
}


def get_total_title_variable_count() -> int:
    return len(HOOK_VARIABLES) + len(ANGLE_VARIABLES) + len(CLOSING_VARIABLES)


def infer_title_tags(keyword: str) -> tuple[str, ...]:
    tags: set[str] = set()

    if any(token in keyword for token in ("수족냉증", "손발", "저림", "저체온", "체온", "감기", "독감", "소화제")):
        tags.add("symptom")

    if any(token in keyword for token in ("소음인", "소양인", "체질")):
        tags.add("constitution")

    if any(token in keyword for token in ("임산부", "임신", "산후", "산모", "출산")):
        tags.add("pregnancy")

    if any(
        token in keyword
        for token in (
            "영양제",
            "유산균",
            "철분",
            "철분제",
            "칼슘",
            "마그네슘",
            "비타민D",
            "엽산",
            "오메가3",
            "홍삼",
            "흑염소",
        )
    ):
        tags.add("nutrition")

    if any(token in keyword for token in ("음식", "식단", "좋은차")):
        tags.add("food")

    if "선물" in keyword:
        tags.add("gift")

    if not tags:
        tags.add("general")

    return tuple(tag for tag in TAG_LABELS if tag in tags)


def _unique_texts(variables: list[TitleVariable]) -> list[str]:
    seen: set[str] = set()
    texts: list[str] = []

    for variable in variables:
        if variable.text in seen:
            continue
        seen.add(variable.text)
        texts.append(variable.text)

    return texts


def _select_variables(
    variables: tuple[TitleVariable, ...],
    tags: tuple[str, ...],
    count: int,
    rng: random.Random,
) -> list[str]:
    selected: list[str] = []
    specific_tags = [tag for tag in tags if tag != "general"] or list(tags)
    for tag in specific_tags:
        tag_candidates = _unique_texts([variable for variable in variables if tag in variable.tags])
        remaining_candidates = [candidate for candidate in tag_candidates if candidate not in selected]
        if not remaining_candidates:
            continue
        selected.append(rng.choice(remaining_candidates))
        if len(selected) >= count:
            return selected

    remaining = count - len(selected)
    if remaining <= 0:
        return selected

    tag_set = set(tags)
    matched = _unique_texts([variable for variable in variables if variable.tags & tag_set])
    general = _unique_texts([variable for variable in variables if "general" in variable.tags])

    matched_fallback = [text for text in matched if text not in selected]
    if matched_fallback:
        selected.extend(rng.sample(matched_fallback, k=min(remaining, len(matched_fallback))))

    remaining = count - len(selected)
    if remaining <= 0:
        return selected

    fallback = [text for text in general if text not in selected]
    if len(fallback) < remaining:
        others = _unique_texts([variable for variable in variables if variable.text not in set(selected + fallback)])
        fallback.extend(text for text in others if text not in fallback)

    if fallback:
        selected.extend(rng.sample(fallback, k=min(remaining, len(fallback))))

    return selected


def _format_variable_block(title: str, items: list[str]) -> list[str]:
    lines = [title]
    for index, item in enumerate(items, start=1):
        lines.append(f"{index}. {item}")
    return lines


def build_title_pattern_mix_block(
    keyword: str,
    rng: random.Random | None = None,
) -> str:
    rng = rng or random.Random()
    tags = infer_title_tags(keyword)
    tag_labels = ", ".join(TAG_LABELS[tag] for tag in tags)

    hooks = _select_variables(HOOK_VARIABLES, tags, count=4, rng=rng)
    angles = _select_variables(ANGLE_VARIABLES, tags, count=4, rng=rng)
    closings = _select_variables(CLOSING_VARIABLES, tags, count=3, rng=rng)

    lines = [
        "[이번 원고의 제목 스타일]: 네이버 뷰탭 패턴 믹스",
        "- 수집 기준: 2026-04-07 네이버 뷰탭 블로그 제목 182개",
        f"- 현재 키워드에서 감지한 제목 축: {tag_labels}",
        "- 훅 변수 1개 + 정보 각도 변수 1개 + 마무리 리듬 변수 1개를 기본으로 섞고, 필요하면 보조 변수 1개를 추가합니다.",
        "- 실제 상위 제목에서 자주 보인 총정리, 완벽 정리 류는 패턴만 참고하고 단어는 그대로 쓰지 않습니다.",
        "",
    ]
    lines.extend(_format_variable_block("[훅 변수]", hooks))
    lines.append("")
    lines.extend(_format_variable_block("[정보 각도 변수]", angles))
    lines.append("")
    lines.extend(_format_variable_block("[마무리 리듬 변수]", closings))

    return "\n".join(lines).strip()

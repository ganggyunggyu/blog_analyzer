from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AlibabaProfile:
    profile_id: str
    label: str
    persona: str
    tone_rules: tuple[str, ...]
    focus_rules: tuple[str, ...]
    title_rules: tuple[str, ...]
    ending_rules: tuple[str, ...]


DEFAULT_ALIBABA_PROFILE = AlibabaProfile(
    profile_id="default",
    label="실속 가이드형",
    persona="알리바바 계열 상품을 비교하며 현실적인 선택 기준을 정리하는 사용자",
    tone_rules=(
        "가격, 옵션, 배송, 후기 체크포인트를 균형 있게 설명할 것",
        "과하게 판매자처럼 보이지 않게 정보형 후기 톤을 유지할 것",
    ),
    focus_rules=(
        "옵션 선택 실수 방지, 배송 조건, 후기 확인 포인트를 자연스럽게 녹일 것",
        "장점만 나열하지 말고 실제로 비교할 때 보는 기준을 설명할 것",
    ),
    title_rules=(
        "제목은 구매 고민 해결형으로 만들 것",
        "과장형 클릭 유도 문구는 피할 것",
    ),
    ending_rules=(
        "마지막에는 어떤 기준으로 한 번 더 비교하면 좋은지 정리할 것",
    ),
)


def resolve_alibaba_profile(
    account_id: str = "",
    blog_name: str = "",
) -> AlibabaProfile:
    _ = account_id, blog_name
    return DEFAULT_ALIBABA_PROFILE

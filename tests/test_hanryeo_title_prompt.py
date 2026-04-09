import random

from _prompts.hanryeo.title_variables import (
    build_title_pattern_mix_block,
    get_total_title_variable_count,
    infer_title_tags,
)
from _prompts.hanryeo.user import get_hanryeo_user_prompt


def test_total_title_variable_count_is_50_or_more() -> None:
    assert get_total_title_variable_count() >= 50


def test_infer_title_tags_detects_composite_keyword() -> None:
    tags = infer_title_tags("초기임산부선물")

    assert "pregnancy" in tags
    assert "gift" in tags


def test_build_title_pattern_mix_block_contains_key_sections() -> None:
    block = build_title_pattern_mix_block(
        keyword="임산부영양제추천",
        rng=random.Random(7),
    )

    assert "[이번 원고의 제목 스타일]: 네이버 뷰탭 패턴 믹스" in block
    assert "현재 키워드에서 감지한 제목 축: 임신/산후, 영양/복용" in block
    assert "[훅 변수]" in block
    assert "[정보 각도 변수]" in block
    assert "[마무리 리듬 변수]" in block
    assert "1. " in block


def test_get_hanryeo_user_prompt_includes_mix_block_and_title_rule() -> None:
    prompt = get_hanryeo_user_prompt(
        keyword="손발이차가울때영양제",
        rng=random.Random(3),
    )

    assert "[키워드]: 손발이차가울때영양제" in prompt
    assert "[이번 원고의 제목 스타일]: 네이버 뷰탭 패턴 믹스" in prompt
    assert "[제목 추가 규칙]" in prompt
    assert "제목에 쉼표" in prompt

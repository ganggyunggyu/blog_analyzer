from llm.blog_filler_pet_v2_service import (
    build_non_matching_title,
    count_keyword_occurrences,
    ensure_title_output_contract,
    replace_title_line,
)


def test_ensure_title_output_contract_removes_duplicate_leading_titles() -> None:
    keyword = "시바견분양"
    text = """시바견분양 현실 기준과 체크 포인트

시바견분양 현실 기준과 체크 포인트
시바견분양 현실 기준과 체크 포인트

안녕하세요 오늘은 시바견분양 전에 볼 포인트를 나눠볼게요

1. 성격
시바견은 독립심이 강한 편이에요
"""

    result = ensure_title_output_contract(
        text=text,
        keyword=keyword,
        target_keyword=keyword,
        live_view_titles=[],
    )

    non_empty_lines = [line.strip() for line in result.splitlines() if line.strip()]

    assert non_empty_lines[0] == "시바견분양 현실 기준과 체크 포인트"
    assert non_empty_lines[1] == "안녕하세요 오늘은 시바견분양 전에 볼 포인트를 나눠볼게요"
    assert non_empty_lines.count("시바견분양 현실 기준과 체크 포인트") == 1


def test_ensure_title_output_contract_inserts_fallback_title_without_dropping_body() -> None:
    keyword = "시바견분양"
    text = """안녕하세요 오늘은 시바견분양 전에 챙길 부분을 먼저 이야기해볼게요

1. 성격
시바견은 고집이 있어서 초반 훈련이 중요해요
"""

    result = ensure_title_output_contract(
        text=text,
        keyword=keyword,
        target_keyword=keyword,
        live_view_titles=[],
    )

    non_empty_lines = [line.strip() for line in result.splitlines() if line.strip()]

    assert non_empty_lines[0].startswith(keyword)
    assert count_keyword_occurrences(non_empty_lines[0], keyword) == 1
    assert non_empty_lines[1] == "안녕하세요 오늘은 시바견분양 전에 챙길 부분을 먼저 이야기해볼게요"


def test_replace_title_line_returns_title_for_empty_text() -> None:
    assert replace_title_line("", "시바견분양 현실 정보") == "시바견분양 현실 정보"


def test_build_non_matching_title_prefers_fresh_skeleton_over_suffix_append() -> None:
    keyword = "시바견분양"
    original_title = "시바견분양 현실 기준과 체크 포인트"

    result = build_non_matching_title(
        title=original_title,
        keyword=keyword,
        target_keyword=keyword,
        live_view_titles=[original_title],
    )

    assert result != original_title
    assert not result.startswith(f"{original_title} ")
    assert count_keyword_occurrences(result, keyword) == 1

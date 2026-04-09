from __future__ import annotations

from _prompts.alibaba.profile import AlibabaProfile


def get_alibaba_user_prompt(
    keyword: str,
    note: str,
    ref: str,
    category: str,
    profile: AlibabaProfile,
) -> str:
    parts = [
        f"[키워드]\n{keyword}",
        f"[카테고리]\n{category or '기타'}",
        f"[원고 스타일]\n{profile.label}\n{profile.persona}",
        (
            "[원고 요청]\n"
            "네이버 블로그용 원고를 작성해주세요.\n"
            "제목 1줄 + 본문 형식으로 출력하고, 본문은 실제 구매를 고민하는 사람이 읽었을 때\n"
            "선택 기준과 체크포인트가 바로 잡히도록 써주세요."
        ),
    ]

    if note:
        parts.append(f"[추가 요청]\n{note}")

    if ref:
        parts.append(f"[참조 원고]\n{ref}")

    parts.append(
        "[반드시 반영할 포인트]\n"
        "- 판매처 조건이 달라질 수 있다는 말은 자연스럽게 넣되, 원고가 겁주기처럼 보이지 않게 작성\n"
        "- 후기형/가이드형/비교형의 결을 살리되 정보 밀도는 유지\n"
        "- 마지막 문단은 과한 CTA 대신 체크포인트 정리 중심으로 마무리"
    )

    return "\n\n".join(parts).strip()

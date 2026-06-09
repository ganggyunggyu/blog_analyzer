from _prompts.alibaba.profile import DEFAULT_ALIBABA_PROFILE
from _prompts.alibaba.system import get_alibaba_system_prompt
from _prompts.alibaba.user import get_alibaba_user_prompt
from llm import alibaba_service
from services.naver_blog_reference_service import NaverBlogReference


def test_alibaba_system_prompt_uses_research_copywriter_contract() -> None:
    prompt = get_alibaba_system_prompt(
        keyword="알리바바구매대행",
        category="유통",
        profile=DEFAULT_ALIBABA_PROFILE,
    )

    assert "네이버/구글 검색 노출에 최적화된 블로그 원고" in prompt
    assert "[키워드]: 알리바바구매대행" in prompt
    assert "알리바바구매대행 site:blog.naver.com" in prompt
    assert "네이버 블로그(blog.naver.com, m.blog.naver.com) URL 최소 3개 이상 확보" in prompt
    assert "최소 2개 본문 확보" in prompt
    assert "최소 1,500자 이상" in prompt
    assert "분석 내용, 소제목 목록, 해시태그, 글자수, URL" in prompt


def test_alibaba_user_prompt_includes_reference_status() -> None:
    prompt = get_alibaba_user_prompt(
        keyword="1688구매대행",
        note="초보자 기준",
        ref="[자동 수집 참고원고]\n본문",
        category="유통",
        profile=DEFAULT_ALIBABA_PROFILE,
        auto_reference_count=1,
    )

    assert "[키워드]\n1688구매대행" in prompt
    assert "[참고원고 확보 수]\n1개" in prompt
    assert "[참고원고 부족 안내]\n필요" in prompt
    assert "[자동 수집 참고원고]" in prompt


def test_build_alibaba_reference_bundle_reports_auto_reference_count(monkeypatch) -> None:
    references = [
        NaverBlogReference(
            title="1688구매대행 전 확인할 조건",
            body="수수료와 배송 조건을 먼저 확인해야 합니다.",
            source_url="https://blog.naver.com/example/1",
            mobile_url="https://m.blog.naver.com/PostView.naver?blogId=example&logNo=1",
        ),
        NaverBlogReference(
            title="1688구매대행 업체 비교 기준",
            body="검수 범위와 통관 안내를 비교하는 흐름이 중요합니다.",
            source_url="https://blog.naver.com/example/2",
            mobile_url="https://m.blog.naver.com/PostView.naver?blogId=example&logNo=2",
        ),
    ]

    monkeypatch.setattr(
        alibaba_service,
        "collect_naver_blog_references",
        lambda query, limit=8: references,
    )

    bundle, count = alibaba_service.build_alibaba_reference_bundle(
        keyword="1688구매대행",
        manual_ref="직접 메모",
    )

    assert count == 2
    assert "[자동 수집 참고원고]" in bundle
    assert "1688구매대행 업체 비교 기준" in bundle
    assert "[사용자 제공 참조원고]" in bundle
    assert "직접 메모" in bundle


def test_alibaba_gen_injects_crawled_reference_bundle(monkeypatch) -> None:
    captured: dict[str, str] = {}

    monkeypatch.setattr(
        alibaba_service,
        "build_alibaba_reference_bundle",
        lambda keyword, manual_ref="": ("[자동 수집 참고원고]\n본문", 2),
    )
    monkeypatch.setattr(
        alibaba_service,
        "comprehensive_text_clean",
        lambda text: text,
    )

    def fake_call_ai(
        model_name: str,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        captured["system_prompt"] = system_prompt
        captured["user_prompt"] = user_prompt
        return "1688구매대행 기준\n\n본문"

    monkeypatch.setattr(alibaba_service, "call_ai", fake_call_ai)

    result = alibaba_service.alibaba_gen("1688구매대행", category="유통")

    assert result["content"] == "1688구매대행 기준\n\n본문"
    assert "[자동 수집 참고원고]" in captured["user_prompt"]
    assert "[참고원고 확보 수]\n2개" in captured["user_prompt"]
    assert "네이버/구글 검색 노출에 최적화된 블로그 원고" in captured["system_prompt"]

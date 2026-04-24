from _prompts.hanryeo.system import get_hanryeo_system_prompt
from _constants.Model import Model
from llm.hanryeo_output_cleanup import sanitize_hanryeo_output
from llm import hanryeo_service
from services import naver_blog_reference_service
from services.naver_blog_reference_service import NaverBlogReference


def test_hanryeo_service_uses_deepseek_v4_flash() -> None:
    assert hanryeo_service.MODEL_NAME == Model.DEEPSEEK_V4_FLASH


def test_extract_naver_blog_urls_deduplicates_and_normalizes() -> None:
    html_text = """
    <html>
      <body>
        <a href="https://blog.naver.com/example_blog/224123456789">a</a>
        <a href="https://blog.naver.com/example_blog/224123456789">dup</a>
        <a href="https://m.blog.naver.com/PostView.naver?blogId=second_blog&amp;logNo=224987654321">b</a>
      </body>
    </html>
    """

    urls = naver_blog_reference_service.extract_naver_blog_urls(html_text, limit=5)

    assert urls == [
        "https://blog.naver.com/example_blog/224123456789",
        "https://blog.naver.com/second_blog/224987654321",
    ]


def test_parse_naver_blog_post_html_extracts_title_and_body() -> None:
    html_text = """
    <html>
      <head>
        <meta property="og:title" content="소음인남자 체질 이해하기" />
      </head>
      <body>
        <div class="se-main-container">
          <p class="se-text-paragraph">소음인남자 체질 이해하기</p>
          <p class="se-text-paragraph">소음인 남자는 섬세한 편입니다.</p>
          <p class="se-text-paragraph">몸을 따뜻하게 유지하는 습관이 중요합니다.</p>
          <p class="se-text-paragraph">특히 소화가 약한 날에는 무리하지 않는 편이 좋습니다.</p>
          <p class="se-text-paragraph">따뜻한 음식과 규칙적인 식사가 도움이 됩니다.</p>
          <p class="se-text-paragraph">작은 루틴이 체력 유지에 보탬이 됩니다.</p>
        </div>
      </body>
    </html>
    """

    title, body = naver_blog_reference_service.parse_naver_blog_post_html(html_text)

    assert title == "소음인남자 체질 이해하기"
    assert "소음인 남자는 섬세한 편입니다." in body
    assert "작은 루틴이 체력 유지에 보탬이 됩니다." in body
    assert "소음인남자 체질 이해하기\n" not in body


def test_build_reference_bundle_merges_auto_and_manual_refs(
    monkeypatch,
) -> None:
    references = [
        NaverBlogReference(
            title="소음인남자 관리 포인트",
            body="체온을 지키고 식사를 거르지 않는 흐름이 중요합니다.",
            source_url="https://blog.naver.com/example/1",
            mobile_url="https://m.blog.naver.com/PostView.naver?blogId=example&logNo=1",
        ),
        NaverBlogReference(
            title="소음인남자 음식 루틴",
            body="따뜻한 성질의 식단과 휴식 리듬을 함께 보는 편이 좋습니다.",
            source_url="https://blog.naver.com/example/2",
            mobile_url="https://m.blog.naver.com/PostView.naver?blogId=example&logNo=2",
        ),
    ]

    monkeypatch.setattr(
        naver_blog_reference_service,
        "collect_naver_blog_references",
        lambda query, limit=8: references,
    )

    bundle = naver_blog_reference_service.build_naver_blog_reference_bundle(
        query="소음인남자",
        manual_ref="직접 메모한 참고 원고",
    )

    assert "[네이버 뷰탭 자동 참조원고]" in bundle
    assert "[참조 1]" in bundle
    assert "소음인남자 관리 포인트" in bundle
    assert "[사용자 제공 참조원고]" in bundle
    assert "직접 메모한 참고 원고" in bundle


def test_system_prompt_requires_closing_block_and_reference_usage() -> None:
    prompt = get_hanryeo_system_prompt()

    assert "[맺음말 블록" in prompt
    assert "체질 / 증상 / 임신·산후 / 영양·섭취" in prompt
    assert "6-9. 참조 원고 활용 규칙" in prompt
    assert "금지 예: 도입부, 핵심 개념, 실천 가이드, Q&A, 마무리 요약, 제품 연결, 관리 제안" in prompt
    assert "소제목은 정확히 5개만 작성한다" in prompt
    assert "4번을 마지막 소제목으로 끝내는 것 금지" in prompt
    assert '"6."으로 시작하는 추가 소제목은 절대 출력하지 않는다' in prompt
    assert "소제목은 반드시 한 줄로 입력하듯 작성한다" in prompt
    assert "소제목에는 줄 길이 규칙을 적용하지 않는다" in prompt
    assert "[실천 항목], [Q&A], [정리], [제품 연결] 같은 대괄호 라벨을 본문에 출력하지 않는다" in prompt
    assert '본문 전체에서 "냥"' in prompt


def test_sanitize_hanryeo_output_rewrites_meta_subtitles() -> None:
    text = """제목

1. 도입부

2. 핵심 개념 ① 혈액량 증가와 말초 분배 변화

3. 핵심 개념 ②

4. 소음인 남자를 위한 실천 가이드 + Q&A

5. 마무리 요약 + 제품 연결

6. 실천 가이드와 자주 묻는 질문

7. 소음인 특징 요약과 관리 제안

8. 요약과
관리 제안
"""

    result = sanitize_hanryeo_output(text)

    assert "1. 먼저 알아둘 점" in result
    assert "2. 혈액량 증가와 말초 분배 변화" in result
    assert "3. 함께 봐야 할 점" in result
    assert "4. 소음인 남자를 위한 관리 포인트" in result
    assert "5. 끝으로 정리해보면" in result
    assert "6. 관리 방법과 궁금증" in result
    assert "7. 소음인 특징 정리" in result
    assert "8. 정리해보면" in result


def test_hanryeo_gen_injects_crawled_reference_bundle(monkeypatch) -> None:
    captured: dict[str, str] = {}

    monkeypatch.setattr(
        hanryeo_service,
        "build_naver_blog_reference_bundle",
        lambda query, manual_ref="": "[네이버 뷰탭 자동 참조원고]\n본문",
    )
    monkeypatch.setattr(
        hanryeo_service,
        "comprehensive_text_clean",
        lambda text: text,
    )

    def fake_call_ai(
        model_name: str,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
    ) -> str:
        captured["user_prompt"] = user_prompt
        return "소음인남자 관리 포인트\n\n5. 마무리 요약 + 제품 연결"

    monkeypatch.setattr(hanryeo_service, "call_ai", fake_call_ai)

    result = hanryeo_service.hanryeo_gen(
        user_instructions="소음인남자",
        ref="수동 참조",
        category="",
    )

    assert result == "소음인남자 관리 포인트\n\n5. 끝으로 정리해보면"
    assert "[참조 원고]" in captured["user_prompt"]
    assert "[네이버 뷰탭 자동 참조원고]" in captured["user_prompt"]

from _prompts.blog_filler.system import get_blog_filler_system_prompt
from _prompts.blog_filler.user import get_blog_filler_user_prompt
from _constants.Model import Model
from llm import (
    blog_filler_diet_v2_service,
    blog_filler_pet_service,
    blog_filler_pet_v2_service,
    blog_filler_restaurant_service,
    blog_filler_service,
)
from services import naver_blog_reference_service


def test_blog_filler_services_use_deepseek_v4_flash() -> None:
    assert blog_filler_service.MODEL_NAME == Model.DEEPSEEK_V4_FLASH
    assert blog_filler_diet_v2_service.MODEL_NAME == Model.DEEPSEEK_V4_FLASH
    assert blog_filler_pet_service.MODEL_NAME == Model.DEEPSEEK_V4_FLASH
    assert blog_filler_pet_v2_service.MODEL_NAME == Model.DEEPSEEK_V4_FLASH
    assert blog_filler_restaurant_service.MODEL_NAME == Model.DEEPSEEK_V4_FLASH


def test_blog_filler_system_prompt_requires_alibaba_dot_com_title() -> None:
    prompt = get_blog_filler_system_prompt(keyword="알리바바 도매")

    assert (
        "제목에 알리바바가 들어가면 반드시 알리바바 닷컴으로 표기하고 알리바바 단독 표기는 금지"
        in prompt
    )


def test_blog_filler_ophthalmology_prompt_uses_master_contract() -> None:
    prompt = get_blog_filler_system_prompt(category="안과", keyword="백내장수술비용")

    assert "안과 시력교정·백내장 분야의 전문 블로그 콘텐츠 라이터" in prompt
    assert "메인 키워드: 백내장수술비용" in prompt
    assert "공백 포함 3,500자 ~ 4,000자" in prompt
    assert "H2 대제목 6~7개" in prompt
    assert "본문 전체에서 8~12회" in prompt
    assert "가격/비용 키워드일 때 필수" in prompt
    assert "첫 줄: 실제 제목만 출력" in prompt
    assert "\"[제목]\" 라벨 출력 금지" in prompt
    assert "1,100~1,500자" not in prompt


def test_extract_naver_view_titles_reads_search_result_titles() -> None:
    html_text = """
    <html>
      <body>
        <script>
          {"title":"<mark>거북목</mark> 스트레칭 비용은","titleEllipsis":0,"type":"searchBasic"}
        </script>
        <a class="api_txt_lines total_tit"><mark>거북목</mark> 교정 전 알아둘 기준</a>
        <script>{"title":"네이버 검색"}</script>
        <script>{"title":"거북목 스트레칭 비용은"}</script>
      </body>
    </html>
    """

    titles = naver_blog_reference_service.extract_naver_view_titles(
        html_text,
        query="거북목",
    )

    assert titles == [
        "거북목 스트레칭 비용은",
        "거북목 교정 전 알아둘 기준",
    ]


def test_blog_filler_user_prompt_includes_naver_title_examples() -> None:
    prompt = get_blog_filler_user_prompt(
        keyword="거북목",
        naver_title_examples=[
            "거북목 스트레칭 비용은",
            "거북목 교정 전 알아둘 기준",
        ],
    )

    assert "## 네이버 검색 제목 예시" in prompt
    assert "- 거북목 스트레칭 비용은" in prompt
    assert "예시 제목과 완전히 같은 제목은 만들지 마세요." in prompt


def test_blog_filler_gen_injects_naver_titles_into_prompt(monkeypatch) -> None:
    captured: dict[str, str] = {}

    monkeypatch.setattr(
        blog_filler_service,
        "collect_naver_view_titles",
        lambda query, limit=8: [
            "알리바바 닷컴 도매 구매 전 확인할 점",
            "알리바바 도매 초보가 보는 기준",
        ],
    )
    monkeypatch.setattr(
        blog_filler_service,
        "get_blog_filler_system_prompt",
        lambda category="", keyword="": "system",
    )
    monkeypatch.setattr(blog_filler_service, "remove_markdown", lambda text: text)
    monkeypatch.setattr(
        blog_filler_service,
        "comprehensive_text_clean",
        lambda text: text,
    )

    def fake_call_ai(
        model_name: str,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        captured["user_prompt"] = user_prompt
        return "알리바바 닷컴 도매 기준\n\n본문"

    monkeypatch.setattr(blog_filler_service, "call_ai", fake_call_ai)

    result = blog_filler_service.blog_filler_gen("알리바바 도매", category="유통")

    assert result == "알리바바 닷컴 도매 기준\n\n본문"
    assert "## 네이버 검색 제목 예시" in captured["user_prompt"]
    assert "알리바바 도매 초보가 보는 기준" in captured["user_prompt"]


def test_blog_filler_gen_passes_naver_titles_to_diet_v2(monkeypatch) -> None:
    captured: dict[str, list[str] | str] = {}

    monkeypatch.setattr(
        blog_filler_service,
        "collect_naver_view_titles",
        lambda query, limit=8: [
            "브로멜라인 복용법 식전 식후 기준",
            "브로멜라인 효과보다 먼저 볼 점",
        ],
    )

    def fake_diet_v2_gen(
        user_instructions: str,
        live_view_titles: list[str] | None = None,
        category: str = "다이어트",
    ) -> dict[str, object]:
        captured["user_instructions"] = user_instructions
        captured["live_view_titles"] = live_view_titles or []
        captured["category"] = category
        return {"manuscript": "브로멜라인 기준\n\n본문"}

    monkeypatch.setattr(
        blog_filler_service,
        "blog_filler_diet_v2_gen",
        fake_diet_v2_gen,
    )

    result = blog_filler_service.blog_filler_gen("브로멜라인", category="다이어트")

    assert result == "브로멜라인 기준\n\n본문"
    assert captured["live_view_titles"] == [
        "브로멜라인 복용법 식전 식후 기준",
        "브로멜라인 효과보다 먼저 볼 점",
    ]

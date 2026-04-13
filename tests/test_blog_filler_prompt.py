from _prompts.blog_filler.system import get_blog_filler_system_prompt


def test_blog_filler_system_prompt_requires_alibaba_dot_com_title() -> None:
    prompt = get_blog_filler_system_prompt(keyword="알리바바 도매")

    assert (
        "제목에 알리바바가 들어가면 반드시 알리바바 닷컴으로 표기하고 알리바바 단독 표기는 금지"
        in prompt
    )

from _prompts.alibaba.profile import DEFAULT_ALIBABA_PROFILE, resolve_alibaba_profile


def test_resolve_alibaba_profile_returns_default_profile() -> None:
    profile = resolve_alibaba_profile()

    assert profile.profile_id == DEFAULT_ALIBABA_PROFILE.profile_id
    assert profile.label == DEFAULT_ALIBABA_PROFILE.label


def test_resolve_alibaba_profile_ignores_account_context() -> None:
    profile = resolve_alibaba_profile(account_id="seller-alpha", blog_name="sample-blog")

    assert profile.profile_id == DEFAULT_ALIBABA_PROFILE.profile_id

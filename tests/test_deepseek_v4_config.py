from _constants.Model import Model
from llm import clean_deepseek_service, deepseek_new_service, deepseek_service
from utils.ai_client.text import get_deepseek_request_options
from utils.ai_client.text_providers import call_chat_completion_text
from utils.ai_client.text_registry import get_model_pricing


class _FakeMessage:
    content = "응답"


class _FakeChoice:
    message = _FakeMessage()


class _FakeChatCompletions:
    def __init__(self) -> None:
        self.request: dict[str, object] = {}

    def create(self, **request: object) -> object:
        self.request = request
        return type("Response", (), {"choices": [_FakeChoice()], "usage": None})()


class _FakeChat:
    def __init__(self) -> None:
        self.completions = _FakeChatCompletions()


class _FakeClient:
    def __init__(self) -> None:
        self.chat = _FakeChat()


def test_deepseek_v4_models_are_available() -> None:
    assert Model.DEEPSEEK_V4_FLASH == "deepseek-v4-flash"
    assert Model.DEEPSEEK_V4_PRO == "deepseek-v4-pro"
    assert deepseek_service.MODEL_NAME == Model.DEEPSEEK_V4_PRO
    assert deepseek_new_service.MODEL_NAME == Model.DEEPSEEK_V4_PRO
    assert clean_deepseek_service.MODEL_NAME == Model.DEEPSEEK_V4_FLASH


def test_deepseek_v4_pro_uses_thinking_mode_options() -> None:
    options = get_deepseek_request_options(Model.DEEPSEEK_V4_PRO)

    assert options == {
        "reasoning_effort": "high",
        "extra_body": {"thinking": {"type": "enabled"}},
    }


def test_deepseek_v4_flash_uses_non_thinking_mode_options() -> None:
    options = get_deepseek_request_options(Model.DEEPSEEK_V4_FLASH)

    assert options == {"extra_body": {"thinking": {"type": "disabled"}}}


def test_chat_completion_forwards_deepseek_extra_body() -> None:
    client = _FakeClient()

    text, input_tokens, output_tokens = call_chat_completion_text(
        client=client,
        model_name=Model.DEEPSEEK_V4_PRO,
        system_prompt="system",
        user_prompt="user",
        provider_name="DeepSeek",
        reasoning_effort="high",
        extra_body={"thinking": {"type": "enabled"}},
    )

    assert text == "응답"
    assert input_tokens == 0
    assert output_tokens == 0
    assert client.chat.completions.request["reasoning_effort"] == "high"
    assert client.chat.completions.request["extra_body"] == {
        "thinking": {"type": "enabled"}
    }


def test_deepseek_v4_pricing_prefers_specific_model_prices() -> None:
    assert get_model_pricing(Model.DEEPSEEK_V4_FLASH) == (0.14, 0.28)
    assert get_model_pricing(Model.DEEPSEEK_V4_PRO) == (1.74, 3.48)

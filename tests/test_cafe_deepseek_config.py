from _constants.Model import Model
from llm import cafe_total_service, gemini_cafe_daily_service, gemini_cafe_service


def test_cafe_generators_use_deepseek_by_default() -> None:
    assert cafe_total_service.DEFAULT_MODEL == Model.DEEPSEEK_V4_FLASH
    assert gemini_cafe_service.MODEL_NAME == Model.DEEPSEEK_V4_FLASH
    assert gemini_cafe_daily_service.MODEL_NAME == Model.DEEPSEEK_V4_FLASH


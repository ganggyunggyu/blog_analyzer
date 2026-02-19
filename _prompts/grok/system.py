from _prompts.service import get_mongo_prompt
from _prompts.grok.prompt import get_grok_system_prompt as _get_template


def get_grok_system_prompt(keyword: str, category: str) -> str:
    mongo_data = get_mongo_prompt.get_mongo_prompt(category, keyword)
    return _get_template(keyword=keyword, category=category, mongo_data=mongo_data)

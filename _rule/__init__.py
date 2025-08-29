import json
from pathlib import Path

base_path = Path(__file__).parent


def load_rules(file_name: str) -> str:
    with open(base_path / file_name, "r", encoding="utf-8") as f:
        return json.dumps(json.load(f), ensure_ascii=False, indent=2)


WORD_RULES = load_rules("word_rule.json")
SEN_RULES = load_rules("sen_rule.json")
PER_EXAMPLE = load_rules("persona_example.json")
STORY_RULE = load_rules("story_rule.json")

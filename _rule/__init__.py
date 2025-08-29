import json
from pathlib import Path

file_path = Path(__file__).parent / "word_rule.json"

with open(file_path, "r", encoding="utf-8") as f:
    WORD_RULES = json.load(f)

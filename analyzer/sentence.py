import re

def split_sentences(text: str) -> list:
    
    sentences = re.split(r'(?<=[\.?!다요])\s+', text)
    return [s.strip() for s in sentences if s.strip()]
import re

def analyze_morphemes(text: str) -> list:
    
    return list(set(re.findall(r'[가-힣]{2,}', text)))

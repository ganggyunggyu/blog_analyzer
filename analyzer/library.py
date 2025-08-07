import os
from pathlib import Path
import kss

def build_sentence_library(directory_path):
    library = {}
    p = Path(directory_path)
    
    for file_path in p.glob('*.txt'):
        category = file_path.stem  # 파일명에서 확장자를 제외한 부분을 카테고리로 사용
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        sentences = kss.split_sentences(content)
        
        if category not in library:
            library[category] = []
        library[category].extend(sentences)
        
    return library

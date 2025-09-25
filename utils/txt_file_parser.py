from __future__ import annotations
from typing import Dict, Any
from pathlib import Path
import tempfile


def parse_txt_file(file_content: bytes, filename: str) -> Dict[str, Any]:
    """
    txt 파일을 받아서 text, category, file_name을 추출하는 유틸 함수

    Args:
        file_content: 업로드된 txt 파일의 바이트 내용
        filename: 파일명

    Returns:
        {
            "text": str,         # 파일 내용 텍스트
            "category": str,     # 파일명에서 추출한 카테고리
            "file_name": str     # 원본 파일명
        }
    """
    # 바이트를 문자열로 디코딩
    try:
        text = file_content.decode('utf-8')
    except UnicodeDecodeError:
        # UTF-8이 안 되면 CP949로 시도
        try:
            text = file_content.decode('cp949')
        except UnicodeDecodeError:
            # 그래도 안 되면 latin-1로 강제 디코딩
            text = file_content.decode('latin-1')

    # 파일명에서 카테고리 추출
    # 예: "위고비_3.txt" -> "위고비"
    file_path = Path(filename)
    category = file_path.stem  # 확장자 제거

    # 언더스코어나 숫자가 있으면 제거해서 카테고리 정리
    if '_' in category:
        category = category.split('_')[0]

    # 숫자만 있는 부분 제거 (예: "위고비3" -> "위고비")
    import re
    category = re.sub(r'\d+$', '', category)

    return {
        "text": text.strip(),
        "category": category or "기타",
        "file_name": filename
    }


def save_temp_txt_file(file_content: bytes, filename: str) -> str:
    """
    임시 txt 파일을 저장하고 경로를 반환하는 함수

    Args:
        file_content: 파일 바이트 내용
        filename: 원본 파일명

    Returns:
        임시 파일 경로
    """
    # 임시 파일 생성
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.txt', delete=False) as temp_file:
        temp_file.write(file_content)
        temp_file_path = temp_file.name

    return temp_file_path
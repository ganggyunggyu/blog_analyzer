"""Analyzer 모듈 공통 설정"""

from _constants.Model import Model

# Analyzer 모듈에서 사용하는 기본 모델
# 이 값을 변경하면 모든 analyzer 파일에 적용됨
ANALYZER_MODEL: str = Model.DEEPSEEK_RES

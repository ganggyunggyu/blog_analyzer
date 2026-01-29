# Blog Analyzer 서버 명령어

# 개발 서버 (자동 리로드 + 액세스 로그 숨김)
dev:
	uv run uvicorn api:app --reload --host 0.0.0.0 --no-access-log

# 개발 서버 (전체 로그)
dev-verbose:
	uv run uvicorn api:app --reload

# 프로덕션 서버
start:
	uv run uvicorn api:app --host 0.0.0.0 --port 8000

# 조용한 서버 (에러만)
quiet:
	uv run uvicorn api:app --reload --log-level error

# 의존성 설치
install:
	uv sync

# 의존성 업데이트
update:
	uv lock --upgrade && uv sync

.PHONY: dev dev-verbose start quiet install update

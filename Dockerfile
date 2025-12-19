FROM python:3.12-slim

WORKDIR /app

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# uv 설치
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# pyproject.toml과 uv.lock 복사
COPY pyproject.toml uv.lock ./

# 의존성 설치 (캐시 활용)
RUN uv sync --frozen --no-dev

# 소스 코드 복사
COPY . .

# 포트 노출
EXPOSE 8080

# 서버 실행 (Fly.io는 PORT 환경변수 사용)
CMD uv run uvicorn api:app --host 0.0.0.0 --port ${PORT:-8080}

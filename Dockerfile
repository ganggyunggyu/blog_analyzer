FROM python:3.11-slim

WORKDIR /app

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    default-jdk \
    && rm -rf /var/lib/apt/lists/*

# JAVA_HOME 설정 (KoNLPy용)
ENV JAVA_HOME=/usr/lib/jvm/default-java

# requirements 복사 및 설치
COPY requirements-server.txt .
RUN pip install --no-cache-dir -r requirements-server.txt

# 소스 코드 복사
COPY . .

# 포트 노출
EXPOSE 8080

# 서버 실행 (Fly.io는 PORT 환경변수 사용)
CMD uvicorn api:app --host 0.0.0.0 --port ${PORT:-8080}

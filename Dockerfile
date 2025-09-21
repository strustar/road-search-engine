# 도로설계 문서 검색 시스템 - Docker 이미지
FROM python:3.9-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 필요한 패키지 설치
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 파일 복사 및 설치
COPY requirements_minimal.txt .
RUN pip install --no-cache-dir -r requirements_minimal.txt

# 프로젝트 파일들 복사 (PDF 파일 제외)
COPY fastapi_server.py .
COPY preprocessing/ ./preprocessing/
COPY rag/ ./rag/

# 필요한 디렉토리 생성
RUN mkdir -p image_cache page_images_cache vector_store

# 포트 노출
EXPOSE 8080

# 환경 변수 설정
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# 애플리케이션 실행 (원래 FastAPI 서버)
CMD uvicorn fastapi_server:app --host 0.0.0.0 --port 8080 --workers 1

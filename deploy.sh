#!/bin/bash

echo "🚀 도로설계 문서 검색 시스템 배포 시작"
echo "========================================"

# Docker 설치 확인
if ! command -v docker &> /dev/null; then
    echo "❌ Docker가 설치되지 않았습니다."
    echo "Docker를 먼저 설치해주세요: https://docs.docker.com/get-docker/"
    exit 1
fi

# Docker Compose 설치 확인
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose가 설치되지 않았습니다."
    echo "Docker Compose를 먼저 설치해주세요: https://docs.docker.com/compose/install/"
    exit 1
fi

# 기존 컨테이너 정리
echo "🧹 기존 컨테이너 정리 중..."
docker-compose down --remove-orphans

# 이미지 빌드
echo "🔨 Docker 이미지 빌드 중..."
docker-compose build --no-cache

# 문서 처리 확인
if [ ! -f "vector_store/road_design_db.index" ]; then
    echo "⚠️  벡터 데이터베이스가 없습니다."
    echo "문서 처리를 먼저 실행해주세요:"
    echo "python3 process_documents_auto.py"
    read -p "계속하시겠습니까? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 서비스 시작
echo "🚀 서비스 시작 중..."
docker-compose up -d

# 서비스 상태 확인
echo "⏳ 서비스 시작 대기 중..."
sleep 10

# 헬스체크
echo "🏥 헬스체크 실행 중..."
for i in {1..30}; do
    if curl -f http://localhost:8080/health &> /dev/null; then
        echo "✅ API 서버 정상 작동"
        break
    fi
    echo "⏳ API 서버 시작 대기 중... ($i/30)"
    sleep 2
done

if curl -f http://localhost:8080/health &> /dev/null; then
    echo ""
    echo "🎉 배포 완료!"
    echo "========================================"
    echo "🌐 접속 정보:"
    echo "   프론트엔드: http://localhost"
    echo "   API 문서: http://localhost:8080/docs"
    echo "   헬스체크: http://localhost:8080/health"
    echo ""
    echo "📊 서비스 상태:"
    docker-compose ps
    echo ""
    echo "📝 로그 확인:"
    echo "   docker-compose logs -f"
    echo ""
    echo "🛑 서비스 중지:"
    echo "   docker-compose down"
else
    echo "❌ 배포 실패"
    echo "로그를 확인해주세요:"
    docker-compose logs
    exit 1
fi

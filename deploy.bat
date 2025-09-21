@echo off
echo 🚀 도로설계 문서 검색 시스템 배포 시작
echo ========================================

REM Docker 설치 확인
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker가 설치되지 않았습니다.
    echo Docker를 먼저 설치해주세요: https://docs.docker.com/get-docker/
    pause
    exit /b 1
)

REM Docker Compose 설치 확인
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker Compose가 설치되지 않았습니다.
    echo Docker Compose를 먼저 설치해주세요: https://docs.docker.com/compose/install/
    pause
    exit /b 1
)

REM 기존 컨테이너 정리
echo 🧹 기존 컨테이너 정리 중...
docker-compose down --remove-orphans

REM 이미지 빌드
echo 🔨 Docker 이미지 빌드 중...
docker-compose build --no-cache

REM 문서 처리 확인
if not exist "vector_store\road_design_db.index" (
    echo ⚠️  벡터 데이터베이스가 없습니다.
    echo 문서 처리를 먼저 실행해주세요:
    echo python process_documents_auto.py
    set /p continue="계속하시겠습니까? (y/N): "
    if /i not "%continue%"=="y" exit /b 1
)

REM 서비스 시작
echo 🚀 서비스 시작 중...
docker-compose up -d

REM 서비스 상태 확인
echo ⏳ 서비스 시작 대기 중...
timeout /t 10 /nobreak >nul

REM 헬스체크
echo 🏥 헬스체크 실행 중...
for /l %%i in (1,1,30) do (
    curl -f http://localhost:8080/health >nul 2>&1
    if !errorlevel! equ 0 (
        echo ✅ API 서버 정상 작동
        goto :success
    )
    echo ⏳ API 서버 시작 대기 중... (%%i/30)
    timeout /t 2 /nobreak >nul
)

echo ❌ 배포 실패
echo 로그를 확인해주세요:
docker-compose logs
pause
exit /b 1

:success
echo.
echo 🎉 배포 완료!
echo ========================================
echo 🌐 접속 정보:
echo    프론트엔드: http://localhost
echo    API 문서: http://localhost:8080/docs
echo    헬스체크: http://localhost:8080/health
echo.
echo 📊 서비스 상태:
docker-compose ps
echo.
echo 📝 로그 확인:
echo    docker-compose logs -f
echo.
echo 🛑 서비스 중지:
echo    docker-compose down
echo.
pause

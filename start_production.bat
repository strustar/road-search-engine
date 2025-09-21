@echo off
echo ========================================
echo 도로설계 문서 검색 시스템 시작
echo ========================================

REM 환경 확인
echo [1/4] Python 환경 확인 중...
python --version
if %errorlevel% neq 0 (
    echo 오류: Python이 설치되지 않았습니다.
    pause
    exit /b 1
)

REM 의존성 확인
echo [2/4] 의존성 확인 중...
python -c "import fastapi, uvicorn, faiss, sentence_transformers" 2>nul
if %errorlevel% neq 0 (
    echo 경고: 일부 의존성이 누락되었습니다.
    echo requirements_production.txt를 설치해주세요:
    echo pip install -r requirements_production.txt
    pause
)

REM 벡터 DB 확인
echo [3/4] 벡터 데이터베이스 확인 중...
if not exist "vector_store\road_design_db.index" (
    echo 경고: 벡터 데이터베이스가 없습니다.
    echo 문서 처리를 먼저 실행해주세요:
    echo python process_documents_auto.py
    pause
)

REM 포트 확인
echo [4/4] 포트 확인 중...
netstat -an | findstr :8080 >nul
if %errorlevel% equ 0 (
    echo 경고: 포트 8080이 이미 사용 중입니다.
    echo 기존 서버를 종료하고 다시 시도해주세요.
    pause
)

REM 서버 시작
echo.
echo FastAPI 서버 시작 중...
echo 프론트엔드: http://localhost:5500/innovative_search_app.html
echo API 문서: http://localhost:8080/docs
echo.
echo 서버를 종료하려면 Ctrl+C를 누르세요.
echo.

REM FastAPI 서버 시작
uvicorn fastapi_server:app --host 0.0.0.0 --port 8080 --workers 1

pause

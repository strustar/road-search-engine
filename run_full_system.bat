@echo off
echo ========================================
echo 도로설계 RAG 시스템 전체 실행
echo ========================================

echo.
echo 1단계: 의존성 설치
pip install -r requirements_full.txt

echo.
echo 2단계: 문서 처리 및 벡터화
python process_all_documents.py

echo.
echo 3단계: 검색 시스템 실행
echo 웹 브라우저에서 http://localhost:8501 을 열어주세요.
streamlit run streamlit_search_app.py

pause
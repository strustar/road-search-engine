# 🚀 도로설계 문서 검색 시스템 배포 가이드

## 📋 프로젝트 개요
- **프로젝트명**: AI-Powered Road Design Search System
- **기능**: 도로설계요령(2020) 및 실무지침(2020) 문서 검색 시스템
- **기술스택**: FastAPI + FAISS + Korean Embedding + HTML/CSS/JS

## 🏗️ 시스템 아키텍처

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Data Layer    │
│   (HTML/JS)     │◄──►│   (FastAPI)     │◄──►│   (FAISS DB)    │
│   Port: 5500    │    │   Port: 8080    │    │   (PDF Files)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📁 배포 파일 구조

```
production/
├── innovative_search_app.html          # 메인 프론트엔드
├── fastapi_server.py                   # 백엔드 API 서버
├── requirements.txt                    # Python 의존성
├── requirements_full.txt               # 전체 의존성 (개발용)
├── run_full_system.bat                 # 시스템 시작 스크립트
├── run_streamlit.bat                   # Streamlit 실행 스크립트
├── 
├── rag/                               # RAG 시스템 모듈
│   ├── __init__.py
│   ├── embedding_engine.py            # 한국어 임베딩 엔진
│   └── vector_database.py             # FAISS 벡터 데이터베이스
├── 
├── preprocessing/                     # 문서 전처리 모듈
│   ├── __init__.py
│   ├── document_loader.py             # PDF 문서 로더
│   └── text_chunker.py                # 텍스트 청킹
├── 
├── pdf_image_renderer.py              # PDF 이미지 렌더러
├── process_all_documents.py           # 문서 처리 스크립트
├── process_documents_auto.py          # 자동 문서 처리
├── 
├── vector_store/                      # 벡터 데이터베이스 저장소
│   ├── road_design_db.index           # FAISS 인덱스
│   ├── road_design_db.pkl             # 메타데이터
│   └── road_design_db_info.json       # DB 정보
├── 
├── image_cache/                       # PDF 이미지 캐시
├── page_images_cache/                 # 페이지 이미지 캐시
├── 
├── 도로설계요령(2020)/                # 도로설계요령 PDF 파일들
│   ├── 제1권 도로계획및 구조.pdf
│   ├── 제2권 토공 및 배수.pdf
│   ├── 제3권 교량.pdf
│   ├── 제4권 터널.pdf
│   └── 제5권 포장 도로안전 부대시설 및 환경.pdf
├── 
└── 실무지침(2020)/                    # 실무지침 PDF 파일들
    ├── 0-간지 -편집.pdf
    ├── 1-목차.pdf
    ├── 2설계행정-327ok.pdf
    ├── 3 교통 및 기하구조-327ok.pdf
    ├── 4토공 및 배수공-편집중.pdf
    ├── 5구조물공-편집중-ok.pdf
    ├── 6포장공-편집.pdf
    ├── 7터널공-편집ok.pdf
    ├── 8 부대공 -편집.pdf
    └── 9기타-편집.pdf
```

## 🔧 시스템 요구사항

### 하드웨어 요구사항
- **CPU**: 4코어 이상 (권장: 8코어)
- **RAM**: 8GB 이상 (권장: 16GB)
- **저장공간**: 10GB 이상 (PDF 파일 + 벡터 DB + 캐시)
- **네트워크**: 안정적인 인터넷 연결 (임베딩 모델 다운로드용)

### 소프트웨어 요구사항
- **OS**: Windows 10/11, Linux (Ubuntu 18.04+), macOS
- **Python**: 3.8 이상 (권장: 3.9+)
- **브라우저**: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+

## 📦 배포 단계

### 1단계: 환경 준비
```bash
# Python 가상환경 생성
python -m venv venv

# 가상환경 활성화 (Windows)
venv\Scripts\activate

# 가상환경 활성화 (Linux/macOS)
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt
```

### 2단계: 문서 데이터 준비
```bash
# PDF 파일들이 올바른 폴더에 있는지 확인
# 도로설계요령(2020)/ 폴더에 5개 파일
# 실무지침(2020)/ 폴더에 10개 파일

# 벡터 데이터베이스 생성 (처음 배포시만)
python process_documents_auto.py
```

### 3단계: 시스템 시작
```bash
# 방법 1: 배치 파일 사용 (Windows)
run_full_system.bat

# 방법 2: 수동 실행
# 터미널 1: FastAPI 서버 시작
uvicorn fastapi_server:app --host 0.0.0.0 --port 8080 --reload

# 터미널 2: 웹 서버 시작 (HTML 파일 제공용)
python -m http.server 5500
```

### 4단계: 접속 확인
- **프론트엔드**: http://localhost:5500/innovative_search_app.html
- **API 문서**: http://localhost:8080/docs
- **헬스체크**: http://localhost:8080/health

## 🌐 프로덕션 배포 옵션

### 옵션 1: 로컬 서버 배포
```bash
# Windows 서비스로 등록
sc create "RoadSearchAPI" binPath="C:\path\to\venv\Scripts\python.exe C:\path\to\fastapi_server.py" start=auto

# 또는 작업 스케줄러로 등록하여 부팅시 자동 시작
```

### 옵션 2: 클라우드 배포 (AWS/Azure/GCP)
```bash
# Docker 컨테이너화
docker build -t road-search-system .
docker run -p 8080:8080 -p 5500:5500 road-search-system

# 또는 서버리스 배포 (AWS Lambda + API Gateway)
```

### 옵션 3: 웹 호스팅 배포
```bash
# Heroku, Vercel, Netlify 등 사용
# FastAPI 백엔드와 정적 HTML 프론트엔드 분리 배포
```

## 🔒 보안 고려사항

### 프로덕션 설정
```python
# fastapi_server.py 수정 필요
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["GET", "POST"],  # 필요한 메서드만 허용
    allow_headers=["*"],
)
```

### 환경 변수 설정
```bash
# .env 파일 생성
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8080
CORS_ORIGINS=https://yourdomain.com
DEBUG=False
```

## 📊 모니터링 및 유지보수

### 로그 관리
- **API 로그**: `fastapi_server.log`
- **문서 처리 로그**: `document_processing.log`
- **에러 로그**: 콘솔 출력 + 파일 로깅

### 성능 모니터링
- **메모리 사용량**: 벡터 DB 로드 상태 확인
- **응답 시간**: API 엔드포인트별 성능 측정
- **캐시 효율성**: 이미지 캐시 적중률 모니터링

### 정기 유지보수
- **주간**: 로그 파일 정리
- **월간**: 벡터 DB 백업
- **분기**: 의존성 업데이트 검토

## 🚨 트러블슈팅

### 일반적인 문제들
1. **포트 충돌**: 8080, 5500 포트가 사용 중인 경우
2. **메모리 부족**: 벡터 DB 로드 실패
3. **PDF 파일 누락**: 문서 폴더에 파일이 없는 경우
4. **권한 문제**: 파일 읽기/쓰기 권한 부족

### 해결 방법
```bash
# 포트 확인
netstat -an | findstr :8080
netstat -an | findstr :5500

# 메모리 사용량 확인
python -c "import psutil; print(f'Memory: {psutil.virtual_memory().percent}%')"

# 파일 권한 확인
ls -la "도로설계요령(2020)/"
ls -la "실무지침(2020)/"
```

## 📞 지원 및 연락처

### 기술 지원
- **문서**: 이 배포 가이드 참조
- **이슈 트래킹**: GitHub Issues 사용
- **로그 분석**: `document_processing.log` 파일 확인

### 업데이트 정보
- **버전**: v1.0.0
- **최종 업데이트**: 2024년 12월
- **호환성**: Python 3.8+, FastAPI 0.68+

---

## 🎯 배포 체크리스트

- [ ] Python 환경 설정 완료
- [ ] 의존성 설치 완료
- [ ] PDF 파일 준비 완료
- [ ] 벡터 데이터베이스 생성 완료
- [ ] FastAPI 서버 실행 확인
- [ ] 웹 서버 실행 확인
- [ ] 브라우저 접속 테스트 완료
- [ ] 검색 기능 테스트 완료
- [ ] PDF 뷰어 기능 테스트 완료
- [ ] 하이라이트 기능 테스트 완료
- [ ] 보안 설정 적용 완료
- [ ] 모니터링 설정 완료

**배포 완료! 🎉**

# 🛣️ Road Design Search Engine

AI-powered Korean Road Design Document Search System

## 📋 프로젝트 개요

도로설계요령(2020) 및 실무지침(2020) 문서를 AI로 검색할 수 있는 시스템입니다.

### ✨ 주요 기능

- **🔍 다중 검색 모드**: 키워드 검색, 벡터 검색, 하이브리드 검색
- **📊 고급 검색 옵션**: 문장 단위/글자 단위 추출, 키워드 점수 계산
- **📁 문서 범위 필터**: 전체, 도로설계요령, 실무지침 선택 검색
- **📄 PDF 뷰어**: 원본 PDF 및 키워드 하이라이트 보기
- **🎯 정확한 매칭**: 키워드 기반 정밀 검색 및 점수 계산

## 🚀 빠른 시작

### 로컬 실행
```bash
# 의존성 설치
pip install -r requirements_production.txt

# 문서 처리 (처음만)
python process_documents_auto.py

# 시스템 시작
start_production.bat  # Windows
./start_production.sh # Linux/macOS
```

### 웹 배포
```bash
# Railway + Vercel 배포
# 자세한 내용은 VERCEL_RAILWAY_DEPLOY.md 참조
```

## 📊 문서 정보

### 도로설계요령(2020) - 5개 파일, 3,871페이지
- 제1권 도로계획및 구조.pdf (621페이지)
- 제2권 토공 및 배수.pdf (761페이지)
- 제3권 교량.pdf (947페이지)
- 제4권 터널.pdf (751페이지)
- 제5권 포장 도로안전 부대시설 및 환경.pdf (791페이지)

### 실무지침(2020) - 10개 파일, 563페이지
- 0-간지 -편집.pdf (23페이지)
- 1-목차.pdf (4페이지)
- 2설계행정-327ok.pdf (223페이지)
- 3 교통 및 기하구조-327ok.pdf (20페이지)
- 4토공 및 배수공-편집중.pdf (66페이지)
- 5구조물공-편집중-ok.pdf (50페이지)
- 6포장공-편집.pdf (70페이지)
- 7터널공-편집ok.pdf (43페이지)
- 8 부대공 -편집.pdf (6페이지)
- 9기타-편집.pdf (52페이지)

## 🔧 기술 스택

- **Backend**: FastAPI, Python
- **Frontend**: HTML, CSS, JavaScript
- **AI/ML**: Sentence Transformers, FAISS
- **Database**: Vector Database (FAISS)
- **Deployment**: Railway, Vercel

## 📚 문서

- [배포 가이드](DEPLOYMENT_GUIDE.md)
- [Vercel + Railway 배포](VERCEL_RAILWAY_DEPLOY.md)
- [단계별 배포 가이드](STEP_BY_STEP_DEPLOY.md)
- [버전 관리 가이드](VERSION_CONTROL_GUIDE.md)

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

## 📞 연락처

프로젝트 링크: [https://github.com/strustar/road-design-search-engine](https://github.com/strustar/road-design-search-engine)

---

**버전**: v1.0.0  
**최종 업데이트**: 2024년 12월

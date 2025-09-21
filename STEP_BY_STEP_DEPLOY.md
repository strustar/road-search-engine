# 🚀 단계별 배포 가이드

## 📚 1단계: Git & GitHub 설정 (완료)

### ✅ 완료된 작업:
- [x] Git 초기화
- [x] .gitignore 생성
- [x] 첫 번째 커밋
- [x] GitHub 저장소 연결

### 🔄 코드 변경 시 워크플로우:
```bash
# 1. 코드 수정
# 2. 변경사항 확인
git status

# 3. 변경된 파일 추가
git add .

# 4. 커밋
git commit -m "변경사항 설명"

# 5. GitHub에 푸시 (자동 배포 트리거)
git push origin main
```

## 🚂 2단계: Railway 백엔드 배포

### **Railway 계정 생성:**
1. https://railway.app/ 접속
2. "Start a New Project" 클릭
3. GitHub 계정으로 로그인
4. "Deploy from GitHub repo" 선택

### **프로젝트 배포:**
1. 생성한 저장소 선택
2. "Deploy Now" 클릭
3. 자동 빌드 시작 (3-5분 소요)

### **환경 변수 설정:**
Railway 대시보드 → Settings → Variables에서 추가:
```
PYTHON_VERSION=3.9
PORT=8080
```

### **배포 확인:**
- Railway 도메인: `https://your-app-name.railway.app`
- 헬스체크: `https://your-app-name.railway.app/health`

## 🌐 3단계: Vercel 프론트엔드 배포

### **Vercel 계정 생성:**
1. https://vercel.com/ 접속
2. "Sign up" 클릭
3. GitHub 계정으로 로그인

### **프로젝트 배포:**
1. "New Project" 클릭
2. GitHub 저장소 선택
3. Framework: "Other" 선택
4. Build Command: (비워둠)
5. Output Directory: `.` (현재 디렉토리)
6. "Deploy" 클릭

### **환경 변수 설정:**
Vercel 대시보드 → Settings → Environment Variables에서 추가:
```
API_URL=https://your-app-name.railway.app
```

### **프론트엔드 코드 수정:**
`innovative_search_app.html`에서 Railway URL로 변경:
```javascript
const API_BASE_URL = window.location.hostname === 'localhost' 
    ? 'http://localhost:8080' 
    : 'https://your-app-name.railway.app';
```

## 📁 4단계: 파일 저장소 설정

### **옵션 1: Railway 내부 저장소 (테스트용)**
- PDF 파일들을 Railway 컨테이너에 직접 업로드
- 휘발성 (컨테이너 재시작 시 삭제 가능)

### **옵션 2: 외부 클라우드 저장소 (권장)**
- AWS S3, Google Cloud Storage, Cloudinary 등
- 안정적이고 확장 가능

## 🔧 5단계: 배포 후 설정

### **도메인 연결:**
- Vercel: Custom domain 설정
- Railway: Custom domain 설정
- SSL 인증서 자동 발급

### **모니터링 설정:**
- Vercel Analytics 활성화
- Railway Metrics 확인
- Uptime Robot으로 가동률 모니터링

## 💰 비용 예상

| 서비스 | 무료 티어 | 유료 플랜 |
|--------|-----------|-----------|
| Vercel | 무제한 | $20/월 |
| Railway | $5 크레딧 | $5/월 |
| **총 비용** | **무료** | **$25/월** |

## 🚨 주의사항

### **Railway 제약사항:**
- 파일 저장: 휘발성
- 메모리: 1GB 제한
- CPU: 제한적

### **Vercel 제약사항:**
- 파일 크기: 50MB 제한
- 실행 시간: 10초 제한

## 🔄 버전 업데이트 과정

### **로컬 → GitHub → 자동 배포:**
```bash
# 1. 로컬에서 코드 수정
# 2. 변경사항 커밋
git add .
git commit -m "feat: 새로운 기능 추가"

# 3. GitHub에 푸시
git push origin main

# 4. 자동 배포 확인
# - Vercel: 2-3분 소요
# - Railway: 3-5분 소요
```

### **배포 상태 확인:**
- Vercel 대시보드에서 확인
- Railway 대시보드에서 확인
- 로그 확인으로 오류 디버깅

## 🎯 최종 접속 정보

- **프론트엔드**: https://your-project.vercel.app
- **백엔드 API**: https://your-app.railway.app
- **API 문서**: https://your-app.railway.app/docs
- **헬스체크**: https://your-app.railway.app/health

---

## 💡 핵심 포인트

1. **GitHub 푸시 = 자동 배포**
2. **환경 변수 설정 중요**
3. **파일 저장소 분리 고려**
4. **모니터링으로 문제 조기 발견**
5. **무료 티어로 시작, 필요시 확장**

**GitHub만 잘 사용하면 배포는 자동! 🚀**

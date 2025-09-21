# 🚀 Vercel + Railway 배포 가이드

## 📋 개요
- **프론트엔드**: Vercel (무료)
- **백엔드**: Railway (무료 티어)
- **파일 저장**: Railway 또는 외부 스토리지

## 🔧 사전 준비

### 1️⃣ GitHub 저장소 생성
```bash
# 1. GitHub에서 새 저장소 생성
# 2. 로컬에서 초기화
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/your-username/road-search-system.git
git push -u origin main
```

### 2️⃣ Railway 계정 생성
- https://railway.app/ 접속
- GitHub 계정으로 로그인

### 3️⃣ Vercel 계정 생성
- https://vercel.com/ 접속
- GitHub 계정으로 로그인

## 🚀 1단계: Railway 백엔드 배포

### **Railway 프로젝트 생성**
```bash
# 1. Railway 대시보드에서 "New Project" 클릭
# 2. "Deploy from GitHub repo" 선택
# 3. 생성한 저장소 선택
# 4. 자동 배포 시작
```

### **환경 변수 설정**
Railway 대시보드에서 다음 환경 변수 추가:
```bash
PYTHON_VERSION=3.9
PORT=8080
```

### **배포 확인**
```bash
# Railway에서 제공하는 도메인 확인
# 예: https://your-app-name.railway.app
# 헬스체크: https://your-app-name.railway.app/health
```

## 🌐 2단계: Vercel 프론트엔드 배포

### **Vercel 프로젝트 생성**
```bash
# 1. Vercel 대시보드에서 "New Project" 클릭
# 2. GitHub 저장소 선택
# 3. Framework: Other 선택
# 4. Build Command: (비워둠)
# 5. Output Directory: . (현재 디렉토리)
# 6. Deploy 클릭
```

### **환경 변수 설정**
Vercel 대시보드에서 환경 변수 추가:
```bash
API_URL=https://your-app-name.railway.app
```

### **프론트엔드 코드 수정**
`innovative_search_app.html`에서 Railway URL로 변경:
```javascript
const API_BASE_URL = window.location.hostname === 'localhost' 
    ? 'http://localhost:8080' 
    : 'https://your-app-name.railway.app';
```

## 📁 3단계: 파일 저장소 설정

### **옵션 1: Railway 내부 저장소 (간단)**
```bash
# Railway에서 파일 업로드
# - PDF 파일들을 Railway 컨테이너에 직접 업로드
# - 휘발성 (컨테이너 재시작 시 삭제 가능)
```

### **옵션 2: 외부 클라우드 저장소 (권장)**
```bash
# AWS S3, Google Cloud Storage, Cloudinary 등 사용
# - 안정적인 파일 저장
# - CDN 지원
# - 확장성 좋음
```

## 🔧 4단계: 배포 후 설정

### **도메인 연결**
```bash
# Vercel
# 1. Settings → Domains
# 2. Custom domain 추가
# 3. DNS 설정

# Railway
# 1. Settings → Domains
# 2. Custom domain 추가
# 3. SSL 인증서 자동 발급
```

### **모니터링 설정**
```bash
# Vercel Analytics 활성화
# Railway Metrics 확인
# Uptime Robot으로 가동률 모니터링
```

## 💰 비용 예상

| 서비스 | 무료 티어 | 유료 플랜 |
|--------|-----------|-----------|
| **Vercel** | 무제한 | $20/월 |
| **Railway** | $5 크레딧 | $5/월 |
| **총 비용** | **무료** | **$25/월** |

## 🚨 주의사항

### **Railway 제약사항**
- ❌ **파일 저장**: 휘발성 (재시작 시 삭제)
- ❌ **메모리**: 1GB 제한
- ❌ **CPU**: 제한적
- ❌ **저장공간**: 1GB 제한

### **Vercel 제약사항**
- ❌ **파일 크기**: 50MB 제한
- ❌ **실행 시간**: 10초 제한
- ❌ **백엔드**: 함수형만 지원

## 🔄 5단계: 확장성 개선

### **파일 저장소 분리**
```python
# fastapi_server.py 수정
import boto3
from botocore.exceptions import NoCredentialsError

def get_file_from_s3(bucket_name, file_key):
    s3 = boto3.client('s3')
    try:
        response = s3.get_object(Bucket=bucket_name, Key=file_key)
        return response['Body'].read()
    except NoCredentialsError:
        print("AWS credentials not available")
        return None
```

### **데이터베이스 분리**
```bash
# Railway에서 PostgreSQL 추가
# 1. Railway 대시보드에서 "New" → "Database" → "PostgreSQL"
# 2. 환경 변수에 DATABASE_URL 추가
# 3. 벡터 데이터베이스를 PostgreSQL로 이동
```

## 📊 성능 최적화

### **캐싱 전략**
```python
# Redis 캐싱 추가
import redis
import json

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def cache_search_results(query, results):
    redis_client.setex(
        f"search:{query}", 
        3600,  # 1시간 캐시
        json.dumps(results)
    )
```

### **CDN 설정**
```bash
# Vercel에서 자동 CDN 제공
# Railway에서 CloudFront 연결
# 이미지 최적화 및 압축
```

## 🎯 배포 체크리스트

- [ ] GitHub 저장소 생성 완료
- [ ] Railway 백엔드 배포 완료
- [ ] Vercel 프론트엔드 배포 완료
- [ ] 환경 변수 설정 완료
- [ ] API URL 수정 완료
- [ ] 파일 저장소 설정 완료
- [ ] 도메인 연결 완료
- [ ] 모니터링 설정 완료

## 🚀 최종 접속 정보

- **프론트엔드**: https://your-project.vercel.app
- **백엔드 API**: https://your-app.railway.app
- **API 문서**: https://your-app.railway.app/docs
- **헬스체크**: https://your-app.railway.app/health

---

## 💡 추천 배포 순서

1. **GitHub 저장소 생성**
2. **Railway 백엔드 배포**
3. **Vercel 프론트엔드 배포**
4. **환경 변수 설정**
5. **테스트 및 확인**

**Vercel + Railway 조합으로 무료로 시작하고 필요시 확장! 🎉**

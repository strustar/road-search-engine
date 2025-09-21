# 📚 Git & GitHub 버전 관리 가이드

## 🔄 기본 워크플로우

### **1. 코드 수정 후 GitHub 업데이트**
```bash
# 현재 상태 확인
git status

# 변경된 파일들 추가
git add .

# 커밋 (변경사항 저장)
git commit -m "feat: API URL 동적 설정 추가"

# GitHub에 푸시
git push origin main
```

### **2. 자동 배포 확인**
```bash
# Vercel: https://vercel.com/dashboard
# Railway: https://railway.app/dashboard
# 배포 상태 자동 확인
```

## 📋 커밋 메시지 규칙

### **커밋 타입**
- `feat`: 새로운 기능
- `fix`: 버그 수정
- `docs`: 문서 수정
- `style`: 코드 스타일 변경
- `refactor`: 코드 리팩토링
- `test`: 테스트 추가/수정
- `chore`: 빌드/설정 변경

### **예시**
```bash
git commit -m "feat: 키워드 점수 계산 기능 추가"
git commit -m "fix: PDF 하이라이트 오류 수정"
git commit -m "docs: 배포 가이드 업데이트"
git commit -m "style: UI 레이아웃 개선"
```

## 🌿 브랜치 전략

### **메인 브랜치**
- `main`: 프로덕션 배포용
- `develop`: 개발용
- `feature/기능명`: 새 기능 개발용

### **브랜치 사용 예시**
```bash
# 새 기능 개발
git checkout -b feature/search-optimization
# 코드 수정...
git add .
git commit -m "feat: 검색 성능 최적화"
git push origin feature/search-optimization

# GitHub에서 Pull Request 생성
# 코드 리뷰 후 main 브랜치에 병합
```

## 🔄 버전 업데이트 과정

### **로컬 → GitHub → 자동 배포**
```bash
# 1. 로컬에서 코드 수정
# 2. 변경사항 커밋
git add .
git commit -m "feat: 새로운 검색 옵션 추가"

# 3. GitHub에 푸시
git push origin main

# 4. 자동 배포 확인
# - Vercel: 2-3분 소요
# - Railway: 3-5분 소요
```

### **배포 상태 확인**
```bash
# Vercel 대시보드에서 확인
# Railway 대시보드에서 확인
# 로그 확인으로 오류 디버깅
```

## 🚨 문제 해결

### **배포 실패 시**
```bash
# 1. 로그 확인
# Vercel: Functions 탭에서 로그 확인
# Railway: Deployments 탭에서 로그 확인

# 2. 환경 변수 확인
# API_URL, DATABASE_URL 등

# 3. 의존성 확인
# requirements.txt, package.json

# 4. 재배포
git commit --allow-empty -m "trigger redeploy"
git push origin main
```

### **롤백 방법**
```bash
# 이전 커밋으로 되돌리기
git log --oneline
git reset --hard <이전-커밋-해시>
git push origin main --force
```

## 📊 배포 모니터링

### **성능 모니터링**
```bash
# Vercel Analytics
# - 페이지 뷰
# - 응답 시간
# - 오류율

# Railway Metrics
# - CPU 사용률
# - 메모리 사용률
# - 네트워크 트래픽
```

### **알림 설정**
```bash
# Vercel: 이메일 알림
# Railway: Slack/Discord 연동
# Uptime Robot: 서비스 가동률 모니터링
```

## 🔧 환경별 배포

### **개발 환경**
```bash
# 로컬 개발
python fastapi_server.py

# 개발 서버
git checkout develop
git push origin develop
```

### **스테이징 환경**
```bash
# 테스트용 배포
git checkout staging
git push origin staging
```

### **프로덕션 환경**
```bash
# 실제 서비스 배포
git checkout main
git push origin main
```

## 📝 배포 체크리스트

### **배포 전 확인사항**
- [ ] 코드 테스트 완료
- [ ] 환경 변수 설정 확인
- [ ] 의존성 업데이트 확인
- [ ] 데이터베이스 마이그레이션 (필요시)
- [ ] 백업 완료

### **배포 후 확인사항**
- [ ] 서비스 정상 작동
- [ ] API 엔드포인트 테스트
- [ ] 데이터베이스 연결 확인
- [ ] 모니터링 설정 확인

---

## 💡 핵심 포인트

1. **GitHub 푸시 = 자동 배포**
2. **커밋 메시지는 명확하게**
3. **브랜치 전략으로 안전한 개발**
4. **모니터링으로 문제 조기 발견**
5. **롤백 계획 항상 준비**

**GitHub만 잘 사용하면 배포는 자동! 🚀**

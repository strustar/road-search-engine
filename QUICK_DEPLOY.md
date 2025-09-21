# 🚀 빠른 웹 배포 가이드

## 🎯 가장 쉬운 배포 방법들

### 1️⃣ **Docker 배포 (추천)**

#### **Windows에서:**
```cmd
# 1. Docker Desktop 설치 (https://docs.docker.com/desktop/windows/install/)

# 2. 프로젝트 폴더에서 실행
deploy.bat

# 3. 접속
# http://localhost (프론트엔드)
# http://localhost:8080/docs (API 문서)
```

#### **Linux/macOS에서:**
```bash
# 1. Docker 설치
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# 2. 프로젝트 폴더에서 실행
./deploy.sh

# 3. 접속
# http://localhost (프론트엔드)
# http://localhost:8080/docs (API 문서)
```

### 2️⃣ **VPS 서버 배포**

#### **DigitalOcean Droplet (월 $24)**
```bash
# 1. Ubuntu 20.04 LTS 서버 생성
# 2. SSH 접속
ssh root@your-server-ip

# 3. Docker 설치
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# 4. 프로젝트 업로드
scp -r ./Ex7O3 root@your-server-ip:/root/
ssh root@your-server-ip
cd /root/Ex7O3

# 5. 배포 실행
./deploy.sh

# 6. 도메인 연결 (선택사항)
# A 레코드: your-domain.com → your-server-ip
```

### 3️⃣ **클라우드 플랫폼 배포**

#### **Railway (간단함)**
```bash
# 1. Railway 계정 생성 (https://railway.app/)
# 2. GitHub에 프로젝트 푸시
# 3. Railway에서 GitHub 연결
# 4. 자동 배포 완료
```

#### **Heroku (안정적)**
```bash
# 1. Heroku CLI 설치
# 2. 로그인
heroku login

# 3. 앱 생성
heroku create your-app-name

# 4. 배포
git push heroku main
```

## 🔧 로컬 테스트

### **Docker 없이 테스트:**
```cmd
# Windows
start_production.bat

# Linux/macOS
./start_production.sh

# 접속: http://localhost:8080
```

## 📊 서버 사양 권장사항

### **최소 사양:**
- **CPU**: 2 코어
- **RAM**: 4GB
- **저장공간**: 20GB
- **네트워크**: 1Gbps

### **권장 사양:**
- **CPU**: 4 코어
- **RAM**: 8GB
- **저장공간**: 50GB
- **네트워크**: 1Gbps

## 💰 비용 비교

| 플랫폼 | 월 비용 | 특징 |
|--------|---------|------|
| **DigitalOcean** | $24 | 안정적, 관리 쉬움 |
| **Linode** | $20 | 가성비 좋음 |
| **Vultr** | $24 | 빠른 성능 |
| **Railway** | $5-20 | 사용량 기반 |
| **Heroku** | $7-25 | 관리형 서비스 |

## 🚨 주의사항

### **배포 전 체크리스트:**
- [ ] Docker 설치 완료
- [ ] 벡터 데이터베이스 생성 완료
- [ ] PDF 파일들 업로드 완료
- [ ] 포트 80, 8080 사용 가능
- [ ] 도메인 설정 (선택사항)

### **보안 설정:**
```bash
# 방화벽 설정
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS
sudo ufw enable
```

## 🔍 문제 해결

### **일반적인 문제들:**
1. **포트 충돌**: 다른 서비스가 80, 8080 포트 사용
2. **메모리 부족**: 서버 사양 업그레이드 필요
3. **Docker 오류**: Docker 재시작 또는 재설치

### **로그 확인:**
```bash
# Docker 로그
docker-compose logs -f

# 시스템 로그
journalctl -u docker
```

## 🎉 배포 완료 후

### **접속 정보:**
- **프론트엔드**: http://your-domain.com
- **API 문서**: http://your-domain.com:8080/docs
- **헬스체크**: http://your-domain.com:8080/health

### **관리 명령어:**
```bash
# 서비스 중지
docker-compose down

# 서비스 재시작
docker-compose restart

# 로그 확인
docker-compose logs -f

# 업데이트
docker-compose pull
docker-compose up -d
```

---

## 🚀 추천 배포 순서

1. **로컬 테스트** → `start_production.bat` 실행
2. **Docker 테스트** → `deploy.bat` 실행  
3. **VPS 배포** → DigitalOcean + Docker
4. **도메인 연결** → SSL 인증서 설정
5. **모니터링 설정** → Uptime Robot 등

**가장 쉬운 방법: Docker + VPS 배포! 🎯**

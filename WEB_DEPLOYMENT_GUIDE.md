# 🌐 웹 배포 가이드 - 도로설계 문서 검색 시스템

## 🚀 배포 옵션들

### 1️⃣ **클라우드 서버 배포 (권장)**

#### **AWS EC2 / Azure VM / GCP Compute Engine**
```bash
# 서버 준비
sudo apt update && sudo apt upgrade -y
sudo apt install python3 python3-pip nginx -y

# 프로젝트 업로드
scp -r ./Ex7O3 user@your-server-ip:/home/user/

# 의존성 설치
cd /home/user/Ex7O3
pip3 install -r requirements_production.txt

# 문서 처리 (한 번만)
python3 process_documents_auto.py

# 시스템 서비스 등록
sudo systemctl enable your-app
sudo systemctl start your-app
```

#### **Docker 배포 (가장 쉬움)**
```dockerfile
# Dockerfile 생성
FROM python:3.9-slim

WORKDIR /app
COPY requirements_production.txt .
RUN pip install -r requirements_production.txt

COPY . .

EXPOSE 8080
CMD ["uvicorn", "fastapi_server:app", "--host", "0.0.0.0", "--port", "8080"]
```

### 2️⃣ **서버리스 배포**

#### **Vercel (프론트엔드) + Railway (백엔드)**
```bash
# 백엔드 - Railway
railway login
railway init
railway up

# 프론트엔드 - Vercel
vercel --prod
```

#### **Heroku (풀스택)**
```bash
# Heroku CLI 설치 후
heroku create your-app-name
git push heroku main
```

### 3️⃣ **VPS 배포 (가성비 좋음)**

#### **DigitalOcean / Linode / Vultr**
```bash
# Ubuntu 20.04 LTS 서버
# 4GB RAM, 2 CPU 코어 권장

# 1. 서버 설정
sudo apt update
sudo apt install python3 python3-pip nginx supervisor -y

# 2. 프로젝트 업로드
git clone your-repo
# 또는 scp로 파일 전송

# 3. 가상환경 설정
python3 -m venv venv
source venv/bin/activate
pip install -r requirements_production.txt

# 4. 문서 처리
python3 process_documents_auto.py

# 5. Nginx 설정
sudo nano /etc/nginx/sites-available/road-search
```

## 🔧 상세 배포 단계 (VPS 예시)

### **1단계: 서버 준비**
```bash
# Ubuntu 20.04 LTS 서버 준비
# 최소 사양: 4GB RAM, 2 CPU, 20GB SSD

# 기본 패키지 설치
sudo apt update && sudo apt upgrade -y
sudo apt install python3 python3-pip python3-venv nginx supervisor git -y
```

### **2단계: 프로젝트 배포**
```bash
# 프로젝트 업로드 (Git 사용)
git clone https://github.com/your-username/road-search-system.git
cd road-search-system

# 또는 직접 파일 업로드
# scp -r ./Ex7O3 user@server-ip:/home/user/
```

### **3단계: Python 환경 설정**
```bash
# 가상환경 생성
python3 -m venv venv
source venv/bin/activate

# 의존성 설치
pip install -r requirements_production.txt

# 문서 처리 (한 번만 실행)
python3 process_documents_auto.py
```

### **4단계: Nginx 설정**
```nginx
# /etc/nginx/sites-available/road-search
server {
    listen 80;
    server_name your-domain.com;

    # 정적 파일 서빙 (HTML, CSS, JS)
    location / {
        root /home/user/road-search-system;
        try_files $uri $uri/ /innovative_search_app.html;
    }

    # API 프록시
    location /api/ {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # 헬스체크
    location /health {
        proxy_pass http://127.0.0.1:8080;
    }
}
```

### **5단계: Supervisor 설정**
```ini
# /etc/supervisor/conf.d/road-search.conf
[program:road-search-api]
command=/home/user/road-search-system/venv/bin/uvicorn fastapi_server:app --host 127.0.0.1 --port 8080
directory=/home/user/road-search-system
user=user
autostart=true
autorestart=true
stderr_logfile=/var/log/road-search-api.err.log
stdout_logfile=/var/log/road-search-api.out.log
```

### **6단계: 서비스 시작**
```bash
# Nginx 설정 활성화
sudo ln -s /etc/nginx/sites-available/road-search /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Supervisor 설정 적용
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start road-search-api

# 서비스 상태 확인
sudo supervisorctl status
```

## 🔒 SSL 인증서 설정 (HTTPS)

### **Let's Encrypt 사용**
```bash
# Certbot 설치
sudo apt install certbot python3-certbot-nginx -y

# SSL 인증서 발급
sudo certbot --nginx -d your-domain.com

# 자동 갱신 설정
sudo crontab -e
# 추가: 0 12 * * * /usr/bin/certbot renew --quiet
```

## 📊 모니터링 설정

### **시스템 모니터링**
```bash
# htop 설치
sudo apt install htop -y

# 로그 모니터링
tail -f /var/log/road-search-api.out.log
tail -f /var/log/nginx/access.log
```

### **백업 설정**
```bash
# 백업 스크립트
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
tar -czf backup_$DATE.tar.gz /home/user/road-search-system
# S3나 다른 클라우드 스토리지로 업로드
```

## 💰 예상 비용

### **VPS (권장)**
- **DigitalOcean**: $24/월 (4GB RAM, 2 CPU)
- **Linode**: $20/월 (4GB RAM, 2 CPU)
- **Vultr**: $24/월 (4GB RAM, 2 CPU)

### **클라우드 서버**
- **AWS EC2 t3.medium**: $30-50/월
- **Azure B2s**: $30-40/월
- **GCP e2-standard-2**: $25-35/월

### **서버리스**
- **Vercel + Railway**: $5-20/월 (사용량에 따라)
- **Heroku**: $7-25/월

## 🚀 빠른 배포 (Docker)

### **Docker Compose 설정**
```yaml
# docker-compose.yml
version: '3.8'
services:
  web:
    build: .
    ports:
      - "80:8080"
    volumes:
      - ./vector_store:/app/vector_store
      - ./image_cache:/app/image_cache
      - ./도로설계요령(2020):/app/도로설계요령(2020)
      - ./실무지침(2020):/app/실무지침(2020)
    restart: unless-stopped
```

### **배포 명령어**
```bash
# Docker 이미지 빌드
docker build -t road-search-system .

# 컨테이너 실행
docker run -d -p 80:8080 --name road-search road-search-system

# 또는 Docker Compose 사용
docker-compose up -d
```

## 🔧 문제 해결

### **일반적인 문제들**
1. **포트 충돌**: 80, 8080 포트 확인
2. **권한 문제**: 파일 권한 설정
3. **메모리 부족**: 서버 사양 업그레이드
4. **SSL 오류**: 인증서 갱신

### **성능 최적화**
```bash
# Nginx 캐싱 설정
location ~* \.(jpg|jpeg|png|gif|ico|css|js)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}

# Gzip 압축
gzip on;
gzip_types text/plain text/css application/json application/javascript;
```

## 📞 지원 및 유지보수

### **정기 작업**
- **주간**: 로그 확인, 성능 모니터링
- **월간**: 보안 업데이트, 백업 확인
- **분기**: 의존성 업데이트, 성능 튜닝

### **모니터링 도구**
- **Uptime Robot**: 서비스 가동률 모니터링
- **Google Analytics**: 사용자 통계
- **Server Status**: 서버 상태 모니터링

---

## 🎯 배포 체크리스트

- [ ] 서버 준비 완료
- [ ] 프로젝트 파일 업로드 완료
- [ ] Python 환경 설정 완료
- [ ] 의존성 설치 완료
- [ ] 문서 처리 완료
- [ ] Nginx 설정 완료
- [ ] SSL 인증서 설정 완료
- [ ] 도메인 연결 완료
- [ ] 모니터링 설정 완료
- [ ] 백업 설정 완료

**웹 배포 완료! 🌐**

**추천 배포 방법: VPS + Docker (가성비 최고)**

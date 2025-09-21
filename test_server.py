"""
Railway 배포 테스트용 간단한 FastAPI 서버
"""
from fastapi import FastAPI
from datetime import datetime

app = FastAPI()

@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "message": "Test server is running"
    }

@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {"message": "Hello World"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)

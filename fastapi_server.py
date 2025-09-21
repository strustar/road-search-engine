"""
FastAPI 기반 벡터 검색 API 서버
도로설계 문서 검색을 위한 RESTful API
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import numpy as np
from datetime import datetime
import uvicorn
import logging
import os
from urllib.parse import quote, unquote
import glob
import fitz  # PyMuPDF
import io
import re

# 로컬 모듈 import
# from rag.embedding_engine import KoreanEmbeddingEngine  # sentence-transformers 제거로 비활성화
# from rag.vector_database import VectorDatabase  # 임베딩 엔진 의존성으로 비활성화
from pdf_image_renderer import PDFImageRenderer

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI 앱 초기화
app = FastAPI(
    title="도로설계 문서 검색 API",
    description="한국어 도로설계 문서에 대한 벡터 기반 검색 API",
    version="1.0.0"
)

# CORS 설정 (프론트엔드 연동용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 전역 변수로 검색 엔진 관리
# embedding_engine = None  # 비활성화
# vector_db = None  # 비활성화
pdf_renderer = None

# ======================== 고급 텍스트 추출 및 스코어링 함수 ========================

def extract_text_by_characters(text: str, keywords: List[str], char_radius: int = 50) -> str:
    """
    청크 내에서 키워드가 포함된 글자 범위만 추출하는 함수
    
    Args:
        text: 원본 텍스트
        keywords: 검색할 키워드 리스트
        char_radius: 주변 글자 수 (기본 50자)
    
    Returns:
        키워드가 포함된 글자 범위의 추출된 텍스트
    """
    if not text or not keywords:
        return text[:500]  # 기본적으로 500자 제한
    
    # 키워드 위치 찾기
    keyword_positions = []
    text_lower = text.lower()
    
    for keyword in keywords:
        keyword_lower = keyword.lower()
        start = 0
        while True:
            pos = text_lower.find(keyword_lower, start)
            if pos == -1:
                break
            keyword_positions.append((pos, pos + len(keyword)))
            start = pos + 1
    
    if not keyword_positions:
        return text[:500]
    
    # 키워드 위치들을 기준으로 범위 계산
    start_pos = max(0, min(pos for pos, _ in keyword_positions) - char_radius)
    end_pos = min(len(text), max(pos for _, pos in keyword_positions) + char_radius)
    
    extracted = text[start_pos:end_pos]
    
    # 추출된 부분에서 키워드 포함 확인
    extracted_lower = extracted.lower()
    keyword_count = 0
    for keyword in keywords:
        if keyword.lower() in extracted_lower:
            keyword_count += 1
    
    # 키워드가 충분히 포함되지 않으면 범위 확장
    if keyword_count < len(keywords):
        # 더 넓은 범위로 재시도
        extended_radius = char_radius * 2
        start_pos = max(0, min(pos for pos, _ in keyword_positions) - extended_radius)
        end_pos = min(len(text), max(pos for _, pos in keyword_positions) + extended_radius)
        extracted = text[start_pos:end_pos]
    
    # 앞뒤에 생략 표시 추가
    if start_pos > 0:
        extracted = "..." + extracted
    if end_pos < len(text):
        extracted = extracted + "..."
    
    return extracted

def calculate_keyword_score(extracted_text: str, input_keywords: List[str]) -> float:
    """
    추출된 텍스트에서 입력 키워드들의 포함 비율을 계산하는 함수
    
    Args:
        extracted_text: 검증할 텍스트
        input_keywords: 사용자가 입력한 키워드 리스트
    
    Returns:
        키워드 포함 비율 (0.0 ~ 100.0, 소수점 첫째 자리까지)
    """
    if not extracted_text or not input_keywords:
        return 0.0
    
    extracted_lower = extracted_text.lower()
    found_keywords = 0
    
    for keyword in input_keywords:
        if keyword.lower() in extracted_lower:
            found_keywords += 1
    
    score = (found_keywords / len(input_keywords)) * 100
    return round(score, 1)

def extract_sentences_with_keywords(text: str, keywords: List[str], context_sentences: int = 0) -> str:
    """
    청크 내에서 키워드가 포함된 문장들만 추출하는 함수

    Args:
        text: 원본 텍스트
        keywords: 검색할 키워드 리스트
        context_sentences: 전후 문장 개수 (0-3)

    Returns:
        키워드가 포함된 문장들과 문맥이 포함된 텍스트
    """
    if not text or not keywords:
        return text

    # 1단계: 텍스트 정제 - 불필요한 공백과 줄바꿈 정리
    cleaned_text = re.sub(r'\s+', ' ', text.strip())

    # 2단계: 한국어 문장 분할 (개선된 패턴)
    sentence_pattern = r'(?<=[다음함됨슴며])\.(?=\s*[가-힣A-Z\n])|(?<=[!?])(?=\s*[가-힣A-Z\n])'
    sentences = re.split(sentence_pattern, cleaned_text)

    # 3단계: 문장 후처리 - 공백 정리 및 빈 문장 제거
    processed_sentences = []
    for sentence in sentences:
        sentence = re.sub(r'\s+', ' ', sentence.strip())
        if sentence and len(sentence) > 2:  # 한 글자 키워드를 위해 조건 완화
            processed_sentences.append(sentence)

    if not processed_sentences:
        return text

    # 4단계: 키워드가 포함된 문장들만 찾기
    keyword_sentences = []
    for i, sentence in enumerate(processed_sentences):
        sentence_lower = sentence.lower()
        for keyword in keywords:
            if keyword.lower() in sentence_lower:
                keyword_sentences.append((i, sentence))
                break  # 하나라도 키워드가 있으면 추가

    if not keyword_sentences:
        # 키워드가 포함된 문장이 없으면 전체 텍스트의 앞부분 반환
        return cleaned_text[:500] + "..." if len(cleaned_text) > 500 else cleaned_text

    # 5단계: 키워드가 포함된 문장들을 중심으로 전후 문맥 포함
    result_indices = set()
    for idx, _ in keyword_sentences:
        start = max(0, idx - context_sentences)
        end = min(len(processed_sentences), idx + context_sentences + 1)
        for i in range(start, end):
            result_indices.add(i)

    # 6단계: 결과 구성 - 연속된 인덱스 그룹화
    result_indices = sorted(list(result_indices))
    result_sentences = []

    for i, idx in enumerate(result_indices):
        # 인덱스 간격이 있으면 생략 표시 추가
        if i > 0 and idx > result_indices[i-1] + 1:
            result_sentences.append("...")
        result_sentences.append(processed_sentences[idx])

    # 7단계: 최종 결과 - 자연스러운 문장 연결
    result_text = " ".join(result_sentences)
    result_text = re.sub(r'\s+', ' ', result_text.strip())
    
    return result_text

# PDF 디렉토리 설정
PDF_DIRECTORIES = [
    "./도로설계요령(2020)",
    "./실무지침(2020)",
    "."  # 루트 디렉토리
]

# ======================== Pydantic 모델 정의 ========================

class SearchRequest(BaseModel):
    """검색 요청 모델"""
    query: str = Field(..., description="검색 쿼리", min_length=1)
    mode: str = Field("hybrid", description="검색 모드: vector, keyword, hybrid")
    max_results: int = Field(10, description="최대 결과 수", ge=1, le=100)
    similarity_threshold: float = Field(0.0, description="유사도 임계값", ge=0.0, le=1.0)
    vector_weight: float = Field(0.7, description="하이브리드 검색시 벡터 가중치", ge=0.0, le=1.0)
    keywords: Optional[List[str]] = Field(None, description="키워드 검색용 단어 리스트")
    sentence_context: int = Field(0, description="전후 문장 개수 (0-3)", ge=0, le=3)
    full_sentences: bool = Field(False, description="키워드 포함 문장 전체 표시")
    document_filter: str = Field("all", description="문서 필터: all, 도로설계요령, 실무지침")
    # 고급 검색 기능 추가
    granularity: str = Field("sentence", description="검색 단위: sentence, char")
    radius: int = Field(1, description="주변 범위: 문장(1-3), 글자(30-100)", ge=1, le=100)

class SearchResult(BaseModel):
    """검색 결과 모델"""
    rank: int
    score: float
    document: str
    metadata: Dict[str, Any]
    matched_keywords: Optional[List[str]] = None
    # 고급 검색 결과 필드 추가
    extracted_text: Optional[str] = None
    keyword_score: Optional[float] = None

class SearchResponse(BaseModel):
    """검색 응답 모델"""
    query: str
    mode: str
    total_results: int
    results: List[SearchResult]
    search_time_ms: float

class DatabaseStats(BaseModel):
    """데이터베이스 통계 모델"""
    total_documents: int
    dimension: int
    index_type: str
    total_searches: int
    last_search: Optional[str]

class ImageRequest(BaseModel):
    """이미지 요청 모델"""
    file_path: str = Field(..., description="PDF 파일 경로")
    page_num: int = Field(..., description="페이지 번호 (0부터 시작)", ge=0)
    keywords: Optional[List[str]] = Field(None, description="하이라이트할 키워드들")
    crop_to_keywords: bool = Field(False, description="키워드 영역만 크롭할지 여부")
    highlight_color: str = Field("rgba(255, 255, 0, 128)", description="하이라이트 색상")

class ImageResponse(BaseModel):
    """이미지 응답 모델"""
    success: bool
    message: str
    image_b64: Optional[str] = None
    pdf_info: Optional[Dict[str, Any]] = None

# ======================== 초기화 함수 ========================

@app.on_event("startup")
async def startup_event():
    """서버 시작시 벡터 DB 및 PDF 렌더러 로드"""
    global pdf_renderer

    try:
        logger.info("벡터 검색 시스템 초기화 중...")

        # 임베딩 엔진 및 벡터 DB 비활성화 (sentence-transformers 제거로 인해)
        logger.info("벡터 검색 기능 비활성화 (키워드 검색만 지원)")

        # PDF 이미지 렌더러 초기화
        pdf_renderer = PDFImageRenderer(
            pdf_directory=".",  # 현재 디렉토리에서 상대 경로 허용
            cache_directory="./image_cache",
            dpi=150
        )
        logger.info("PDF 이미지 렌더러 초기화 완료")

    except Exception as e:
        logger.error(f"초기화 실패: {e}")
        raise

# ======================== API 엔드포인트 ========================

@app.get("/", tags=["기본"])
async def root():
    """API 루트 엔드포인트"""
    return {
        "message": "도로설계 문서 검색 API",
        "version": "1.0.0",
        "endpoints": {
            "search": "/api/search",
            "stats": "/api/stats",
            "health": "/health"
        }
    }

@app.get("/health", tags=["기본"])
async def health_check():
    """헬스 체크 엔드포인트"""
    if vector_db is None or embedding_engine is None:
        raise HTTPException(status_code=503, detail="서비스 준비되지 않음")

    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "vector_db_loaded": vector_db.index.ntotal > 0,
        "embedding_engine_ready": embedding_engine.model is not None
    }

@app.post("/api/search", tags=["검색"])
async def search(request: SearchRequest):
    """
    문서 검색 API - 문서 필터링 기능 추가
    """
    if vector_db is None or embedding_engine is None:
        raise HTTPException(status_code=503, detail="검색 시스템이 준비되지 않았습니다")

    start_time = datetime.now()

    try:
        # 고급 검색 파라미터 로깅
        logger.info(f"Search received - Query: '{request.query}', Mode: '{request.mode}', Filter: '{request.document_filter}', Granularity: '{request.granularity}', Radius: {request.radius}")
        
        # 키워드 파싱 (최대 5개로 제한)
        input_keywords = request.keywords or request.query.split()
        if len(input_keywords) > 5:
            input_keywords = input_keywords[:5]
            logger.info(f"키워드 5개로 제한: {input_keywords}")
        
        # 필터링을 위해 더 많은 결과 요청
        # 키워드 검색의 경우 필터링 후에도 충분한 결과를 얻기 위해 더 많이 요청
        if request.mode == "keyword":
            # 키워드 검색은 필터링을 고려하여 더 많은 결과 요청
            search_k = max(200, request.max_results * 10)  # 최소 200개, 또는 요청 결과의 10배
        else:
            search_k = max(50, request.max_results * 3)  # 최소 50개, 또는 요청 결과의 3배

        if request.mode == "vector":
            query_embedding = embedding_engine.encode_query(request.query)
            results = vector_db.search(query_embedding, k=search_k, min_similarity=0.0)
        
        elif request.mode == "keyword":
            results = vector_db.keyword_search(input_keywords, match_all=False, k=search_k)
        
        else:  # hybrid
            query_embedding = embedding_engine.encode_query(request.query)
            results = vector_db.hybrid_search(
                query_embedding, input_keywords, k=search_k, vector_weight=request.vector_weight
            )

        # 필터링 로직 (메타데이터의 'category' 기준)
        if request.document_filter and request.document_filter != "all":
            initial_count = len(results)
            results = [
                r for r in results if r.get('metadata', {}).get('category') == request.document_filter
            ]
            logger.info(f"Filtered results for '{request.document_filter}': {initial_count} -> {len(results)}")

        # 최종 결과 수를 max_results에 맞춤
        final_results = results[:request.max_results]

        # 결과 포맷팅 - 고급 검색 기능 적용
        formatted_results = []

        for i, result in enumerate(final_results):
            score_key = 'final_score' if request.mode == 'hybrid' else ('similarity' if request.mode == 'vector' else 'match_score')
            original_document = result['document']
            
            # 고급 추출 로직 적용
            extracted_text = None
            keyword_score = None
            
            if request.mode in ['keyword', 'hybrid'] and input_keywords:
                # 청크 내에서 키워드가 포함된 부분만 추출
                if request.granularity == "sentence":
                    # 문장 단위 추출 - 키워드가 포함된 문장들만
                    extracted_text = extract_sentences_with_keywords(
                        original_document, input_keywords, request.radius
                    )
                elif request.granularity == "char":
                    # 글자 단위 추출 - 키워드 위치 기반으로 범위 추출
                    extracted_text = extract_text_by_characters(
                        original_document, input_keywords, request.radius
                    )
                
                # 추출된 부분에서만 키워드 스코어 계산
                if extracted_text and extracted_text != original_document:
                    keyword_score = calculate_keyword_score(extracted_text, input_keywords)
                    logger.info(f"Result {i+1}: Keyword score {keyword_score}% - extracted_text length: {len(extracted_text)} (original: {len(original_document)})")
                else:
                    # 추출되지 않았으면 전체 청크에서 점수 계산
                    keyword_score = calculate_keyword_score(original_document, input_keywords)
                    extracted_text = original_document[:500]  # 기본 표시
            
            # 기존 방식으로 fallback
            if not extracted_text:
                if (request.mode in ['keyword', 'hybrid'] and (request.full_sentences or request.sentence_context > 0)):
                    extracted_text = extract_sentences_with_keywords(
                        original_document, input_keywords, request.sentence_context
                    )
                else:
                    extracted_text = original_document[:500]

            formatted_results.append(SearchResult(
                rank=i + 1,
                score=result.get(score_key, 0.0),
                document=extracted_text,  # 추출된 텍스트 사용
                metadata=result['metadata'],
                matched_keywords=result.get('matched_keywords'),
                extracted_text=extracted_text,
                keyword_score=keyword_score
            ))

        search_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        response = SearchResponse(
            query=request.query,
            mode=request.mode,
            total_results=len(formatted_results),
            results=formatted_results,
            search_time_ms=round(search_time_ms, 2)
        )
        response_dict = response.dict()
        response_dict['search_mode'] = request.mode
        return response_dict

    except Exception as e:
        logger.error(f"검색 오류: {e}")
        raise HTTPException(status_code=500, detail=f"검색 중 오류 발생: {str(e)}")

@app.get("/api/stats", response_model=DatabaseStats, tags=["통계"])
async def get_stats():
    """데이터베이스 통계 정보"""
    if vector_db is None or embedding_engine is None:
        raise HTTPException(status_code=503, detail="시스템이 준비되지 않았습니다")

    db_stats = vector_db.get_stats()
    model_info = embedding_engine.get_model_info()

    return DatabaseStats(
        total_documents=db_stats['total_documents'],
        dimension=db_stats['dimension'],
        index_type=db_stats['index_type'],
        total_searches=db_stats['total_searches'],
        last_search=db_stats['last_search'],
        model_name=model_info['model_name'],
        status="operational"
    )

@app.get("/api/documents/{doc_id}", tags=["문서"])
async def get_document(doc_id: int):
    """특정 문서 조회"""
    if vector_db is None:
        raise HTTPException(status_code=503, detail="시스템이 준비되지 않았습니다")

    if doc_id < 0 or doc_id >= len(vector_db.documents):
        raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다")

    return {
        "id": doc_id,
        "document": vector_db.documents[doc_id],
        "metadata": vector_db.metadatas[doc_id]
    }

@app.get("/api/similar/{doc_id}", tags=["문서"])
async def find_similar_documents(
    doc_id: int,
    k: int = Query(5, description="반환할 유사 문서 수", ge=1, le=20)
):
    """특정 문서와 유사한 문서 찾기"""
    if vector_db is None or embedding_engine is None:
        raise HTTPException(status_code=503, detail="시스템이 준비되지 않았습니다")

    if doc_id < 0 or doc_id >= len(vector_db.documents):
        raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다")

    try:
        # 해당 문서의 텍스트로 임베딩 생성
        document_text = vector_db.documents[doc_id]
        query_embedding = embedding_engine.encode_query(document_text)

        # 유사 문서 검색
        results = vector_db.search(query_embedding, k=k+1)  # +1 because it will include itself

        # 자기 자신 제외
        similar_docs = [r for r in results if r['vector_id'] != doc_id][:k]

        return {
            "source_document_id": doc_id,
            "similar_documents": [
                {
                    "id": r['vector_id'],
                    "similarity": r['similarity'],
                    "document_preview": r['document'][:200],
                    "metadata": r['metadata']
                }
                for r in similar_docs
            ]
        }

    except Exception as e:
        logger.error(f"유사 문서 검색 오류: {e}")
        raise HTTPException(status_code=500, detail=f"오류 발생: {str(e)}")

# ======================== PDF 서빙 엔드포인트 ========================

def find_pdf_file(filename: str) -> Optional[str]:
    """PDF 파일을 여러 디렉토리에서 검색"""
    for directory in PDF_DIRECTORIES:
        # 정확한 파일명으로 검색
        pdf_path = os.path.join(directory, filename)
        if os.path.exists(pdf_path) and pdf_path.lower().endswith('.pdf'):
            return pdf_path

        # glob 패턴으로 검색 (파일명이 부분적으로 일치하는 경우)
        pattern = os.path.join(directory, f"*{filename}*")
        matches = glob.glob(pattern)
        pdf_matches = [m for m in matches if m.lower().endswith('.pdf')]
        if pdf_matches:
            return pdf_matches[0]

    return None

@app.get("/api/pdf/{filename:path}", tags=["PDF"])
async def serve_pdf(filename: str):
    """PDF 파일 서빙"""
    try:
        # URL 디코딩
        decoded_filename = unquote(filename)
        logger.info(f"PDF 요청: {decoded_filename}")

        # 파일 검색
        pdf_path = find_pdf_file(decoded_filename)
        if not pdf_path:
            raise HTTPException(status_code=404, detail=f"PDF 파일을 찾을 수 없습니다: {decoded_filename}")

        # 파일 존재 확인
        if not os.path.exists(pdf_path):
            raise HTTPException(status_code=404, detail="파일이 존재하지 않습니다")

        logger.info(f"PDF 파일 서빙: {pdf_path}")

        # PDF 파일 반환 (브라우저에서 직접 표시)
        return FileResponse(
            path=pdf_path,
            media_type="application/pdf",
            headers={"Content-Disposition": "inline"}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF 서빙 오류: {e}")
        raise HTTPException(status_code=500, detail=f"PDF 파일 서빙 중 오류 발생: {str(e)}")

@app.get("/api/pdf-page-image/{filename:path}/{page}", tags=["PDF"])
async def serve_pdf_page_as_image(filename: str, page: int):
    """PDF 페이지를 흰색 배경의 PNG 이미지로 변환하여 반환"""
    try:
        # URL 디코딩
        decoded_filename = unquote(filename)
        logger.info(f"PDF 페이지 이미지 요청: {decoded_filename}, 페이지: {page}")

        # 파일 검색
        pdf_path = find_pdf_file(decoded_filename)
        if not pdf_path:
            raise HTTPException(status_code=404, detail=f"PDF 파일을 찾을 수 없습니다: {decoded_filename}")

        # PDF 열기
        doc = fitz.open(pdf_path)
        if page < 1 or page > len(doc):
            raise HTTPException(status_code=404, detail=f"페이지 {page}를 찾을 수 없습니다 (총 {len(doc)} 페이지)")

        page_obj = doc[page - 1]  # 0-based index

        # 고해상도로 페이지를 이미지로 변환 (흰색 배경)
        mat = fitz.Matrix(2.0, 2.0)  # 2배 확대로 고화질
        pix = page_obj.get_pixmap(matrix=mat, alpha=False)  # alpha=False로 흰색 배경

        # PNG 이미지 데이터
        img_data = pix.tobytes("png")

        doc.close()

        logger.info(f"PDF 페이지 이미지 생성 성공: {decoded_filename}, 페이지: {page}")

        return Response(
            content=img_data,
            media_type="image/png",
            headers={
                "Content-Disposition": f"inline; filename=page_{page}.png"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF 페이지 이미지 생성 오류: {e}")
        raise HTTPException(status_code=500, detail=f"PDF 페이지 이미지 생성 중 오류 발생: {str(e)}")

@app.get("/api/pdf-info/{filename:path}", tags=["PDF"])
async def get_pdf_info(filename: str):
    """PDF 파일의 기본 정보 반환 (총 페이지 수, 메타데이터 등)"""
    try:
        # URL 디코딩
        decoded_filename = unquote(filename)
        logger.info(f"PDF 정보 요청: {decoded_filename}")

        # 파일 검색
        pdf_path = find_pdf_file(decoded_filename)
        if not pdf_path:
            raise HTTPException(status_code=404, detail=f"PDF 파일을 찾을 수 없습니다: {decoded_filename}")

        # PDF 열기
        doc = fitz.open(pdf_path)
        total_pages = len(doc)

        # 기본 정보 수집
        metadata = doc.metadata

        doc.close()

        return {
            "filename": decoded_filename,
            "total_pages": total_pages,
            "metadata": {
                "title": metadata.get("title", ""),
                "author": metadata.get("author", ""),
                "creator": metadata.get("creator", ""),
                "producer": metadata.get("producer", "")
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF 정보 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=f"PDF 정보 조회 중 오류 발생: {str(e)}")

@app.get("/api/test-endpoint", tags=["Test"])
async def test_endpoint():
    """Test endpoint to verify server reloading"""
    return {"message": "Test endpoint working", "timestamp": "2025-09-17"}

@app.get("/api/pdf-highlight/{filename:path}/{page}/{keyword}", tags=["PDF"])
async def highlight_pdf_page(filename: str, page: int, keyword: str):
    """PDF 페이지에 키워드 하이라이트해서 이미지로 반환"""
    try:
        # URL 디코딩
        decoded_filename = unquote(filename)
        decoded_keyword = unquote(keyword)
        logger.info(f"PDF 하이라이트 요청: {decoded_filename}, 페이지: {page}, 키워드: {decoded_keyword}")

        # 파일 검색
        pdf_path = find_pdf_file(decoded_filename)
        if not pdf_path:
            raise HTTPException(status_code=404, detail=f"PDF 파일을 찾을 수 없습니다: {decoded_filename}")

        # PDF 열기
        doc = fitz.open(pdf_path)
        if page < 1 or page > len(doc):
            raise HTTPException(status_code=404, detail=f"페이지 {page}를 찾을 수 없습니다 (총 {len(doc)} 페이지)")

        page_obj = doc[page - 1]  # 0-based index

        # 지능형 키워드 검색 및 하이라이트
        def smart_keyword_search(page, keyword):
            """지능형 키워드 검색: 정확한 매칭 + 단어별 분리 검색"""
            all_instances = []

            # 1. 정확한 키워드 매칭 시도
            exact_matches = page.search_for(keyword)
            all_instances.extend(exact_matches)

            # 2. 띄어쓰기로 분리된 키워드 개별 검색
            words = keyword.split()
            if len(words) > 1:  # 복합 키워드인 경우
                for word in words:
                    if len(word) > 1:  # 1글자 단어 제외
                        word_matches = page.search_for(word)
                        all_instances.extend(word_matches)

            # 중복 제거 (같은 위치의 하이라이트 방지)
            unique_instances = []
            for inst in all_instances:
                is_duplicate = False
                for existing in unique_instances:
                    # 겹치는 영역이 있는지 확인
                    if (abs(inst.x0 - existing.x0) < 5 and
                        abs(inst.y0 - existing.y0) < 5):
                        is_duplicate = True
                        break
                if not is_duplicate:
                    unique_instances.append(inst)

            return unique_instances

        keyword_instances = smart_keyword_search(page_obj, decoded_keyword)
        highlight_count = 0

        for inst in keyword_instances:
            highlight = page_obj.add_highlight_annot(inst)
            highlight.set_colors(stroke=[1, 1, 0])  # 노란색 하이라이트
            highlight.update()
            highlight_count += 1

        logger.info(f"하이라이트 적용: {highlight_count}개 키워드 발견")

        # 고해상도 이미지로 변환 (2배 확대)
        pix = page_obj.get_pixmap(matrix=fitz.Matrix(2, 2))
        img_data = pix.tobytes("png")

        doc.close()

        return Response(
            content=img_data,
            media_type="image/png",
            headers={
                "Content-Disposition": f"inline; filename=highlight_page_{page}.png",
                "Cache-Control": "max-age=3600"  # 1시간 캐시
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF 하이라이트 오류: {e}")
        raise HTTPException(status_code=500, detail=f"하이라이트 처리 중 오류 발생: {str(e)}")

@app.get("/api/pdf-list", tags=["PDF"])
async def list_pdfs():
    """사용 가능한 PDF 파일 목록 반환"""
    try:
        pdf_files = []
        for directory in PDF_DIRECTORIES:
            if os.path.exists(directory):
                pattern = os.path.join(directory, "*.pdf")
                files = glob.glob(pattern)
                for file_path in files:
                    filename = os.path.basename(file_path)
                    pdf_files.append({
                        "filename": filename,
                        "path": file_path,
                        "directory": directory,
                        "size": os.path.getsize(file_path)
                    })

        return {
            "total_files": len(pdf_files),
            "files": pdf_files
        }

    except Exception as e:
        logger.error(f"PDF 목록 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=f"PDF 목록 조회 중 오류 발생: {str(e)}")

# ======================== 이미지 렌더링 엔드포인트 ========================

@app.post("/api/render-page", tags=["이미지"])
async def render_pdf_page_with_highlights(request: ImageRequest):
    """
    PDF 페이지를 키워드 하이라이트와 함께 이미지로 렌더링

    - **file_path**: PDF 파일 경로 (상대 경로)
    - **page_num**: 페이지 번호 (0부터 시작)
    - **keywords**: 하이라이트할 키워드들 (선택사항)
    - **crop_to_keywords**: 키워드 영역만 크롭할지 여부
    - **highlight_color**: 하이라이트 색상
    """
    if pdf_renderer is None:
        raise HTTPException(status_code=503, detail="PDF 렌더러가 준비되지 않았습니다")

    try:
        logger.info(f"PDF 이미지 렌더링 요청: {request.file_path}, 페이지: {request.page_num}")

        # PDF 정보 조회
        pdf_info = pdf_renderer.get_pdf_info(request.file_path)
        if not pdf_info:
            raise HTTPException(status_code=404, detail=f"PDF 파일을 찾을 수 없습니다: {request.file_path}")

        # 페이지 번호 유효성 검사
        if request.page_num >= pdf_info.get('page_count', 0) or request.page_num < 0:
            raise HTTPException(
                status_code=400,
                detail=f"잘못된 페이지 번호: {request.page_num} (총 {pdf_info.get('page_count', 0)}페이지)"
            )

        # 이미지 렌더링
        image_b64 = pdf_renderer.render_page_with_highlights(
            file_path=request.file_path,
            page_num=request.page_num,
            keywords=request.keywords or [],
            crop_to_keywords=request.crop_to_keywords,
            highlight_color=request.highlight_color
        )

        if image_b64 is None:
            raise HTTPException(status_code=500, detail="이미지 렌더링에 실패했습니다")

        return ImageResponse(
            success=True,
            message="이미지 렌더링 성공",
            image_b64=image_b64,
            pdf_info=pdf_info
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF 이미지 렌더링 오류: {e}")
        raise HTTPException(status_code=500, detail=f"렌더링 중 오류 발생: {str(e)}")

@app.get("/api/render-page/{file_path:path}/{page_num}", tags=["이미지"])
async def render_pdf_page_simple(
    file_path: str,
    page_num: int,
    keywords: Optional[str] = Query(None, description="쉼표로 구분된 키워드들"),
    crop: bool = Query(False, description="키워드 영역만 크롭할지 여부"),
    color: str = Query("rgba(255, 255, 0, 128)", description="하이라이트 색상")
):
    """
    간단한 GET 방식 PDF 페이지 이미지 렌더링

    - **file_path**: PDF 파일 경로
    - **page_num**: 페이지 번호 (0부터 시작)
    - **keywords**: 쉼표로 구분된 키워드들 (예: "도로,설계")
    - **crop**: 키워드 영역만 크롭할지 여부
    - **color**: 하이라이트 색상
    """
    # 키워드 파싱
    keyword_list = []
    if keywords:
        keyword_list = [k.strip() for k in keywords.split(',') if k.strip()]

    # ImageRequest 객체 생성
    request = ImageRequest(
        file_path=unquote(file_path),
        page_num=page_num,
        keywords=keyword_list if keyword_list else None,
        crop_to_keywords=crop,
        highlight_color=color
    )

    # POST 엔드포인트 재사용
    return await render_pdf_page_with_highlights(request)

# ======================== 메인 실행 ========================

if __name__ == "__main__":
    # 서버 실행
    uvicorn.run(
        "fastapi_server:app",
        host="0.0.0.0",
        port=8080,
        reload=False,
        log_level="info"
    )
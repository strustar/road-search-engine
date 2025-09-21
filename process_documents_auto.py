"""
자동 문서 처리 스크립트 (사용자 입력 없이)
"""

import os
import sys
import time
from typing import List
import logging

# 로컬 모듈 import
from preprocessing.document_loader import DocumentLoader
from preprocessing.text_chunker import KoreanTextChunker
from rag.embedding_engine import KoreanEmbeddingEngine
from rag.vector_database import VectorDatabase

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def process_all_pdfs():
    """모든 PDF 자동 처리"""
    
    print("="*60)
    print("문서 벡터화 시작")
    print("="*60)
    
    # 컴포넌트 초기화
    loader = DocumentLoader()
    chunker = KoreanTextChunker(chunk_size=1000, chunk_overlap=200)
    embedding_engine = KoreanEmbeddingEngine()
    vector_db = VectorDatabase(
        dimension=embedding_engine.dimension,
        index_type="cosine",
        storage_dir="./vector_store"
    )
    
    # PDF 파일 목록
    pdf_files = []
    
    # 도로설계요령 폴더
    road_design_dir = "도로설계요령(2020)"
    if os.path.exists(road_design_dir):
        for file in os.listdir(road_design_dir):
            if file.endswith('.pdf'):
                pdf_files.append(os.path.join(road_design_dir, file))
    
    # 실무지침 폴더  
    practice_dir = "실무지침(2020)"
    if os.path.exists(practice_dir):
        for file in os.listdir(practice_dir):
            if file.endswith('.pdf'):
                pdf_files.append(os.path.join(practice_dir, file))
    
    if not pdf_files:
        print("처리할 PDF 파일이 없습니다.")
        return False
    
    print(f"발견된 파일: {len(pdf_files)}개")
    
    # 통계
    total_chunks = 0
    processed_files = 0
    
    # 파일별 처리
    for i, file_path in enumerate(pdf_files, 1):
        try:
            print(f"\n[{i}/{len(pdf_files)}] 처리 중: {os.path.basename(file_path)}")
            
            # 1. PDF 로드
            documents = loader.load_pdf(file_path)
            if not documents:
                print(f"  로드 실패: {file_path}")
                continue
            
            print(f"  - 페이지 수: {len(documents)}")
            
            # 2. 텍스트 청킹
            chunks = chunker.chunk_documents(documents)
            if not chunks:
                print(f"  청킹 실패: {file_path}")
                continue
            
            print(f"  - 청크 수: {len(chunks)}")
            
            # 3. 카테고리 메타데이터 추가
            if "도로설계요령" in file_path:
                category = "도로설계요령"
            elif "실무지침" in file_path:
                category = "실무지침"
            else:
                category = "기타"
            
            # 각 청크에 카테고리 추가
            for chunk in chunks:
                chunk.metadata['category'] = category
            
            # 4. 임베딩 생성
            chunk_texts = [chunk.page_content for chunk in chunks]
            chunk_metadatas = [chunk.metadata for chunk in chunks]
            
            embeddings = embedding_engine.encode_texts(chunk_texts, show_progress=False)
            if embeddings.size == 0:
                print(f"  임베딩 실패: {file_path}")
                continue
            
            # 4. 벡터 DB에 추가
            vector_db.add_documents(embeddings, chunk_metadatas, chunk_texts)
            
            total_chunks += len(chunks)
            processed_files += 1
            print(f"  완료! (누적 청크: {total_chunks})")
            
        except Exception as e:
            print(f"  오류 발생: {e}")
            continue
    
    # 저장
    print("\n벡터 DB 저장 중...")
    if vector_db.save_database("road_design_db"):
        print("저장 완료!")
    else:
        print("저장 실패!")
        return False
    
    # 결과 출력
    print("\n" + "="*60)
    print("처리 완료!")
    print(f"처리된 파일: {processed_files}/{len(pdf_files)}")
    print(f"총 청크 수: {total_chunks}")
    print("="*60)
    
    return True

if __name__ == "__main__":
    try:
        success = process_all_pdfs()
        if success:
            print("\n성공! 이제 streamlit run streamlit_search_app.py를 실행하세요.")
        else:
            print("\n처리 실패!")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n중단되었습니다.")
        sys.exit(0)
    except Exception as e:
        print(f"\n오류: {e}")
        sys.exit(1)
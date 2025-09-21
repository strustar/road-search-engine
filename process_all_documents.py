"""
전체 문서 처리 스크립트
15개 PDF → 청킹 → 임베딩 → 벡터 DB 저장
"""

import os
import sys
import time
from typing import List
import logging
from tqdm import tqdm
import argparse

# 로컬 모듈 import
from preprocessing.document_loader import DocumentLoader
from preprocessing.text_chunker import KoreanTextChunker
from rag.embedding_engine import KoreanEmbeddingEngine
from rag.vector_database import VectorDatabase

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('document_processing.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DocumentProcessor:
    """전체 문서 처리 클래스"""
    
    def __init__(self):
        self.loader = DocumentLoader()
        self.chunker = KoreanTextChunker(
            chunk_size=1000,
            chunk_overlap=200,
            preserve_structure=True
        )
        self.embedding_engine = KoreanEmbeddingEngine()
        self.vector_db = VectorDatabase(
            dimension=self.embedding_engine.dimension,
            index_type="cosine",
            storage_dir="./vector_store"
        )
        
        # 처리 통계
        self.stats = {
            'total_files': 0,
            'processed_files': 0,
            'total_pages': 0,
            'total_chunks': 0,
            'failed_files': [],
            'processing_time': 0
        }
    
    def get_pdf_files(self) -> List[str]:
        """처리할 PDF 파일 목록 가져오기"""
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
        
        logger.info(f"처리 대상 PDF 파일 {len(pdf_files)}개 발견")
        return sorted(pdf_files)
    
    def process_single_pdf(self, file_path: str) -> bool:
        """단일 PDF 처리"""
        try:
            logger.info(f"처리 시작: {file_path}")
            
            # 1. PDF 로드
            documents = self.loader.load_pdf(file_path)
            if not documents:
                logger.warning(f"문서 로드 실패: {file_path}")
                return False
            
            # 메타데이터에 'source'로 전체 파일 경로 추가
            for doc in documents:
                doc.metadata['source'] = file_path.replace('\\', '/')

            self.stats['total_pages'] += len(documents)
            
            # 2. 텍스트 청킹
            chunks = self.chunker.chunk_documents(documents)
            if not chunks:
                logger.warning(f"청킹 실패: {file_path}")
                return False
            
            self.stats['total_chunks'] += len(chunks)
            
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
            
            embeddings, metadatas = self.embedding_engine.encode_documents(chunks)
            if embeddings.size == 0:
                logger.warning(f"임베딩 생성 실패: {file_path}")
                return False
            
            # 4. 벡터 DB에 추가
            self.vector_db.add_documents(embeddings, metadatas, chunk_texts)
            
            logger.info(f"처리 완료: {file_path} ({len(chunks)}개 청크)")
            return True
            
        except Exception as e:
            logger.error(f"처리 중 오류 발생: {file_path} - {e}")
            return False
    
    def process_all_documents(self, save_interval: int = 3):
        """모든 문서 처리"""
        start_time = time.time()
        
        # PDF 파일 목록 가져오기
        pdf_files = self.get_pdf_files()
        if not pdf_files:
            logger.error("처리할 PDF 파일이 없습니다.")
            return False
        
        self.stats['total_files'] = len(pdf_files)
        
        # 파일별 처리
        logger.info("="*60)
        logger.info(f"전체 문서 처리 시작: {len(pdf_files)}개 파일")
        logger.info("="*60)
        
        with tqdm(pdf_files, desc="PDF 처리 진행", unit="파일") as pbar:
            for i, file_path in enumerate(pbar):
                pbar.set_description(f"처리 중: {os.path.basename(file_path)}")
                
                success = self.process_single_pdf(file_path)
                
                if success:
                    self.stats['processed_files'] += 1
                    pbar.set_postfix({
                        "성공": self.stats['processed_files'],
                        "청크": self.stats['total_chunks']
                    })
                else:
                    self.stats['failed_files'].append(file_path)
                    pbar.set_postfix({
                        "성공": self.stats['processed_files'], 
                        "실패": len(self.stats['failed_files'])
                    })
                
                # 중간 저장 (메모리 관리)
                if (i + 1) % save_interval == 0:
                    logger.info(f"중간 저장 중... ({i+1}/{len(pdf_files)})")
                    self.vector_db.save_database("road_design_db")
        
        # 최종 저장
        logger.info("최종 벡터 DB 저장 중...")
        if self.vector_db.save_database("road_design_db"):
            logger.info("벡터 데이터베이스 저장 완료")
        else:
            logger.error("벡터 데이터베이스 저장 실패")
        
        # 처리 통계
        self.stats['processing_time'] = time.time() - start_time
        self.print_processing_stats()
        
        return True
    
    def print_processing_stats(self):
        """처리 통계 출력"""
        logger.info("\n" + "="*60)
        logger.info("문서 처리 완료 통계")
        logger.info("="*60)
        logger.info(f"총 파일 수: {self.stats['total_files']}개")
        logger.info(f"성공 처리: {self.stats['processed_files']}개")
        logger.info(f"실패 파일: {len(self.stats['failed_files'])}개")
        logger.info(f"총 페이지: {self.stats['total_pages']}개")
        logger.info(f"총 청크: {self.stats['total_chunks']}개")
        logger.info(f"처리 시간: {self.stats['processing_time']:.2f}초")
        
        if self.stats['failed_files']:
            logger.warning("\n실패한 파일들:")
            for failed_file in self.stats['failed_files']:
                logger.warning(f"  - {failed_file}")
        
        # 벡터 DB 통계
        db_stats = self.vector_db.get_stats()
        logger.info(f"\n벡터 데이터베이스 정보:")
        logger.info(f"저장된 문서: {db_stats['total_documents']}개")
        logger.info(f"임베딩 차원: {db_stats['dimension']}")
        logger.info(f"인덱스 타입: {db_stats['index_type']}")
        
        # 성능 계산
        if self.stats['processing_time'] > 0:
            files_per_sec = self.stats['processed_files'] / self.stats['processing_time']
            chunks_per_sec = self.stats['total_chunks'] / self.stats['processing_time']
            logger.info(f"처리 성능:")
            logger.info(f"  파일/초: {files_per_sec:.2f}")
            logger.info(f"  청크/초: {chunks_per_sec:.2f}")
        
        logger.info("="*60)


def main():
    """메인 실행 함수"""
    
    parser = argparse.ArgumentParser(description="도로설계·실무지침 문서 벡터화 스크립트")
    parser.add_argument('-y', '--yes', action='store_true', help='확인 프롬프트를 건너뛰고 바로 실행합니다.')
    args = parser.parse_args()
    
    print("도로설계·실무지침 문서 벡터화 시작")
    print("="*60)
    
    # 필요한 패키지 확인
    try:
        import sentence_transformers
        import faiss
        import tqdm
    except ImportError as e:
        print(f"❌ 필요한 패키지가 설치되지 않음: {e}")
        print("다음 명령으로 설치하세요:")
        print("pip install sentence-transformers faiss-cpu tqdm")
        sys.exit(1)
    
    # 처리기 초기화 및 실행
    try:
        processor = DocumentProcessor()
        
        # 사용자 확인
        pdf_files = processor.get_pdf_files()
        if not pdf_files:
            print("❌ 처리할 PDF 파일이 없습니다.")
            print("도로설계요령(2020)/ 또는 실무지침(2020)/ 폴더에 PDF 파일이 있는지 확인하세요.")
            sys.exit(1)
        
        if not args.yes:
            print(f"발견된 파일: {len(pdf_files)}개")
            for i, file_path in enumerate(pdf_files, 1):
                print(f"  {i:2d}. {os.path.basename(file_path)}")
            
            response = input(f"\n이 {len(pdf_files)}개 파일을 처리하시겠습니까? (y/N): ").lower()
            if response != 'y':
                print("처리를 취소했습니다.")
                sys.exit(0)
        
        # 처리 시작
        success = processor.process_all_documents()
        
        if success:
            print("\n모든 문서 처리가 완료되었습니다!")
            print("이제 'streamlit run streamlit_search_app.py'로 검색을 시작할 수 있습니다.")
        else:
            print("\n문서 처리 중 오류가 발생했습니다.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n사용자에 의해 중단되었습니다.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"예상치 못한 오류 발생: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
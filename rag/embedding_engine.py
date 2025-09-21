"""
RAG 3단계: Embedding Engine
한국어 텍스트 임베딩 및 벡터화
"""
import os
import numpy as np
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
import pickle
import json
from langchain.schema import Document
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KoreanEmbeddingEngine:
    """한국어 특화 임베딩 엔진"""
    
    def __init__(self, 
                 model_name: str = "jhgan/ko-sroberta-multitask",
                 cache_dir: str = "./models",
                 use_cache: bool = True):
        
        self.model_name = model_name
        self.cache_dir = cache_dir
        self.use_cache = use_cache
        self.model = None
        self.dimension = None
        
        # 캐시 디렉토리 생성
        os.makedirs(cache_dir, exist_ok=True)
        
        # 모델 로드
        self._load_model()
    
    def _load_model(self):
        """임베딩 모델 로드"""
        try:
            logger.info(f"임베딩 모델 로드 중: {self.model_name}")

            # PyTorch meta tensor 문제 해결을 위한 설정
            import torch
            torch.set_num_threads(1)  # 멀티스레딩 이슈 방지

            self.model = SentenceTransformer(
                self.model_name,
                cache_folder=self.cache_dir,
                device='cpu'  # CPU 사용 강제 지정
            )

            # 모델을 명시적으로 CPU로 이동
            self.model.to('cpu')

            # 차원 확인
            test_embedding = self.model.encode("테스트")
            self.dimension = len(test_embedding)

            logger.info(f"모델 로드 완료. 임베딩 차원: {self.dimension}")

        except Exception as e:
            logger.error(f"모델 로드 실패: {e}")
            raise
    
    def encode_texts(self, texts: List[str], show_progress: bool = True) -> np.ndarray:
        """텍스트 리스트를 임베딩으로 변환"""
        try:
            if not texts:
                return np.array([])
            
            logger.info(f"{len(texts)}개 텍스트 임베딩 생성 중...")
            
            # 배치 처리로 임베딩 생성
            embeddings = self.model.encode(
                texts,
                show_progress_bar=show_progress,
                batch_size=32,  # 메모리 효율성 고려
                normalize_embeddings=True  # 코사인 유사도 최적화
            )
            
            logger.info(f"임베딩 생성 완료: {embeddings.shape}")
            return embeddings
            
        except Exception as e:
            logger.error(f"임베딩 생성 실패: {e}")
            return np.array([])
    
    def encode_documents(self, documents: List[Document]) -> tuple[np.ndarray, List[Dict]]:
        """Document 객체들을 임베딩으로 변환 (메타데이터 포함)"""
        try:
            # 텍스트와 메타데이터 분리
            texts = [doc.page_content for doc in documents]
            metadatas = [doc.metadata for doc in documents]
            
            # 텍스트 임베딩
            embeddings = self.encode_texts(texts)
            
            # 임베딩에 ID 추가
            for i, metadata in enumerate(metadatas):
                metadata['embedding_id'] = i
            
            return embeddings, metadatas
            
        except Exception as e:
            logger.error(f"문서 임베딩 실패: {e}")
            return np.array([]), []
    
    def encode_query(self, query: str) -> np.ndarray:
        """검색 쿼리를 임베딩으로 변환"""
        try:
            embedding = self.model.encode(
                [query],
                normalize_embeddings=True
            )
            return embedding[0]
            
        except Exception as e:
            logger.error(f"쿼리 임베딩 실패: {e}")
            return np.array([])
    
    def calculate_similarity(self, 
                           query_embedding: np.ndarray, 
                           doc_embeddings: np.ndarray) -> np.ndarray:
        """코사인 유사도 계산"""
        try:
            # 이미 정규화된 벡터이므로 내적으로 코사인 유사도 계산
            similarities = np.dot(doc_embeddings, query_embedding)
            return similarities
            
        except Exception as e:
            logger.error(f"유사도 계산 실패: {e}")
            return np.array([])
    
    def save_embeddings(self, 
                       embeddings: np.ndarray, 
                       metadatas: List[Dict], 
                       filepath: str):
        """임베딩과 메타데이터를 파일로 저장"""
        try:
            data = {
                'embeddings': embeddings,
                'metadatas': metadatas,
                'model_name': self.model_name,
                'dimension': self.dimension
            }
            
            with open(filepath, 'wb') as f:
                pickle.dump(data, f)
            
            logger.info(f"임베딩 저장 완료: {filepath}")
            
        except Exception as e:
            logger.error(f"임베딩 저장 실패: {e}")
    
    def load_embeddings(self, filepath: str) -> tuple[np.ndarray, List[Dict]]:
        """저장된 임베딩과 메타데이터 로드"""
        try:
            with open(filepath, 'rb') as f:
                data = pickle.load(f)
            
            embeddings = data['embeddings']
            metadatas = data['metadatas']
            
            logger.info(f"임베딩 로드 완료: {embeddings.shape}, {len(metadatas)}개 메타데이터")
            return embeddings, metadatas
            
        except Exception as e:
            logger.error(f"임베딩 로드 실패: {e}")
            return np.array([]), []
    
    def get_model_info(self) -> Dict[str, Any]:
        """모델 정보 반환"""
        return {
            'model_name': self.model_name,
            'dimension': self.dimension,
            'cache_dir': self.cache_dir
        }


def main():
    """테스트 함수"""
    # 테스트용 문서들
    test_documents = [
        Document(
            page_content="도로의 설계속도는 도로의 기능, 지형, 기상조건 등을 고려하여 결정한다.",
            metadata={"file_name": "test1.pdf", "page": 1}
        ),
        Document(
            page_content="차로폭은 설계속도, 교통량, 차량구성 등을 고려하여 3.0m 이상으로 한다.",
            metadata={"file_name": "test2.pdf", "page": 1}
        ),
        Document(
            page_content="교차로는 도로의 교통용량과 안전성을 결정하는 중요한 요소이다.",
            metadata={"file_name": "test3.pdf", "page": 1}
        )
    ]
    
    print("임베딩 엔진 테스트 시작")
    print("="*50)
    
    # 임베딩 엔진 초기화
    engine = KoreanEmbeddingEngine()
    
    # 문서 임베딩
    embeddings, metadatas = engine.encode_documents(test_documents)
    
    if embeddings.size > 0:
        print(f"✅ 임베딩 생성 성공: {embeddings.shape}")
        
        # 쿼리 테스트
        query = "도로 설계속도"
        query_embedding = engine.encode_query(query)
        
        if query_embedding.size > 0:
            # 유사도 계산
            similarities = engine.calculate_similarity(query_embedding, embeddings)
            
            print(f"\n검색어: '{query}'")
            print("유사도 결과:")
            for i, (sim, meta) in enumerate(zip(similarities, metadatas)):
                print(f"  {i+1}. {sim:.4f} - {meta['file_name']}")
                print(f"     {test_documents[i].page_content[:50]}...")
        
        # 저장/로드 테스트
        test_file = "test_embeddings.pkl"
        engine.save_embeddings(embeddings, metadatas, test_file)
        
        loaded_embeddings, loaded_metadatas = engine.load_embeddings(test_file)
        if loaded_embeddings.size > 0:
            print(f"\n✅ 저장/로드 테스트 성공")
        
        # 정리
        if os.path.exists(test_file):
            os.remove(test_file)


if __name__ == "__main__":
    main()
"""
RAG 4단계: Vector Database
FAISS 기반 벡터 데이터베이스와 키워드 검색
"""
import os
import faiss
import numpy as np
import json
from typing import List, Dict, Any, Tuple, Optional
import pickle
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VectorDatabase:
    """FAISS 기반 벡터 데이터베이스"""
    
    def __init__(self, 
                 dimension: int,
                 index_type: str = "cosine",
                 storage_dir: str = "./vector_store"):
        
        self.dimension = dimension
        self.index_type = index_type
        self.storage_dir = storage_dir
        
        # 저장소 디렉토리 생성
        os.makedirs(storage_dir, exist_ok=True)
        
        # FAISS 인덱스 초기화
        self.index = self._create_index()
        self.metadatas = []
        self.documents = []  # 원본 텍스트 저장
        
        # 검색 통계
        self.search_stats = {
            'total_searches': 0,
            'last_search': None
        }
    
    def _create_index(self):
        """FAISS 인덱스 생성"""
        if self.index_type == "cosine":
            # 코사인 유사도용 인덱스 (정규화된 벡터)
            index = faiss.IndexFlatIP(self.dimension)
        elif self.index_type == "l2":
            # L2 거리용 인덱스
            index = faiss.IndexFlatL2(self.dimension)
        else:
            # 기본값: 내적 (코사인 유사도)
            index = faiss.IndexFlatIP(self.dimension)
        
        logger.info(f"FAISS 인덱스 생성: {self.index_type}, 차원: {self.dimension}")
        return index
    
    def add_documents(self, 
                     embeddings: np.ndarray, 
                     metadatas: List[Dict], 
                     documents: List[str]):
        """문서와 임베딩을 데이터베이스에 추가"""
        try:
            if embeddings.shape[0] != len(metadatas) or embeddings.shape[0] != len(documents):
                raise ValueError("임베딩, 메타데이터, 문서 수가 일치하지 않음")
            
            # 임베딩 정규화 (코사인 유사도용)
            if self.index_type == "cosine":
                embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
            
            # FAISS 인덱스에 추가
            self.index.add(embeddings.astype('float32'))
            
            # 메타데이터와 문서 저장
            start_id = len(self.metadatas)
            for i, (metadata, document) in enumerate(zip(metadatas, documents)):
                metadata['vector_id'] = start_id + i
                metadata['added_at'] = datetime.now().isoformat()
            
            self.metadatas.extend(metadatas)
            self.documents.extend(documents)
            
            logger.info(f"벡터 DB에 {len(documents)}개 문서 추가 완료 (총 {len(self.documents)}개)")
            
        except Exception as e:
            logger.error(f"문서 추가 실패: {e}")
            raise
    
    def search(self, 
               query_embedding: np.ndarray, 
               k: int = 5,
               min_similarity: float = 0.0) -> List[Dict[str, Any]]:
        """벡터 유사도 검색"""
        try:
            if self.index.ntotal == 0:
                logger.warning("인덱스가 비어있음")
                return []
            
            # 쿼리 임베딩 정규화
            if self.index_type == "cosine":
                query_embedding = query_embedding / np.linalg.norm(query_embedding)
            
            # FAISS 검색
            query_vector = query_embedding.reshape(1, -1).astype('float32')
            similarities, indices = self.index.search(query_vector, min(k, self.index.ntotal))
            
            # 결과 구성
            results = []
            for sim, idx in zip(similarities[0], indices[0]):
                if sim >= min_similarity and idx < len(self.metadatas):
                    result = {
                        'similarity': float(sim),
                        'document': self.documents[idx],
                        'metadata': self.metadatas[idx].copy(),
                        'vector_id': idx
                    }
                    results.append(result)
            
            # 검색 통계 업데이트
            self.search_stats['total_searches'] += 1
            self.search_stats['last_search'] = datetime.now().isoformat()
            
            logger.info(f"벡터 검색 완료: {len(results)}개 결과 (임계값: {min_similarity})")
            return results
            
        except Exception as e:
            logger.error(f"벡터 검색 실패: {e}")
            return []
    
    def keyword_search(self, 
                      keywords: List[str], 
                      match_all: bool = False,
                      k: int = 10) -> List[Dict[str, Any]]:
        """키워드 기반 검색 (벡터 검색 보완용)"""
        try:
            results = []
            
            for i, (document, metadata) in enumerate(zip(self.documents, self.metadatas)):
                doc_lower = document.lower()
                keyword_matches = []
                
                for keyword in keywords:
                    keyword_lower = keyword.lower()
                    if keyword_lower in doc_lower:
                        keyword_matches.append(keyword)
                
                # 매칭 조건 확인
                if match_all and len(keyword_matches) == len(keywords):
                    # 모든 키워드 매칭
                    match_score = 1.0
                elif not match_all and keyword_matches:
                    # 일부 키워드 매칭
                    match_score = len(keyword_matches) / len(keywords)
                else:
                    continue
                
                result = {
                    'match_score': match_score,
                    'matched_keywords': keyword_matches,
                    'document': document,
                    'metadata': metadata.copy(),
                    'vector_id': i
                }
                results.append(result)
            
            # 매칭 점수로 정렬 (점수가 같을 때는 카테고리별 균등 분배를 위해 랜덤 요소 추가)
            import random
            results.sort(key=lambda x: (x['match_score'], random.random()), reverse=True)
            
            # 상위 k개 결과만 반환
            results = results[:k]
            
            logger.info(f"키워드 검색 완료: {len(results)}개 결과")
            return results
            
        except Exception as e:
            logger.error(f"키워드 검색 실패: {e}")
            return []
    
    def hybrid_search(self,
                     query_embedding: np.ndarray,
                     keywords: List[str],
                     k: int = 10,
                     vector_weight: float = 0.7) -> List[Dict[str, Any]]:
        """하이브리드 검색 (벡터 + 키워드)"""
        try:
            # 벡터 검색
            vector_results = self.search(query_embedding, k=k*2)  # 더 많이 가져와서 필터링
            
            # 키워드 검색
            keyword_results = self.keyword_search(keywords, match_all=False)
            
            # 결과 통합 및 점수 조합
            combined_results = {}
            
            # 벡터 검색 결과 처리
            for result in vector_results:
                vector_id = result['vector_id']
                combined_results[vector_id] = {
                    'vector_score': result['similarity'] * vector_weight,
                    'keyword_score': 0.0,
                    'document': result['document'],
                    'metadata': result['metadata'],
                    'vector_id': vector_id,
                    'matched_keywords': []
                }
            
            # 키워드 검색 결과 처리
            for result in keyword_results:
                vector_id = result['vector_id']
                keyword_score = result['match_score'] * (1 - vector_weight)
                
                if vector_id in combined_results:
                    combined_results[vector_id]['keyword_score'] = keyword_score
                    combined_results[vector_id]['matched_keywords'] = result['matched_keywords']
                else:
                    combined_results[vector_id] = {
                        'vector_score': 0.0,
                        'keyword_score': keyword_score,
                        'document': result['document'],
                        'metadata': result['metadata'],
                        'vector_id': vector_id,
                        'matched_keywords': result['matched_keywords']
                    }
            
            # 최종 점수 계산 및 정렬
            final_results = []
            for result in combined_results.values():
                result['final_score'] = result['vector_score'] + result['keyword_score']
                final_results.append(result)
            
            final_results.sort(key=lambda x: x['final_score'], reverse=True)
            
            # 상위 k개 결과만 반환
            final_results = final_results[:k]
            
            logger.info(f"하이브리드 검색 완료: {len(final_results)}개 결과")
            return final_results
            
        except Exception as e:
            logger.error(f"하이브리드 검색 실패: {e}")
            return []
    
    def save_database(self, filename_prefix: str = "vector_db"):
        """데이터베이스 저장"""
        try:
            # FAISS 인덱스 저장
            index_path = os.path.join(self.storage_dir, f"{filename_prefix}.index")
            faiss.write_index(self.index, index_path)
            
            # 메타데이터와 문서 저장
            data_path = os.path.join(self.storage_dir, f"{filename_prefix}.pkl")
            with open(data_path, 'wb') as f:
                pickle.dump({
                    'metadatas': self.metadatas,
                    'documents': self.documents,
                    'dimension': self.dimension,
                    'index_type': self.index_type,
                    'search_stats': self.search_stats
                }, f)
            
            # 정보 파일 저장
            info_path = os.path.join(self.storage_dir, f"{filename_prefix}_info.json")
            with open(info_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'total_documents': len(self.documents),
                    'dimension': self.dimension,
                    'index_type': self.index_type,
                    'created_at': datetime.now().isoformat(),
                    'search_stats': self.search_stats
                }, f, ensure_ascii=False, indent=2)
            
            logger.info(f"데이터베이스 저장 완료: {filename_prefix}")
            return True
            
        except Exception as e:
            logger.error(f"데이터베이스 저장 실패: {e}")
            return False
    
    def load_database(self, filename_prefix: str = "vector_db") -> bool:
        """데이터베이스 로드"""
        try:
            # FAISS 인덱스 로드
            index_path = os.path.join(self.storage_dir, f"{filename_prefix}.index")
            if os.path.exists(index_path):
                self.index = faiss.read_index(index_path)
            else:
                logger.warning("인덱스 파일을 찾을 수 없음")
                return False
            
            # 메타데이터와 문서 로드
            data_path = os.path.join(self.storage_dir, f"{filename_prefix}.pkl")
            if os.path.exists(data_path):
                with open(data_path, 'rb') as f:
                    data = pickle.load(f)
                    
                self.metadatas = data['metadatas']
                self.documents = data['documents']
                self.search_stats = data.get('search_stats', {'total_searches': 0})
            else:
                logger.warning("데이터 파일을 찾을 수 없음")
                return False
            
            logger.info(f"데이터베이스 로드 완료: {len(self.documents)}개 문서")
            return True
            
        except Exception as e:
            logger.error(f"데이터베이스 로드 실패: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """데이터베이스 통계 정보"""
        return {
            'total_documents': len(self.documents),
            'dimension': self.dimension,
            'index_type': self.index_type,
            'total_searches': self.search_stats['total_searches'],
            'last_search': self.search_stats['last_search']
        }


def main():
    """테스트 함수"""
    print("벡터 데이터베이스 테스트 시작")
    print("="*50)
    
    # 테스트 데이터
    dimension = 768
    test_embeddings = np.random.rand(3, dimension).astype('float32')
    test_documents = [
        "도로의 설계속도는 안전성과 효율성을 고려하여 결정한다.",
        "차로폭은 3.0m 이상으로 설계하며 교통량에 따라 조정한다.", 
        "교차로 설계에서는 시거확보가 중요한 요소이다."
    ]
    test_metadatas = [
        {"file_name": "설계기준.pdf", "page": 1, "section": "설계속도"},
        {"file_name": "도로구조.pdf", "page": 5, "section": "차로설계"},
        {"file_name": "교차로.pdf", "page": 10, "section": "교차로설계"}
    ]
    
    # 벡터 DB 생성
    db = VectorDatabase(dimension=dimension)
    
    # 문서 추가
    db.add_documents(test_embeddings, test_metadatas, test_documents)
    
    # 벡터 검색 테스트
    query_embedding = np.random.rand(dimension).astype('float32')
    vector_results = db.search(query_embedding, k=2)
    
    print(f"벡터 검색 결과: {len(vector_results)}개")
    for i, result in enumerate(vector_results):
        print(f"  {i+1}. 유사도: {result['similarity']:.4f}")
        print(f"      파일: {result['metadata']['file_name']}")
    
    # 키워드 검색 테스트
    keyword_results = db.keyword_search(["도로", "설계"])
    
    print(f"\n키워드 검색 결과: {len(keyword_results)}개")
    for i, result in enumerate(keyword_results):
        print(f"  {i+1}. 매칭점수: {result['match_score']:.2f}")
        print(f"      키워드: {result['matched_keywords']}")
    
    # 저장/로드 테스트
    if db.save_database("test_db"):
        print("\n✅ 데이터베이스 저장 성공")
    
    # 새로운 DB 인스턴스로 로드 테스트
    new_db = VectorDatabase(dimension=dimension)
    if new_db.load_database("test_db"):
        print("✅ 데이터베이스 로드 성공")
        stats = new_db.get_stats()
        print(f"   로드된 문서 수: {stats['total_documents']}")


if __name__ == "__main__":
    main()
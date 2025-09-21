"""
RAG 2단계: Text Chunking
한국어 도로설계 문서에 특화된 텍스트 분할기
"""
import re
from typing import List, Dict, Any
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KoreanTextChunker:
    """한국어 특화 텍스트 청킹"""
    
    def __init__(self, 
                 chunk_size: int = 1000, 
                 chunk_overlap: int = 200,
                 preserve_structure: bool = True):
        
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.preserve_structure = preserve_structure
        
        # 한국어 특화 구분자
        self.korean_separators = [
            "\n\n\n",  # 큰 단락 구분
            "\n\n",    # 단락 구분
            "\n",      # 줄바꿈
            "。",      # 일본식 마침표 (기술문서에 가끔 나타남)
            ".",       # 마침표
            "!",       # 느낌표
            "?",       # 물음표
            ";",       # 세미콜론
            ":",       # 콜론
            " ",       # 공백
            ""         # 마지막 수단
        ]
        
        # 도로설계요령 구조 패턴
        self.structure_patterns = [
            r"제\d+권\s+.+",      # 제1권 도로계획및 기하구조
            r"제\d+편\s+.+",      # 제1편 총론
            r"제\d+장\s+.+",      # 제1장
            r"제\d+절\s+.+",      # 제1절  
            r"\d+\.\d+\s+.+",     # 1.1 항목
            r"\d+\.\d+\.\d+\s+.+", # 1.1.1 세부항목
        ]
        
        # 청킹기 초기화
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=self.korean_separators,
            length_function=len,
            is_separator_regex=False
        )
    
    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        """문서 리스트를 청킹"""
        all_chunks = []
        
        for doc in documents:
            chunks = self.chunk_single_document(doc)
            all_chunks.extend(chunks)
            
        logger.info(f"총 {len(documents)}개 문서를 {len(all_chunks)}개 청크로 분할")
        return all_chunks
    
    def chunk_single_document(self, document: Document) -> List[Document]:
        """단일 문서 청킹"""
        try:
            # 기본 메타데이터 보존
            base_metadata = document.metadata.copy()
            
            # 구조 기반 전처리
            if self.preserve_structure:
                processed_text = self._preprocess_structure(document.page_content)
            else:
                processed_text = document.page_content
            
            # RecursiveCharacterTextSplitter로 청킹
            text_chunks = self.splitter.split_text(processed_text)
            
            # Document 객체로 변환하며 메타데이터 추가
            chunks = []
            for i, chunk_text in enumerate(text_chunks):
                # 청크 메타데이터 생성
                chunk_metadata = base_metadata.copy()
                chunk_metadata.update({
                    'chunk_index': i,
                    'chunk_id': f"{base_metadata.get('file_name', 'unknown')}_{i}",
                    'chunk_size': len(chunk_text),
                    'total_chunks': len(text_chunks),
                    'section': self._extract_section(chunk_text),
                    'keywords': self._extract_keywords(chunk_text)
                })
                
                chunk_doc = Document(
                    page_content=chunk_text,
                    metadata=chunk_metadata
                )
                chunks.append(chunk_doc)
            
            logger.info(f"{base_metadata.get('file_name', 'unknown')}: {len(chunks)}개 청크 생성")
            return chunks
            
        except Exception as e:
            logger.error(f"청킹 오류: {e}")
            return []
    
    def _preprocess_structure(self, text: str) -> str:
        """구조 정보 전처리"""
        # 제목과 본문 사이에 구분자 추가
        for pattern in self.structure_patterns:
            text = re.sub(pattern, lambda m: f"\n\n{m.group()}\n\n", text)
        
        # 연속된 공백 정리
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r' +', ' ', text)
        
        return text.strip()
    
    def _extract_section(self, text: str) -> str:
        """텍스트에서 섹션 정보 추출"""
        # 제목 패턴 찾기
        for pattern in self.structure_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group().strip()
        
        # 첫 줄이 제목일 가능성
        first_line = text.split('\n')[0].strip()
        if len(first_line) < 100:  # 제목은 보통 짧음
            return first_line
        
        return "본문"
    
    def _extract_keywords(self, text: str) -> List[str]:
        """간단한 키워드 추출"""
        # 도로 관련 전문용어들
        road_terms = [
            '도로', '차로', '중앙분리대', '보도', '자전거도로',
            '교차로', '회전교차로', '지하차도', '육교', '터널',
            '교량', '포장', '아스팔트', '콘크리트', '배수',
            '안전시설', '방호울타리', '표지판', '신호등',
            '설계속도', '계획교통량', '서비스수준', '용량분석',
            '토공', '성토', '절토', '옹벽', '비탈면'
        ]
        
        found_keywords = []
        text_lower = text.lower()
        
        for term in road_terms:
            if term in text:
                found_keywords.append(term)
        
        return found_keywords[:5]  # 최대 5개


def main():
    """테스트 함수"""
    from preprocessing.document_loader import DocumentLoader
    
    # 테스트용 문서 로드
    loader = DocumentLoader()
    
    # 하나의 PDF로 테스트
    test_file = "도로설계요령(2020)/제1권 도로계획및 구조.pdf"
    documents = loader.load_pdf(test_file)
    
    if documents:
        # 청킹 테스트
        chunker = KoreanTextChunker(chunk_size=800, chunk_overlap=100)
        chunks = chunker.chunk_documents(documents[:3])  # 처음 3페이지만 테스트
        
        print(f"테스트 결과: {len(chunks)}개 청크 생성")
        
        # 첫 번째 청크 정보 출력
        if chunks:
            first_chunk = chunks[0]
            print("\n" + "="*50)
            print("첫 번째 청크 예시:")
            print("="*50)
            print(f"섹션: {first_chunk.metadata['section']}")
            print(f"키워드: {first_chunk.metadata['keywords']}")
            print(f"청크 크기: {first_chunk.metadata['chunk_size']}")
            print(f"내용 (앞부분):\n{first_chunk.page_content[:200]}...")


if __name__ == "__main__":
    main()
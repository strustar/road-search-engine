"""
RAG 1단계: Document Loader
문서 로드 모듈 - PDF 파일을 읽어 Document 객체로 변환
"""
import os
from typing import List, Dict, Optional
from pathlib import Path
from langchain.schema import Document
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentLoader:
    """문서 로더 클래스 - 다양한 형식의 문서를 로드"""
    
    def __init__(self, encoding: str = 'utf-8'):
        self.encoding = encoding
        self.loaded_documents = []
        
    def load_pdf(self, file_path: str) -> List[Document]:
        """단일 PDF 파일 로드"""
        try:
            loader = PyPDFLoader(file_path)
            documents = loader.load()
            
            # 메타데이터 추가
            for doc in documents:
                doc.metadata['source_type'] = 'pdf'
                doc.metadata['file_name'] = Path(file_path).name
                doc.metadata['file_path'] = file_path
                
            logger.info(f"PDF 로드 완료: {file_path} - {len(documents)}개 페이지")
            return documents
            
        except Exception as e:
            logger.error(f"PDF 로드 실패: {file_path} - {str(e)}")
            return []
    
    def load_directory(self, directory_path: str, glob_pattern: str = "**/*.pdf") -> List[Document]:
        """디렉토리의 모든 PDF 파일 로드"""
        try:
            loader = DirectoryLoader(
                directory_path,
                glob=glob_pattern,
                loader_cls=PyPDFLoader
            )
            documents = loader.load()
            
            # 디렉토리별 메타데이터 추가
            for doc in documents:
                doc.metadata['source_directory'] = directory_path
                doc.metadata['source_type'] = 'pdf'
                
            logger.info(f"디렉토리 로드 완료: {directory_path} - {len(documents)}개 문서")
            return documents
            
        except Exception as e:
            logger.error(f"디렉토리 로드 실패: {directory_path} - {str(e)}")
            return []
    
    def load_multiple_pdfs(self, file_paths: List[str]) -> List[Document]:
        """여러 PDF 파일을 한번에 로드"""
        all_documents = []
        
        for file_path in file_paths:
            if os.path.exists(file_path):
                docs = self.load_pdf(file_path)
                all_documents.extend(docs)
            else:
                logger.warning(f"파일이 존재하지 않음: {file_path}")
                
        logger.info(f"총 {len(all_documents)}개 문서 로드 완료")
        self.loaded_documents = all_documents
        return all_documents
    
    def get_document_info(self) -> Dict:
        """로드된 문서 정보 반환"""
        if not self.loaded_documents:
            return {"status": "No documents loaded"}
            
        info = {
            "total_documents": len(self.loaded_documents),
            "total_pages": sum(1 for doc in self.loaded_documents),
            "sources": list(set(doc.metadata.get('file_name', 'Unknown') 
                              for doc in self.loaded_documents)),
            "total_characters": sum(len(doc.page_content) 
                                  for doc in self.loaded_documents)
        }
        return info
    
    def clear_documents(self):
        """로드된 문서 초기화"""
        self.loaded_documents = []
        logger.info("문서 초기화 완료")


def main():
    """테스트 실행"""
    loader = DocumentLoader()
    
    # 도로설계요령 PDF 로드 테스트
    road_design_dir = "도로설계요령(2020)"
    if os.path.exists(road_design_dir):
        documents = loader.load_directory(road_design_dir)
        info = loader.get_document_info()
        
        print("=" * 50)
        print("도로설계요령 문서 로드 결과")
        print("=" * 50)
        print(f"총 문서 수: {info['total_documents']}")
        print(f"총 페이지 수: {info['total_pages']}")
        print(f"총 문자 수: {info['total_characters']:,}")
        print(f"소스 파일:")
        for source in info['sources']:
            print(f"  - {source}")
    
    # 실무지침 PDF 로드 테스트
    practice_guide_dir = "실무지침(2020)"
    if os.path.exists(practice_guide_dir):
        loader.clear_documents()
        documents = loader.load_directory(practice_guide_dir)
        info = loader.get_document_info()
        
        print("\n" + "=" * 50)
        print("실무지침 문서 로드 결과")
        print("=" * 50)
        print(f"총 문서 수: {info['total_documents']}")
        print(f"총 페이지 수: {info['total_pages']}")
        print(f"총 문자 수: {info['total_characters']:,}")
        print(f"소스 파일:")
        for source in info['sources']:
            print(f"  - {source}")


if __name__ == "__main__":
    main()
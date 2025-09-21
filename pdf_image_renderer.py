"""
PDF 이미지 렌더링 모듈
PDF 페이지를 이미지로 변환하고 키워드 영역을 하이라이트하는 기능
"""

import fitz  # PyMuPDF
import os
import io
import base64
from PIL import Image, ImageDraw, ImageFont
from typing import List, Dict, Any, Tuple, Optional
import hashlib
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PDFImageRenderer:
    """PDF 페이지를 이미지로 렌더링하고 키워드 하이라이트 기능 제공"""

    def __init__(self,
                 pdf_directory: str,
                 cache_directory: str = "./image_cache",
                 dpi: int = 150):
        """
        초기화

        Args:
            pdf_directory: PDF 파일들이 있는 디렉토리
            cache_directory: 이미지 캐시 저장 디렉토리
            dpi: 렌더링 해상도 (기본 150dpi)
        """
        self.pdf_directory = pdf_directory
        self.cache_directory = cache_directory
        self.dpi = dpi
        self.scale_factor = dpi / 72.0  # PDF 기본 72dpi에서 변환

        # 캐시 디렉토리 생성
        os.makedirs(cache_directory, exist_ok=True)

        logger.info(f"PDF 이미지 렌더러 초기화: DPI={dpi}, 캐시경로={cache_directory}")

    def get_cache_key(self,
                     file_path: str,
                     page_num: int,
                     keywords: List[str] = None) -> str:
        """캐시 키 생성"""
        key_data = f"{file_path}:{page_num}:{self.dpi}"
        if keywords:
            key_data += f":{':'.join(sorted(keywords))}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def render_page_to_image(self,
                           file_path: str,
                           page_num: int,
                           use_cache: bool = True) -> Optional[Image.Image]:
        """
        PDF 페이지를 PIL Image로 렌더링

        Args:
            file_path: PDF 파일 경로
            page_num: 페이지 번호 (0부터 시작)
            use_cache: 캐시 사용 여부

        Returns:
            PIL Image 객체 또는 None
        """
        try:
            # 캐시 확인
            cache_key = self.get_cache_key(file_path, page_num)
            cache_path = os.path.join(self.cache_directory, f"{cache_key}.png")

            if use_cache and os.path.exists(cache_path):
                logger.info(f"캐시에서 이미지 로드: {cache_path}")
                return Image.open(cache_path)

            # PDF 열기
            full_path = os.path.join(self.pdf_directory, file_path)
            if not os.path.exists(full_path):
                logger.error(f"PDF 파일을 찾을 수 없음: {full_path}")
                return None

            doc = fitz.open(full_path)

            # 페이지 유효성 검사
            if page_num >= doc.page_count or page_num < 0:
                logger.error(f"잘못된 페이지 번호: {page_num} (총 {doc.page_count}페이지)")
                doc.close()
                return None

            # 페이지 렌더링
            page = doc[page_num]
            mat = fitz.Matrix(self.scale_factor, self.scale_factor)
            pix = page.get_pixmap(matrix=mat)

            # PIL Image로 변환
            img_data = pix.tobytes("png")
            image = Image.open(io.BytesIO(img_data))

            # 캐시에 저장
            if use_cache:
                image.save(cache_path, "PNG", optimize=True)
                logger.info(f"이미지 캐시 저장: {cache_path}")

            doc.close()
            logger.info(f"페이지 렌더링 완료: {file_path} 페이지 {page_num}")

            return image

        except Exception as e:
            logger.error(f"페이지 렌더링 실패: {e}")
            return None

    def find_text_positions(self,
                          file_path: str,
                          page_num: int,
                          keywords: List[str]) -> List[Dict[str, Any]]:
        """
        PDF 페이지에서 키워드들의 위치 좌표 찾기

        Args:
            file_path: PDF 파일 경로
            page_num: 페이지 번호
            keywords: 찾을 키워드 리스트

        Returns:
            키워드 위치 정보 리스트
        """
        positions = []

        try:
            full_path = os.path.join(self.pdf_directory, file_path)
            doc = fitz.open(full_path)

            if page_num >= doc.page_count or page_num < 0:
                doc.close()
                return positions

            page = doc[page_num]

            for keyword in keywords:
                # 텍스트 검색
                text_instances = page.search_for(keyword)

                for rect in text_instances:
                    # 좌표를 이미지 스케일로 변환
                    scaled_rect = rect * self.scale_factor

                    position = {
                        'keyword': keyword,
                        'bbox': [scaled_rect.x0, scaled_rect.y0,
                                scaled_rect.x1, scaled_rect.y1],
                        'width': scaled_rect.width,
                        'height': scaled_rect.height
                    }
                    positions.append(position)

            doc.close()
            logger.info(f"키워드 위치 찾기 완료: {len(positions)}개 발견")

        except Exception as e:
            logger.error(f"키워드 위치 찾기 실패: {e}")

        return positions

    def highlight_keywords(self,
                         image: Image.Image,
                         positions: List[Dict[str, Any]],
                         highlight_color: str = "rgba(255, 255, 0, 128)") -> Image.Image:
        """
        이미지에 키워드 하이라이트 추가

        Args:
            image: 원본 이미지
            positions: 키워드 위치 정보
            highlight_color: 하이라이트 색상

        Returns:
            하이라이트가 추가된 이미지
        """
        try:
            # RGBA 모드로 변환
            if image.mode != 'RGBA':
                image = image.convert('RGBA')

            # 오버레이 생성
            overlay = Image.new('RGBA', image.size, (255, 255, 255, 0))
            draw = ImageDraw.Draw(overlay)

            # 하이라이트 그리기
            for pos in positions:
                bbox = pos['bbox']
                draw.rectangle(bbox, fill=highlight_color)

            # 오버레이 합성
            highlighted = Image.alpha_composite(image, overlay)

            logger.info(f"하이라이트 추가 완료: {len(positions)}개 영역")
            return highlighted

        except Exception as e:
            logger.error(f"하이라이트 추가 실패: {e}")
            return image

    def crop_keyword_area(self,
                         image: Image.Image,
                         positions: List[Dict[str, Any]],
                         padding: int = 50) -> Optional[Image.Image]:
        """
        키워드 영역만 크롭

        Args:
            image: 원본 이미지
            positions: 키워드 위치 정보
            padding: 여백 픽셀

        Returns:
            크롭된 이미지 또는 None
        """
        if not positions:
            return None

        try:
            # 모든 키워드 영역을 포함하는 바운딩 박스 계산
            all_bboxes = [pos['bbox'] for pos in positions]

            min_x = min(bbox[0] for bbox in all_bboxes) - padding
            min_y = min(bbox[1] for bbox in all_bboxes) - padding
            max_x = max(bbox[2] for bbox in all_bboxes) + padding
            max_y = max(bbox[3] for bbox in all_bboxes) + padding

            # 이미지 경계 내로 제한
            min_x = max(0, min_x)
            min_y = max(0, min_y)
            max_x = min(image.width, max_x)
            max_y = min(image.height, max_y)

            # 크롭
            cropped = image.crop((min_x, min_y, max_x, max_y))

            logger.info(f"키워드 영역 크롭 완료: {cropped.size}")
            return cropped

        except Exception as e:
            logger.error(f"키워드 영역 크롭 실패: {e}")
            return None

    def render_page_with_highlights(self,
                                  file_path: str,
                                  page_num: int,
                                  keywords: List[str],
                                  crop_to_keywords: bool = False,
                                  highlight_color: str = "rgba(255, 255, 0, 128)") -> Optional[str]:
        """
        키워드 하이라이트가 있는 페이지 이미지를 Base64로 반환

        Args:
            file_path: PDF 파일 경로
            page_num: 페이지 번호
            keywords: 하이라이트할 키워드들
            crop_to_keywords: 키워드 영역만 크롭할지 여부
            highlight_color: 하이라이트 색상

        Returns:
            Base64 인코딩된 이미지 문자열 또는 None
        """
        try:
            # 페이지 렌더링
            image = self.render_page_to_image(file_path, page_num)
            if image is None:
                return None

            if keywords:
                # 키워드 위치 찾기
                positions = self.find_text_positions(file_path, page_num, keywords)

                if positions:
                    # 하이라이트 추가
                    image = self.highlight_keywords(image, positions, highlight_color)

                    # 키워드 영역만 크롭 (옵션)
                    if crop_to_keywords:
                        cropped = self.crop_keyword_area(image, positions)
                        if cropped:
                            image = cropped

            # Base64로 변환
            buffer = io.BytesIO()
            image.save(buffer, format='PNG', optimize=True)
            img_b64 = base64.b64encode(buffer.getvalue()).decode()

            logger.info(f"이미지 생성 완료: {file_path} 페이지 {page_num}")
            return img_b64

        except Exception as e:
            logger.error(f"하이라이트 이미지 생성 실패: {e}")
            return None

    def get_pdf_info(self, file_path: str) -> Dict[str, Any]:
        """PDF 파일 정보 반환"""
        try:
            full_path = os.path.join(self.pdf_directory, file_path)
            doc = fitz.open(full_path)

            info = {
                'page_count': doc.page_count,
                'title': doc.metadata.get('title', ''),
                'author': doc.metadata.get('author', ''),
                'subject': doc.metadata.get('subject', ''),
                'file_size': os.path.getsize(full_path)
            }

            doc.close()
            return info

        except Exception as e:
            logger.error(f"PDF 정보 조회 실패: {e}")
            return {}


def main():
    """테스트 함수"""
    print("PDF 이미지 렌더러 테스트 시작")

    # 테스트 설정
    pdf_dir = "./도로설계요령(2020)"
    renderer = PDFImageRenderer(pdf_dir, dpi=150)

    # PDF 파일 목록 확인
    if os.path.exists(pdf_dir):
        pdf_files = [f for f in os.listdir(pdf_dir) if f.endswith('.pdf')]
        if pdf_files:
            test_file = pdf_files[0]
            print(f"테스트 파일: {test_file}")

            # PDF 정보 출력
            info = renderer.get_pdf_info(test_file)
            print(f"페이지 수: {info.get('page_count', 0)}")

            # 첫 번째 페이지 렌더링 테스트
            image = renderer.render_page_to_image(test_file, 0)
            if image:
                print(f"[성공] 페이지 렌더링 성공: {image.size}")
            else:
                print("[실패] 페이지 렌더링 실패")

            # 키워드 검색 테스트
            keywords = ["도로", "설계"]
            positions = renderer.find_text_positions(test_file, 0, keywords)
            print(f"키워드 '{keywords}' 발견: {len(positions)}개")

            # 하이라이트 이미지 생성 테스트
            highlighted_b64 = renderer.render_page_with_highlights(
                test_file, 0, keywords, crop_to_keywords=True
            )
            if highlighted_b64:
                print(f"[성공] 하이라이트 이미지 생성 성공: {len(highlighted_b64)} bytes")
            else:
                print("[실패] 하이라이트 이미지 생성 실패")
        else:
            print("PDF 파일이 없습니다.")
    else:
        print(f"PDF 디렉토리가 없습니다: {pdf_dir}")


if __name__ == "__main__":
    main()
"""
URL 파싱 및 검증을 위한 모듈
"""

import re
from enum import Enum
from typing import Optional, Tuple, Dict
from urllib.parse import urlparse, urljoin
from dataclasses import dataclass
from ..config import (
    COUPANG_PRODUCT_PATTERN,
    NAVER_SHOPPING_PATTERN,
    SITE_URLS,
    SUPPORTED_SITES
)

class SiteType(str, Enum):
    """지원하는 사이트 타입"""
    COUPANG = 'coupang'
    NAVER = 'naver'
    UNKNOWN = 'unknown'

@dataclass
class URLValidationResult:
    """URL 검증 결과를 담는 데이터 클래스"""
    is_valid: bool
    error_message: Optional[str] = None
    site_type: Optional[str] = None
    product_id: Optional[str] = None

class URLParser:
    """URL 파싱 및 검증을 위한 클래스"""
    
    @staticmethod
    def normalize_url(url: str) -> str:
        """
        URL을 정규화합니다.
        
        Args:
            url (str): 정규화할 URL
            
        Returns:
            str: 정규화된 URL
        """
        # 공백 제거
        url = url.strip()
        
        # 프로토콜이 없는 경우 https:// 추가
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        # URL 파싱 및 재조합하여 정규화
        try:
            parsed = urlparse(url)
            # URL 재조합 시 기본 프로토콜을 https로 설정
            if not parsed.scheme:
                parsed = parsed._replace(scheme='https')
            return parsed.geturl()
        except Exception:
            return url
    
    @staticmethod
    def validate_url(url: str) -> URLValidationResult:
        """
        URL이 유효한 형식인지 검사합니다.
        
        Args:
            url (str): 검사할 URL
            
        Returns:
            URLValidationResult: URL 검증 결과
        """
        print(f"\n[DEBUG] 입력된 URL: {url}")
        
        if not url:
            return URLValidationResult(
                is_valid=False,
                error_message="URL이 비어있습니다."
            )
        
        try:
            # URL 정규화
            normalized_url = URLParser.normalize_url(url)
            print(f"[DEBUG] 정규화된 URL: {normalized_url}")
            
            result = urlparse(normalized_url)
            print(f"[DEBUG] 파싱된 URL 구성요소:")
            print(f"- scheme: {result.scheme}")
            print(f"- netloc: {result.netloc}")
            print(f"- path: {result.path}")
            
            # 기본 URL 형식 검증
            if not all([result.scheme, result.netloc]):
                print("[DEBUG] URL 형식 검증 실패: scheme 또는 netloc 없음")
                return URLValidationResult(
                    is_valid=False,
                    error_message="유효하지 않은 URL 형식입니다."
                )
            
            # 지원하는 사이트인지 확인
            supported_domains = [urlparse(url).netloc for url in SITE_URLS.values()]
            print(f"[DEBUG] 지원하는 도메인: {supported_domains}")
            print(f"[DEBUG] 현재 도메인: {result.netloc}")
            
            if not any(domain in result.netloc for domain in supported_domains):
                print("[DEBUG] 지원하지 않는 사이트")
                return URLValidationResult(
                    is_valid=False,
                    error_message=f"지원하지 않는 사이트입니다. 지원하는 사이트: {', '.join(SUPPORTED_SITES)}"
                )
            
            # 사이트 식별 및 상품 ID 추출
            site_info = URLParser.identify_site(normalized_url)
            print(f"[DEBUG] 식별된 사이트 정보: {site_info}")
            
            if not site_info:
                print("[DEBUG] 상품 페이지 URL이 아님")
                return URLValidationResult(
                    is_valid=False,
                    error_message="상품 페이지 URL이 아닙니다."
                )
                
            return URLValidationResult(
                is_valid=True,
                site_type=site_info[0],
                product_id=site_info[1]
            )
            
        except Exception as e:
            print(f"[DEBUG] 예외 발생: {str(e)}")
            return URLValidationResult(
                is_valid=False,
                error_message=f"URL 검증 중 오류 발생: {str(e)}"
            )
    
    @staticmethod
    def identify_site(url: str) -> Optional[Tuple[str, str]]:
        """
        URL을 분석하여 사이트 종류와 상품 ID를 반환합니다.
        
        Args:
            url (str): 분석할 URL
            
        Returns:
            Optional[Tuple[str, str]]: (사이트 종류, 상품 ID) 튜플 또는 None
        """

        # 쿠팡 URL 체크
        coupang_match = re.match(COUPANG_PRODUCT_PATTERN, url)
        if coupang_match:
            return ('coupang', coupang_match.group(1))
            
        # 네이버 쇼핑 URL 체크
        naver_match = re.match(NAVER_SHOPPING_PATTERN, url)
        if naver_match:
            return ('naver', naver_match.group(1))
            
        return None
    
    @staticmethod
    def get_site_info(url: str) -> Dict[str, str]:
        """
        URL에서 사이트 정보를 추출하여 반환합니다.
        
        Args:
            url (str): 분석할 URL
            
        Returns:
            Dict[str, str]: 사이트 정보를 담은 딕셔너리
        """
        validation_result = URLParser.validate_url(url)
        
        if not validation_result.is_valid:
            raise ValueError(validation_result.error_message)
            
        return {
            'site_type': validation_result.site_type,
            'product_id': validation_result.product_id,
            'normalized_url': URLParser.normalize_url(url)
        }
        
    def get_site_type(self, url: str) -> SiteType:
        """
        URL에서 사이트 타입을 추출합니다.
        
        Args:
            url (str): 분석할 URL
            
        Returns:
            SiteType: 사이트 타입
        """
        site_info = self.identify_site(url)
        if not site_info:
            return SiteType.UNKNOWN
        return SiteType(site_info[0])
        
    def extract_product_id(self, url: str) -> Optional[str]:
        """
        URL에서 상품 ID를 추출합니다.
        
        Args:
            url (str): 분석할 URL
            
        Returns:
            Optional[str]: 상품 ID 또는 None
        """
        site_info = self.identify_site(url)
        if not site_info:
            return None
        return site_info[1] 
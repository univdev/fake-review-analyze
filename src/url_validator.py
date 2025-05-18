"""
URL 검증 도구

사용법:
    python url_validator.py [URL]
    
예시:
    python url_validator.py https://www.coupang.com/vp/products/123456
"""

import sys
from utils.url_parser import URLParser
from config import SUPPORTED_SITES

def print_usage():
    """사용법을 출력합니다."""
    print(__doc__)

def validate_and_print_result(url: str):
    """URL을 검증하고 결과를 출력합니다."""
    print(f"\n입력된 URL: {url}")
    print("-" * 50)
    
    # URL 검증
    result = URLParser.validate_url(url)
    
    if result.is_valid:
        print("✅ URL 검증 성공")
        print(f"사이트: {result.site_type}")
        print(f"상품 ID: {result.product_id}")
        
        # 정규화된 URL 출력
        normalized_url = URLParser.normalize_url(url)
        if normalized_url != url:
            print(f"정규화된 URL: {normalized_url}")
    else:
        print("❌ URL 검증 실패")
        print(f"오류: {result.error_message}")
        
        if "지원하지 않는 사이트" in result.error_message:
            print(f"\n현재 지원하는 사이트:")
            for site in SUPPORTED_SITES:
                print(f"- {site}")

def main():
    """메인 함수"""
    # 명령행 인자 확인
    if len(sys.argv) != 2:
        print_usage()
        sys.exit(1)
    
    # URL 검증
    url = sys.argv[1]
    validate_and_print_result(url)

if __name__ == "__main__":
    main() 
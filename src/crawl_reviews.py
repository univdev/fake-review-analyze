"""
리뷰 크롤링 스크립트

사용법:
    python crawl_reviews.py [URL] [페이지수]
    
예시:
    python crawl_reviews.py https://www.coupang.com/vp/products/123456 5
"""

import sys
import os
import argparse
import atexit
from typing import Optional, Tuple
from urllib.parse import urlparse, parse_qs
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

from src.utils.webdriver import create_webdriver
from src.utils.url_parser import URLParser
from src.utils.page_navigator import PageNavigator
from src.utils.csv_exporter import export_to_csv
from src.models.review import Review
from src.crawlers.crawler_factory import ReviewCrawlerFactory
from src.utils.exceptions import CrawlerException
from src.utils.logger import crawler_logger
from src.utils.shutdown import shutdown_handler

def parse_arguments() -> Tuple[str, Optional[int]]:
    """커맨드라인 인자를 파싱합니다."""
    parser = argparse.ArgumentParser(description="상품 리뷰 크롤링 도구")
    parser.add_argument("url", help="상품 URL")
    parser.add_argument("pages", type=int, nargs="?", default=None,
                       help="크롤링할 페이지 수 (기본값: 전체)")
    
    args = parser.parse_args()
    return args.url, args.pages

def setup_webdriver() -> webdriver.Chrome:
    """WebDriver를 설정합니다."""
    driver = create_webdriver()
    
    # 종료 처리기에 WebDriver 등록
    shutdown_handler.register_driver(driver)
    
    return driver

def cleanup_csv_exporter():
    """CSV 파일을 정리합니다."""
    try:
        export_to_csv([], {}, "")
    except Exception as e:
        crawler_logger.error("CSV 파일 정리 중 오류 발생", error=e)

def main():
    """메인 함수"""
    # 인자 파싱
    url, max_pages = parse_arguments()
    
    print("🚀 리뷰 크롤링을 시작합니다...")
    print(f"URL: {url}")
    print(f"크롤링할 페이지 수: {'전체' if max_pages is None else max_pages}")
    print("-" * 50)
    
    # URL 검증
    url_parser = URLParser()
    validation_result = url_parser.validate_url(url)
    if not validation_result.is_valid:
        print(f"❌ {validation_result.error_message}")
        sys.exit(1)
    
    try:
        # 종료 처리 설정
        shutdown_handler.setup()
        
        # CSV 정리 작업 등록
        shutdown_handler.register_cleanup(cleanup_csv_exporter)
        atexit.register(shutdown_handler.cleanup_on_exit)
        
        # WebDriver 초기화
        with setup_webdriver() as driver:
            try:
                # 크롤러 생성
                crawler = ReviewCrawlerFactory.create_crawler(url, driver)
                if not crawler:
                    sys.exit(1)
                
                # 상품 정보 수집
                print("\n📦 상품 정보 수집 중...")
                product_info = crawler.get_product_info()
                if product_info['name']:
                    print(f"상품명: {product_info['name']}")
                    print(f"평균 평점: {product_info['average_rating']}")
                    print(f"리뷰 수: {product_info['review_count']}")
                else:
                    print("⚠️ 상품 정보를 가져오지 못했습니다.")
                
                # 리뷰 크롤링
                print("\n📝 리뷰 수집 중...")
                reviews = crawler.crawl_reviews(max_pages)
                
                if not reviews:
                    print("❌ 수집된 리뷰가 없습니다.")
                    sys.exit(1)
                
                print(f"✅ 총 {len(reviews)}개의 리뷰를 수집했습니다.")
                
                # CSV 파일로 저장
                print("\n💾 CSV 파일 저장 중...")
                filepath = export_to_csv(reviews, product_info, crawler.site_type)
                
                print("\n✨ 크롤링이 완료되었습니다!")
                print(f"CSV 파일 경로: {filepath}")
                
            except KeyboardInterrupt:
                print("\n\n⚠️ 사용자에 의해 크롤링이 중단되었습니다.")
                sys.exit(0)
            except Exception as e:
                print(f"\n❌ 오류 발생: {str(e)}")
                sys.exit(1)
    except Exception as e:
        print(f"\n❌ 오류 발생: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 
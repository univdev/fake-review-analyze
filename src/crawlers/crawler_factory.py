"""
크롤러 팩토리 모듈
"""

from typing import Optional
from selenium.webdriver.remote.webdriver import WebDriver
from src.crawlers.base_crawler import ReviewCrawler
from src.crawlers.coupang_crawler import CoupangReviewCrawler
from src.crawlers.naver_crawler import NaverReviewCrawler
from src.utils.url_parser import URLParser, SiteType

class ReviewCrawlerFactory:
    """리뷰 크롤러 팩토리"""
    
    @staticmethod
    def create_crawler(url: str, driver: WebDriver) -> Optional[ReviewCrawler]:
        """
        URL에 맞는 크롤러를 생성합니다.
        
        Args:
            url (str): 상품 URL
            driver (WebDriver): Selenium WebDriver 인스턴스
            
        Returns:
            Optional[ReviewCrawler]: 크롤러 인스턴스. URL이 유효하지 않은 경우 None 반환
        """
        url_parser = URLParser()
        site_type = url_parser.get_site_type(url)
        product_id = url_parser.extract_product_id(url)
        
        if not product_id:
            print("❌ 상품 ID를 추출할 수 없습니다.")
            return None
        
        if site_type == SiteType.COUPANG:
            return CoupangReviewCrawler(driver, product_id)
        elif site_type == SiteType.NAVER:
            return NaverReviewCrawler(driver, product_id)
        else:
            print(f"❌ 지원하지 않는 사이트입니다: {site_type}")
            return None 
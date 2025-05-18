"""
페이지 탐색 범위 설정 및 관리를 위한 모듈
"""

from typing import Optional, Dict, Tuple
from dataclasses import dataclass
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

@dataclass
class PageInfo:
    """페이지 정보를 담는 데이터 클래스"""
    total_pages: int
    current_page: int = 1
    requested_pages: Optional[int] = None
    
    @property
    def pages_to_crawl(self) -> int:
        """크롤링할 페이지 수를 반환합니다."""
        if self.requested_pages is None or self.requested_pages > self.total_pages:
            return self.total_pages
        return self.requested_pages

class PageNavigator:
    """페이지 탐색 및 범위 설정을 위한 클래스"""
    
    def __init__(self, driver: WebDriver):
        """
        PageNavigator 초기화
        
        Args:
            driver (WebDriver): Selenium WebDriver 인스턴스
        """
        self.driver = driver
        self._page_info: Optional[PageInfo] = None
        
    @property
    def page_info(self) -> Optional[PageInfo]:
        """현재 페이지 정보를 반환합니다."""
        return self._page_info
    
    def get_total_pages(self, site_type: str, product_id: str) -> int:
        """
        특정 상품의 총 리뷰 페이지 수를 확인합니다.
        
        Args:
            site_type (str): 사이트 종류 ('coupang' 또는 'naver')
            product_id (str): 상품 ID
            
        Returns:
            int: 총 페이지 수
            
        Raises:
            ValueError: 지원하지 않는 사이트이거나 페이지 수를 가져오는데 실패한 경우
        """
        if site_type == 'coupang':
            return self._get_coupang_total_pages()
        elif site_type == 'naver':
            return self._get_naver_total_pages()
        else:
            raise ValueError(f"지원하지 않는 사이트입니다: {site_type}")
    
    def _get_coupang_total_pages(self) -> int:
        """쿠팡 상품의 총 리뷰 페이지 수를 확인합니다."""
        try:
            # 페이지네이션 요소 대기
            pagination = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "js_reviewArticlePageNavigationContainer"))
            )
            
            # 마지막 페이지 버튼 찾기
            last_page_btn = pagination.find_elements(By.CSS_SELECTOR, "button.js_reviewArticlePageNavigationButton")[-1]
            return int(last_page_btn.get_attribute("data-page"))
            
        except (TimeoutException, NoSuchElementException, ValueError) as e:
            # 리뷰가 없거나 1페이지만 있는 경우
            try:
                # 리뷰 개수 확인
                review_count = self.driver.find_element(By.CLASS_NAME, "js_reviewArticleCount").text
                return max(1, int(int(review_count.replace(",", "")) / 10))
            except:
                return 1
    
    def _get_naver_total_pages(self) -> int:
        """네이버 쇼핑 상품의 총 리뷰 페이지 수를 확인합니다."""
        try:
            # 페이지네이션 요소 대기
            pagination = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "pagination_pagination__JW7zT"))
            )
            
            # 마지막 페이지 버튼 찾기
            last_page_btn = pagination.find_elements(By.CSS_SELECTOR, "a.pagination_btn__mEwdB")[-1]
            return int(last_page_btn.text)
            
        except (TimeoutException, NoSuchElementException, ValueError) as e:
            # 리뷰가 없거나 1페이지만 있는 경우
            try:
                # 리뷰 개수 확인
                review_count = self.driver.find_element(By.CLASS_NAME, "review_total_count__PjXXP").text
                return max(1, int(int(review_count.replace(",", "")) / 20))  # 네이버는 페이지당 20개
            except:
                return 1
    
    def set_page_range(self, total_pages: int, requested_pages: Optional[int] = None) -> PageInfo:
        """
        크롤링할 페이지 범위를 설정합니다.
        
        Args:
            total_pages (int): 총 페이지 수
            requested_pages (Optional[int]): 사용자가 요청한 페이지 수
            
        Returns:
            PageInfo: 설정된 페이지 정보
            
        Raises:
            ValueError: 페이지 수가 0 이하인 경우
        """
        if total_pages <= 0:
            raise ValueError("총 페이지 수는 1 이상이어야 합니다.")
            
        if requested_pages is not None and requested_pages <= 0:
            raise ValueError("요청 페이지 수는 1 이상이어야 합니다.")
            
        self._page_info = PageInfo(
            total_pages=total_pages,
            requested_pages=requested_pages
        )
        
        return self._page_info
    
    def go_to_page(self, page_number: int, site_type: str) -> bool:
        """
        특정 페이지로 이동합니다.
        
        Args:
            page_number (int): 이동할 페이지 번호
            site_type (str): 사이트 종류 ('coupang' 또는 'naver')
            
        Returns:
            bool: 페이지 이동 성공 여부
        """
        if not self._page_info:
            raise ValueError("페이지 범위가 설정되지 않았습니다. set_page_range()를 먼저 호출하세요.")
            
        if page_number < 1 or page_number > self._page_info.total_pages:
            return False
            
        try:
            if site_type == 'coupang':
                return self._go_to_coupang_page(page_number)
            elif site_type == 'naver':
                return self._go_to_naver_page(page_number)
            else:
                raise ValueError(f"지원하지 않는 사이트입니다: {site_type}")
                
        except Exception as e:
            print(f"페이지 이동 중 오류 발생: {str(e)}")
            return False
    
    def _go_to_coupang_page(self, page_number: int) -> bool:
        """쿠팡 리뷰의 특정 페이지로 이동합니다."""
        try:
            # 페이지네이션 버튼 찾기
            pagination = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "js_reviewArticlePageNavigationContainer"))
            )
            
            # 페이지 버튼 클릭
            page_btn = pagination.find_element(By.CSS_SELECTOR, f"button[data-page='{page_number}']")
            page_btn.click()
            
            # 페이지 로딩 대기
            WebDriverWait(self.driver, 10).until(
                EC.staleness_of(page_btn)
            )
            
            self._page_info.current_page = page_number
            return True
            
        except Exception as e:
            print(f"쿠팡 페이지 이동 중 오류: {str(e)}")
            return False
    
    def _go_to_naver_page(self, page_number: int) -> bool:
        """네이버 쇼핑 리뷰의 특정 페이지로 이동합니다."""
        try:
            # 페이지네이션 버튼 찾기
            pagination = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "pagination_pagination__JW7zT"))
            )
            
            # 페이지 버튼 클릭
            page_btn = pagination.find_element(By.CSS_SELECTOR, f"a[aria-label='페이지 {page_number}']")
            page_btn.click()
            
            # 페이지 로딩 대기
            WebDriverWait(self.driver, 10).until(
                EC.staleness_of(page_btn)
            )
            
            self._page_info.current_page = page_number
            return True
            
        except Exception as e:
            print(f"네이버 페이지 이동 중 오류: {str(e)}")
            return False 
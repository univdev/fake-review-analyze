"""
크롤러 기본 인터페이스
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Tuple
from contextlib import contextmanager
import socket
from urllib3.exceptions import MaxRetryError, NewConnectionError
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, 
    NoSuchElementException,
    WebDriverException,
    StaleElementReferenceException,
    ElementNotInteractableException,
    ElementClickInterceptedException
)
from selenium.webdriver.common.by import By

from ..models.review import Review
from ..utils.page_navigator import PageNavigator
from ..utils.exceptions import (
    CrawlerContext,
    CrawlerException,
    ElementNotFoundError,
    TimeoutError,
    WebDriverError,
    NavigationError,
    ParsingError,
    NetworkError,
    StaleElementError,
    InteractionError
)
from ..utils.retry import retry
from ..utils.rate_limiter import rate_limiter, RequestType
from ..utils.logger import crawler_logger
import os
from datetime import datetime
import time

class ReviewCrawler(ABC):
    """리뷰 크롤러 기본 클래스"""
    
    def __init__(self, driver: WebDriver, product_id: str):
        """
        ReviewCrawler 초기화
        
        Args:
            driver (WebDriver): Selenium WebDriver 인스턴스
            product_id (str): 상품 ID
        """
        self.driver = driver
        self.product_id = product_id
        self.page_navigator = PageNavigator(driver)
        crawler_logger.info(
            f"크롤러 초기화",
            {"site_type": self.site_type, "product_id": product_id}
        )
        
    @property
    @abstractmethod
    def site_type(self) -> str:
        """사이트 타입을 반환합니다. ('coupang' 또는 'naver')"""
        pass
        
    def get_context(self, page_number: Optional[int] = None, element_info: Optional[Dict[str, Any]] = None) -> CrawlerContext:
        """현재 크롤러의 컨텍스트 정보를 생성합니다."""
        return CrawlerContext(
            url=self.driver.current_url,
            site_type=self.site_type,
            product_id=self.product_id,
            page_number=page_number,
            element_info=element_info
        )
        
    @contextmanager
    def error_handler(self, operation: str, page_number: Optional[int] = None, element_info: Optional[Dict[str, Any]] = None):
        """
        예외 처리를 위한 컨텍스트 매니저
        
        Args:
            operation (str): 수행 중인 작업 설명
            page_number (Optional[int]): 현재 페이지 번호
            element_info (Optional[Dict[str, Any]]): 처리 중인 요소 정보
        """
        context = self.get_context(page_number, element_info)
        try:
            yield
        except (socket.gaierror, ConnectionError, MaxRetryError, NewConnectionError) as e:
            crawler_logger.error(
                f"{operation} 중 네트워크 오류: {str(e)}",
                error=e,
                context=context.__dict__
            )
            rate_limiter.on_failure(self.site_type, RequestType.NAVIGATION)
            raise NetworkError(f"{operation} 중 네트워크 오류: {str(e)}", context) from e
        except TimeoutException as e:
            crawler_logger.error(
                f"{operation} 시간 초과",
                error=e,
                context=context.__dict__
            )
            rate_limiter.on_failure(self.site_type, RequestType.ELEMENT_QUERY)
            raise TimeoutError(f"{operation} 시간 초과", context) from e
        except StaleElementReferenceException as e:
            crawler_logger.error(
                f"{operation} 중 요소가 더 이상 유효하지 않음",
                error=e,
                context=context.__dict__
            )
            rate_limiter.on_failure(self.site_type, RequestType.ELEMENT_QUERY)
            raise StaleElementError(f"{operation} 중 요소가 더 이상 유효하지 않음", context) from e
        except (ElementNotInteractableException, ElementClickInterceptedException) as e:
            crawler_logger.error(
                f"{operation} 중 요소와 상호작용 불가: {str(e)}",
                error=e,
                context=context.__dict__
            )
            rate_limiter.on_failure(self.site_type, RequestType.INTERACTION)
            raise InteractionError(f"{operation} 중 요소와 상호작용 불가: {str(e)}", context) from e
        except NoSuchElementException as e:
            crawler_logger.error(
                str(e),
                error=e,
                context=context.__dict__
            )
            rate_limiter.on_failure(self.site_type, RequestType.ELEMENT_QUERY)
            raise ElementNotFoundError(str(e), context) from e
        except WebDriverException as e:
            crawler_logger.error(
                f"{operation} 중 WebDriver 오류: {str(e)}",
                error=e,
                context=context.__dict__
            )
            rate_limiter.on_failure(self.site_type, RequestType.NAVIGATION)
            raise WebDriverError(f"{operation} 중 WebDriver 오류: {str(e)}", context) from e
        except Exception as e:
            crawler_logger.error(
                f"{operation} 중 예상치 못한 오류: {str(e)}",
                error=e,
                context=context.__dict__
            )
            if isinstance(e, CrawlerException):
                raise
            raise CrawlerException(f"{operation} 중 예상치 못한 오류: {str(e)}", context) from e
            
    def on_retry(self, state):
        """재시도 시 호출되는 콜백 함수"""
        crawler_logger.warning(
            f"{state.attempts}번째 재시도",
            {
                "site_type": self.site_type,
                "product_id": self.product_id,
                "error": str(state.last_error)
            }
        )
            
    @retry(max_attempts=3, base_delay=1.0, exceptions=(NetworkError, TimeoutError, StaleElementError))
    def wait_for_element(self, by, value: str, timeout: int = 10, operation: str = "요소 대기") -> Tuple[bool, Any]:
        """
        요소가 나타날 때까지 대기합니다.
        
        Args:
            by: 요소 찾기 방법 (By.ID, By.CLASS_NAME 등)
            value (str): 찾을 요소의 값
            timeout (int): 대기 시간 (초)
            operation (str): 수행 중인 작업 설명
            
        Returns:
            Tuple[bool, Any]: (성공 여부, 찾은 요소)
            
        Raises:
            TimeoutError: 요소를 찾지 못한 경우
        """
        # 요청 제한 준수
        rate_limiter.wait(self.site_type, RequestType.ELEMENT_QUERY)
        
        crawler_logger.debug(
            f"{operation} 시작",
            {"by": str(by), "value": value, "timeout": timeout}
        )
        
        try:
            with self.error_handler(operation, element_info={"by": str(by), "value": value}):
                element = WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((by, value))
                )
                
                # 요소가 화면에 표시되고 클릭 가능한지 확인
                WebDriverWait(self.driver, timeout/2).until(
                    EC.element_to_be_clickable((by, value))
                )
                
                crawler_logger.debug(
                    f"{operation} 성공",
                    {"by": str(by), "value": value}
                )
                
                rate_limiter.on_success(self.site_type, RequestType.ELEMENT_QUERY)
                return True, element
                
        except (TimeoutException, StaleElementReferenceException) as e:
            crawler_logger.warning(
                f"{operation} 실패, 동적 로딩 대기",
                {"by": str(by), "value": value, "error": str(e)}
            )
            
            # 페이지가 완전히 로드될 때까지 대기
            try:
                WebDriverWait(self.driver, timeout).until(
                    lambda driver: driver.execute_script("return document.readyState") == "complete"
                )
                
                # Ajax 요청이 완료될 때까지 대기
                WebDriverWait(self.driver, timeout).until(
                    lambda driver: driver.execute_script("return jQuery.active == 0")
                )
                
                # 다시 시도
                element = WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((by, value))
                )
                
                rate_limiter.on_success(self.site_type, RequestType.ELEMENT_QUERY)
                return True, element
                
            except Exception as e:
                rate_limiter.on_failure(self.site_type, RequestType.ELEMENT_QUERY)
                return False, None
            
    @retry(max_attempts=3, base_delay=1.0, exceptions=(NetworkError, TimeoutError, StaleElementError))
    def wait_for_elements(self, by, value: str, timeout: int = 10, operation: str = "요소들 대기") -> Tuple[bool, List[Any]]:
        """
        여러 요소가 나타날 때까지 대기합니다.
        
        Args:
            by: 요소 찾기 방법 (By.ID, By.CLASS_NAME 등)
            value (str): 찾을 요소의 값
            timeout (int): 대기 시간 (초)
            operation (str): 수행 중인 작업 설명
            
        Returns:
            Tuple[bool, List[Any]]: (성공 여부, 찾은 요소들)
            
        Raises:
            TimeoutError: 요소를 찾지 못한 경우
        """
        # 요청 제한 준수
        rate_limiter.wait(self.site_type, RequestType.ELEMENT_QUERY)
        
        crawler_logger.debug(
            f"{operation} 시작",
            {"by": str(by), "value": value, "timeout": timeout}
        )
        
        try:
            with self.error_handler(operation, element_info={"by": str(by), "value": value}):
                elements = WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_all_elements_located((by, value))
                )
                
                crawler_logger.debug(
                    f"{operation} 성공",
                    {"by": str(by), "value": value, "count": len(elements)}
                )
                
                rate_limiter.on_success(self.site_type, RequestType.ELEMENT_QUERY)
                return True, elements
                
        except (TimeoutException, StaleElementReferenceException) as e:
            crawler_logger.warning(
                f"{operation} 실패, 동적 로딩 대기",
                {"by": str(by), "value": value, "error": str(e)}
            )
            
            # 페이지가 완전히 로드될 때까지 대기
            try:
                WebDriverWait(self.driver, timeout).until(
                    lambda driver: driver.execute_script("return document.readyState") == "complete"
                )
                
                # Ajax 요청이 완료될 때까지 대기
                WebDriverWait(self.driver, timeout).until(
                    lambda driver: driver.execute_script("return jQuery.active == 0")
                )
                
                # 다시 시도
                elements = WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_all_elements_located((by, value))
                )
                
                rate_limiter.on_success(self.site_type, RequestType.ELEMENT_QUERY)
                return True, elements
                
            except Exception as e:
                rate_limiter.on_failure(self.site_type, RequestType.ELEMENT_QUERY)
                return False, []
            
    def take_screenshot(self, name: str):
        """현재 페이지의 스크린샷을 저장합니다."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshots/{self.site_type}_{name}_{timestamp}.png"
        os.makedirs("screenshots", exist_ok=True)
        self.driver.save_screenshot(filename)
        crawler_logger.info(f"스크린샷 저장: {filename}")

    @retry(max_attempts=3, base_delay=2.0, exceptions=(NetworkError, TimeoutError, NavigationError))
    def navigate_to_product(self):
        """상품 페이지로 이동합니다."""
        url = f"https://www.coupang.com/vp/products/{self.product_id}"
        
        try:
            # 쿠팡 메인 페이지 먼저 방문
            self.driver.get("https://www.coupang.com")
            time.sleep(3)  # 메인 페이지에서 잠시 대기
            
            # 상품 페이지로 이동
            self.driver.get(url)
            time.sleep(2)  # 초기 로딩 대기
            
            # URL이 제대로 설정되었는지 확인
            current_url = self.driver.current_url
            if "data:" in current_url or "about:blank" in current_url:
                crawler_logger.warning("페이지 로딩 실패, 재시도 중...")
                
                # 디버깅을 위한 스크린샷
                self.take_screenshot("data_url_detected")
                
                # 잠시 대기 후 다시 시도
                time.sleep(5)  # 더 긴 대기 시간
                self.driver.get(url)
                time.sleep(3)  # 추가 대기
                
                # URL 재확인
                current_url = self.driver.current_url
                if "data:" in current_url or "about:blank" in current_url:
                    # 디버깅을 위한 스크린샷
                    self.take_screenshot("data_url_persists")
                    
                    # 사용자가 상황을 확인할 수 있도록 충분한 시간 대기
                    crawler_logger.warning("페이지 상태 확인을 위해 30초 대기...")
                    time.sleep(30)
                    
                    raise NavigationError(f"페이지 접근 실패: {url}")
            
            # DOM이 준비될 때까지 대기
            try:
                WebDriverWait(self.driver, 30).until(
                    lambda driver: (
                        driver.execute_script("return document.readyState") == "complete" and
                        len(driver.find_elements(By.TAG_NAME, "body")) > 0 and
                        len(driver.find_elements(By.CLASS_NAME, "prod-buy-header")) > 0
                    )
                )
            except TimeoutException:
                # 타임아웃 발생 시 스크린샷 저장하고 계속 진행
                crawler_logger.warning("페이지 로딩 타임아웃, 상태 확인을 위해 대기...")
                self.take_screenshot("timeout_state")
                time.sleep(30)  # 사용자가 상태를 확인할 수 있도록 대기
            
            # 최종 스크린샷
            self.take_screenshot("navigation_complete")
            
            # 페이지 상태 출력
            crawler_logger.info(f"최종 URL: {self.driver.current_url}")
            crawler_logger.info(f"페이지 제목: {self.driver.title}")
            
        except Exception as e:
            crawler_logger.error(f"페이지 이동 중 오류: {str(e)}")
            self.take_screenshot("navigation_error")
            
            # 오류 발생 시에도 브라우저를 유지하고 상태를 확인할 수 있도록 대기
            crawler_logger.warning("오류 상태 확인을 위해 30초 대기...")
            time.sleep(30)
            
            raise NavigationError(f"페이지 이동 중 오류: {str(e)}")
            
        crawler_logger.info(f"페이지 이동 성공: {url}")
        
        # 성공하더라도 잠시 대기하여 상태 확인 가능하도록 함
        time.sleep(5)

    @abstractmethod
    def get_reviews_from_current_page(self) -> List[Review]:
        """현재 페이지의 리뷰들을 수집합니다."""
        pass
        
    @abstractmethod
    def get_product_info(self) -> dict:
        """상품 정보를 수집합니다."""
        pass
        
    @retry(max_attempts=3, base_delay=2.0, exceptions=(NetworkError, TimeoutError, NavigationError), on_retry=on_retry)
    def crawl_reviews(self, max_pages: Optional[int] = None) -> List[Review]:
        """
        리뷰를 크롤링합니다.
        
        Args:
            max_pages (Optional[int]): 크롤링할 최대 페이지 수
            
        Returns:
            List[Review]: 수집된 리뷰 목록
        """
        reviews = []
        
        # 상품 페이지로 이동
        self.navigate_to_product()
        
        # 리뷰 수집
        page_number = 1
        while True:
            with self.error_handler("리뷰 수집", page_number=page_number):
                # 현재 페이지의 리뷰 수집
                success, page_reviews = self.get_reviews_from_current_page()
                if success:
                    reviews.extend(page_reviews)
                    rate_limiter.on_success(self.site_type, RequestType.ELEMENT_QUERY)
                else:
                    rate_limiter.on_failure(self.site_type, RequestType.ELEMENT_QUERY)
                    crawler_logger.warning(f"페이지 {page_number}의 리뷰 수집 실패")
                
                # 최대 페이지 수 체크
                if max_pages and page_number >= max_pages:
                    break
                    
                # 다음 페이지로 이동
                success = self.page_navigator.go_to_next_page()
                if success:
                    rate_limiter.on_success(self.site_type, RequestType.NAVIGATION)
                    page_number += 1
                else:
                    rate_limiter.on_failure(self.site_type, RequestType.NAVIGATION)
                    break
                
        return reviews 
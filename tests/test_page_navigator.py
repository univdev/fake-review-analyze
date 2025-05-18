import unittest
from unittest.mock import Mock, patch
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from src.utils.page_navigator import PageNavigator, PageInfo

class TestPageNavigator(unittest.TestCase):
    def setUp(self):
        """각 테스트 전에 실행되는 설정"""
        self.mock_driver = Mock(spec=WebDriver)
        self.navigator = PageNavigator(self.mock_driver)
        
    def test_page_info_initialization(self):
        """PageInfo 초기화 테스트"""
        page_info = PageInfo(total_pages=10)
        self.assertEqual(page_info.total_pages, 10)
        self.assertEqual(page_info.current_page, 1)
        self.assertIsNone(page_info.requested_pages)
        
    def test_pages_to_crawl_property(self):
        """pages_to_crawl 프로퍼티 테스트"""
        # requested_pages가 None인 경우
        page_info = PageInfo(total_pages=10)
        self.assertEqual(page_info.pages_to_crawl, 10)
        
        # requested_pages가 total_pages보다 작은 경우
        page_info = PageInfo(total_pages=10, requested_pages=5)
        self.assertEqual(page_info.pages_to_crawl, 5)
        
        # requested_pages가 total_pages보다 큰 경우
        page_info = PageInfo(total_pages=10, requested_pages=15)
        self.assertEqual(page_info.pages_to_crawl, 10)
        
    def test_set_page_range_validation(self):
        """set_page_range 메소드의 유효성 검사 테스트"""
        # 정상 케이스
        page_info = self.navigator.set_page_range(total_pages=10, requested_pages=5)
        self.assertEqual(page_info.total_pages, 10)
        self.assertEqual(page_info.requested_pages, 5)
        
        # 총 페이지 수가 0 이하인 경우
        with self.assertRaises(ValueError):
            self.navigator.set_page_range(total_pages=0)
            
        # 요청 페이지 수가 0 이하인 경우
        with self.assertRaises(ValueError):
            self.navigator.set_page_range(total_pages=10, requested_pages=0)
            
    @patch('selenium.webdriver.support.ui.WebDriverWait')
    def test_get_coupang_total_pages(self, mock_wait):
        """쿠팡 총 페이지 수 가져오기 테스트"""
        # 페이지네이션이 있는 경우
        mock_last_btn = Mock()
        mock_last_btn.get_attribute.return_value = "5"
        mock_pagination = Mock()
        mock_pagination.find_elements.return_value = [mock_last_btn]
        
        mock_wait.return_value.until.return_value = mock_pagination
        
        total_pages = self.navigator.get_total_pages("coupang", "123456")
        self.assertEqual(total_pages, 5)
        
        # 페이지네이션이 없고 리뷰 수만 있는 경우
        mock_wait.return_value.until.side_effect = TimeoutException()
        mock_review_count = Mock()
        mock_review_count.text = "50"
        self.mock_driver.find_element.return_value = mock_review_count
        
        total_pages = self.navigator.get_total_pages("coupang", "123456")
        self.assertEqual(total_pages, 5)  # 50개 리뷰 = 5페이지 (페이지당 10개)
        
    @patch('selenium.webdriver.support.ui.WebDriverWait')
    def test_get_naver_total_pages(self, mock_wait):
        """네이버 총 페이지 수 가져오기 테스트"""
        # 페이지네이션이 있는 경우
        mock_last_btn = Mock()
        mock_last_btn.text = "8"
        mock_pagination = Mock()
        mock_pagination.find_elements.return_value = [mock_last_btn]
        
        mock_wait.return_value.until.return_value = mock_pagination
        
        total_pages = self.navigator.get_total_pages("naver", "123456")
        self.assertEqual(total_pages, 8)
        
        # 페이지네이션이 없고 리뷰 수만 있는 경우
        mock_wait.return_value.until.side_effect = TimeoutException()
        mock_review_count = Mock()
        mock_review_count.text = "100"
        self.mock_driver.find_element.return_value = mock_review_count
        
        total_pages = self.navigator.get_total_pages("naver", "123456")
        self.assertEqual(total_pages, 5)  # 100개 리뷰 = 5페이지 (페이지당 20개)
        
    def test_go_to_page_validation(self):
        """go_to_page 메소드의 유효성 검사 테스트"""
        # 페이지 범위가 설정되지 않은 경우
        with self.assertRaises(ValueError):
            self.navigator.go_to_page(1, "coupang")
            
        # 페이지 범위 설정
        self.navigator.set_page_range(total_pages=5)
        
        # 유효하지 않은 페이지 번호
        self.assertFalse(self.navigator.go_to_page(0, "coupang"))
        self.assertFalse(self.navigator.go_to_page(6, "coupang"))
        
        # 지원하지 않는 사이트
        with self.assertRaises(ValueError):
            self.navigator.go_to_page(1, "unknown")
            
    @patch('selenium.webdriver.support.ui.WebDriverWait')
    def test_go_to_coupang_page(self, mock_wait):
        """쿠팡 페이지 이동 테스트"""
        self.navigator.set_page_range(total_pages=5)
        
        # 정상 케이스
        mock_pagination = Mock()
        mock_page_btn = Mock()
        mock_pagination.find_element.return_value = mock_page_btn
        mock_wait.return_value.until.return_value = mock_pagination
        
        self.assertTrue(self.navigator.go_to_page(2, "coupang"))
        self.assertEqual(self.navigator._page_info.current_page, 2)
        
        # 페이지 이동 실패
        mock_pagination.find_element.side_effect = NoSuchElementException()
        self.assertFalse(self.navigator.go_to_page(3, "coupang"))
        
    @patch('selenium.webdriver.support.ui.WebDriverWait')
    def test_go_to_naver_page(self, mock_wait):
        """네이버 페이지 이동 테스트"""
        self.navigator.set_page_range(total_pages=5)
        
        # 정상 케이스
        mock_pagination = Mock()
        mock_page_btn = Mock()
        mock_pagination.find_element.return_value = mock_page_btn
        mock_wait.return_value.until.return_value = mock_pagination
        
        self.assertTrue(self.navigator.go_to_page(2, "naver"))
        self.assertEqual(self.navigator._page_info.current_page, 2)
        
        # 페이지 이동 실패
        mock_pagination.find_element.side_effect = NoSuchElementException()
        self.assertFalse(self.navigator.go_to_page(3, "naver"))

if __name__ == '__main__':
    unittest.main() 
import unittest
from src.utils.url_parser import URLParser, URLValidationResult

class TestURLParser(unittest.TestCase):
    def test_normalize_url(self):
        test_cases = [
            # 기본 URL
            ("www.coupang.com/vp/products/123456", "https://www.coupang.com/vp/products/123456"),
            # 프로토콜이 있는 URL
            ("http://www.coupang.com/vp/products/123456", "http://www.coupang.com/vp/products/123456"),
            # 공백이 있는 URL
            ("  www.coupang.com/vp/products/123456  ", "https://www.coupang.com/vp/products/123456"),
            # 이미 정규화된 URL
            ("https://www.coupang.com/vp/products/123456", "https://www.coupang.com/vp/products/123456"),
        ]
        
        for input_url, expected_url in test_cases:
            with self.subTest(input_url=input_url):
                self.assertEqual(URLParser.normalize_url(input_url), expected_url)
    
    def test_validate_url(self):
        test_cases = [
            # 유효한 쿠팡 URL
            (
                "https://www.coupang.com/vp/products/123456",
                URLValidationResult(
                    is_valid=True,
                    site_type="coupang",
                    product_id="123456"
                )
            ),
            # 유효한 네이버 쇼핑 URL
            (
                "https://shopping.naver.com/product/123456",
                URLValidationResult(
                    is_valid=True,
                    site_type="naver",
                    product_id="123456"
                )
            ),
            # 빈 URL
            (
                "",
                URLValidationResult(
                    is_valid=False,
                    error_message="URL이 비어있습니다."
                )
            ),
            # 잘못된 형식의 URL
            (
                "invalid-url",
                URLValidationResult(
                    is_valid=False,
                    error_message="유효하지 않은 URL 형식입니다."
                )
            ),
            # 지원하지 않는 사이트
            (
                "https://www.amazon.com/product/123456",
                URLValidationResult(
                    is_valid=False,
                    error_message="지원하지 않는 사이트입니다. 지원하는 사이트: coupang, naver"
                )
            ),
            # 상품 페이지가 아닌 URL
            (
                "https://www.coupang.com/",
                URLValidationResult(
                    is_valid=False,
                    error_message="상품 페이지 URL이 아닙니다."
                )
            ),
        ]
        
        for input_url, expected_result in test_cases:
            with self.subTest(input_url=input_url):
                result = URLParser.validate_url(input_url)
                self.assertEqual(result.is_valid, expected_result.is_valid)
                self.assertEqual(result.error_message, expected_result.error_message)
                self.assertEqual(result.site_type, expected_result.site_type)
                self.assertEqual(result.product_id, expected_result.product_id)
    
    def test_identify_site(self):
        test_cases = [
            # 쿠팡 URL
            (
                "https://www.coupang.com/vp/products/123456",
                ("coupang", "123456")
            ),
            # 네이버 쇼핑 URL (product)
            (
                "https://shopping.naver.com/product/123456",
                ("naver", "123456")
            ),
            # 네이버 쇼핑 URL (catalog)
            (
                "https://shopping.naver.com/catalog/123456",
                ("naver", "123456")
            ),
            # 잘못된 URL
            (
                "https://www.coupang.com/",
                None
            ),
            # 지원하지 않는 사이트
            (
                "https://www.amazon.com/product/123456",
                None
            ),
        ]
        
        for input_url, expected_result in test_cases:
            with self.subTest(input_url=input_url):
                self.assertEqual(URLParser.identify_site(input_url), expected_result)
    
    def test_get_site_info(self):
        # 유효한 URL 테스트
        valid_url = "www.coupang.com/vp/products/123456"
        expected_info = {
            'site_type': 'coupang',
            'product_id': '123456',
            'normalized_url': 'https://www.coupang.com/vp/products/123456'
        }
        self.assertEqual(URLParser.get_site_info(valid_url), expected_info)
        
        # 잘못된 URL에 대한 예외 발생 테스트
        invalid_urls = [
            "",  # 빈 URL
            "invalid-url",  # 잘못된 형식
            "https://www.amazon.com/product/123456",  # 지원하지 않는 사이트
            "https://www.coupang.com/",  # 상품 페이지가 아님
        ]
        
        for url in invalid_urls:
            with self.subTest(url=url):
                with self.assertRaises(ValueError):
                    URLParser.get_site_info(url)

if __name__ == '__main__':
    unittest.main() 
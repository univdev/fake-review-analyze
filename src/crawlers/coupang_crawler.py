"""
쿠팡 리뷰 크롤러
"""

import re
from datetime import datetime
from typing import List, Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from .base_crawler import ReviewCrawler
from ..models.review import Review, ReviewRating, ReviewImages
from ..utils.exceptions import (
    InvalidDataError,
    ElementNotFoundError,
    ParsingError
)

class CoupangReviewCrawler(ReviewCrawler):
    """쿠팡 리뷰 크롤러"""
    
    @property
    def site_type(self) -> str:
        return 'coupang'
    
    def get_product_info(self) -> dict:
        """상품 정보를 수집합니다."""
        with self.error_handler("상품 정보 수집"):
            # 상품명 - 여러 클래스 시도
            title_selectors = [
                (By.CLASS_NAME, "product-title"),
                (By.CLASS_NAME, "prod-buy-header__title"),
                (By.CSS_SELECTOR, ".prod-buy-header h2"),
                (By.CSS_SELECTOR, "[class*='prod-buy-header'] h2")  # 동적 클래스 대응
            ]
            
            title_element = None
            for by, value in title_selectors:
                try:
                    # 페이지 완전 로딩 대기
                    WebDriverWait(self.driver, 10).until(
                        lambda driver: (
                            driver.execute_script("return document.readyState") == "complete" and
                            len(driver.find_elements(By.TAG_NAME, "body")) > 0
                        )
                    )
                    
                    # 요소 존재 확인
                    if len(self.driver.find_elements(by, value)) > 0:
                        # 요소가 보이고 클릭 가능할 때까지 대기
                        title_element = WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((by, value))
                        )
                        break
                except:
                    continue
            
            if not title_element:
                # 스크린샷 저장
                self.take_screenshot("title_not_found")
                raise ElementNotFoundError("상품명을 찾을 수 없습니다.")
            
            product_name = title_element.text.strip()
            if not product_name:
                raise InvalidDataError("product_name", "빈 문자열")
            
            # 평균 평점 - 여러 셀렉터 시도
            rating_selectors = [
                (By.CLASS_NAME, "prod-buy-header__rating"),
                (By.CSS_SELECTOR, "[class*='rating']"),
                (By.CSS_SELECTOR, "[class*='star-rating']")
            ]
            
            rating_element = None
            for by, value in rating_selectors:
                try:
                    elements = self.driver.find_elements(by, value)
                    if elements:
                        rating_element = elements[0]
                        break
                except:
                    continue
                    
            if not rating_element:
                raise ElementNotFoundError("평균 평점을 찾을 수 없습니다.")
                
            try:
                avg_rating = float(rating_element.find_element(By.TAG_NAME, "span").text)
            except (ValueError, AttributeError) as e:
                raise InvalidDataError("average_rating", rating_element.text) from e
            
            # 리뷰 수 - 여러 셀렉터 시도
            review_count_selectors = [
                (By.CLASS_NAME, "prod-buy-header__review-count"),
                (By.CSS_SELECTOR, "[class*='review-count']"),
                (By.CSS_SELECTOR, "a[href*='productReview']")
            ]
            
            review_count_element = None
            for by, value in review_count_selectors:
                try:
                    elements = self.driver.find_elements(by, value)
                    if elements:
                        review_count_element = elements[0]
                        break
                except:
                    continue
                    
            if not review_count_element:
                raise ElementNotFoundError("리뷰 수를 찾을 수 없습니다.")
                
            try:
                review_count = int(review_count_element.text.replace(",", ""))
            except (ValueError, AttributeError) as e:
                raise InvalidDataError("review_count", review_count_element.text) from e
            
            return {
                'name': product_name,
                'average_rating': avg_rating,
                'review_count': review_count
            }
    
    def get_reviews_from_current_page(self) -> List[Review]:
        """현재 페이지의 리뷰들을 수집합니다."""
        reviews = []
        
        # 리뷰 목록 대기
        review_elements = self.wait_for_elements(
            By.CLASS_NAME, "js_reviewArticleContainer",
            operation="리뷰 목록 요소 대기"
        )
        
        for element in review_elements:
            try:
                review = self._parse_review_element(element)
                if review:
                    reviews.append(review)
            except ParsingError as e:
                print(f"⚠️ {str(e)}")
                continue
                    
        return reviews
    
    def _parse_review_element(self, element) -> Optional[Review]:
        """리뷰 요소를 파싱합니다."""
        element_info = {"class": element.get_attribute("class")}
        
        with self.error_handler("리뷰 요소 파싱", element_info=element_info):
            # 리뷰 ID
            review_id = element.get_attribute("data-review-id")
            if not review_id:
                raise InvalidDataError("review_id", None)
            
            # 평점 - data-rating 속성 사용
            try:
                rating_element = element.find_element(By.CSS_SELECTOR, "[data-rating]")
                rating = ReviewRating(score=float(rating_element.get_attribute("data-rating")))
            except (NoSuchElementException, ValueError, AttributeError) as e:
                raise InvalidDataError("rating", rating_element.text if 'rating_element' in locals() else None) from e
            
            # 작성일
            try:
                date_text = element.find_element(By.CLASS_NAME, "js_reviewArticleCreateDate").text
                created_at = datetime.strptime(date_text, "%Y.%m.%d")
            except (NoSuchElementException, ValueError) as e:
                raise InvalidDataError("created_at", date_text if 'date_text' in locals() else None) from e
            
            # 구매자 정보 - js_reviewUserProfileImage 클래스 사용
            try:
                author = element.find_element(By.CLASS_NAME, "js_reviewUserProfileImage").text
            except NoSuchElementException as e:
                raise ElementNotFoundError("js_reviewUserProfileImage") from e
            
            # 구매 옵션
            try:
                option_info = element.find_element(By.CLASS_NAME, "js_reviewArticleOptionName").text
            except NoSuchElementException:
                option_info = None
                
            # 리뷰 내용
            try:
                content = element.find_element(By.CLASS_NAME, "js_reviewArticleContent").text.strip()
            except NoSuchElementException as e:
                raise ElementNotFoundError("js_reviewArticleContent") from e
            
            # 도움이 됐어요 수
            try:
                likes = int(element.find_element(
                    By.CLASS_NAME, "js_reviewArticleHelpfulCount"
                ).text.replace(",", ""))
            except (NoSuchElementException, ValueError):
                likes = 0
                
            # 이미지
            try:
                image_elements = element.find_elements(By.CSS_SELECTOR, ".js_reviewArticleImageContainer img")
                image_urls = [img.get_attribute("src") for img in image_elements]
                images = ReviewImages.create(image_urls) if image_urls else None
            except Exception:
                images = None
                
            return Review(
                id=review_id,
                product_id=self.product_id,
                rating=rating,
                content=content,
                created_at=created_at,
                site=self.site_type,
                author=author,
                option_info=option_info,
                likes=likes,
                images=images
            ) 
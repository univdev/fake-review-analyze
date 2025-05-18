"""
네이버 쇼핑 리뷰 크롤러
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

class NaverReviewCrawler(ReviewCrawler):
    """네이버 쇼핑 리뷰 크롤러"""
    
    @property
    def site_type(self) -> str:
        return 'naver'
    
    def get_product_info(self) -> dict:
        """상품 정보를 수집합니다."""
        with self.error_handler("상품 정보 수집"):
            # 상품명
            product_name = self.wait_for_element(
                By.CLASS_NAME, "product_title_text__wWwGj",
                operation="상품명 요소 대기"
            ).text.strip()
            
            # 평균 평점
            try:
                rating_text = self.driver.find_element(
                    By.CLASS_NAME, "product_review_score__yGkGb"
                ).text.replace("평점", "").strip()
                avg_rating = float(rating_text)
            except (NoSuchElementException, ValueError, AttributeError) as e:
                raise InvalidDataError("average_rating", rating_text if 'rating_text' in locals() else None) from e
            
            # 리뷰 수
            try:
                review_count_text = self.driver.find_element(
                    By.CLASS_NAME, "product_review_count__mRWxH"
                ).text
                review_count = int(re.search(r'\d+', review_count_text.replace(",", "")).group())
            except (NoSuchElementException, ValueError, AttributeError) as e:
                raise InvalidDataError("review_count", review_count_text if 'review_count_text' in locals() else None) from e
            
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
            By.CLASS_NAME, "reviewItem_review_item__2aYAB",
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
            review_id = element.get_attribute("id")
            if not review_id:
                # id가 없는 경우 임의로 생성
                review_id = f"naver_{self.product_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # 평점
            try:
                rating_text = element.find_element(
                    By.CLASS_NAME, "reviewItem_info_grade__1s0Kh"
                ).text.replace("평점", "").strip()
                rating = ReviewRating(score=float(rating_text))
            except (NoSuchElementException, ValueError, AttributeError) as e:
                raise InvalidDataError("rating", rating_text if 'rating_text' in locals() else None) from e
            
            # 작성일
            try:
                date_text = element.find_element(By.CLASS_NAME, "reviewItem_info_date__1DvUK").text
                created_at = datetime.strptime(date_text, "%Y.%m.%d.")
            except (NoSuchElementException, ValueError) as e:
                raise InvalidDataError("created_at", date_text if 'date_text' in locals() else None) from e
            
            # 구매자 정보
            try:
                author = element.find_element(By.CLASS_NAME, "reviewItem_info_user__1WUwj").text
            except NoSuchElementException as e:
                raise ElementNotFoundError("reviewItem_info_user__1WUwj") from e
            
            # 구매 옵션
            try:
                option_info = element.find_element(By.CLASS_NAME, "reviewItem_option__3xQGy").text
            except NoSuchElementException:
                option_info = None
                
            # 리뷰 제목
            try:
                title = element.find_element(By.CLASS_NAME, "reviewItem_title__3jUBx").text.strip()
            except NoSuchElementException:
                title = None
                
            # 리뷰 내용
            try:
                content = element.find_element(By.CLASS_NAME, "reviewItem_text__2MeUk").text.strip()
            except NoSuchElementException as e:
                raise ElementNotFoundError("reviewItem_text__2MeUk") from e
            
            # 도움이 돼요 수
            try:
                likes_text = element.find_element(
                    By.CLASS_NAME, "reviewItem_help_count__3Ml7n"
                ).text
                likes = int(re.search(r'\d+', likes_text).group())
            except (NoSuchElementException, AttributeError, ValueError):
                likes = 0
                
            # 이미지
            try:
                image_elements = element.find_elements(
                    By.CSS_SELECTOR, ".reviewItem_thumb_container__1iKDx img"
                )
                image_urls = [img.get_attribute("src") for img in image_elements]
                images = ReviewImages.create(image_urls) if image_urls else None
            except Exception:
                images = None
                
            # 구매일
            try:
                purchase_text = element.find_element(
                    By.CLASS_NAME, "reviewItem_info_purchase_date__4XTRF"
                ).text.replace("구매", "").strip()
                purchase_date = datetime.strptime(purchase_text, "%Y.%m.%d.")
            except (NoSuchElementException, ValueError):
                purchase_date = None
                
            return Review(
                id=review_id,
                product_id=self.product_id,
                rating=rating,
                content=content,
                created_at=created_at,
                site=self.site_type,
                title=title,
                author=author,
                purchase_date=purchase_date,
                option_info=option_info,
                likes=likes,
                images=images
            ) 
"""
리뷰 데이터 모델
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List

@dataclass
class ReviewRating:
    """리뷰 평점 정보"""
    score: float  # 전체 평점
    max_score: float = 5.0  # 최대 평점 (기본값 5점)
    
    @property
    def normalized_score(self) -> float:
        """5점 만점 기준으로 정규화된 평점을 반환합니다."""
        return (self.score / self.max_score) * 5.0

@dataclass
class ReviewImages:
    """리뷰 이미지 정보"""
    urls: List[str]  # 이미지 URL 목록
    count: int  # 이미지 개수
    
    @classmethod
    def create(cls, urls: List[str]) -> 'ReviewImages':
        """ReviewImages 인스턴스를 생성합니다."""
        return cls(urls=urls, count=len(urls))

@dataclass
class Review:
    """리뷰 데이터"""
    # 필수 필드
    id: str  # 리뷰 ID
    product_id: str  # 상품 ID
    rating: ReviewRating  # 평점
    content: str  # 리뷰 내용
    created_at: datetime  # 작성일
    site: str  # 사이트 ('coupang' 또는 'naver')
    
    # 선택 필드
    title: Optional[str] = None  # 리뷰 제목
    author: Optional[str] = None  # 작성자
    purchase_date: Optional[datetime] = None  # 구매일
    option_info: Optional[str] = None  # 구매 옵션 정보
    likes: Optional[int] = None  # 좋아요 수
    images: Optional[ReviewImages] = None  # 이미지 정보
    
    def to_dict(self) -> dict:
        """리뷰 데이터를 딕셔너리로 변환합니다."""
        review_dict = {
            'id': self.id,
            'product_id': self.product_id,
            'rating': self.rating.score,
            'normalized_rating': self.rating.normalized_score,
            'content': self.content,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'site': self.site,
            'title': self.title,
            'author': self.author,
            'purchase_date': self.purchase_date.strftime('%Y-%m-%d') if self.purchase_date else None,
            'option_info': self.option_info,
            'likes': self.likes,
            'image_count': self.images.count if self.images else 0,
            'image_urls': self.images.urls if self.images else []
        }
        return review_dict 
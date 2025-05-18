"""
CSV 파일 저장 유틸리티
"""

import os
import csv
from datetime import datetime
from typing import List, Dict, Any

from ..models.review import Review

class CSVExporter:
    """CSV 파일 저장 유틸리티"""
    
    def __init__(self, output_dir: str = "data/raw"):
        """
        CSVExporter 초기화
        
        Args:
            output_dir (str): CSV 파일을 저장할 디렉토리 경로
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
    def save_reviews(self, reviews: List[Review], product_info: Dict[str, Any], site_type: str) -> str:
        """
        리뷰 데이터를 CSV 파일로 저장합니다.
        
        Args:
            reviews (List[Review]): 저장할 리뷰 목록
            product_info (Dict[str, Any]): 상품 정보
            site_type (str): 사이트 타입 ('coupang' 또는 'naver')
            
        Returns:
            str: 저장된 CSV 파일의 경로
        """
        # 파일명 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        product_name = product_info.get('name', 'unknown_product')
        safe_product_name = "".join(c if c.isalnum() else "_" for c in product_name)[:50]
        filename = f"{site_type}_{safe_product_name}_{timestamp}.csv"
        filepath = os.path.join(self.output_dir, filename)
        
        # CSV 파일 작성
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=self._get_csv_fields())
            
            # 헤더 작성
            writer.writeheader()
            
            # 상품 정보 작성
            product_row = {
                'id': 'product_info',
                'product_id': product_info.get('id', 'unknown'),
                'name': product_info.get('name', 'N/A'),
                'content': f"상품명: {product_info.get('name', 'N/A')}",
                'rating': product_info.get('average_rating', 'N/A'),
                'review_count': product_info.get('review_count', 'N/A'),
                'site': site_type
            }
            writer.writerow(product_row)
            
            # 리뷰 데이터 작성
            for review in reviews:
                writer.writerow(review.to_dict())
                
        print(f"✅ CSV 파일 저장 완료: {filepath}")
        return filepath
        
    @staticmethod
    def _get_csv_fields() -> List[str]:
        """CSV 파일의 필드명 목록을 반환합니다."""
        return [
            'id',
            'product_id',
            'name',
            'rating',
            'normalized_rating',
            'content',
            'created_at',
            'site',
            'title',
            'author',
            'purchase_date',
            'option_info',
            'likes',
            'image_count',
            'image_urls',
            'review_count'
        ]

# 전역 인스턴스 생성
_exporter = CSVExporter()

def export_to_csv(reviews: List[Review], product_info: Dict[str, Any], site_type: str) -> str:
    """
    리뷰 데이터를 CSV 파일로 저장합니다.
    
    Args:
        reviews (List[Review]): 저장할 리뷰 목록
        product_info (Dict[str, Any]): 상품 정보
        site_type (str): 사이트 타입 ('coupang' 또는 'naver')
        
    Returns:
        str: 저장된 CSV 파일의 경로
    """
    return _exporter.save_reviews(reviews, product_info, site_type)

__all__ = ['export_to_csv'] 
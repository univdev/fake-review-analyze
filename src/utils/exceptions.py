"""
크롤러 예외 처리를 위한 계층적 예외 클래스 구조
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class CrawlerContext:
    """크롤러 작업 컨텍스트 정보"""
    url: str
    site_type: str
    product_id: str
    page_number: Optional[int] = None
    element_info: Optional[Dict[str, Any]] = None
    timestamp: datetime = datetime.now()

class CrawlerException(Exception):
    """크롤러 기본 예외 클래스"""
    
    def __init__(self, message: str, context: Optional[CrawlerContext] = None):
        self.message = message
        self.context = context
        self.timestamp = datetime.now()
        super().__init__(self.format_message())
        
    def format_message(self) -> str:
        """예외 메시지를 포맷팅합니다."""
        base_msg = f"[{self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}] {self.message}"
        if self.context:
            context_info = [
                f"URL: {self.context.url}",
                f"사이트: {self.context.site_type}",
                f"상품 ID: {self.context.product_id}"
            ]
            if self.context.page_number:
                context_info.append(f"페이지: {self.context.page_number}")
            if self.context.element_info:
                context_info.append(f"요소 정보: {self.context.element_info}")
            return f"{base_msg}\n컨텍스트:\n" + "\n".join(f"- {info}" for info in context_info)
        return base_msg

class NetworkError(CrawlerException):
    """네트워크 관련 예외"""
    pass

class ConnectionError(NetworkError):
    """연결 실패 예외"""
    pass

class TimeoutError(NetworkError):
    """타임아웃 예외"""
    pass

class HTTPError(NetworkError):
    """HTTP 응답 관련 예외"""
    
    def __init__(self, status_code: int, *args, **kwargs):
        self.status_code = status_code
        super().__init__(f"HTTP {status_code} 에러", *args, **kwargs)

class RateLimitError(HTTPError):
    """요청 제한 초과 예외"""
    
    def __init__(self, retry_after: Optional[int] = None, *args, **kwargs):
        self.retry_after = retry_after
        message = f"요청 제한 초과. {f'재시도 대기 시간: {retry_after}초' if retry_after else ''}"
        super().__init__(429, message, *args, **kwargs)

class ParsingError(CrawlerException):
    """데이터 파싱 관련 예외"""
    pass

class ElementNotFoundError(ParsingError):
    """요소를 찾을 수 없는 예외"""
    
    def __init__(self, selector: str, *args, **kwargs):
        self.selector = selector
        super().__init__(f"요소를 찾을 수 없음: {selector}", *args, **kwargs)

class InvalidDataError(ParsingError):
    """데이터 형식이 잘못된 예외"""
    
    def __init__(self, field: str, value: Any, *args, **kwargs):
        self.field = field
        self.invalid_value = value
        super().__init__(f"잘못된 데이터 형식: {field} = {value}", *args, **kwargs)

class NavigationError(CrawlerException):
    """페이지 탐색 관련 예외"""
    pass

class PageNotFoundError(NavigationError):
    """페이지를 찾을 수 없는 예외"""
    pass

class InvalidPageError(NavigationError):
    """잘못된 페이지 번호 예외"""
    
    def __init__(self, page_number: int, total_pages: int, *args, **kwargs):
        self.page_number = page_number
        self.total_pages = total_pages
        super().__init__(
            f"잘못된 페이지 번호: {page_number} (총 페이지: {total_pages})",
            *args, **kwargs
        )

class ResourceError(CrawlerException):
    """리소스 관련 예외"""
    pass

class WebDriverError(ResourceError):
    """WebDriver 관련 예외"""
    pass

class StorageError(ResourceError):
    """데이터 저장 관련 예외"""
    pass

class StaleElementError(WebDriverError):
    """요소가 더 이상 유효하지 않은 예외"""
    pass

class InteractionError(WebDriverError):
    """요소와 상호작용 불가능한 예외"""
    pass 
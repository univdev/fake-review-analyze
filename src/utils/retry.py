"""
재시도 메커니즘 구현
"""

import time
import random
from functools import wraps
from typing import Optional, Type, Tuple, Callable, Any
from datetime import datetime

from .exceptions import (
    CrawlerException,
    NetworkError,
    TimeoutError,
    HTTPError,
    RateLimitError
)

class RetryState:
    """재시도 상태 정보"""
    
    def __init__(self, max_attempts: int, base_delay: float):
        self.attempts = 0
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.start_time = datetime.now()
        self.last_error: Optional[Exception] = None
        
    @property
    def should_retry(self) -> bool:
        """재시도 가능 여부를 반환합니다."""
        return self.attempts < self.max_attempts
        
    def calculate_delay(self, jitter: float = 0.1) -> float:
        """
        다음 재시도까지의 대기 시간을 계산합니다.
        
        Args:
            jitter (float): 무작위성을 추가하기 위한 지터 비율 (0.0 ~ 1.0)
            
        Returns:
            float: 대기 시간 (초)
        """
        # 지수 백오프: base_delay * (2 ^ attempt)
        delay = self.base_delay * (2 ** self.attempts)
        
        # 지터 추가: delay * (1 ± jitter)
        if jitter > 0:
            delay *= (1 + random.uniform(-jitter, jitter))
            
        return delay
        
    def record_attempt(self, error: Exception):
        """재시도 시도를 기록합니다."""
        self.attempts += 1
        self.last_error = error

def is_retriable(error: Exception) -> Tuple[bool, Optional[float]]:
    """
    예외가 재시도 가능한지 확인합니다.
    
    Args:
        error (Exception): 확인할 예외
        
    Returns:
        Tuple[bool, Optional[float]]: (재시도 가능 여부, 강제 대기 시간)
    """
    # 네트워크 관련 오류는 재시도 가능
    if isinstance(error, NetworkError):
        if isinstance(error, RateLimitError):
            # 429 에러는 retry-after 헤더 값만큼 대기 후 재시도
            return True, error.retry_after
        if isinstance(error, HTTPError):
            # 5xx 에러만 재시도
            return error.status_code >= 500, None
        # 기타 네트워크 오류(연결 실패, 타임아웃 등)는 재시도
        return True, None
        
    # 기타 예외는 재시도하지 않음
    return False, None

def retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    exceptions: Tuple[Type[Exception], ...] = (CrawlerException,),
    on_retry: Optional[Callable[[RetryState], Any]] = None
):
    """
    함수 실행을 재시도하는 데코레이터
    
    Args:
        max_attempts (int): 최대 재시도 횟수
        base_delay (float): 기본 대기 시간 (초)
        exceptions (Tuple[Type[Exception], ...]): 재시도할 예외 타입들
        on_retry (Optional[Callable[[RetryState], Any]]): 재시도 시 호출할 콜백 함수
        
    Returns:
        Any: 함수의 반환값
        
    Raises:
        Exception: 모든 재시도가 실패한 경우 마지막 예외를 다시 발생
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            state = RetryState(max_attempts, base_delay)
            
            while True:
                try:
                    return func(*args, **kwargs)
                    
                except exceptions as e:
                    state.record_attempt(e)
                    
                    # 재시도 가능 여부 확인
                    retriable, forced_delay = is_retriable(e)
                    if not retriable or not state.should_retry:
                        raise
                        
                    # 재시도 콜백 호출
                    if on_retry:
                        on_retry(state)
                        
                    # 대기 시간 계산 및 대기
                    delay = forced_delay if forced_delay is not None else state.calculate_delay()
                    time.sleep(delay)
                    
        return wrapper
    return decorator 
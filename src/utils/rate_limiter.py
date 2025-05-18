"""
요청 제한 구현
"""

import time
import threading
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import deque
from enum import Enum

class RequestType(Enum):
    """요청 유형"""
    NAVIGATION = "navigation"  # 페이지 이동
    ELEMENT_QUERY = "element_query"  # 요소 조회
    INTERACTION = "interaction"  # 클릭, 입력 등 상호작용

@dataclass
class RateLimitConfig:
    """요청 제한 설정"""
    requests_per_second: float  # 초당 최대 요청 수
    burst_size: int  # 버스트 크기 (한 번에 처리 가능한 최대 요청 수)
    backoff_factor: float = 2.0  # 요청 실패 시 대기 시간 증가 배수
    min_delay: float = 0.5  # 최소 대기 시간 (초)
    max_delay: float = 30.0  # 최대 대기 시간 (초)

class AdaptiveTokenBucket:
    """적응형 토큰 버킷 알고리즘 구현"""
    
    def __init__(self, config: RateLimitConfig):
        """
        AdaptiveTokenBucket 초기화
        
        Args:
            config (RateLimitConfig): 요청 제한 설정
        """
        self.config = config
        self.rate = config.requests_per_second
        self.capacity = config.burst_size
        self.tokens = config.burst_size
        self.last_update = time.time()
        self.lock = threading.Lock()
        self.current_delay = config.min_delay
        self.success_count = 0
        self.failure_count = 0
        
    def _add_tokens(self):
        """현재 시간까지의 토큰을 추가합니다."""
        now = time.time()
        time_passed = now - self.last_update
        new_tokens = time_passed * self.rate
        
        self.tokens = min(self.capacity, self.tokens + new_tokens)
        self.last_update = now
        
    def try_consume(self, tokens: int = 1) -> bool:
        """
        토큰을 소비하려고 시도합니다.
        
        Args:
            tokens (int): 소비할 토큰 수
            
        Returns:
            bool: 토큰 소비 성공 여부
        """
        with self.lock:
            self._add_tokens()
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
                
            return False
            
    def consume(self, tokens: int = 1):
        """
        토큰을 소비합니다. 토큰이 부족한 경우 대기합니다.
        
        Args:
            tokens (int): 소비할 토큰 수
        """
        while not self.try_consume(tokens):
            time.sleep(self.current_delay)
            
    def on_success(self):
        """요청 성공 시 호출됩니다."""
        with self.lock:
            self.success_count += 1
            self.failure_count = 0
            
            # 연속 성공 시 대기 시간 감소
            if self.success_count >= 5:
                self.current_delay = max(
                    self.config.min_delay,
                    self.current_delay / self.config.backoff_factor
                )
                self.success_count = 0
                
    def on_failure(self):
        """요청 실패 시 호출됩니다."""
        with self.lock:
            self.failure_count += 1
            self.success_count = 0
            
            # 실패 시 대기 시간 증가
            self.current_delay = min(
                self.config.max_delay,
                self.current_delay * self.config.backoff_factor
            )

class SlidingWindowCounter:
    """슬라이딩 윈도우 카운터 구현"""
    
    def __init__(self, window_size: int, max_requests: int):
        """
        SlidingWindowCounter 초기화
        
        Args:
            window_size (int): 윈도우 크기 (초)
            max_requests (int): 윈도우 내 최대 요청 수
        """
        self.window_size = window_size
        self.max_requests = max_requests
        self.requests = deque()
        self.lock = threading.Lock()
        
    def _cleanup_old_requests(self):
        """만료된 요청을 제거합니다."""
        now = datetime.now()
        window_start = now - timedelta(seconds=self.window_size)
        
        while self.requests and self.requests[0] < window_start:
            self.requests.popleft()
            
    def try_add_request(self) -> bool:
        """
        새 요청을 추가하려고 시도합니다.
        
        Returns:
            bool: 요청 추가 성공 여부
        """
        with self.lock:
            self._cleanup_old_requests()
            
            if len(self.requests) < self.max_requests:
                self.requests.append(datetime.now())
                return True
                
            return False
            
    def add_request(self):
        """새 요청을 추가합니다. 제한에 도달한 경우 대기합니다."""
        while not self.try_add_request():
            time.sleep(0.1)  # 100ms 대기 후 재시도

class RateLimiter:
    """요청 제한 관리자"""
    
    def __init__(self):
        self._limiters: Dict[Tuple[str, RequestType], AdaptiveTokenBucket] = {}
        self._counters: Dict[str, SlidingWindowCounter] = {}
        self._lock = threading.Lock()
        
    def configure(self, site: str, config: RateLimitConfig):
        """
        사이트별 요청 제한을 설정합니다.
        
        Args:
            site (str): 사이트 식별자
            config (RateLimitConfig): 요청 제한 설정
        """
        with self._lock:
            # 요청 유형별로 다른 설정 적용
            nav_config = RateLimitConfig(
                requests_per_second=config.requests_per_second * 0.5,  # 더 엄격한 제한
                burst_size=max(1, config.burst_size // 2),
                backoff_factor=config.backoff_factor,
                min_delay=config.min_delay * 2,  # 더 긴 대기 시간
                max_delay=config.max_delay
            )
            
            query_config = RateLimitConfig(
                requests_per_second=config.requests_per_second * 1.5,  # 더 자유로운 제한
                burst_size=config.burst_size,
                backoff_factor=config.backoff_factor,
                min_delay=config.min_delay,
                max_delay=config.max_delay
            )
            
            interaction_config = RateLimitConfig(
                requests_per_second=config.requests_per_second,
                burst_size=config.burst_size,
                backoff_factor=config.backoff_factor,
                min_delay=config.min_delay * 1.5,  # 중간 수준의 대기 시간
                max_delay=config.max_delay
            )
            
            # 요청 유형별 토큰 버킷 생성
            self._limiters[(site, RequestType.NAVIGATION)] = AdaptiveTokenBucket(nav_config)
            self._limiters[(site, RequestType.ELEMENT_QUERY)] = AdaptiveTokenBucket(query_config)
            self._limiters[(site, RequestType.INTERACTION)] = AdaptiveTokenBucket(interaction_config)
            
            # 전체 요청에 대한 슬라이딩 윈도우 카운터
            self._counters[site] = SlidingWindowCounter(
                window_size=60,  # 1분
                max_requests=config.burst_size * 60  # 분당 최대 요청 수
            )
            
    def wait(self, site: str, request_type: RequestType = RequestType.ELEMENT_QUERY):
        """
        요청 제한을 준수하기 위해 필요한 만큼 대기합니다.
        
        Args:
            site (str): 사이트 식별자
            request_type (RequestType): 요청 유형
        """
        key = (site, request_type)
        if key in self._limiters:
            self._limiters[key].consume()
            
        if site in self._counters:
            self._counters[site].add_request()
            
    def on_success(self, site: str, request_type: RequestType = RequestType.ELEMENT_QUERY):
        """요청 성공을 기록합니다."""
        key = (site, request_type)
        if key in self._limiters:
            self._limiters[key].on_success()
            
    def on_failure(self, site: str, request_type: RequestType = RequestType.ELEMENT_QUERY):
        """요청 실패를 기록합니다."""
        key = (site, request_type)
        if key in self._limiters:
            self._limiters[key].on_failure()

# 전역 인스턴스 생성
rate_limiter = RateLimiter()

# 기본 설정
rate_limiter.configure('coupang', RateLimitConfig(
    requests_per_second=1.0,  # 초당 1개 요청 (기본값 증가)
    burst_size=5,  # 최대 5개 연속 요청
    backoff_factor=2.0,  # 실패 시 대기 시간 2배씩 증가
    min_delay=0.5,  # 최소 0.5초 대기
    max_delay=30.0  # 최대 30초 대기
))

rate_limiter.configure('naver', RateLimitConfig(
    requests_per_second=1.0,  # 초당 1개 요청 (기본값 증가)
    burst_size=5,  # 최대 5개 연속 요청
    backoff_factor=2.0,  # 실패 시 대기 시간 2배씩 증가
    min_delay=0.5,  # 최소 0.5초 대기
    max_delay=30.0  # 최대 30초 대기
)) 
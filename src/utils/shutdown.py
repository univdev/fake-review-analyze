"""
안전한 종료 처리 구현
"""

import os
import sys
import signal
import threading
from typing import List, Callable, Optional
from datetime import datetime
from selenium.webdriver.remote.webdriver import WebDriver

from .logger import crawler_logger

class ShutdownHandler:
    """안전한 종료 처리 관리자"""
    
    def __init__(self):
        self._shutdown_flag = threading.Event()
        self._cleanup_handlers: List[Callable] = []
        self._driver: Optional[WebDriver] = None
        self._original_sigint = signal.getsignal(signal.SIGINT)
        self._original_sigterm = signal.getsignal(signal.SIGTERM)
        
    def register_driver(self, driver: WebDriver):
        """WebDriver 인스턴스를 등록합니다."""
        self._driver = driver
        
    def register_cleanup(self, handler: Callable):
        """정리 작업 핸들러를 등록합니다."""
        self._cleanup_handlers.append(handler)
        
    def is_shutdown_requested(self) -> bool:
        """종료가 요청되었는지 확인합니다."""
        return self._shutdown_flag.is_set()
        
    def _cleanup(self):
        """등록된 정리 작업을 실행합니다."""
        crawler_logger.info("정리 작업 시작")
        
        # 등록된 정리 작업 실행
        for handler in self._cleanup_handlers:
            try:
                handler()
            except Exception as e:
                crawler_logger.error("정리 작업 중 오류 발생", error=e)
                
        # WebDriver 정리
        if self._driver:
            try:
                crawler_logger.info("WebDriver 종료")
                self._driver.quit()
            except Exception as e:
                crawler_logger.error("WebDriver 종료 중 오류 발생", error=e)
                
        crawler_logger.info("정리 작업 완료")
        
    def _signal_handler(self, signum, frame):
        """시그널 핸들러"""
        signal_name = "SIGINT" if signum == signal.SIGINT else "SIGTERM"
        crawler_logger.warning(f"{signal_name} 시그널 수신")
        
        if not self._shutdown_flag.is_set():
            self._shutdown_flag.set()
            self._cleanup()
            
            # 원래의 시그널 핸들러 호출
            if signum == signal.SIGINT and self._original_sigint:
                self._original_sigint(signum, frame)
            elif signum == signal.SIGTERM and self._original_sigterm:
                self._original_sigterm(signum, frame)
                
    def setup(self):
        """종료 처리 설정"""
        # 시그널 핸들러 등록
        signal.signal(signal.SIGINT, self._signal_handler)   # Ctrl+C
        signal.signal(signal.SIGTERM, self._signal_handler)  # kill
        
        crawler_logger.info("종료 처리 설정 완료")
        
    def cleanup_on_exit(self):
        """프로그램 종료 시 정리 작업 실행"""
        if not self._shutdown_flag.is_set():
            self._shutdown_flag.set()
            self._cleanup()
            
# 전역 인스턴스 생성
shutdown_handler = ShutdownHandler() 
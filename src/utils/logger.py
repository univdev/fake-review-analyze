"""
로깅 시스템 구현
"""

import os
import sys
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from pathlib import Path

class DateTimeEncoder(json.JSONEncoder):
    """datetime 객체를 JSON으로 직렬화하기 위한 인코더"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

class CrawlerLogger:
    """크롤러 로깅 시스템"""
    
    def __init__(self, log_dir: str = "logs"):
        """
        CrawlerLogger 초기화
        
        Args:
            log_dir (str): 로그 파일을 저장할 디렉토리
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # 기본 로거 설정
        self.logger = logging.getLogger("crawler")
        self.logger.setLevel(logging.INFO)
        
        # 이미 핸들러가 있다면 제거
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
            
        # 콘솔 핸들러 추가
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # 파일 핸들러 추가
        self.setup_file_handlers()
        
    def setup_file_handlers(self):
        """파일 핸들러를 설정합니다."""
        # 일반 로그 파일
        log_file = self.log_dir / f"crawler_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
        
        # 에러 로그 파일
        error_log_file = self.log_dir / f"error_{datetime.now().strftime('%Y%m%d')}.log"
        error_handler = logging.FileHandler(error_log_file, encoding="utf-8")
        error_handler.setLevel(logging.ERROR)
        error_formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s\n%(exc_info)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        error_handler.setFormatter(error_formatter)
        self.logger.addHandler(error_handler)
        
        # 상세 JSON 로그 파일
        self.json_log_file = self.log_dir / f"detailed_{datetime.now().strftime('%Y%m%d')}.jsonl"
        
    def format_context(self, context: Optional[Dict[str, Any]] = None) -> str:
        """컨텍스트 정보를 문자열로 포맷팅합니다."""
        if not context:
            return ""
            
        return f" [Context: {json.dumps(context, ensure_ascii=False, cls=DateTimeEncoder)}]"
        
    def info(self, message: str, context: Optional[Dict[str, Any]] = None):
        """정보 로그를 기록합니다."""
        self.logger.info(f"{message}{self.format_context(context)}")
        self._write_json_log("INFO", message, context)
        
    def warning(self, message: str, context: Optional[Dict[str, Any]] = None):
        """경고 로그를 기록합니다."""
        self.logger.warning(f"{message}{self.format_context(context)}")
        self._write_json_log("WARNING", message, context)
        
    def error(self, message: str, error: Optional[Exception] = None, context: Optional[Dict[str, Any]] = None):
        """에러 로그를 기록합니다."""
        if error:
            self.logger.error(
                f"{message}{self.format_context(context)}",
                exc_info=error
            )
        else:
            self.logger.error(f"{message}{self.format_context(context)}")
            
        self._write_json_log("ERROR", message, context, error)
        
    def debug(self, message: str, context: Optional[Dict[str, Any]] = None):
        """디버그 로그를 기록합니다."""
        self.logger.debug(f"{message}{self.format_context(context)}")
        self._write_json_log("DEBUG", message, context)
        
    def _write_json_log(
        self,
        level: str,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        error: Optional[Exception] = None
    ):
        """상세 JSON 로그를 기록합니다."""
        log_entry = {
            "timestamp": datetime.now(),
            "level": level,
            "message": message,
            "context": context
        }
        
        if error:
            log_entry["error"] = {
                "type": type(error).__name__,
                "message": str(error),
                "traceback": self._format_traceback(error)
            }
            
        with open(self.json_log_file, "a", encoding="utf-8") as f:
            json.dump(log_entry, f, ensure_ascii=False, cls=DateTimeEncoder)
            f.write("\n")
            
    def _format_traceback(self, error: Exception) -> Optional[str]:
        """예외의 트레이스백을 포맷팅합니다."""
        import traceback
        if error.__traceback__:
            return "".join(traceback.format_tb(error.__traceback__))
        return None
        
# 전역 로거 인스턴스 생성
crawler_logger = CrawlerLogger() 
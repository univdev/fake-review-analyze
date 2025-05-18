"""
WebDriver 유틸리티
"""

import os
import sys
import platform
from typing import Optional
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.config import HEADERS, SELENIUM_TIMEOUT, SELENIUM_IMPLICIT_WAIT
from src.utils.logger import crawler_logger

def get_chrome_version() -> Optional[str]:
    """
    시스템에 설치된 Chrome 브라우저의 버전을 확인합니다.
    
    Returns:
        Optional[str]: Chrome 버전 또는 None
    """
    try:
        if platform.system() == 'Darwin':  # macOS
            import subprocess
            process = subprocess.Popen(
                ['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '--version'],
                stdout=subprocess.PIPE
            )
            output = process.communicate()[0].decode('utf-8')
            return output.strip().split()[-1]  # "Google Chrome XX.X.XXXX.XX" -> "XX.X.XXXX.XX"
    except Exception as e:
        crawler_logger.warning(f"Chrome 버전 확인 중 오류 발생: {e}")
    return None

def create_chrome_options() -> Options:
    """Chrome 옵션을 생성합니다."""
    options = Options()
    
    # 기본 옵션 (headless 모드 비활성화)
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--start-maximized')
    
    # 실제 브라우저처럼 보이기 위한 설정
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_experimental_option('useAutomationExtension', False)
    
    # 최신 Chrome User-Agent 설정
    options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36')
    
    # 추가 헤더 설정
    options.add_argument('--accept-language=ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7')
    options.add_argument('--accept=text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7')
    
    # 브라우저 지문 설정
    options.add_argument('--disable-features=IsolateOrigins,site-per-process')
    options.add_argument('--disable-site-isolation-trials')
    
    # WebGL 벤더 및 렌더러 설정
    options.add_argument('--use-gl=desktop')
    options.add_argument('--use-angle=default')
    
    # 추가 성능 최적화 옵션
    prefs = {
        'profile.default_content_setting_values': {
            'notifications': 2,
            'images': 1,
            'javascript': 1,
            'cookies': 1,
            'plugins': 1,
            'popups': 2,
            'geolocation': 2,
            'auto_select_certificate': 2,
            'fullscreen': 2,
            'mouselock': 2,
            'mixed_script': 1,
            'media_stream': 2,
            'media_stream_mic': 2,
            'media_stream_camera': 2,
            'protocol_handlers': 2,
            'ppapi_broker': 2,
            'automatic_downloads': 2,
            'midi_sysex': 2,
            'push_messaging': 2,
            'ssl_cert_decisions': 2,
            'metro_switch_to_desktop': 2,
            'protected_media_identifier': 2,
            'app_banner': 2,
            'site_engagement': 2,
            'durable_storage': 2
        },
        'profile.password_manager_enabled': False,
        'profile.managed_default_content_settings.images': 1,
        'profile.default_content_settings.cookies': 1,
        'profile.managed_default_content_settings.javascript': 1
    }
    options.add_experimental_option('prefs', prefs)
    
    return options

def create_webdriver() -> webdriver.Chrome:
    """
    Chrome WebDriver 인스턴스를 생성하고 설정합니다.
    
    Returns:
        webdriver.Chrome: 설정된 Chrome WebDriver 인스턴스
        
    Raises:
        Exception: WebDriver 생성 실패 시
    """
    try:
        # Chrome 옵션 설정
        chrome_options = create_chrome_options()
        chrome_options.add_argument(f"user-agent={HEADERS['User-Agent']}")
        
        # 브라우저 자동 종료 방지
        chrome_options.add_experimental_option("detach", True)
        
        # macOS의 경우 추가 설정
        if platform.system() == 'Darwin':
            if platform.machine() == 'arm64':  # Apple Silicon
                chrome_options.add_argument("--disable-software-rasterizer")
                chrome_version = get_chrome_version()
                if chrome_version:
                    crawler_logger.info(f"감지된 Chrome 버전: {chrome_version}")
                    driver_manager = ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()
                else:
                    driver_manager = ChromeDriverManager().install()
            else:
                driver_manager = ChromeDriverManager().install()
        else:
            driver_manager = ChromeDriverManager().install()
            
        # WebDriver 생성
        service = Service(driver_manager)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # 페이지 로드 타임아웃 설정 (60초로 증가)
        driver.set_page_load_timeout(60)
        
        # 암시적 대기 시간 설정 (30초)
        driver.implicitly_wait(30)
        
        return driver
        
    except Exception as e:
        crawler_logger.error(f"WebDriver 생성 실패: {str(e)}")
        raise 
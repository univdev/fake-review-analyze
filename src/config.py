"""
Configuration settings for the fake review analysis project.
"""

import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

# Project Root Directory
PROJECT_ROOT = Path(__file__).parent.parent

# Data Directories
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"

# Ensure directories exist
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Crawler Settings
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
}

# Selenium Settings
SELENIUM_TIMEOUT = 10  # seconds
SELENIUM_IMPLICIT_WAIT = 5  # seconds

# URL Patterns
COUPANG_PRODUCT_PATTERN = r"https?://(?:www\.)?coupang\.com/vp/products/(\d+)"
NAVER_SHOPPING_PATTERN = r"https?://(?:www\.)?shopping\.naver\.com/(?:product|catalog)/(\d+)"

# File Settings
TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"
CSV_FILENAME_FORMAT = "reviews_{site}_{product_id}_{timestamp}.csv"

# Default configurations
DEFAULT_TIMEOUT = 30  # seconds
DEFAULT_RETRY_COUNT = 3
DEFAULT_DELAY = 2  # seconds between requests

# User agent settings
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
]

# File settings
OUTPUT_DIR = "data"

# Site specific settings
SUPPORTED_SITES = ["coupang", "naver"]
SITE_URLS = {
    "coupang": "https://www.coupang.com/vp/products/{product_id}",
    "naver": "https://shopping.naver.com/product/{product_id}"
} 
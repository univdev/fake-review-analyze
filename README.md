# 거짓 리뷰 분석 프로젝트

온라인 쇼핑몰의 거짓 리뷰를 판단하기 위한 데이터 수집 크롤러입니다.

## 기능

- 쿠팡과 네이버 쇼핑 리뷰 데이터 수집
- URL 기반 자동 사이트 분류
- CSV 형식 데이터 저장
- 크롤링 방지 기능 우회
- 자동 페이지네이션 처리

## 설치 방법

1. 가상환경 생성 및 활성화:

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 또는
.\venv\Scripts\activate  # Windows
```

2. 의존성 설치:

```bash
pip install -r requirements.txt
```

## 사용 방법

1. 환경 설정:

   - `.env` 파일을 생성하고 필요한 설정을 추가

2. 크롤러 실행:
   ```bash
   python src/main.py [URL]
   ```

## 프로젝트 구조

```
.
├── src/               # 소스 코드
├── tests/             # 테스트 코드
├── docs/              # 문서
├── data/              # 수집된 데이터 (자동 생성)
├── requirements.txt   # 의존성 목록
└── README.md         # 프로젝트 문서
```

## 개발 환경

- Python 3.x
- 주요 라이브러리:
  - requests
  - beautifulsoup4
  - pandas

## 라이선스

MIT License

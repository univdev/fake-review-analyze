# 11번가 리뷰 크롤러

## 설명

사용자가 입력한 상품 URL과 옵션에 따라 11번가 상품 리뷰를 자동으로 크롤링하여 저장하는 도구입니다.

## 지원 웹사이트

- [11번가](https://www.11st.co.kr)

## 사용 기술

- [Playwright](https://playwright.dev/) (웹 자동화 및 크롤링)
- [Commander](https://github.com/tj/commander.js/) (CLI 옵션 파싱)

## 사용법

### 개발 서버 실행 (자동 재시작)

```bash
pnpm dev
```

### 빌드

```bash
pnpm build
```

### 빌드 후 실행

```bash
pnpm start
```

### CLI 옵션 예시

```bash
pnpm dev -- --url "https://www.11st.co.kr/products/123456" --max-count 20
```

- `--url` : 크롤링할 상품의 URL (필수)
- `--max-count` : 최대 크롤링할 리뷰 개수 (기본값: 10)

> `--`를 붙여야 CLI 옵션이 tsx/dev에 전달됩니다.

## 크롤링 법적 경고

> 본 도구는 학습 및 연구 목적용입니다. 웹사이트의 이용약관 및 관련 법률을 반드시 준수하세요.

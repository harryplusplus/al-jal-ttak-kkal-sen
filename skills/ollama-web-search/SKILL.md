---
name: ollama-web-search
description: Ollama 웹 검색 API를 사용해 웹을 검색합니다. 사용자가 최신 정보, 뉴스, 사실 확인, 웹 검색을 요청할 때 사용하세요.
license: MIT
compatibility: uv와 인터넷 접속이 필요합니다.
metadata:
  author: al-jal-ttak-kkal-sen
  version: "1.0"
---

# 웹 검색 (Ollama Web Search)

Ollama 웹 검색 API를 사용해 최신 정보를 검색합니다.

## 전제 조건

- `OLLAMA_API_KEY` 환경변수가 설정되어 있어야 합니다.
- `uv`가 설치되어 있어야 합니다.
- 인터넷 접속이 가능해야 합니다.

## 사용법

### 기본 검색

```bash
uv run scripts/search.py "검색할 내용"
```

### 결과 개수 지정

```bash
uv run scripts/search.py "검색할 내용" --max-results 5
```

`--max-results` 옵션으로 반환할 결과 개수를 지정할 수 있습니다 (기본값: 5, 최대: 10).

## 출력 형식

JSON 배열로 검색 결과가 출력됩니다. 각 결과는 다음 필드를 포함합니다:

| 필드 | 설명 |
|-------|------|
| `title` | 웹 페이지 제목 |
| `url` | 웹 페이지 URL |
| `content` | 웹 페이지 내용 발췌 |

## 주의사항

- 검색 결과는 최대 10개까지 요청할 수 있습니다.
- `OLLAMA_API_KEY`가 설정되지 않은 경우 오류 메시지가 출력됩니다. 사용자에게 환경변수 설정을 안내하세요.
- 검색 결과가 많을 수 있으므로, 필요한 경우 `--max-results`로 결과 개수를 조절하세요.
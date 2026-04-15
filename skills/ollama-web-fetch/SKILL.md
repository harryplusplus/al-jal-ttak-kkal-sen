---
name: ollama-web-fetch
description: "웹 페치 스킬입니다. 특정 URL의 본문 텍스트, 제목, 링크를 읽을 때 사용하세요. 실행: bash 도구로 uv run scripts/fetch.py URL 을 실행. URL에 https://가 없어도 자동 처리됩니다. 결과는 JSON으로 title, content, links를 반환합니다."
license: MIT
compatibility: uv와 인터넷 접속이 필요합니다.
metadata:
  author: al-jal-ttak-kkal-sen
  version: "1.0"
---

# 웹 페이지 가져오기 (Ollama Web Fetch)

Ollama 웹 페치 API를 사용해 지정한 URL의 웹 페이지 내용을 가져옵니다.

## 전제 조건

- `OLLAMA_API_KEY` 환경변수가 설정되어 있어야 합니다.
- `uv`가 설치되어 있어야 합니다.
- 인터넷 접속이 가능해야 합니다.

## 사용법

```bash
uv run scripts/fetch.py "https://example.com"
```

URL을 인수로 전달하세요. `https://` 접두사가 없어도 자동으로 처리됩니다.

## 출력 형식

JSON 객체로 웹 페이지 정보가 출력됩니다:

| 필드 | 설명 |
|-------|------|
| `title` | 웹 페이지 제목 |
| `content` | 웹 페이지 본문 내용 |
| `links` | 페이지에 포함된 링크 목록 |

## 주의사항

- `OLLAMA_API_KEY`가 설정되지 않은 경우 오류 메시지가 출력됩니다. 사용자에게 환경변수 설정을 안내하세요.
- 일부 웹 페이지는 접근이 제한될 수 있습니다.
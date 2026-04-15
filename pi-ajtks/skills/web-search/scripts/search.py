# /// script
# requires-python = ">=3.10"
# ///

"""Ollama 웹 검색 스크립트

Ollama Web Search API를 사용해 웹을 검색합니다.

사용법:
    uv run search.py "검색어" [--max-results N]

환경변수:
    OLLAMA_API_KEY - Ollama API 키 (필수)
"""

import argparse
import contextlib
import json
import os
import sys
import urllib.error
import urllib.request

API_URL = "https://ollama.com/api/web_search"


class _Args(argparse.Namespace):
    query: str
    max_results: int


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ollama 웹 검색 API를 사용해 웹을 검색합니다.",
        epilog=('예시:\n  uv run search.py "최신 AI 뉴스"\n  uv run search.py "올라마란 무엇인가" --max-results 3\n'),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "query",
        help="검색할 질의 문자열",
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=5,
        help="반환할 최대 검색 결과 개수 (기본값: 5, 최대: 10)",
    )
    args = parser.parse_args(namespace=_Args())

    # OLLAMA_API_KEY 확인
    api_key = os.environ.get("OLLAMA_API_KEY")
    if not api_key:
        print(
            "오류: OLLAMA_API_KEY 환경변수가 설정되지 않았습니다.\n"
            "OLLAMA_API_KEY 환경변수를 설정해주세요.\n"
            "API 키는 https://ollama.com/settings/keys 에서 생성할 수 있습니다.",
            file=sys.stderr,
        )
        sys.exit(1)

    # max_results 범위 검증
    max_results = args.max_results
    if max_results < 1:
        print("오류: --max-results는 1 이상이어야 합니다.", file=sys.stderr)
        sys.exit(1)
    if max_results > 10:
        print("오류: --max-results는 최대 10까지 가능합니다.", file=sys.stderr)
        sys.exit(1)

    # API 요청
    payload = json.dumps(
        {
            "query": args.query,
            "max_results": max_results,
        }
    ).encode("utf-8")

    req = urllib.request.Request(
        API_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req) as resp:
            body = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        if e.code == 401:
            print(
                "오류: OLLAMA_API_KEY가 유효하지 않습니다.\n"
                "올바른 API 키를 설정해주세요.\n"
                "API 키는 https://ollama.com/settings/keys 에서 확인할 수 있습니다.",
                file=sys.stderr,
            )
        else:
            error_body = ""
            with contextlib.suppress(Exception):
                error_body = e.read().decode("utf-8", errors="replace")
            print(
                f"오류: API 요청 실패 (HTTP {e.code})\n{error_body}",
                file=sys.stderr,
            )
        sys.exit(1)
    except urllib.error.URLError as e:
        print(
            f"오류: 네트워크 연결에 실패했습니다.\n{e.reason}",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        print(
            f"오류: API 응답을 파싱할 수 없습니다.\n{body}",
            file=sys.stderr,
        )
        sys.exit(1)

    # 결과 출력
    results = data.get("results", [])
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

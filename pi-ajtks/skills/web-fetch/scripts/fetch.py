# /// script
# requires-python = ">=3.10"
# ///

"""Ollama 웹 페치 스크립트

Ollama Web Fetch API를 사용해 웹 페이지 내용을 가져옵니다.

사용법:
    uv run fetch.py "URL"

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

API_URL = "https://ollama.com/api/web_fetch"


class _Args(argparse.Namespace):
    url: str


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ollama 웹 페치 API를 사용해 웹 페이지 내용을 가져옵니다.",
        epilog=('예시:\n  uv run fetch.py "https://ollama.com"\n  uv run fetch.py "ollama.com"\n'),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "url",
        help="가져올 웹 페이지 URL",
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

    # URL 정규화 - 스킴이 없으면 https:// 추가
    url = args.url
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    # API 요청
    payload = json.dumps({"url": url}).encode("utf-8")

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
        elif e.code == 404:
            print(
                f"오류: 지정한 URL의 웹 페이지를 찾을 수 없습니다.\nURL: {url}",
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
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

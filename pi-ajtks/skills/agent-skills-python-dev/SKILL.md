---
name: agent-skills-python-dev
description: >-
  Agent Skills 내 Python 스크립트의 코드 품질을 검사하는 스킬입니다.
  ruff 포맷/린트와 pyright 타입체크를 Agent Skills 스크립트 관례에
  맞게 실행합니다. Agent Skills에 Python 스크립트를 포함할 때,
  스크립트 품질 검사나 PEP 723 준수 확인이 필요할 때 사용하세요.
license: MIT
compatibility: uv가 필요합니다.
metadata:
  author: al-jal-ttak-kkal-sen
  version: "1.0"
---

# Agent Skills Python Development

Agent Skills 내 Python 스크립트의 코드 품질을 검사합니다.

Agent Skills 스펙은 스크립트 포함 시 다음 관례를 권장합니다:
- PEP 723 인라인 메타데이터로 `uv run` 실행
- JSON 출력은 stdout, 진단은 stderr
- 대화형 입력 금지 (argparse 등 사용)
- 의미 있는 종료 코드

이 스킬은 위 관례에 맞춘 ruff/pyright 설정을 사용합니다.
프로젝트의 pyproject.toml에 의존하지 않습니다.

## 사용 가능한 스크립트

- **`scripts/check.py`** — ruff 포맷/린트 + pyright 타입체크

## 워크플로우

### 전체 검사

```bash
uv run scripts/check.py <path>...
```

### 자동 수정

```bash
uv run scripts/check.py <path>... --fix
```

### 개별 검사

```bash
uv run scripts/check.py <path>... --format-only
uv run scripts/check.py <path>... --lint-only
uv run scripts/check.py <path>... --typecheck-only
```

### 빠른 검사 (타입체크 생략)

```bash
uv run scripts/check.py <path>... --format-only --lint-only
```

## 설정

`assets/ruff.toml`과 `assets/pyrightconfig.json`의 설정을 사용합니다:

| 설정 | 값 | 이유 |
|------|-----|------|
| line-length | 120 | 스크립트는 프로젝트보다 관대 |
| target-version | py310 | PEP 723 `requires-python`과 일치 |
| typeCheckingMode | strict | 장기 유지보수 용이 |
| lint select | E,F,W,I,UP,B,SIM,RUF | 합리적 기본 규칙 세트 |

프로젝트 설정에 의존하지 않고 `--config`/`--project`로 스킬 내장 설정을 강제합니다.

## 다른 스킬과의 관계

- **agent-skills-dev**: 스펙 검증(validate), 속성 읽기, 스캐폴딩
- **agent-skills-python-dev** (이 스킬): Python 스크립트 품질 검사
- **agent-skills-review**: 종합 검수 (위 두 스킬을 모두 호출)

## 주의사항

- `uvx`로 ruff/pyright를 실행하므로 uv가 설치되어 있어야 합니다.
- `_common.py` 등 프라이빗 모듈(`_` 접두사)의 임포트는 `extraPaths`로 자동 해결됩니다.
- 타입체크는 `--typecheck-only`로 단독 실행하거나 기본 전체 검사에 포함됩니다.
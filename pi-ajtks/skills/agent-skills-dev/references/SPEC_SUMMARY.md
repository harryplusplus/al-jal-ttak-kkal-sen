# Agent Skills 스펙 요약

Agent Skills 개방형 포맷의 축약 참조.
전체 스펙: https://agentskills.io/specification
리포지토리: https://github.com/agentskills/agentskills

## 디렉토리 구조

```
skill-name/
├── SKILL.md          # 필수: 메타데이터 + 지시사항
├── scripts/          # 선택: 실행 가능한 코드
├── references/       # 선택: 문서
├── assets/           # 선택: 템플릿, 리소스
└── ...               # 추가 파일/디렉토리 가능
```

## SKILL.md 형식

YAML frontmatter + Markdown 본문:

```markdown
---
name: skill-name
description: 이 스킬이 하는 일과 언제 사용하는지.
license: Apache-2.0
compatibility: Python 3.10+ 필요
allowed-tools: Bash(git:*) Read
metadata:
  author: org-name
  version: "1.0"
---

# 스킬 지시사항

본문 내용은 여기에...
```

### frontmatter 필드

| 필드 | 필수 | 제약 |
|------|------|------|
| `name` | 예 | 최대 64자. 소문자, 숫자, 하이픈만. 시작/끝 하이픈 금지. 연속 하이픈 금지. 디렉토리명과 일치해야 함. |
| `description` | 예 | 최대 1024자. 비어있으면 안 됨. 하는 일 + 사용 시점 모두 기술. |
| `license` | 아니요 | 문자열. 라이선스 이름 또는 번들된 라이선스 파일 참조. |
| `compatibility` | 아니요 | 최대 500자. 환경 요구사항. |
| `allowed-tools` | 아니요 | 공백으로 구분된 문자열. 사전 승인된 도구. 실험적. |
| `metadata` | 아니요 | 문자열→문자열 매핑. 클라이언트별 속성. |

### name 규칙

- 1~64자
- `a-z`, `0-9`, `-`만 사용
- `-`로 시작하거나 끝날 수 없음
- `--`(연속 하이픈) 금지
- 부모 디렉토리명과 일치해야 함
- 유니코드: NFKC 정규화 적용

### description 작성 가이드

- **하는 일**과 **사용 시점** 모두 기술
- 활성화 조건 명시: "~할 때", "~하는 경우"로 에이전트가 판단할 수 있게 작성
- 사용자 의도에 집중, 구현이 아닌
- 활성화 키워드를 구체적으로 포함
- 1024자 제한

## 점진적 공개

3단계 컨텍스트 로딩:

1. **카탈로그** (~50-100 토큰/스킬): `name` + `description`만 시작 시 로드
2. **지시사항** (<5000 토큰 권장): SKILL.md 본문 전체를 활성화 시 로드
3. **리소스** (필요 시): scripts/, references/, assets/는 필요할 때만 로드

SKILL.md은 500줄 이하 권장. 상세 내용은 별도 파일로 분리.

## 파일 참조

- 스킬 루트에서 상대 경로 사용
- SKILL.md에서 한 단계 깊이까지만 참조
- 깊이 중첩된 참조 체인 피하기

## 스크립트 작성 관례

- 자체 포함 또는 의존성을 명확히 문서화
- PEP 723 인라인 메타데이터 사용 (`uv run`으로 실행)
- 대화형 프롬프트 금지 — CLI 인수, 환경변수, stdin으로 입력
- JSON은 stdout, 진단은 stderr로 출력 분리
- 실행 가능한 오류 메시지 제공
- 멱등성(idempotency) 권장
- 의미 있는 종료 코드 사용

## 검증 체크리스트

- [ ] SKILL.md 존재, 유효한 YAML frontmatter
- [ ] `name` 필드: 필수, 유효한 형식, 디렉토리명과 일치
- [ ] `description` 필드: 필수, 비어있지 않음, ≤1024자
- [ ] 예상치 못한 frontmatter 필드 없음
- [ ] `compatibility` ≤500자 (있는 경우)
- [ ] `metadata` 값이 문자열→문자열 매핑 (있는 경우)
- [ ] 본문이 비어있지 않고 명확한 지시사항 포함
- [ ] 본문 500줄 이하
- [ ] 스크립트가 PEP 723 메타데이터 포함
- [ ] 파일 참조에 상대 경로 사용

## 자주하는 실수

- description에 콜론이 포함되면 YAML에서 따옴표 필요 (PyYAML은 관대하지만 strictyaml은 아님)
- `metadata` 값은 모두 문자열이어야 함 (숫자는 따옴표: `version: "1.0"`)
- `allowed-tools`는 하이픈 사용 (underscore 아님)
- 디렉토리명이 `name` 필드와 정확히 일치해야 함
- SKILL.md (대문자)가 skill.md (소문자)보다 우선
---
name: agent-skills-review
description: >-
  Agent Skills를 검수하는 스킬입니다. 스펙 준수, description 품질, 본문 구조,
  스크립트 품질, 코드 품질을 종합 검수합니다. 다른 에이전트가 만든 스킬을
  검수하거나 자체 스킬의 품질을 확인할 때 사용하세요. 스킬 검수, 품질 평가,
  리뷰 작업에 활성화하세요.
license: MIT
compatibility: uv가 필요합니다.
metadata:
  author: al-jal-ttak-kkal-sen
  version: "1.0"
---

# Agent Skills Review

Agent Skills의 품질을 종합 검수합니다. **비판적 검수자** 관점에서 접근합니다.

## 사용 가능한 스크립트

- **`scripts/review.py`** — 종합 검수 (스펙 + 품질 + 코드)

## 검수 워크플로우

### 기본 검수

```bash
uv run scripts/review.py <skill-dir>
```

타입체크 생략 (빠른 검수):

```bash
uv run scripts/review.py <skill-dir> --skip-typecheck
```

### 결과 해석

| severity | 의미 | 액션 |
|----------|------|------|
| critical | 필수 수정 — 스펙 위반/동작 불가 | 즉시 수정 |
| warning | 권장 수정 — 품질/효과 문제 | 수정 권장 |
| suggestion | 개선 제안 — 더 나은 스킬을 위해 | 검토 후 반영 |
| info | 참고 사항 | 불필요 |

### 검수 후 피드백 전달

Inspector가 발견한 critical/warning 항목을 Builder에게 전달:

1. `findings` 배열에서 `severity: critical` 항목 먼저 수정
2. `severity: warning` 항목 검토
3. `suggestion` 항목은 선택 반영
4. 수정 후 재검수

## 검수 관점 (Builder와의 차이)

Builder는 "어떻게 만들지"에 집중하지만, Inspector는 **"어디서 실패하지"**에 집중합니다:

- **description**: 에이전트가 이 스킬을 언제 활성화해야 하는지 명확한가?
- **gotchas**: 에이전트가 혼자서는 절대 모를 비자명적 사실이 있는가?
- **스크립트**: 대화형 입력 없이 자동화 환경에서 동작하는가?
- **출력**: JSON으로 프로그래밍틱하게 소비 가능한가?

## 주의사항

- review.py는 agent-skills-dev의 validate.py와 check.py를 내부적으로 호출합니다.
- agent-skills-dev 스킬이 같은 환경에 설치되어 있어야 합니다.
- 검수 대상 스킬의 scripts/에 Python 파일이 있으면 check.py가 실행됩니다.

## 상세 체크리스트

전체 검수 기준은 [REVIEW_CHECKLIST.md](references/REVIEW_CHECKLIST.md)를 참조하세요.
# Agent Skills 검수 체크리스트

Agent Skills 품질 평가를 위한 축약 검수 기준.
기반: https://agentskills.io/specification 및 작성 가이드

## 스펙 준수 (Critical)

- [ ] SKILL.md 존재 (대문자 권장)
- [ ] YAML frontmatter가 유효함 (---으로 시작/종료)
- [ ] `name` 필드: 있음, 유효한 형식, 디렉토리명과 일치
- [ ] `description` 필드: 있음, 비어있지 않음, ≤1024자
- [ ] 예상치 못한 frontmatter 필드 없음
- [ ] `compatibility` ≤500자 (있는 경우)
- [ ] `metadata`가 문자열→문자열 매핑 (있는 경우)

## description 품질 (Critical/Warning)

- [ ] 최소 50자 이상, 구체적 키워드 포함
- [ ] 명령형 표현 사용 ("이 스킬을 사용하세요 ~할 때")
- [ ] 언제 활성화할지 설명 (하는 일뿐만 아니라)
- [ ] 사용자 의도에 집중, 구현이 아님
- [ ] 에이전트 발견을 위한 키워드 포함
- [ ] 암시적 활성화 경우 언급 ("~를 명시하지 않아도")

## 본문 품질 (Warning/Suggestion)

- [ ] 비어있지 않고 명확한 지시사항 포함
- [ ] "사용 시점" 또는 활성화 조건 섹션 있음
- [ ] 단계별 지시사항 섹션 있음
- [ ] "주의사항" 섹션 있음 (비자명적 사실)
- [ ] 500줄 이하 (상세 내용은 references/로 분리)
- [ ] 채워지지 않은 플레이스홀더 없음 ([describe...], TODO, FIXME)
- [ ] 파일 참조에 상대 경로 사용

## 스크립트 품질 (Warning/Suggestion)

- [ ] PEP 723 인라인 메타데이터 (`# /// script` 블록) 포함
- [ ] 대화형 입력 없음 (input() 금지)
- [ ] JSON 출력은 stdout, 진단은 stderr
- [ ] argparse 또는 CLI 인수 파싱 사용
- [ ] 실행 가능한 오류 메시지 제공
- [ ] 의미 있는 종료 코드 사용
- [ ] 멱등성(idempotency) 권장

## 코드 품질 (Warning)

- [ ] ruff format: 통과
- [ ] ruff check: 에러 없음
- [ ] pyright: 타입 에러 없음

## 구조 (Info/Suggestion)

- [ ] SKILL.md (대문자) 권장
- [ ] evals/ 디렉토리와 테스트 케이스 권장
- [ ] scripts/ 디렉토리 (실행 코드가 있는 경우)
- [ ] references/ (상세 문서)
- [ ] assets/ (템플릿, 리소스)

## 심각도 가이드

| 심각도 | 의미 |
|--------|------|
| critical | 필수 수정 — 스펙 위반 또는 동작 불가 |
| warning | 권장 수정 — 품질/효과 문제 |
| suggestion | 개선 제안 — 더 나은 스킬을 위해 |
| info | 참고 사항 — 조치 불필요 |
---
name: pi-ajtks-extension-dev
description: >-
  Pi 확장을 개발하고 유지관리하는 스킬입니다. TypeScript 확장 파일의 포맷,
  린트, 타입체크를 검사합니다. Pi 확장을 만들거나 수정할 때, 확장 품질
  검사가 필요할 때 사용하세요.
license: MIT
compatibility: uv가 필요합니다.
metadata:
  author: al-jal-ttak-kkal-sen
  version: "1.0"
---

# Pi Extension Development

Pi 확장(extensions)의 코드 품질을 검사합니다.

## 사용 가능한 스크립트

- **`scripts/check.py`** — oxfmt 포맷/린트 + tsgo 타입체크

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

## 설정

npx로 호출하므로 별도 설치가 필요 없습니다:

| 도구 | npm 패키지 | 용도 |
|------|-----------|------|
| oxfmt | `oxfmt` | 포맷 |
| oxlint | `oxlint` | 린트 |
| tsgo | `@typescript/native-preview` | 타입체크 |

`npx`가 최초 실행 시 자동 다운로드합니다.

## 프로젝트 구조

```
pi-ajtks/
├── package.json          # peerDependencies: pi-coding-agent, typebox
├── extensions/
│   ├── hindsight.ts      # Pi 확장
│   ├── grep.ts
│   └── temperature.ts
└── skills/
    └── ...
```

- Pi 확장은 TypeScript로 작성, jiti가 TS를 직접 실행 (JS 빌드 불필요)
- `@mariozechner/pi-coding-agent`와 `@sinclair/typebox`는 peerDependencies
- 추가 의존성은 `dependencies`에 선언, `pnpm install`로 설치

## 안전한 테스트

확장은 Pi 설정에서 명시적으로 선택한 것만 로드됩니다. 개발 중인 확장이 자동으로 로드될 걱정 없이 안전하게 개발할 수 있습니다.

```bash
# 단일 확장 격리 테스트
pi -e ./extensions/my-extension.ts

# 프롬프트와 함께 테스트
pi -e ./extensions/my-extension.ts -p "테스트 프롬프트"

# 세션 미저장 1회성 테스트
pi -e ./extensions/my-extension.ts --no-session -p "테스트"
```

개발 완료 후 `~/.pi/agent/settings.json`의 패키지 `extensions` 목록에 추가하면 Pi에 반영됩니다:

```json
{
  "packages": [
    {
      "source": "../../repo/al-jal-ttak-kkal-sen/pi-ajtks",
      "extensions": ["extensions/grep.ts", "extensions/my-extension.ts"],
      "skills": [...]
    }
  ]
}
```

## Pi 확장 API

확장은 `ExtensionAPI`를 받아 이벤트 구독, 도구 등록, 명령어 추가:

```typescript
import type { ExtensionAPI } from '@mariozechner/pi-coding-agent'

export default function (pi: ExtensionAPI) {
  pi.on('session_start', async (event, ctx) => {
    ctx.ui.notify('Extension loaded!', 'info')
  })
}
```

주요 이벤트: `session_start`, `session_shutdown`, `before_agent_start`, `agent_end`, `tool_call`, `tool_result`

주요 API: `pi.registerTool()`, `pi.registerCommand()`, `pi.exec()`, `pi.sendMessage()`, `ctx.ui.notify()`, `ctx.sessionManager`

상세 API: Pi 확장 문서는 `@mariozechner/pi-coding-agent` 패키지의 `docs/extensions.md`를 참조하세요.

## 주의사항

- 확장 팩토리 함수는 `async function`도 가능 (초기화 시 비동기 작업 필요한 경우)
- `ctx.signal`로 에이전트 중단 시 작업 취소 가능
- `console.error()`로 디버그 로그 출력 (파일 로깅은 직접 구현)
- 확장에서 발생한 예외는 Pi가 캐치하지만, `throw`로 확장 로딩 실패를 알릴 수 있음
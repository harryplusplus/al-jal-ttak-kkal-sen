# OpenClaw Home

## Architecture

```
OpenClaw (Discord) ──┐
                     ├─→ Hindsight API (:8888) ─→ PostgreSQL (hindsight DB)
OpenCode (TUI) ──────┘         │                     ├─ pgvector (벡터 검색)
                               │                     ├─ vchord (의존성)
Control Plane (API 조회)        ├─→ Ollama (:11434)   ├─ vchord_bm25 (BM25)
                               │   ├─ glm-5.1:cloud  └─ pg_tokenizer (한국어 토크나이징)
                               │   └─ nomic-embed-text-v2-moe
                               └─← 
```

## Setup

### PostgreSQL

```sh
createdb hindsight
brew install pgvector
psql -d hindsight -c "CREATE EXTENSION IF NOT EXISTS vector CASCADE;"
```

### vchord (소스 빌드, Rust nightly 필요)

```sh
cd VectorChord-1.1.1 && make build && make install
psql -d hindsight -c "ALTER SYSTEM SET shared_preload_libraries = 'vchord';"
brew services restart postgresql@18
psql -d hindsight -c "CREATE EXTENSION IF NOT EXISTS vchord CASCADE;"
```

### pg_tokenizer + vchord_bm25 (pgrx 0.16.1 필요)

```sh
cargo install cargo-pgrx --version 0.16.1 --locked

cd pg_tokenizer.rs-0.1.1
cargo pgrx install --release --pg-config /opt/homebrew/bin/pg_config

cd VectorChord-bm25-0.3.0
cargo pgrx install --release --pg-config /opt/homebrew/bin/pg_config

psql -d hindsight -c "ALTER SYSTEM SET shared_preload_libraries = 'vchord,pg_tokenizer';"
brew services restart postgresql@18
psql -d hindsight -c "CREATE EXTENSION IF NOT EXISTS pg_tokenizer CASCADE;"
psql -d hindsight -c "CREATE EXTENSION IF NOT EXISTS vchord_bm25 CASCADE;"
```

### .env

`.env.example` 참고

### 실행

Hindsight API:
```sh
uv run --env-file .env hindsight-api
```

Hindsight Control Plane:
```sh
pnpm i && uv run --env-file .env pnpm hindsight-control-plane
```

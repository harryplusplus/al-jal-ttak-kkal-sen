# OpenClaw Home

## Architecture

```
OpenClaw ────────────────┐
                         ├─→ Hindsight API ─→ PostgreSQL
OpenCode ────────────────┤       │            ├─ pgvector (vector search)
                         │       │            ├─ vchord (dependency)
Hindsight Control Plane ─┘       │            ├─ vchord_bm25 (BM25 search)
                                 └─→ Ollama   └─ pg_tokenizer (Korean tokenizer)
                                     ├─ glm-5.1:cloud
                                     └─ nomic-embed-text-v2-moe
```

## Setup

### PostgreSQL

```sh
brew install postgresql@18
brew services start postgresql@18
createdb hindsight
```

### pgvector

```sh
brew install pgvector
```

### vchord (source build, requires Rust nightly)

```sh
curl -fsSL https://github.com/tensorchord/VectorChord/archive/refs/tags/1.1.1.tar.gz | tar -xz
make build -C VectorChord-1.1.1 && make install -C VectorChord-1.1.1
```

### pg_tokenizer + vchord_bm25 (requires pgrx 0.16.1)

```sh
cargo install cargo-pgrx --version 0.16.1 --locked

curl -fsSL https://github.com/tensorchord/pg_tokenizer.rs/archive/refs/tags/0.1.1.tar.gz | tar -xz
cargo pgrx install --release --pg-config /opt/homebrew/bin/pg_config --manifest-path pg_tokenizer.rs-0.1.1/Cargo.toml

curl -fsSL https://github.com/tensorchord/VectorChord-bm25/archive/refs/tags/0.3.0.tar.gz | tar -xz
cargo pgrx install --release --pg-config /opt/homebrew/bin/pg_config --manifest-path VectorChord-bm25-0.3.0/Cargo.toml
```

### Activate extensions

```sh
psql -d hindsight -c "ALTER SYSTEM SET shared_preload_libraries = 'vchord,pg_tokenizer';"
brew services restart postgresql@18
psql -d hindsight -c "CREATE EXTENSION IF NOT EXISTS vector CASCADE;"
psql -d hindsight -c "CREATE EXTENSION IF NOT EXISTS vchord CASCADE;"
psql -d hindsight -c "CREATE EXTENSION IF NOT EXISTS pg_tokenizer CASCADE;"
psql -d hindsight -c "CREATE EXTENSION IF NOT EXISTS vchord_bm25 CASCADE;"
```

### .env

See `.env.example`

### Run

Hindsight API:
```sh
uv run --env-file .env hindsight-api
```

Hindsight Control Plane:
```sh
pnpm i && uv run --env-file .env pnpm hindsight-control-plane
```
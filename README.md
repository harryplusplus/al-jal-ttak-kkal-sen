# Harry's OpenClaw Home

## Dependencies

- uv
- pnpm
- postgres
- ollama

### Ollama Setup

```sh
ollama pull nomic-embed-text-v2-moe
```

### Postgres Setup

```sh
createdb hindsight
brew install pgvector
psql -d hindsight -c "CREATE EXTENSION IF NOT EXISTS vector CASCADE;"
psql -d hindsight -c "CREATE EXTENSION IF NOT EXISTS vchord CASCADE;"
```

### VectorChord BM25 Setup

#### VectorChord

[VectorChord Installation / Source](https://docs.vectorchord.ai/vectorchord/getting-started/installation.html#source)

```sh
cd VectorChord-1.1.1
make build
make install
```

```sh
psql -d hindsight -c "ALTER SYSTEM SET shared_preload_libraries = 'vchord';"
brew services restart postgresql@18
psql -d hindsight -c "CREATE EXTENSION IF NOT EXISTS vchord CASCADE;"
```

#### pg_tokenizer.rs

[GitHub](https://github.com/tensorchord/pg_tokenizer.rs)

```sh
cargo install cargo-pgrx --version 0.16.1 --locked
```

```sh
cd pg_tokenizer.rs-0.1.1
cargo pgrx install --release --pg-config /opt/homebrew/bin/pg_config
```

```sh
psql -d hindsight -c "CREATE EXTENSION IF NOT EXISTS pg_tokenizer CASCADE;"
```

#### VectorChord-bm25

[GitHub](https://github.com/tensorchord/VectorChord-bm25)

```sh
cd VectorChord-bm25-0.3.0
cargo pgrx install --release --pg-config /opt/homebrew/bin/pg_config
```

```sh
psql -d hindsight -c "ALTER SYSTEM SET shared_preload_libraries = 'vchord,pg_tokenizer';"
brew services restart postgresql@18
psql -d hindsight -c "CREATE EXTENSION IF NOT EXISTS vchord_bm25 CASCADE;"
```

### Hindsight Setup

#### Configure LLM

[Configuration](https://hindsight.vectorize.io/developer/configuration)

#### .env

```
HINDSIGHT_API_DATABASE_URL=postgresql://harry@localhost:5432/hindsight
HINDSIGHT_API_LLM_BASE_URL=http://localhost:11434/v1
HINDSIGHT_API_LLM_API_KEY=ollama
HINDSIGHT_API_LLM_MODEL=glm-5.1:cloud
HINDSIGHT_API_EMBEDDINGS_PROVIDER=openai
HINDSIGHT_API_EMBEDDINGS_OPENAI_BASE_URL=http://localhost:11434/v1
HINDSIGHT_API_EMBEDDINGS_OPENAI_MODEL=nomic-embed-text-v2-moe
HINDSIGHT_API_EMBEDDINGS_OPENAI_API_KEY=ollama
HINDSIGHT_API_TEXT_SEARCH_EXTENSION=vchord
```

#### Run API Server

```sh
uv run --env-file .env hindsight-api
```

#### Run Dashboard

```sh
pnpm i
uv run --env-file .env pnpm hindsight-control-plane
```

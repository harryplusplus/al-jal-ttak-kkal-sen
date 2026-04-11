# Al Jal Ttak Kkal Sen

"Al Jal Ttak Kkal Sen" is the Korean alphabet rendering of 알잘딱깔센 — roughly, "doing the right thing, cleanly, with good sense."

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

```sh
uv run setup
```

### .env

See `.env.example`

### Run

Hindsight API:
```sh
tmux new -s hs-api 'uv run hs-api'
```

Hindsight Control Plane:
```sh
tmux new -s hs-web 'uv run hs-web'
```

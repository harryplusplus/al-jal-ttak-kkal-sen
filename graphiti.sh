#!/usr/bin/env bash
set -euo pipefail

SESSION_NAME="graphiti"

docker compose up -d --wait

if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
  echo "tmux session '$SESSION_NAME' already exists"
  exit 0
fi

tmux new-session -d -s "$SESSION_NAME" -c "$(pwd)/external/graphiti/mcp_server" \
  "uv run main.py --config ../../../config/graphiti.yaml"

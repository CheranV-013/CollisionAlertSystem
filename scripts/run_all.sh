#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
source "$ROOT/.venv/bin/activate"
(cd "$ROOT/backend" && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000) &
(cd "$ROOT/frontend" && npm run dev -- --host 0.0.0.0) &
wait


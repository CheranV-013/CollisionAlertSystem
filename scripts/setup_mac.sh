#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
python3 -m venv "$ROOT/.venv"
source "$ROOT/.venv/bin/activate"
python -m pip install -r "$ROOT/backend/requirements.txt"
(cd "$ROOT/frontend" && npm install)
echo "Ready. Run: $ROOT/scripts/run_all.sh"


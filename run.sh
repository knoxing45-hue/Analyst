#!/usr/bin/env bash
# Run the full stack locally (backend + frontend).

set -e

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== Starting backend (FastAPI) on :8000 ==="
(cd "$ROOT/backend" && source venv/bin/activate && uvicorn app.main:app --reload --port 8000) &
BACKEND_PID=$!

echo "=== Starting frontend (Vite) on :5173 ==="
(cd "$ROOT/frontend" && npm run dev) &
FRONTEND_PID=$!

trap "echo 'Stopping...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT INT TERM

wait

#!/usr/bin/env bash
# KnightLife — start all services in separate Terminal tabs
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND="$ROOT/backend"
VENV="$BACKEND/.venv/bin/activate"

# ── Write .env.local if missing ───────────────────────────────────────────────
if [ ! -f "$ROOT/.env.local" ]; then
  echo "VITE_API_URL=http://localhost:8000" > "$ROOT/.env.local"
  echo "[knightlife] Created .env.local"
fi

# ── Helper: open a new Terminal tab running a command ────────────────────────
open_tab() {
  local title="$1"
  local cmd="$2"
  osascript <<EOF
tell application "Terminal"
  tell application "System Events" to keystroke "t" using command down
  delay 0.3
  do script "printf '\\\\e]0;${title}\\\\a'; ${cmd}" in front window
end tell
EOF
}

echo "[knightlife] Starting all services…"

# Tab 1 — FastAPI
open_tab "KL · API" \
  "cd '$BACKEND' && source '$VENV' && uvicorn api.main:app --reload --host 0.0.0.0 --port 8000"

sleep 0.5

# Tab 2 — LLM Workers
open_tab "KL · Workers" \
  "cd '$BACKEND' && source '$VENV' && python run_workers.py"

sleep 0.5

# Tab 3 — Vite dev server
open_tab "KL · Frontend" \
  "cd '$ROOT' && npm run dev"

echo "[knightlife] All tabs launched."
echo "  API      → http://localhost:8000"
echo "  API docs → http://localhost:8000/docs"
echo "  Frontend → http://localhost:5173"

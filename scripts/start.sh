#!/usr/bin/env bash
set -euo pipefail

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

mkdir -p data/logs

if command -v curl >/dev/null; then
  if ! curl -fsS http://localhost:11434/api/tags >/dev/null 2>&1; then
    if command -v ollama >/dev/null; then
      echo "[jarvis] Starting Ollama in background"
      nohup ollama serve > data/logs/ollama.log 2>&1 &
      sleep 3
    else
      echo "[jarvis] Ollama not found; backend will start but model requests will fail"
    fi
  fi
fi

echo "[jarvis] Starting API in background"
nohup poetry run uvicorn api.main:app --host 0.0.0.0 --port 8000 > data/logs/api.log 2>&1 &
API_PID=$!

if command -v pnpm >/dev/null; then
  echo "[jarvis] Starting dashboard in background"
  (
    cd dashboard
    export NEXT_PUBLIC_JARVIS_API_BASE_URL="${NEXT_PUBLIC_JARVIS_API_BASE_URL:-http://localhost:8000}"
    export NEXT_PUBLIC_JARVIS_AUTH_TOKEN="${NEXT_PUBLIC_JARVIS_AUTH_TOKEN:-${JARVIS_AUTH_TOKEN:-}}"
    nohup pnpm dev > ../data/logs/dashboard.log 2>&1 &
  )
fi

echo "[jarvis] API: http://localhost:8000"
echo "[jarvis] Dashboard: http://localhost:3000"
echo "[jarvis] Logs: data/logs"

wait "$API_PID"

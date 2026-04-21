#!/usr/bin/env bash
set -euo pipefail

echo "[jarvis] Starting API"
uvicorn api.main:app --host 0.0.0.0 --port 8000


#!/usr/bin/env bash
set -euo pipefail

echo "[jarvis] Verifying local prerequisites"
command -v curl >/dev/null || { echo "curl is required"; exit 1; }
command -v ffmpeg >/dev/null || echo "ffmpeg not found yet"
command -v python3 >/dev/null || echo "python3 not found yet"
command -v pnpm >/dev/null || echo "pnpm not found yet"

echo "[jarvis] Preparing local directories"
mkdir -p data/chroma data/conversations data/logs

if command -v poetry >/dev/null; then
  echo "[jarvis] Installing Python dependencies with poetry"
  poetry install
else
  echo "[jarvis] Poetry not found; install it or adapt to uv/pip before running backend"
fi

if command -v pnpm >/dev/null; then
  echo "[jarvis] Installing dashboard dependencies"
  (cd dashboard && pnpm install)
fi

echo "[jarvis] Setup scaffold completed"


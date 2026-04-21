#!/usr/bin/env bash
set -euo pipefail

echo "[jarvis] Verifying local prerequisites"
command -v curl >/dev/null || { echo "curl is required"; exit 1; }
command -v ffmpeg >/dev/null || echo "[jarvis] ffmpeg not found yet"
command -v python3 >/dev/null || echo "[jarvis] python3 not found yet"
command -v pnpm >/dev/null || echo "[jarvis] pnpm not found yet"

OS_NAME="$(uname -s || echo unknown)"

if ! command -v ollama >/dev/null; then
  echo "[jarvis] Ollama not found, attempting installation"
  if [[ "$OS_NAME" == "Linux" ]]; then
    curl -fsSL https://ollama.com/install.sh | sh
  elif command -v winget.exe >/dev/null; then
    winget.exe install --id Ollama.Ollama -e || true
  else
    echo "[jarvis] Install Ollama manually before running Jarvis"
  fi
fi

echo "[jarvis] Preparing local directories"
mkdir -p data/chroma data/conversations data/logs models/piper bin/piper

if command -v poetry >/dev/null; then
  echo "[jarvis] Installing Python dependencies with poetry"
  poetry install
  echo "[jarvis] Installing runtime extras used by voice and provider integrations"
  poetry run python -m pip install python-multipart piper-tts
  echo "[jarvis] Installing Playwright browser"
  poetry run playwright install chromium
else
  echo "[jarvis] Poetry not found; install it or adapt to uv/pip before running backend"
fi

if command -v pnpm >/dev/null; then
  echo "[jarvis] Installing dashboard dependencies"
  (cd dashboard && pnpm install)
fi

echo "[jarvis] Pulling Ollama models"
bash scripts/install_models.sh || true

if command -v poetry >/dev/null; then
  echo "[jarvis] Downloading Piper voices into models/piper"
  poetry run python -m piper.download_voices pt_BR-faber-medium --data-dir models/piper || true
  poetry run python -m piper.download_voices en_US-ryan-high --data-dir models/piper || true
fi

echo "[jarvis] Configure these secrets in .env before first full use:"
echo "  NOTION_TOKEN"
echo "  SPOTIFY_CLIENT_ID / SPOTIFY_CLIENT_SECRET or PKCE redirect"
echo "  GOOGLE_CLIENT_SECRETS_FILE"
echo "  OUTLOOK_CLIENT_ID"

echo "[jarvis] Setup scaffold completed"

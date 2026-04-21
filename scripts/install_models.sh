#!/usr/bin/env bash
set -euo pipefail

command -v ollama >/dev/null || { echo "ollama is required"; exit 1; }

echo "[jarvis] Pulling local models"
ollama pull mistral-nemo:12b-instruct-2407-q4_K_M
ollama pull phi3:mini
ollama pull nomic-embed-text
echo "[jarvis] Ensure Piper voices exist under models/piper:"
echo "  pt_BR-faber-medium.onnx"
echo "  en_US-ryan-high.onnx"

echo "[jarvis] Model installation completed"

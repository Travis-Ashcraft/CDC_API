#!/usr/bin/env sh
set -e

export OLLAMA_HOST="http://127.0.0.1:11434"

# 1) Start Ollama in the background
ollama serve &

# 2) Wait for Ollama to respond on /ping
echo "Waiting for Ollama to come online…"
until curl --silent http://127.0.0.1:11434/ping >/dev/null 2>&1; do
  sleep 1
done
echo "✅ Ollama is now alive."

# 3) Pull the 0.6 B model (if not already cached)
ollama pull qwen3:0.6b || true

# 4) Launch FastAPI (Uvicorn)
exec python3 -m uvicorn main:app --host 0.0.0.0 --port "${PORT:-4000}"

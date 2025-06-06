#!/usr/bin/env sh
set -e

# 1) Force Ollama to bind only to loopback (127.0.0.1:11434)
export OLLAMA_HOST="http://127.0.0.1:11434"

# 2) Start the Ollama server in the background
ollama serve &

# 3) Wait a few seconds for Ollama to initialize
sleep 5

# 4) Pull the smallest Qwen 3 model (0.6 B parameters, ≈523 MB on disk).
#    If it’s already present in Ollama’s cache, this is a no-op.
ollama pull qwen3:0.6b || true

# 5) Launch Uvicorn (FastAPI) on Render’s assigned $PORT (or 4000 locally)
exec python3 -m uvicorn main:app --host 0.0.0.0 --port "${PORT:-4000}"

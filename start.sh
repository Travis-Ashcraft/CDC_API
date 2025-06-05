#!/usr/bin/env sh
set -e

# Start Ollama (defaults to port 11434)
ollama serve &

sleep 3

# Start FastAPI (bind to Render’s $PORT or fall back to 4000)
exec python3 -m uvicorn main:app --host 0.0.0.0 --port "${PORT:-4000}"

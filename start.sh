#!/usr/bin/env sh
set -e

# Force Ollama to bind only to loopback so Render (or Docker) doesn’t expose it publicly
export OLLAMA_HOST="http://127.0.0.1:11434"

# 1) Start the Ollama server in the background
ollama serve &

# 2) Give Ollama a few seconds to spin up
sleep 3

# 3) Pull the quantized 7 B model (llama2-7b-4bit).
#    If it’s already downloaded, this is a no-op.
ollama pull llama2:7b-4bit || true

# 4) Launch FastAPI (Uvicorn) on the Render‐assigned port (or 4000 locally)
exec python3 -m uvicorn main:app --host 0.0.0.0 --port "${PORT:-4000}"
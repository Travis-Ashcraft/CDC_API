#!/usr/bin/env sh
set -e

# 1) Force Ollama to bind to 127.0.0.1:11434 (loopback) via OLLAMA_HOST
export OLLAMA_HOST="http://127.0.0.1:11434"

# 2) Start Ollama in the background (it will now listen only on 127.0.0.1:11434)
ollama serve &

# 3) Give Ollama a moment to start up
sleep 3

# 4) Pull llama2 into Ollama’s cache (after the server is running)
#    If it’s already there, this will be a no-op.
ollama pull llama2 || true

# 5) Finally, launch Uvicorn (FastAPI) on the Render‐assigned port (or 4000 locally)
exec python3 -m uvicorn main:app --host 0.0.0.0 --port "${PORT:-4000}"

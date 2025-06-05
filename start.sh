#!/usr/bin/env sh
set -e

# 1) Start Ollama (listening on 11434 by default) in the background
ollama serve &

# 2) Give Ollama a moment to spin up
sleep 3

# 3) Launch Uvicorn (FastAPI) on the port assigned by Render, or 4000 locally
exec python3 -m uvicorn main:app --host 0.0.0.0 --port "${PORT:-4000}"

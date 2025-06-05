#!/usr/bin/env sh
set -e

# 1) Start Ollama on 127.0.0.1:11434 (INTERNAL only) in the background
ollama serve --host 127.0.0.1 &

# 2) Give Ollama a moment to spin up
sleep 3

# 3) Launch Uvicorn (FastAPI) on the Render‐assigned port (or 4000 locally)
exec python3 -m uvicorn main:app --host 0.0.0.0 --port "${PORT:-4000}"

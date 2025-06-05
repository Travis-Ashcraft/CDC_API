#!/usr/bin/env sh
set -e

# 1) Start Ollama on port 11434 in the background
ollama serve --port 11434 &

# 2) Give Ollama a moment to spin up
sleep 3

# 3) Run Uvicorn via python -m uvicorn so that --port is accepted
exec python3 -m uvicorn main:app --host 0.0.0.0 --port ${PORT:-4000}

#!/usr/bin/env sh
set -e

# 1) Pull llama2 if it isn't already pulled.
#    If the pull fails, we ignore the error and carry on (maybe it was already present).
ollama pull llama2 || true

# 2) Start Ollama in the background (it now has the model)
ollama serve &

# 3) Wait a few seconds for Ollama to spin up
sleep 3

# 4) Launch Uvicorn (FastAPI) on the Render-assigned port (or 4000 locally)
exec python3 -m uvicorn main:app --host 0.0.0.0 --port "${PORT:-4000}"

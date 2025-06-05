# main.py (chat-only, no Gradio/TTS)

import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

import httpx
from dotenv import load_dotenv

load_dotenv()  # load .env if you need other env vars later

app = FastAPI()

# Only allow requests from your known origins. Adjust or expand if needed.
origins = [
    "https://travis-ashcraft.github.io",
    "http://localhost:63343",
    "http://localhost:63342",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)

# 1) Health check
@app.get("/")
async def root():
    return "✅ CDC AI Proxy (Chat-only) is running."

# 2) Proxy chat requests directly to Ollama
@app.post("/api/chat")
async def proxy_chat(request: Request):
    body = await request.json()
    try:
        async with httpx.AsyncClient() as client:
            ollama_resp = await client.post(
                "http://localhost:11434/api/chat", json=body, timeout=60
            )
            return JSONResponse(
                content=ollama_resp.json(), status_code=ollama_resp.status_code
            )
    except Exception:
        raise HTTPException(status_code=500, detail="Proxy to Ollama failed.")

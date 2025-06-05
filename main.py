# main.py
import os
import base64
from io import BytesIO
from typing import Optional, Dict, Any

from fastapi import FastAPI, HTTPException, Request, Header
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import httpx
import databases
from aiosmtplib import SMTP
from email.message import EmailMessage
from gradio_client import Client as GradioClient
from dotenv import load_dotenv

load_dotenv()  # load .env

DATABASE_URL = os.getenv("DATABASE_URL")
ADMIN_KEY = os.getenv("ADMIN_KEY")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")
EMAIL_USERNAME = os.getenv("EMAIL_USERNAME")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

# 1) Async DB setup
database = databases.Database(DATABASE_URL)

app = FastAPI()
origins = [
    "https://travis-ashcraft.github.io",
    "http://localhost:63343",
    "http://localhost:63342",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "x-admin-key", "x-admin-token"],
)

# 2) Pydantic models
class StartSessionPayload(BaseModel):
    email: str
    persona: str

class ReportIssuePayload(BaseModel):
    email: str
    persona: str
    prompt: str
    response: str
    comment: Optional[str] = None

class SendTranscriptPayload(BaseModel):
    email: str
    persona: str
    transcript: str

class SaveTranscriptPayload(BaseModel):
    sessionId: int
    prompt: str
    response: str

# 3) Startup / shutdown connects to DB
@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

# 4) Helper: send an HTML email via Gmail SMTP
async def send_email(subject: str, html_content: str, to_email: str):
    if not EMAIL_USERNAME or not EMAIL_PASSWORD:
        raise RuntimeError("EMAIL_USERNAME / EMAIL_PASSWORD not set")
    message = EmailMessage()
    message["From"] = f"CDC AI Service <{EMAIL_USERNAME}>"
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(html_content, subtype="html")

    smtp = SMTP(hostname="smtp.gmail.com", port=587, start_tls=True)
    await smtp.connect()
    await smtp.login(EMAIL_USERNAME, EMAIL_PASSWORD)
    await smtp.send_message(message)
    await smtp.quit()

# 5) Health check
@app.get("/")
async def root():
    return "✅ CDC AI Proxy is running."

# 6) Test DB connectivity
@app.get("/api/test-db")
async def test_db():
    try:
        row = await database.fetch_one("SELECT NOW()")
        return {"message": "DB connected", "time": row["now"]}
    except Exception:
        raise HTTPException(status_code=500, detail="DB connection failed")

# 7) Create a new session
@app.post("/api/startSession")
async def start_session(payload: StartSessionPayload):
    email = payload.email.strip().lower()
    persona_name = payload.persona.strip()
    try:
        # Insert or update user
        user_q = """
        INSERT INTO users (email) 
        VALUES (:email)
        ON CONFLICT (email) DO UPDATE SET email = EXCLUDED.email
        RETURNING id
        """
        user_row = await database.fetch_one(user_q, values={"email": email})
        user_id = user_row["id"]

        # Insert or update persona
        persona_q = """
        INSERT INTO personas (name) 
        VALUES (:name)
        ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
        RETURNING id
        """
        persona_row = await database.fetch_one(persona_q, values={"name": persona_name})
        persona_id = persona_row["id"]

        # Create session
        session_q = """
        INSERT INTO sessions (user_id, persona_id) 
        VALUES (:uid, :pid)
        RETURNING id, created_at
        """
        sess = await database.fetch_one(
            session_q, values={"uid": user_id, "pid": persona_id}
        )
        session_id = sess["id"]
        session_created_at = sess["created_at"]

        # Increment interaction count
        await database.execute(
            "UPDATE personas SET interaction_count = interaction_count + 1 WHERE id = :pid",
            values={"pid": persona_id},
        )

        return {"sessionId": session_id, "sessionCreatedAt": session_created_at}
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to start session")

# 8) Proxy chat requests to Ollama
@app.post("/api/chat")
async def proxy_chat(request: Request):
    # Directly pull the raw JSON body; no Pydantic model needed
    body = await request.json()
    try:
        async with httpx.AsyncClient() as client:
            ollama_resp = await client.post("http://localhost:11434/api/chat", json=body, timeout=60)
            return JSONResponse(content=ollama_resp.json(), status_code=200)
    except Exception:
        raise HTTPException(status_code=500, detail="Proxy failed")

# 9) Report issue via email
@app.post("/api/reportIssue")
async def report_issue(payload: ReportIssuePayload):
    html = f"""
    <div style="font-family: sans-serif; padding: 1rem;">
      <h2 style="color: #D21F3C;">CDC AI Persona Report</h2>
      <p><strong>Persona:</strong> {payload.persona}</p>
      <p><strong>Submitted by:</strong> {payload.email}</p>
      <p><strong>User Prompt:</strong><br><code>{payload.prompt}</code></p>
      <p><strong>AI Response:</strong></p>
      <div style="border-left:4px solid #D21F3C; background:#f9f9f9; padding: .5rem;">
        <pre style="white-space: pre-wrap;">{payload.response}</pre>
      </div>
      <p><strong>Comments:</strong><br>{payload.comment or "None"}</p>
      <hr />
      <p style="font-size:.8rem; color:#666;">Sent at: {__import__('datetime').datetime.now()}</p>
    </div>
    """
    try:
        await send_email(
            subject=f"AI Issue Report – {payload.persona} – {payload.email}",
            html_content=html,
            to_email="Travis.ashcraft@tstc.edu",
        )
        return {"message": "Email sent successfully"}
    except Exception:
        raise HTTPException(status_code=500, detail="Email failed to send")

# 10) Send transcript via email
@app.post("/api/sendTranscript")
async def send_transcript(payload: SendTranscriptPayload):
    html = f"""
    <div style="font-family: sans-serif; padding: 1rem;">
      <h2 style="color: #D21F3C;">CDC AI Interaction Transcript</h2>
      <p><strong>Persona:</strong> {payload.persona}</p>
      <p><strong>Submitted by:</strong> {payload.email}</p>
      <hr />
      {payload.transcript}
      <hr />
      <p style="font-size:.8rem; color:#666;">Sent automatically by CDC AI</p>
    </div>
    """
    try:
        await send_email(
            subject=f"CDC AI Transcript – {payload.persona} – {payload.email}",
            html_content=html,
            to_email=payload.email,
        )
        return {"message": "Transcript sent successfully"}
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to send transcript")

# 11) Save a transcript to the database
@app.post("/api/saveTranscript")
async def save_transcript(payload: SaveTranscriptPayload):
    if not (payload.sessionId and payload.prompt and payload.response):
        raise HTTPException(status_code=400, detail="Missing required fields")
    try:
        q = """
        INSERT INTO transcripts (session_id, prompt, response)
        VALUES (:sid, :prompt, :response)
        RETURNING id
        """
        row = await database.fetch_one(
            q,
            values={
                "sid": payload.sessionId,
                "prompt": payload.prompt,
                "response": payload.response,
            },
        )
        return {"message": "Saved successfully.", "id": row["id"]}
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to save transcript")

# 12) Fetch transcripts by email
@app.get("/api/transcripts/by-email/{email}")
async def get_transcripts_by_email(email: str):
    q = """
    SELECT 
      t.prompt, 
      t.response, 
      t.timestamp, 
      p.name AS persona,
      s.created_at AS session_created_at
    FROM transcripts t
    JOIN sessions s ON t.session_id = s.id
    JOIN users u ON s.user_id = u.id
    JOIN personas p ON s.persona_id = p.id
    WHERE LOWER(u.email) = LOWER(:email)
    ORDER BY s.created_at DESC, t.timestamp ASC
    """
    try:
        rows = await database.fetch_all(q, values={"email": email.strip().lower()})
        grouped: Dict[str, Any] = {}
        for r in rows:
            key = f"{r['persona']}_{r['session_created_at'].strftime('%Y-%m-%dT%H-%M')}"
            grouped.setdefault(key, []).append(
                {
                    "prompt": r["prompt"],
                    "response": r["response"],
                    "timestamp": r["timestamp"].isoformat(),
                }
            )
        return {"transcripts": grouped}
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch transcripts")

# 13) Debug user lookup
@app.get("/api/debug/user/{email}")
async def debug_user(email: str):
    q = """
    SELECT u.id AS user_id, u.email, s.id AS session_id, p.name AS persona
    FROM users u
    LEFT JOIN sessions s ON s.user_id = u.id
    LEFT JOIN personas p ON s.persona_id = p.id
    WHERE u.email = :email
    """
    try:
        rows = await database.fetch_all(q, values={"email": email.strip().lower()})
        return {"data": rows}
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch user info")

# 14) Wipe user data (admin only)
@app.delete("/api/wipe-user/{email}")
async def wipe_user(email: str, x_admin_token: Optional[str] = Header(None)):
    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Unauthorized")
    try:
        user_row = await database.fetch_one(
            "SELECT id FROM users WHERE email = :email", values={"email": email.strip().lower()}
        )
        if not user_row:
            raise HTTPException(status_code=404, detail="User not found")
        uid = user_row["id"]
        await database.execute(
            """
            DELETE FROM transcripts
            WHERE session_id IN (
              SELECT id FROM sessions WHERE user_id = :uid
            )
            """,
            values={"uid": uid},
        )
        await database.execute("DELETE FROM sessions WHERE user_id = :uid", values={"uid": uid})
        await database.execute("DELETE FROM users WHERE id = :uid", values={"uid": uid})
        return {"message": f"✅ User data for {email} wiped successfully."}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to wipe user")

# 15) List all users (admin only)
@app.get("/api/admin/users")
async def admin_list_users(x_admin_key: Optional[str] = Header(None)):
    if x_admin_key != ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Unauthorized")
    try:
        rows = await database.fetch_all("SELECT id, email FROM users ORDER BY email ASC")
        return {"users": rows}
    except Exception:
        raise HTTPException(status_code=500, detail="Database error")

# 16) List all personas (admin only)
@app.get("/api/admin/personas")
async def admin_list_personas(x_admin_key: Optional[str] = Header(None)):
    if x_admin_key != ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Unauthorized")
    try:
        rows = await database.fetch_all(
            "SELECT id, name, interaction_count FROM personas ORDER BY interaction_count DESC"
        )
        return {"personas": rows}
    except Exception:
        raise HTTPException(status_code=500, detail="Database error")

# 17) TTS: call Gradio on localhost:7860
@app.get("/api/synthesize")
async def synthesize(text: Optional[str] = None):
    if not text:
        raise HTTPException(status_code=400, detail="Missing text")
    try:
        client = GradioClient("http://localhost:7860")
        estimated_tokens = max(100, int(len(text) * 3.5))
        normalized = min(estimated_tokens / 1200, 1)
        speed_factor = 0.91 + 0.09 * (normalized ** 0.6)

        result = client.predict(
            "/generate_audio",
            {
                "text_input": text,
                "audio_prompt_input": None,
                "max_new_tokens": estimated_tokens,
                "cfg_scale": 3.8,
                "temperature": 1.3,
                "top_p": 0.95,
                "cfg_filter_top_k": 30,
                "speed_factor": speed_factor,
            },
            api_name="/generate_audio",
        )

        file_data = result.get("data", [None])[0]
        if isinstance(file_data, str) and file_data.startswith("data:audio/wav;base64,"):
            b64 = file_data.split("data:audio/wav;base64,")[1]
            audio_bytes = base64.b64decode(b64)
            return StreamingResponse(BytesIO(audio_bytes), media_type="audio/wav")
        elif isinstance(file_data, dict) and file_data.get("url"):
            audio_url = file_data["url"]
            async with httpx.AsyncClient() as client_http:
                audio_resp = await client_http.get(audio_url, timeout=60)
                return StreamingResponse(audio_resp.aiter_bytes(), media_type="audio/wav")
        else:
            raise HTTPException(status_code=500, detail="TTS returned unexpected format")
    except Exception:
        raise HTTPException(status_code=500, detail="TTS failed")

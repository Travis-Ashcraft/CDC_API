# ─────────────────────────────────────────────────────────────
# 1) Base image: Ollama’s official image
# ─────────────────────────────────────────────────────────────
FROM ollama/ollama:latest

# 2) Install Python 3, pip, build tools, and dos2unix
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        bash \
        python3 \
        python3-pip \
        build-essential \
        ca-certificates \
        git \
        dos2unix && \
    rm -rf /var/lib/apt/lists/*

# 3) Set working directory
WORKDIR /app

# 4) Copy requirements.txt and install Python dependencies
COPY requirements.txt /app/
RUN pip3 install --no-cache-dir -r requirements.txt

# 5) Copy the rest of the app (including start.sh)
COPY . /app/

# 6) Normalize line endings and make start.sh executable
RUN dos2unix /app/start.sh && chmod +x /app/start.sh

# 7) Expose only FastAPI’s port (4000). Do NOT expose 11434.
EXPOSE 4000

# 8) Launch start.sh (which runs Ollama + Uvicorn)
ENTRYPOINT ["./start.sh"]

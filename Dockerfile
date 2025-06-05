# ─────────────────────────────────────────────────────────────
# 1) Use Ollama’s official image as base (Debian‐based)
# ─────────────────────────────────────────────────────────────
FROM ollama/ollama:latest

# 2) Install Python 3, pip, and build dependencies (plus dos2unix)
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

# 3) Create and set working directory
WORKDIR /app

# 4) Copy requirements and install Python dependencies
COPY requirements.txt /app/
RUN pip3 install --no-cache-dir -r requirements.txt

# 5) Copy the rest of your code (including start.sh)
COPY . /app/

# 6) Force Unix (LF) line endings and make start.sh executable
RUN dos2unix /app/start.sh && chmod +x /app/start.sh

# 7) Expose only the FastAPI port (container’s 4000)
EXPOSE 4000

# 8) Entrypoint: run our start.sh (launches Ollama on 127.0.0.1:11434, then FastAPI on $PORT)
ENTRYPOINT ["./start.sh"]

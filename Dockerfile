FROM ollama/ollama:latest

# 1) Install Python, pip, dos2unix, etc.
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

WORKDIR /app

# 2) Copy & install Python deps
COPY requirements.txt /app/
RUN pip3 install --no-cache-dir -r requirements.txt

# 3) Copy the app (including start.sh)
COPY . /app/

# 4) Force LF line endings & make start.sh executable
RUN dos2unix /app/start.sh && chmod +x /app/start.sh

# 5) Pull the llama2 model into Ollama’s cache
RUN ollama pull llama2

# 6) Expose only FastAPI’s port (4000)
EXPOSE 4000

# 7) Entrypoint runs start.sh (which starts Ollama + Uvicorn)
ENTRYPOINT ["./start.sh"]

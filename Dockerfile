FROM ollama/ollama:latest

# 1) Install Python 3, pip, build tools, dos2unix, etc.
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

# 2) Copy & install Python dependencies
COPY requirements.txt /app/
RUN pip3 install --no-cache-dir -r requirements.txt

# 3) Copy all application files (including our start.sh and main.py)
COPY . /app/

# 4) Normalize line endings for start.sh and make it executable
RUN dos2unix /app/start.sh && chmod +x /app/start.sh

# 5) Expose only FastAPI’s port (4000); Ollama’s 11434 remains bound to localhost
EXPOSE 4000

# 6) Entrypoint: run start.sh (which starts Ollama + pulls llama2:7b-4bit + starts Uvicorn)
ENTRYPOINT ["./start.sh"]

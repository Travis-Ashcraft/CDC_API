FROM ollama/ollama:latest

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

COPY requirements.txt /app/
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . /app/

# Normalize line endings and make start.sh executable
RUN dos2unix /app/start.sh && chmod +x /app/start.sh

# Expose only FastAPI’s port (4000)
EXPOSE 4000

# Run start.sh, which will (1) pull llama2 if needed, (2) start Ollama, (3) start Uvicorn
ENTRYPOINT ["./start.sh"]

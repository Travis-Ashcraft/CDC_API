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

# Force LF endings and chmod +x
RUN dos2unix /app/start.sh && chmod +x /app/start.sh

EXPOSE 11434 4000

ENTRYPOINT ["./start.sh"]

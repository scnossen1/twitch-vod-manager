FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
RUN pip install --no-cache-dir yt-dlp pyyaml

# Copy all scripts and configs
COPY twitch_downloader.py cleanup.py config.yaml run.sh ./
RUN chmod +x run.sh

ENTRYPOINT ["./run.sh"]
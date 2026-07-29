FROM python:3.11-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir faster-whisper yt-dlp

WORKDIR /app
COPY transcribe.py .

ENTRYPOINT ["python3", "transcribe.py"]

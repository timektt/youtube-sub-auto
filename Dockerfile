FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    ffmpeg \
    fonts-noto-thai \
    fonts-noto-unhinted \
    git \
    curl && \
    rm -rf /var/lib/apt/lists/*

COPY ./fonts/NotoSansThai-SemiBold.ttf /usr/share/fonts/truetype/NotoSansThai-SemiBold.ttf
RUN fc-cache -f -v

RUN pip install --no-cache-dir \
    git+https://github.com/openai/whisper.git \
    argostranslate \
    ffmpeg-python \
    yt-dlp

RUN python -m argostranslate.cli download en th

WORKDIR /app
COPY entrypoint.py .

RUN mkdir -p /app/input /app/output

ENTRYPOINT ["python", "entrypoint.py"]

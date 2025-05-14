FROM python:3.10-slim

# === [1] ติดตั้งเครื่องมือพื้นฐาน และ Font Engine ===
RUN apt-get update && apt-get install -y \
    ffmpeg \
    fontconfig \
    git \
    curl \
 && rm -rf /var/lib/apt/lists/*

# === [2] เพิ่มฟอนต์ไทย (โหลดมาวางในโฟลเดอร์ fonts/ ข้างนอก)
COPY fonts/NotoSansThai-SemiBold.ttf /usr/share/fonts/truetype/noto/

# === [3] Refresh font cache และตรวจสอบว่าฟอนต์มีจริง
RUN fc-cache -f -v && \
    fc-list | grep "Noto Sans Thai" || echo "❌ Thai font not found!"

# === [4] ติดตั้ง Python Libraries
RUN pip install --no-cache-dir \
    git+https://github.com/openai/whisper.git \
    argostranslate \
    ffmpeg-python \
    yt-dlp

# === [5] ดาวน์โหลดโมเดลแปล Argos ภาษาอังกฤษ -> ไทย
RUN python -m argostranslate.cli download en th

# === [6] กำหนด Directory และ Copy Scripts
WORKDIR /app
COPY entrypoint.py .

# === [7] สร้างโฟลเดอร์ input / output สำหรับ mount
RUN mkdir -p /app/input /app/output

ENTRYPOINT ["python", "entrypoint.py"]

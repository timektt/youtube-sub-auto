FROM python:3.10-slim

# === [1] ติดตั้งเครื่องมือพื้นฐาน และระบบฟอนต์ ===
RUN apt-get update && apt-get install -y \
    ffmpeg \
    fontconfig \
    git \
    curl \
    libmagic1 \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# === [2] คัดลอก requirements.txt แล้วติดตั้ง Python packages ===
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# === [3] เพิ่มฟอนต์ไทยที่รองรับวรรณยุกต์ได้ดี
COPY fonts/NotoSansThai-SemiBold.ttf /usr/share/fonts/truetype/noto/

# === [4] รีเฟรช font cache และเช็คว่าฟอนต์โหลดจริง
RUN fc-cache -f -v && \
    echo "🎯 ฟอนต์ทั้งหมด:" && fc-list | grep "Noto Sans Thai" || echo "❌ Thai font not found!"

# === [5] ดาวน์โหลดภาษา Argos EN → TH
RUN python -m argostranslate.cli download en th

# === [6] เตรียมสภาพแวดล้อมทำงาน
WORKDIR /app
COPY entrypoint.py .

# === [7] สร้างโฟลเดอร์สำหรับ mount input/output
RUN mkdir -p /app/input /app/output

ENTRYPOINT ["python", "entrypoint.py"]

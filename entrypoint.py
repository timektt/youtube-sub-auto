import os
import sys
import subprocess
import whisper
import argostranslate.package
import argostranslate.translate

INPUT_DIR = "input"
OUTPUT_DIR = "output"
FONT_NAME = "NotoSansThai-SemiBold"

os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# === [1] รับลิงก์ YouTube ===
if len(sys.argv) < 2:
    print("❌ กรุณาใส่ลิงก์ YouTube เป็น argument เช่น:   docker compose run --rm transcriber https://youtu.be/...")
    sys.exit(1)

YOUTUBE_URL = sys.argv[1]
print(f"📥 กำลังดาวน์โหลดวิดีโอจาก: {YOUTUBE_URL}")

# === [2] ดาวน์โหลดวิดีโอ ===
video_filename = "video_downloaded.mp4"
video_path = os.path.join(INPUT_DIR, video_filename)
subprocess.run(["yt-dlp", "-f", "mp4", YOUTUBE_URL, "-o", video_path], check=True)

# === [3] โหลด Whisper Model ===
model_size = os.getenv("WHISPER_MODEL", "base")
print(f"🧠 โหลด Whisper Model: {model_size}")
model = whisper.load_model(model_size)

# === [4] ถอดเสียง ===
print("🔊 ถอดเสียง...")
result = model.transcribe(video_path, fp16=False)

srt_path = os.path.join(INPUT_DIR, "video_downloaded.srt")
srt_th_path = os.path.join(INPUT_DIR, "video_downloaded_th.srt")
segments = result["segments"]

# === [5] โหลดแพ็กเกจ Argos EN→TH ===
def translate_to_thai(text: str) -> str:
    try:
        available_packages = argostranslate.package.get_available_packages()
        package_to_install = next((p for p in available_packages if p.from_code == "en" and p.to_code == "th"), None)
        if package_to_install:
            download_path = package_to_install.download()
            argostranslate.package.install_from_path(download_path)

        installed_languages = argostranslate.translate.get_installed_languages()
        from_lang = next((l for l in installed_languages if l.code == "en"), None)
        to_lang = next((l for l in installed_languages if l.code == "th"), None)
        if from_lang and to_lang:
            translation = from_lang.get_translation(to_lang)
            return translation.translate(text)
    except Exception as e:
        print(f"⚠️ แปลไม่สำเร็จ: {text} → {e}")
    return text

# === [6] สร้าง SRT ทั้งอังกฤษและไทย ===
def format_time(t):
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = int(t % 60)
    ms = int((t - int(t)) * 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

with open(srt_path, "w", encoding="utf-8") as f_en, open(srt_th_path, "w", encoding="utf-8") as f_th:
    for i, seg in enumerate(segments, 1):
        start = seg["start"]
        end = seg["end"]
        text_en = seg["text"].strip()
        text_th = translate_to_thai(text_en)

        f_en.write(f"{i}\n{format_time(start)} --> {format_time(end)}\n{text_en}\n\n")
        f_th.write(f"{i}\n{format_time(start)} --> {format_time(end)}\n{text_th}\n\n")

# === [7] สร้าง .ass แบบมี Style ไทยแท้ ===
def write_ass_with_style(srt_input_path, ass_output_path, font_name):
    with open(srt_input_path, 'r', encoding='utf-8') as f:
        srt_lines = f.readlines()

    with open(ass_output_path, 'w', encoding='utf-8') as f:
        # Header
        f.write("[Script Info]\n")
        f.write("Title: Auto Subtitle\n")
        f.write("ScriptType: v4.00+\n")
        f.write("PlayResX: 1280\n")
        f.write("PlayResY: 720\n\n")

        f.write("[V4+ Styles]\n")
        f.write("Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, "
                "Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
                "Alignment, MarginL, MarginR, MarginV, Encoding\n")
        f.write(f"Style: Default,{font_name},42,&H00FFFFFF,&H000000FF,&H00000000,&H64000000,"
                "0,0,0,0,100,100,0,0,1,2,1,2,30,30,20,1\n\n")

        f.write("[Events]\n")
        f.write("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")

        # Dialogue
        index = 0
        while index < len(srt_lines):
            if srt_lines[index].strip().isdigit():
                start_end = srt_lines[index + 1].strip().split(' --> ')
                start = start_end[0].replace(',', '.')
                end = start_end[1].replace(',', '.')
                text = srt_lines[index + 2].strip().replace('\n', '').replace('\r', '')
                f.write(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}\n")
                index += 4
            else:
                index += 1

ass_path = os.path.join(INPUT_DIR, "video_downloaded_th.ass")
print("📝 สร้าง .ass พร้อม Style ฟอนต์ไทย")
write_ass_with_style(srt_th_path, ass_path, FONT_NAME)

# === [8] ฝังซับไทยลงวิดีโอ ===
output_path = os.path.join(OUTPUT_DIR, "video_withsub.mp4")
print("🔥 ฝังซับลงวิดีโอ")
subprocess.run([
    "ffmpeg", "-y",
    "-i", video_path,
    "-vf", f"ass={ass_path}",
    "-c:a", "copy",
    output_path
], check=True)

print(f"\n✅ เสร็จแล้ว! วิดีโออยู่ที่: {output_path}")

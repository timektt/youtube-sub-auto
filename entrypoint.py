import os
import sys
import subprocess
import whisper
import argostranslate.package
import argostranslate.translate

# === [0] CONFIG ===
INPUT_DIR = os.getenv("INPUT_DIR", "input")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "output")
FONT_NAME = os.getenv("FONT_NAME", "NotoSansThai-SemiBold")
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")

os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# === [1] Get YouTube URL ===
if len(sys.argv) < 2:
    print("❌ Please provide a YouTube URL as an argument.")
    sys.exit(1)

YOUTUBE_URL = sys.argv[1]
print(f"📥 Downloading video from: {YOUTUBE_URL}")

# === [2] Download video ===
video_filename = "video_downloaded.mp4"
video_path = os.path.join(INPUT_DIR, video_filename)
subprocess.run(["yt-dlp", "-f", "mp4", YOUTUBE_URL, "-o", video_path], check=True)

# === [3] Load Whisper Model ===
print(f"🧠 Loading Whisper Model: {WHISPER_MODEL}")
model = whisper.load_model(WHISPER_MODEL)

# === [4] Transcribe audio ===
print("🔊 Transcribing audio...")
result = model.transcribe(video_path, fp16=False)
segments = result["segments"]

srt_path = os.path.join(INPUT_DIR, "video_downloaded.srt")
srt_th_path = os.path.join(INPUT_DIR, "video_downloaded_th.srt")

# === [5] Load Argos Translate (once) ===
from_lang = None
to_lang = None
translator = None

try:
    installed_languages = argostranslate.translate.get_installed_languages()
    from_lang = next((l for l in installed_languages if l.code == "en"), None)
    to_lang = next((l for l in installed_languages if l.code == "th"), None)

    if not from_lang or not to_lang:
        print("⬇️  Installing Argos EN→TH...")
        available_packages = argostranslate.package.get_available_packages()
        package = next((p for p in available_packages if p.from_code == "en" and p.to_code == "th"), None)
        if package:
            download_path = package.download()
            argostranslate.package.install_from_path(download_path)
            installed_languages = argostranslate.translate.get_installed_languages()
            from_lang = next((l for l in installed_languages if l.code == "en"), None)
            to_lang = next((l for l in installed_languages if l.code == "th"), None)

    if from_lang and to_lang:
        translator = from_lang.get_translation(to_lang)

except Exception as e:
    print(f"❌ Failed to load Argos Translate: {e}")
    translator = None

# === [5.2] Translate EN → TH ===
def translate_to_thai(text: str) -> str:
    if not translator:
        return text
    try:
        return translator.translate(text)
    except Exception as e:
        print(f"⚠️ Translation failed: {text} → {e}")
        return text

# === [6] Save SRT files ===
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

# === [7] Sync SRT timing using ffsubsync ===
synced_srt_path = os.path.join(INPUT_DIR, "synced_th.srt")
print("🕐 Syncing subtitle timing using ffsubsync...")
subprocess.run([
    "ffsubsync", video_path,
    "-i", srt_th_path,
    "-o", synced_srt_path,
    "--overwrite"
], check=True)

# === [8] Convert synced SRT to styled ASS ===
def write_ass_with_style(srt_input_path, ass_output_path, font_name):
    with open(srt_input_path, 'r', encoding='utf-8') as f:
        srt_lines = f.readlines()

    with open(ass_output_path, 'w', encoding='utf-8') as f:
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

        index = 0
        while index < len(srt_lines):
            if srt_lines[index].strip().isdigit():
                start_end = srt_lines[index + 1].strip().split(' --> ')
                start = start_end[0].replace(',', '.')
                end = start_end[1].replace(',', '.')
                text = srt_lines[index + 2].strip()
                f.write(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}\n")
                index += 4
            else:
                index += 1

ass_path = os.path.join(INPUT_DIR, "video_downloaded_th.ass")
print("📝 Generating styled ASS subtitle...")
write_ass_with_style(synced_srt_path, ass_path, FONT_NAME)

# === [9] Burn subtitle into video ===
output_path = os.path.join(OUTPUT_DIR, "video_withsub.mp4")
print("🔥 Embedding subtitle into video")
subprocess.run([
    "ffmpeg", "-y",
    "-i", video_path,
    "-vf", f"ass={ass_path}",
    "-c:a", "copy",
    output_path
], check=True)

if not os.path.exists(output_path):
    print("❌ Output video not created.")
    sys.exit(1)

print(f"\n✅ Done! Output video: {output_path}")

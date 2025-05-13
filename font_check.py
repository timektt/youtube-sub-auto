import subprocess
import matplotlib.font_manager as fm
import os

FONT_NAME = "FC Ekaluck Bold"  # 👈 เปลี่ยนตามชื่อจริงที่ทดสอบ

def is_font_available(font_name):
    font_list = fm.findSystemFonts(fontpaths=None, fontext='ttf')
    for path in font_list:
        try:
            if font_name.lower() in fm.FontProperties(fname=path).get_name().lower():
                return True
        except:
            continue
    return False

def test_font_render_preview(font_name):
    print("🧪 ทดสอบฟอนต์ด้วย drawtext...")
    test_cmd = [
        "ffmpeg", "-f", "lavfi", "-i", "color=s=1280x720:d=2",
        "-vf", f"drawtext=font='{font_name}':text='ขึ้น เขียน อธิบาย':fontsize=48",
        "-frames:v", "1", "temp/font_test.png"
    ]
    try:
        subprocess.run(test_cmd, check=True)
        print("✅ ฟอนต์ผ่าน: ดูผลที่ temp/font_test.png")
    except subprocess.CalledProcessError:
        print("❌ ทดสอบไม่ผ่าน: ฟอนต์อาจไม่รองรับไทยหรือ FFmpeg หาไม่เจอ")

if __name__ == "__main__":
    if not is_font_available(FONT_NAME):
        print(f"❌ ไม่พบฟอนต์ '{FONT_NAME}' ในระบบ Windows!")
    else:
        print(f"✅ พบฟอนต์ '{FONT_NAME}' ในระบบ ✔")
        os.makedirs("temp", exist_ok=True)
        test_font_render_preview(FONT_NAME)

# font_path_check.py
import os
from matplotlib import font_manager

fonts = font_manager.findSystemFonts(fontpaths=None, fontext='ttf')
for path in fonts:
    if "NotoSansThai" in path:
        print(path)

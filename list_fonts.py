import matplotlib.font_manager as fm

for font_path in fm.findSystemFonts(fontpaths=None, fontext='ttf'):
    try:
        name = fm.FontProperties(fname=font_path).get_name()
        print(name)
    except Exception:
        continue

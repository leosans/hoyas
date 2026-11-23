"""Bake the soft shadow behind each plant's name, so the page needs no SVG filter.

  python3 bake_shadows.py <renders dir> <out dir>

The artifact draws the shadow live with an SVG filter (#nu-shadow): the umbel's shape at 10%, blurred 62px, filled
with a colored grain. That filter is expensive to paint (a large blur plus feTurbulence on two full-size layers).
Here it is split into what it is made of:
- <plant>-shade.png: the umbel's shape, blurred (full strength; the page applies the 10%), covering the filter's
  region (150% of the umbel, centered). Small, because a blurred shape needs few pixels.
- grain.png: the filter's colored grain as a seamless 128px tile (@2x, 64 colors), the same for every plant, rendered by
  Chrome from the filter's own feTurbulence and color matrix.
The page fills a layer with the grain and masks it with the shade, which equals the filter's result.
The blur is baked for an umbel shown 1000px wide (its size on desktop).
"""
import glob, os, sys
from PIL import Image, ImageFilter
from playwright.sync_api import sync_playwright

raw, out = sys.argv[1:3]
os.makedirs(out, exist_ok=True)

S_CSS, BLUR_CSS, PX = 1000, 62, 256          # umbel size in CSS px, the filter's blur, umbel size in the mask
K = PX / S_CSS
REGION = int(PX * 1.5)                        # the filter region: x/y -25%, width/height 150%
SRC = "-three.webp"   # the umbel behind the name, as drawn by bake_renders.py
for f in sorted(glob.glob(os.path.join(raw, "*" + SRC))):
    a = Image.open(f).convert("RGBA").getchannel("A").resize((PX, PX), Image.LANCZOS)
    m = Image.new("L", (REGION, REGION), 0); m.paste(a, ((REGION - PX) // 2, (REGION - PX) // 2))
    m = m.filter(ImageFilter.GaussianBlur(BLUR_CSS * K))
    shade = Image.merge("LA", (Image.new("L", m.size, 0), m))
    shade.save(os.path.join(out, os.path.basename(f).replace(SRC, "-shade.png")), optimize=True)

GRAIN = """<!doctype html><html><body style="margin:0;background:transparent">
<svg width="128" height="128" style="display:block"><filter id="g" x="0" y="0" width="128" height="128" filterUnits="userSpaceOnUse" color-interpolation-filters="sRGB">
<feTurbulence type="fractalNoise" baseFrequency=".85" numOctaves="2" seed="4" stitchTiles="stitch"/>
<feColorMatrix type="matrix" values="1.1 0 0 0 -.3  0 1.1 0 0 -.3  0 0 1.1 0 -.3  0 0 0 2.2 -.4"/>
</filter><rect width="128" height="128" filter="url(#g)"/></svg></body></html>"""
with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path="/usr/bin/google-chrome")
    pg = b.new_page(viewport={"width": 128, "height": 128}, device_scale_factor=2)
    pg.set_content(GRAIN)
    pg.screenshot(path=os.path.join(out, "grain.png"), omit_background=True, clip={"x": 0, "y": 0, "width": 128, "height": 128})
    b.close()
import shutil, subprocess
if shutil.which("pngquant"):   # noise doesn't compress; 64 colors of it look the same
    g = os.path.join(out, "grain.png"); subprocess.run(["pngquant", "64", "--speed", "1", "--strip", "--force", "--output", g, g], check=True)
print("shades:", len(glob.glob(os.path.join(out, "*-shade.png"))))

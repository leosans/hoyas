#!/usr/bin/env python3
"""Trace the site's SF Symbols into inline SVG, for the deployed site.

In the artifact every icon is an SF Symbol written as its own character (ICON_SET in template.html, between
/*ICON-SET:BEGIN*/ and /*ICON-SET:END*/), drawn with the SF Pro font. The live site can't count on that font, so this
script reads each symbol from SF Pro (Regular weight, medium scale: the font's default) and writes:
  - ICON_DATA between /*ICON-DATA:BEGIN*/ and /*ICON-DATA:END*/: {key: [width in em, path]}, 1em tall, the text
    baseline where the font has it, so sf() draws SVG that sits and scales like the glyph;
  - every static icon in the markup, <span class="sf ..." data-icon="key" aria-hidden="true">char</span>, as that SVG.

Usage: python3 trace_icons.py page.html SF-Pro.ttf      (rewrites page.html; running it twice changes nothing)
Needs fontTools (pip install fonttools).
"""
import json, re, sys
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

BASE = 1752   # y of the 1em box's top, in font units (2048 per em)

def num(m):
    v = round(float(m.group(0)), 1)
    return str(int(v)) if v == int(v) else str(v)

def trace(font, cp):
    gs, cmap = font.getGlyphSet(), font.getBestCmap()
    g = cmap.get(cp)
    if g is None: sys.exit(f"U+{cp:X} isn't in this SF Pro (is it newer than the font?)")
    pen = SVGPathPen(gs); gs[g].draw(TransformPen(pen, (1, 0, 0, -1, 0, BASE)))
    return round(gs[g].width / 2048, 4), re.sub(r"-?\d+(?:\.\d+)?", num, pen.getCommands())

def svg(key, cls, w, d):
    """The same markup the page's svgIcon() writes."""
    return (f'<svg class="{cls}" data-icon="{key}" viewBox="0 0 {round(w * 2048)} 2048" width="{w}em" height="1em" '
            f'fill="currentColor" aria-hidden="true" focusable="false"><path d="{d}"/></svg>')

def main(page, fontpath):
    t = open(page, encoding="utf-8").read()
    m = re.search(r"/\*ICON-SET:BEGIN\*/const ICON_SET = (.*?);/\*ICON-SET:END\*/", t, re.S)
    if not m: sys.exit("ICON_SET markers not found")
    icon_set, font = json.loads(m.group(1)), TTFont(fontpath)
    data = {}
    for k, v in icon_set.items():
        ch = v["char"]
        if len(ch) != 1: sys.exit(f"{k}: char should be one symbol, got {ch!r}")
        data[k] = trace(font, ord(ch))
    blob = json.dumps({k: [w, d] for k, (w, d) in data.items()}, separators=(",", ":"))
    t, n = re.subn(r"/\*ICON-DATA:BEGIN\*/.*?/\*ICON-DATA:END\*/", lambda _: f"/*ICON-DATA:BEGIN*/const ICON_DATA = {blob};/*ICON-DATA:END*/", t, flags=re.S)
    if n != 1: sys.exit("ICON_DATA markers not found")
    def static(mm):
        cls, key = mm.group(1), mm.group(2)
        if key not in data: sys.exit(f"static icon {key!r} isn't in ICON_SET")
        return svg(key, cls, *data[key])
    t, s = re.subn(r'<span class="(sf(?: [^"]*)?)" data-icon="([\w-]+)" aria-hidden="true">[^<]*</span>', static, t)
    open(page, "w", encoding="utf-8").write(t)
    print(f"traced {len(data)} symbols, {s} static icons")

if __name__ == "__main__":
    if len(sys.argv) != 3: sys.exit(__doc__)
    main(*sys.argv[1:])

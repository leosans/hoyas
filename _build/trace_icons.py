#!/usr/bin/env python3
"""Trace the page's SF Symbols into inline SVG.

usage: python3 _build/trace_icons.py <SF-Pro-Text-Regular.otf> <in.html> <out.html>

Fills /*ICON-DATA:BEGIN*/ ... /*ICON-DATA:END*/ with {key: [width_em, path]} and turns
static <span class="sf ..." data-icon="k" aria-hidden="true">CHAR</span> markup into the
same <svg> that svgIcon() writes. The SVG box is 1em tall with its bottom .1445em below
the baseline (CSS .sf vertical-align), so y' = 1752 - y at 2048 units per em.
"""
import json, re, sys
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

font_path, src, dst = sys.argv[1:4]
html = open(src, encoding="utf-8").read()

m = re.search(r"/\*ICON-SET:BEGIN\*/const ICON_SET = (\{.*?\});/\*ICON-SET:END\*/", html, re.S)
icon_set = json.loads(m.group(1))

font = TTFont(font_path)
upm = font["head"].unitsPerEm
cmap = font.getBestCmap()
gs = font.getGlyphSet()
hmtx = font["hmtx"]
s = 2048 / upm
base = round(2048 * (1 - .1445))  # 1752

def fmt(v):
    v = round(v, 1)
    return str(int(v)) if v == int(v) else str(v)

data = {}
for key, v in icon_set.items():
    cp = ord(v["char"]) if len(v["char"]) == 1 else None
    if cp is None:
        raise SystemExit(f"{key}: not a single codepoint")
    gname = cmap.get(cp)
    if not gname:
        raise SystemExit(f"{key} ({v['symbol']}, U+{cp:X}) is not in {font_path}")
    pen = SVGPathPen(gs, ntos=fmt)
    gs[gname].draw(TransformPen(pen, (s, 0, 0, -s, 0, base)))
    adv = hmtx[gname][0] * s
    data[key] = [round(adv / 2048, 4), pen.getCommands()]

html = re.sub(r"/\*ICON-DATA:BEGIN\*/.*?/\*ICON-DATA:END\*/",
              lambda _: "/*ICON-DATA:BEGIN*/const ICON_DATA = " + json.dumps(data, separators=(",", ":")) + ";/*ICON-DATA:END*/",
              html, flags=re.S)

def svg(m):
    cls, k = m.group(1), m.group(2)
    w, d = data[k]
    return (f'<svg class="{cls}" data-icon="{k}" viewBox="0 0 {round(w*2048)} 2048" width="{w}em" height="1em" '
            f'fill="currentColor" aria-hidden="true" focusable="false"><path d="{d}"/></svg>')

html, n = re.subn(r'<span class="(sf[^"]*)" data-icon="([^"]+)" aria-hidden="true">[^<]*</span>', svg, html)
open(dst, "w", encoding="utf-8").write(html)
print(f"traced {len(data)} icons, {n} static")

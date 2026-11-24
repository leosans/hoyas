"""Turn the Hoya Collection artifact's index.html into the lighter published page.

  python3 build.py <artifact index.html> <saved designs .json> <out index.html> <renders dir>

The artifact already shows pictures rather than live 3D. For the published site this:
- reads every picture from renders/ (drawn by bake_renders.py from the saved designs), never from the artifact's
  own storage (/_blob/...), which GitHub Pages can't reach; the address carries a version made from the pictures
  themselves, so a browser's stored copy is never mistaken for a changed picture;
- removes the flower builder, the 3D renderer, the flat fallback drawing, the reference-photo list and the database;
- draws the shadow behind the name from a baked shade per plant plus a shared grain (bake_shadows.py), in place of
  the expensive #nu-shadow SVG filter;
- writes the saved designs and the soil drawing into the page, and works out each plant's design (and accent) once.
Every cut checks its markers, so a changed artifact fails loudly instead of building a broken page.
"""
import re, glob, hashlib, json, os, sys

src, designs, dst, renders = sys.argv[1:5]
h = open(src, encoding="utf-8").read()

def cut(start, end, repl="", keep_end=True):
    global h
    i = h.find(start); assert i >= 0, f"start marker not found: {start[:60]!r}"
    j = h.find(end, i); assert j >= 0, f"end marker not found: {end[:60]!r}"
    h = h[:i] + repl + (h[j:] if keep_end else h[j + len(end):])

def sub(old, new, count=1):
    global h
    n = h.count(old); assert n == count, f"expected {count}x, found {n}x: {old[:70]!r}"
    h = h.replace(old, new)

def drop_line(marker):
    global h
    i = h.find(marker); assert i >= 0, f"line not found: {marker[:60]!r}"
    h = h[:h.rfind("\n", 0, i) + 1] + h[h.find("\n", i) + 1:]

# the pictures' version: a short fingerprint of every picture in renders/
fp = hashlib.sha256()
for f in sorted(glob.glob(os.path.join(renders, "*"))):
    fp.update(os.path.basename(f).encode()); fp.update(open(f, "rb").read())
V = fp.hexdigest()[:8]

# 1. the 3D renderer, the flat fallback drawing, the builder and the database
cut("const F3D = (() => {", "flowerOnly};\n})();\n", keep_end=False)
cut("/* Even spacing over the dome", "/* umbels are shown as 3D stills.")
# the segmented-control thumb (stretchThumb, slideSeg, moveSegThumb) sits in the builder's code but the home page uses it
seg_i = h.find("/* a segmented control's thumb stretches"); seg_j = h.find("function renderBuilder(p){", seg_i)
assert 0 <= seg_i < seg_j, "segmented-control code not found"
seg_code = h[seg_i:seg_j]
cut("/* ---------- flower builder (#build, #build-<plant>) ---------- */", "/* routing */", seg_code)
drop_line("const PHOTOS = ")
# placeholders that the renderer used to fill in are never made now
cut("let hydrateRun = 0;\nfunction hydrateUmbels(){", "  requestAnimationFrame(step);\n}\n", "function hydrateUmbels(){}\n", keep_end=False)
# a picture that can't load is simply left out (the flat drawing that stood in needed the renderer)
sub('  if(p && el.classList.contains("art") && el.dataset.kind !== "flower" && el.dataset.kind !== "leaf") el.outerHTML = drawSpec(specOf(p), p.name, el.getAttribute("alt") || "", false);\n  else el.remove();',
    '  el.remove();')

# 2. every picture from renders/, versioned by the pictures themselves
sub('  if(o && o.images){ const id = o.images[kind] || (kind === "thumb" && o.images.front); if(id) return "/_blob/" + id; }\n', "")
# the artifact's own version numbers change from time to time, so match any
def resub(pat, new):
    global h
    h, n = re.subn(pat, lambda _: new, h); assert n == 1, f"expected 1x, found {n}x: {pat!r}"
resub(r"RENDERS_V = \d+,", f'RENDERS_V = "{V}",')
resub(r'\("renders/" \+ id \+ "-" \+ k \+ "\.webp\?v=\d+"\)', f'("renders/" + id + "-" + k + ".webp?v={V}")')

# 3. the shadow behind the name: the shared grain masked by the plant's baked shade, at the filter's 10%, over the
#    filter's region (150%, centered); it fades in with the umbel. The SVG filter goes.
sub('if(view === "three") return picImg(p, "three", "nu-sh nu-mul", "", true) + picImg(p, "three", "nu-sh nu-ovl", "", true) + picImg(p, "three", "art art3d", label);',
    'if(view === "three"){ const sh = k => `<i class="nu-sh ${k}" aria-hidden="true"><b style="--m:url(renders/${slug(p.name)}-shade.png?v=' + V + ')"></b></i>`;\n'
    '    return sh("nu-mul") + sh("nu-ovl") + picImg(p, "three", "art art3d", label); }')
sub("filter:url(#nu-shadow); -webkit-filter:url(#nu-shadow); ", "")
sub(".nu-mul{mix-blend-mode:multiply}",
    ".nu-sh{opacity:0; transition:opacity .25s var(--ease)}\n"
    ".name-umbel:has(img.art.on) .nu-sh{opacity:1}\n"
    f".nu-sh b{{position:absolute; inset:-25%; opacity:.1; background:url(renders/grain.png?v={V}) 0 0/128px 128px;"
    " -webkit-mask:var(--m) center/100% 100% no-repeat; mask:var(--m) center/100% 100% no-repeat}\n"
    ".nu-mul{mix-blend-mode:multiply}")
cut("<!-- the umbel shadow behind the hoya name", "</filter></svg>\n", keep_end=False)
assert "#nu-shadow" not in h

# 3b. no design system page: its styles, header button, code and route go; #design opens the home page
cut("/* ===== design system page (#design) ===== */", "</style>")
drop_line('id="design-link"')
cut("/* ---------- design system (#design)", "function route(instant){")
sub('    if(id === "design"){ B.plant = null; view.innerHTML = renderDesign(); bindDesign(); document.title = "Design system · Hoya Collection"; }\n    else if(id === "build"',
    '    if(id === "build"')
sub('id === "design" ? "design" : (id', '(id')
for gone in ("renderDesign", "bindDesign", "dsValues", 'href="#design"', "design-link"):
    assert gone not in h, f"design system still referenced: {gone}"

# 4. routing: no builder page; old builder links open the plant (or the home page)
sub('    if(id === "build" || id.startsWith("build-")){ const bp = builderPlant(id); view.innerHTML = renderBuilder(bp); bindBuilder(bp); document.title = "Flower builder · " + bp.name; }\n    else if(p){ B.plant = null; ',
    '    if(p){ ')
sub('    else { B.plant = null; ', '    else { ')
sub('  const id = location.hash.slice(1), p = DATA.find(x => slug(x.name) === id);',
    '  if(/^#build/.test(location.hash)){ history.replaceState(null, "", "#" + location.hash.slice(1).replace(/^build-?/, "")); }\n'
    '  const id = location.hash.slice(1), p = DATA.find(x => slug(x.name) === id);')
drop_line('document.getElementById("builder-link")')
drop_line('id="builder-link"')

# 5. saved designs written into the page (without the artifact's picture ids), and each plant worked out once
ov = {d["plant"]: {k: v for k, v in d.items() if k != "images"} for d in json.load(open(designs, encoding="utf-8"))}
sub("let OVERRIDES = {};", "let OVERRIDES = " + json.dumps(ov, separators=(",", ":"), ensure_ascii=False) + ";")
sub("function specOf(p){ const sp = savedSpec(p); if(!sp.accentManual) sp.accent = autoAccent(sp, COLORS[p.name]); return sp; }",
    "const SPEC_MEMO = new Map();\n"
    "function specOf(p){ let sp = SPEC_MEMO.get(p.name); if(!sp){ sp = savedSpec(p); if(!sp.accentManual) sp.accent = autoAccent(sp, COLORS[p.name]); SPEC_MEMO.set(p.name, sp); } return Object.assign({}, sp); }")

for gone in ("F3D.stillOf", "renderBuilder", "bindBuilder", "drawSpec(", "B.plant", "builder-link", "return \"/_blob/\""):
    assert gone not in h.replace("F3D.stillOf(sp, name", ""), f"still referenced: {gone}"
open(dst, "w", encoding="utf-8").write(h)

# 6. the soil drawing: the same for every plant (a fixed seed) but slow to place grain by grain, so it is drawn once
#    here and written into the page
import functools, http.server, threading
from playwright.sync_api import sync_playwright
Hd = functools.partial(http.server.SimpleHTTPRequestHandler, directory=os.path.dirname(os.path.abspath(dst))); Hd.log_message = lambda *a: None
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Hd); threading.Thread(target=srv.serve_forever, daemon=True).start()
with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path="/usr/bin/google-chrome"); pg = b.new_page()
    pg.goto(f"http://127.0.0.1:{srv.server_port}/{os.path.basename(dst)}#"); pg.wait_for_function("typeof soilPot === 'function'")
    soil = pg.evaluate("() => { SOIL_SVG = ''; return soilPot(); }"); b.close()
srv.shutdown()
assert soil.startswith("<svg"), "soil drawing failed"
sub('let SOIL_SVG = "";', "let SOIL_SVG = " + json.dumps(soil, ensure_ascii=False) + ";")
open(dst, "w", encoding="utf-8").write(h)
print(f"{len(open(src, encoding='utf-8').read())//1024} KB -> {len(h)//1024} KB, pictures v{V}")

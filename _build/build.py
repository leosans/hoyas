"""Turn the Hoya Collection artifact's index.html into the lighter published page.

  python3 build.py <artifact index.html> <saved designs .json list> <out index.html>

What changes:
- the flower builder, the 3D (WebGL) renderer, the flat SVG fallback, the reference-photo list and the
  database code are removed;
- every umbel, flower and leaf picture is a prebaked PNG in stills/ (see bake.py), shown with the same
  classes, so size and placement are unchanged;
- the saved designs are written into the page, so colors and placements need no extra request.
Every cut checks that its markers exist, so a changed artifact fails loudly instead of building a broken page.
"""
import json, sys

src, designs, dst = sys.argv[1:4]
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

# 1. the 3D renderer
cut("const F3D = (() => {", "flowerOnly};\n})();\n", keep_end=False)

# 2. the flat SVG fallback (even spacing, flower turn, drawSpec): only used when WebGL is missing, and by the builder
cut("/* Even spacing over the dome", "/* umbels are shown as 3D stills.")

# 3. umbels: prebaked PNGs in place of placeholders that were filled in by the renderer
UMBEL = r'''/* umbels are prebaked PNG stills (stills/<plant>-front.png, -hero.png), drawn from the saved designs */
const stillImg = (cls, src, px, label, lazy) => `<img class="${cls}" src="${src}" width="${px}" height="${px}" ${label === null ? 'alt="" aria-hidden="true"' : `alt="${esc(label)}"`} decoding="async"${lazy ? ' loading="lazy"' : ' fetchpriority="high"'} onload="this.classList.add('art-in')">`;
function umbel(p, view){
  const label = "Umbel of flowers in the colors of " + p.name, s = "stills/" + slug(p.name);
  if(view === "three"){
    /* behind the name, the umbel casts two identical soft shadows: the first multiplies, the second overlays it.
       Each is the shared grain masked by the umbel's baked, blurred shape (see bake_shadows.py); all three fade in
       together once the umbel has loaded */
    const sh = k => `<i class="nu-sh ${k}" aria-hidden="true"><b style="--m:url(${s}-shade.png)"></b></i>`;
    return sh("nu-mul") + sh("nu-ovl") + `<img class="art art3d" src="${s}-hero.png" width="1400" height="1400" alt="${esc(label)}" decoding="async" fetchpriority="high" onload="this.parentNode.querySelectorAll('.nu-sh,.art').forEach(e=>e.classList.add('art-in'))">`;
  }
  return stillImg("art art3d", s + "-front.png", 720, label, true);
}
function hydrateUmbels(){}
'''
cut("/* umbels are shown as 3D stills.", "  requestAnimationFrame(step);\n}\n", UMBEL, keep_end=False)   # through the end of hydrateUmbels

# 4. the reference photos (builder only)
i = h.find("const PHOTOS = "); assert i >= 0, "PHOTOS not found"
h = h[:i] + h[h.find("\n", i) + 1:]

# 5. the builder and the database
cut("/* ---------- flower builder (#build, #build-<plant>) ---------- */", "/* routing */")

# 6. Bloom and Leaves tiles: prebaked PNGs
cut("function mountBloom(p){", "function route(instant){", r'''function mountBloom(p){
  const slot = document.getElementById("bloom-3d"); if(!slot) return;
  slot.insertAdjacentHTML("beforeend", stillImg("bloom-canvas", "stills/" + slug(p.name) + "-bloom.png", 520, null, true));
}
/* the leaves: a length of stem with its leaves, a still picture */
function mountLeaves(p){
  const slot = document.getElementById("leaf-pair"); if(!slot) return;
  slot.insertAdjacentHTML("beforeend", stillImg("bloom-canvas", "stills/" + slug(p.name) + "-leaf.png", 760, null, true));
}
''')

# 7. routing: no builder page; old builder links open the plant (or the home page)
sub('''    if(id === "build" || id.startsWith("build-")){ const bp = builderPlant(id); view.innerHTML = renderBuilder(bp); bindBuilder(bp); document.title = "Flower builder · " + bp.name; }
    else if(p){ B.plant = null; ''', '''    if(p){ ''')
sub('''    else { B.plant = null; view.innerHTML = renderHome();''', '''    else { view.innerHTML = renderHome();''')
sub('''  const id = location.hash.slice(1), p = DATA.find(x => slug(x.name) === id);''',
    '''  if(/^#build/.test(location.hash)){ history.replaceState(null, "", "#" + location.hash.slice(1).replace(/^build-?/, "")); }
  const id = location.hash.slice(1), p = DATA.find(x => slug(x.name) === id);''')
i = h.find('document.getElementById("builder-link")'); assert i >= 0
h = h[:h.rfind("\n", 0, i) + 1] + h[h.find("\n", i) + 1:]
sub("fitType(); moveSegThumb(true); }", "fitType(); }")
i = h.find('id="builder-link"'); assert i >= 0
h = h[:h.rfind("\n", 0, i) + 1] + h[h.find("\n", i) + 1:]

# 8. styles: pictures are images now
sub("canvas.art3d{display:block}", ".art3d{display:block}")
# the name's shadow: the grain masked by the baked shade, at the filter's 10%, over the filter's region (150%, centered),
# hidden until it fades in with the umbel. The SVG filter itself goes.
sub("filter:url(#nu-shadow); -webkit-filter:url(#nu-shadow); ", "")
sub(".nu-mul{mix-blend-mode:multiply}", ".nu-sh:not(.art-in){visibility:hidden}\n"
    ".nu-sh b{position:absolute; inset:-25%; opacity:.1; background:url(stills/grain.png) 0 0/128px 128px;"
    " -webkit-mask:var(--m) center/100% 100% no-repeat; mask:var(--m) center/100% 100% no-repeat}\n"
    ".nu-mul{mix-blend-mode:multiply}")
cut("<!-- the umbel shadow behind the hoya name", "</filter></svg>\n", keep_end=False)
assert "#nu-shadow" not in h

# 8b. a plant's design (and its accent color) is worked out once: the designs never change on this page
sub("function specOf(p){ const sp = savedSpec(p); if(!sp.accentManual) sp.accent = autoAccent(sp, COLORS[p.name]); return sp; }",
    "const SPEC_MEMO = new Map();\n"
    "function specOf(p){ let sp = SPEC_MEMO.get(p.name); if(!sp){ sp = savedSpec(p); if(!sp.accentManual) sp.accent = autoAccent(sp, COLORS[p.name]); SPEC_MEMO.set(p.name, sp); } return Object.assign({}, sp); }")

# 9. saved designs, written into the page
ov = {d["plant"]: d for d in json.load(open(designs, encoding="utf-8"))}
sub("let OVERRIDES = {};", "let OVERRIDES = " + json.dumps(ov, separators=(",", ":"), ensure_ascii=False) + ";")

# nothing left that needs the removed parts
for gone in ("F3D.", "renderBuilder", "bindBuilder", "window.claude", "drawSpec(", "PHOTOS", "B.plant", "builder-link"):
    assert gone not in h, f"still referenced: {gone}"

open(dst, "w", encoding="utf-8").write(h)

# 10. the soil drawing: the same for every plant (a fixed seed), but slow to place grain by grain, so it is drawn once
# here and written into the page
import functools, http.server, os, threading
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
print(f"{len(open(src, encoding='utf-8').read())//1024} KB -> {len(h)//1024} KB")

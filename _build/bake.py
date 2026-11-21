"""Render every plant's stills with the page's own WebGL renderer and save them as PNGs.

Usage: python3 bake.py <artifact index.html> <saved designs .json> <out_dir> [max plants]
The artifact page is served from a scratch folder next to its fonts; the saved designs are set straight
into the page, so the artifact's own file works unchanged.
"""
import base64, functools, http.server, json, os, sys, threading
from playwright.sync_api import sync_playwright

import shutil, tempfile
src, designs, out = sys.argv[1:4]
limit = int(sys.argv[4]) if len(sys.argv) > 4 else None
os.makedirs(out, exist_ok=True)
site = tempfile.mkdtemp()
shutil.copy(src, os.path.join(site, "index.html"))
fonts = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "fonts")
if os.path.isdir(fonts): shutil.copytree(fonts, os.path.join(site, "fonts"))
saved = {d["plant"]: d for d in json.load(open(designs, encoding="utf-8"))}

Handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=site)
Handler.log_message = lambda *a: None
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 8765), Handler)
threading.Thread(target=srv.serve_forever, daemon=True).start()

JS_LIST = "() => DATA.map(p => ({name: p.name, slug: slug(p.name)}))"
JS_ONE = """async (name) => {
  const p = DATA.find(x => x.name === name), sp = specOf(p);
  const png = c => c ? c.toDataURL("image/png") : null;
  F3D.stillOf(sp, p.name, "front");   /* warm-up: first draw of a renderer can come out before its programs settle */
  return {
    front: png(F3D.stillOf(sp, p.name, "front")),
    hero:  png(F3D.stillOf(sp, p.name, "three")),
    bloom: png(F3D.flowerStill(sp)),
    leaf:  png(F3D.leafStill(sp, true)),
  };
}"""

with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path="/usr/bin/google-chrome", headless=True,
                           args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
    page = b.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto("http://127.0.0.1:8765/index.html")
    page.wait_for_function("typeof DATA === 'object' && typeof F3D === 'object'", timeout=30000)
    page.evaluate("o => { OVERRIDES = o; }", saved)
    plants = page.evaluate(JS_LIST)[:limit]
    manifest = {}
    for i, p in enumerate(plants):
        r = page.evaluate(JS_ONE, p["name"])
        manifest[p["name"]] = {}
        for kind, url in r.items():
            if not url:
                manifest[p["name"]][kind] = None
                continue
            fn = f"{p['slug']}-{kind}.png"
            with open(os.path.join(out, fn), "wb") as f:
                f.write(base64.b64decode(url.split(",", 1)[1]))
            manifest[p["name"]][kind] = fn
        print(f"{i+1}/{len(plants)} {p['name']}", flush=True)
    json.dump(manifest, open(os.path.join(out, "manifest.json"), "w"), indent=1)
    print("page errors:", errors)
    b.close()
srv.shutdown()

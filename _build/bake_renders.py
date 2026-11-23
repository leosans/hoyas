"""Render every plant's pictures the way the artifact does, for the published site.

  python3 bake_renders.py <artifact index.html> <saved designs .json> <out dir> [max plants]

The artifact shows pictures, not live 3D: plants without a saved design use the bundled renders/<slug>-<kind>.webp,
and plants with one use pictures uploaded to the artifact's own storage (/_blob/<id>), which the published site can't
reach. So this draws all five kinds for every plant with the artifact's own drawPictures(), from the saved designs,
and the published page reads every picture from renders/. Kinds: front, three (behind the name), flower, leaf, thumb.
"""
import base64, functools, http.server, json, os, shutil, sys, tempfile, threading
from playwright.sync_api import sync_playwright

src, designs, out = sys.argv[1:4]
limit = int(sys.argv[4]) if len(sys.argv) > 4 else None
os.makedirs(out, exist_ok=True)
site = tempfile.mkdtemp()
shutil.copy(src, os.path.join(site, "index.html"))
fonts = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "fonts")
if os.path.isdir(fonts): shutil.copytree(fonts, os.path.join(site, "fonts"))
saved = {d["plant"]: {k: v for k, v in d.items() if k != "images"} for d in json.load(open(designs, encoding="utf-8"))}

H = functools.partial(http.server.SimpleHTTPRequestHandler, directory=site); H.log_message = lambda *a: None
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H); threading.Thread(target=srv.serve_forever, daemon=True).start()

JS_ONE = """async (name) => {
  const p = DATA.find(x => x.name === name), sp = savedSpec(p);
  const blobs = await drawPictures(p.name, sp), out = {};
  for (const k of PIC_KINDS) out[k] = await new Promise(r => { const f = new FileReader(); f.onload = () => r(f.result); f.readAsDataURL(blobs[k]); });
  return out;
}"""
with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path="/usr/bin/google-chrome", headless=True,
                           args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
    page = b.new_page(); errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(f"http://127.0.0.1:{srv.server_port}/index.html")
    page.wait_for_function("typeof DATA === 'object' && typeof drawPictures === 'function'", timeout=30000)
    page.evaluate("o => { OVERRIDES = o; }", saved)
    plants = page.evaluate("() => DATA.map(p => ({name: p.name, slug: slug(p.name)}))")[:limit]
    for i, p in enumerate(plants):
        r = page.evaluate(JS_ONE, p["name"])
        for kind, url in r.items():
            with open(os.path.join(out, f"{p['slug']}-{kind}.webp"), "wb") as f:
                f.write(base64.b64decode(url.split(",", 1)[1]))
        print(f"{i+1}/{len(plants)} {p['name']}", flush=True)
    print("page errors:", errors)
    b.close()
srv.shutdown()

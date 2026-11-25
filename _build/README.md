# How the published site is built

GitHub Pages skips this folder (its name starts with `_`), so nothing here is published.

The site is built from the **Hoya Collection** artifact, without the flower builder. The artifact itself shows pictures rather than live 3D: bundled ones in `renders/` for plants without a saved design, and ones uploaded to the artifact's own storage for plants with one. The published site can't reach that storage, so every picture is drawn here and published in `renders/`.

1. Copy the artifact's `index.html` to `_build/artifact-index.html`, and its `fonts/` to the repo root. Skip `photos/` (builder only) and the artifact's own `renders/` (drawn again in step 4).
2. Export the saved designs from the artifact's database (collection `flowers`) as a JSON list to `_build/flowers.json`. An `images` field, if present, is ignored.
3. Trace the SF Symbols into SVG. The artifact writes its icons as SF Symbol characters, which only show where SF Pro is installed. The tracer is the artifact's own `tools/trace_icons.py.txt`, saved here as `trace_icons.py`. Stage `/Library/Fonts/SF-Pro.ttf` from Leo's Mac (never commit it), copy the page to a scratch file, then:
   `python3 _build/trace_icons.py <traced.html> <SF-Pro.ttf>`
   It rewrites the page in place: it fills `ICON_DATA` and turns the static icons in the markup into inline SVG. Use `<traced.html>` in place of `_build/artifact-index.html` in the steps below.
4. Draw every plant's pictures with the artifact's own `drawPictures()`, from the saved designs:
   `python3 _build/bake_renders.py _build/artifact-index.html _build/flowers.json <scratch>`
   This takes about 15 minutes for 84 plants. Each plant gets five WebP files: `front` (720 px, the umbel tile), `three` (1400 px, behind the name), `flower` (520 px, the Bloom tile), `leaf` (760 px, the Leaves tile) and `thumb` (216 px, the home cards).
   `renders-raw.sha256` lists the last bake. If `sha256sum -c` passes in the scratch folder and the list of plants is the same, the pictures haven't changed.
5. Bake the name shadows (one small blurred mask per plant, plus a shared grain tile):
   `python3 _build/bake_shadows.py <scratch> <scratch>`, then run `pngquant --speed 1 --strip --force --ext .png <scratch>/*-shade.png`.
   Replace `renders/` with the scratch folder's contents.
6. Build the page:
   `python3 _build/build.py <traced.html> _build/flowers.json index.html renders [--keep-builder]`
   With `--keep-builder` the flower builder stays (with its 3D renderer), and the artifact's `photos/` must be in the repo root for its photo reference. With no database on the live site it can't save; the builder says so itself. Without it, the builder is cut and `photos/` can be removed.

`build.py` does the following:
- reads every picture from `renders/`, with a version made from the pictures themselves, so browsers never keep a stale copy;
- removes the builder, the design system page (`#design` opens the home page), the 3D renderer, the fallback drawing and the database;
- replaces the slow `#nu-shadow` filter with the baked shadows;
- writes the designs and the soil drawing into the page, and works out each plant's colors only once.

It stops with an error if the artifact's code no longer matches one of its cuts.

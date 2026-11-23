# How the published site is built

GitHub Pages skips this folder (its name starts with `_`), so nothing here is published.

The site is built from the **Hoya Collection** artifact, without the flower builder. The artifact itself shows pictures rather than live 3D: bundled ones in `renders/` for plants without a saved design, and ones uploaded to the artifact's own storage for plants with one. The published site can't reach that storage, so every picture is drawn here and published in `renders/`.

1. Copy the artifact's `index.html` to `_build/artifact-index.html`, and its `fonts/` to the repo root. Skip `photos/` (builder only) and the artifact's own `renders/` (drawn again in step 3).
2. Export the saved designs from the artifact's database (collection `flowers`) as a JSON list to `_build/flowers.json`. An `images` field, if present, is ignored.
3. Draw every plant's pictures with the artifact's own `drawPictures()`, from the saved designs:
   `python3 _build/bake_renders.py _build/artifact-index.html _build/flowers.json <scratch>`
   This takes about 15 minutes for 84 plants. Each plant gets five WebP files: `front` (720 px, the umbel tile), `three` (1400 px, behind the name), `flower` (520 px, the Bloom tile), `leaf` (760 px, the Leaves tile) and `thumb` (216 px, the home cards).
   `renders-raw.sha256` lists the last bake. If `sha256sum -c` passes in the scratch folder and the list of plants is the same, the pictures haven't changed.
4. Bake the name shadows (one small blurred mask per plant, plus a shared grain tile):
   `python3 _build/bake_shadows.py <scratch> <scratch>`, then run `pngquant --speed 1 --strip --force --ext .png <scratch>/*-shade.png`.
   Replace `renders/` with the scratch folder's contents.
5. Build the page:
   `python3 _build/build.py _build/artifact-index.html _build/flowers.json index.html renders`

`build.py` does the following:
- reads every picture from `renders/`, with a version made from the pictures themselves, so browsers never keep a stale copy;
- removes the builder, the 3D renderer, the fallback drawing and the database;
- replaces the slow `#nu-shadow` filter with the baked shadows;
- writes the designs and the soil drawing into the page, and works out each plant's colors only once.

It stops with an error if the artifact's code no longer matches one of its cuts.

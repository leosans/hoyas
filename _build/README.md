# How the published site is built

GitHub Pages skips this folder (its name starts with `_`), so nothing here is published.

The site is built from the **Hoya Collection** artifact, without the flower builder. Every flower and leaf picture is a prebaked PNG in `stills/`.

1. Copy the artifact's `index.html` to `_build/artifact-index.html` and its `fonts/` to the repo root.
2. Export the saved designs from the artifact's database (the `flowers` collection) as a JSON list to `_build/flowers.json`.
3. Bake the pictures. This renders every plant with the artifact's own 3D renderer and the saved designs:
   `python3 _build/bake.py _build/artifact-index.html _build/flowers.json stills`
4. Compress the pictures, which keeps transparency and size:
   `pngquant --quality=75-95 --speed 1 --strip --force --ext .png stills/*.png`
5. Bake the name shadows (one small blurred mask per plant plus a shared grain tile), from the raw renders:
   `python3 _build/bake_shadows.py <raw stills> stills`
   Then run `pngquant --speed 1 --strip --force --ext .png stills/*-shade.png`.
6. Build the page:
   `python3 _build/build.py _build/artifact-index.html _build/flowers.json index.html`

`build.py` also writes the soil drawing into the page (it's the same for every plant, but slow to draw), works out each plant's colors only once, and swaps the name shadow's SVG filter for the baked mask. It stops with an error if the artifact has changed in a way that its cuts no longer match.

Four pictures per plant, all transparent:

| File | Pixels | Used for |
| --- | --- | --- |
| `<plant>-front.png` | 720 | home cards and the umbel tile |
| `<plant>-hero.png` | 1400 | the umbel behind the name |
| `<plant>-bloom.png` | 520 | the Bloom tile |
| `<plant>-leaf.png` | 760 | the Leaves tile |
| `<plant>-shade.png` | 384 | the shadow behind the name (a blurred mask, used with `grain.png`) |

## Skipping the compression step

`stills-raw.sha256` lists the checksums of the last bake's raw renders, before compression. After baking to a scratch folder, run `cd <scratch> && sha256sum -c ../_build/stills-raw.sha256`. If every file matches and the list of plants is the same, the pictures haven't changed: keep `stills/` as it is. If anything differs, compress the new bake, replace `stills/`, and rewrite `stills-raw.sha256`.

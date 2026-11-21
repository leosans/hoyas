# How the published site is built

GitHub Pages skips this folder (its name starts with `_`), so nothing here is published.

The site is built from the **Hoya Collection** artifact, without the flower builder. Every flower and leaf picture is a prebaked PNG in `stills/`.

1. Copy the artifact's `index.html` to `_build/artifact-index.html` and its `fonts/` to the repo root.
2. Export the saved designs from the artifact's database (the `flowers` collection) as a JSON list to `_build/flowers.json`.
3. Bake the pictures. This renders every plant with the artifact's own 3D renderer and the saved designs:
   `python3 _build/bake.py _build/artifact-index.html _build/flowers.json stills`
4. Compress the pictures, which keeps transparency and size:
   `pngquant --quality=75-95 --speed 1 --strip --force --ext .png stills/*.png`
5. Build the page:
   `python3 _build/build.py _build/artifact-index.html _build/flowers.json index.html`

`build.py` stops with an error if the artifact has changed in a way that its cuts no longer match.

Four pictures per plant, all transparent:

| File | Pixels | Used for |
| --- | --- | --- |
| `<plant>-front.png` | 720 | home cards and the umbel tile |
| `<plant>-hero.png` | 1400 | the umbel behind the name |
| `<plant>-bloom.png` | 520 | the Bloom tile |
| `<plant>-leaf.png` | 760 | the Leaves tile |

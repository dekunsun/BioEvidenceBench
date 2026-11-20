# Poster

Portrait, 24 × 36 in, one page, in the layout of the LiveLab poster (github.com/dekunsun/livelab/poster).

- `poster.html`: the source. Edit this, never the PDF.
- `poster.pdf`: printed from the source with headless Chromium (`render.js`). Print at 100 %, no scaling.
- `preview.png`: a half-scale screenshot of the same page.
- `fig/`: the three charts (`extraction_poster.png`, `ladder_poster.png`, `linking_poster.png`) are drawn by
  `src/plot_poster_charts.py` at the width they occupy on the poster, so every label is the body size; values are read
  from the run records. University of Pennsylvania logo (reversed, for the dark band) and the AI4S.fyi logo and QR codes
  are reused from the LiveLab poster; `qr_repo.svg` points to this repository.

Rebuild after editing the source:

```bash
python src/plot_poster_charts.py
cd poster && node render.js "$PWD"
```

`render.js` prints the height of each row and of the main area; if `main` scrolls past its client height, a row
overflowed and the bottom of the poster is cut. Type: three sizes only, as in LiveLab (83 px title, 34 px panel
titles, 26 px everything else).

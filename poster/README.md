# Poster

Portrait **A1 (594 × 841 mm)**, one page, for Deep Matters 2026 (Agents for Science, 26 November 2026; the organisers asked for A1 and "fun, engaging and agentic-related"). Version 2 (2026-11-24, after the author found version 1 weaker than the other documents): text in HTML at poster sizes, real scans as the visual centre (crops cut at full resolution by `src/make_poster_assets.py` into `fig/v2/`), in reading order 01 Motivation (the BULIMUS hook) → 02 Methodology (same pages, three texts, one agent; 607 labels before any output; plan frozen) → 03 Results (the agent's five steps, each marked leaks / holds / needs people with its number; a "spot the fake" quiz as step 1 up close, answer printed upside down) → 04 Case study 本草綱目 → 05 Conclusion (one rule per step), then the materials-papers analogy with the limits, and the QR codes. Drawn on a 24 × 33.92 in canvas zoomed by 0.9744; body text prints at about 20 pt, numbers at 40 pt. Earlier versions are kept: `poster_a1_v1.*` (first A1) and `poster_a0.*` (A0).

- `poster.html`: the source. Edit this, never the PDF.
- `poster.pdf`: printed from the source with headless Chromium (`node render.js "$PWD" poster A1`), A1. Print at 100 %, no scaling.
- `preview.png`: a half-scale screenshot of the same page.
- `fig/`: the three charts (`extraction_poster.png`, `ladder_poster.png`, `linking_poster.png`) are drawn by
  `src/plot_poster_charts.py` at the width they occupy on the poster, so every label is the body size; values are read
  from the run records. University of Pennsylvania logo (reversed, for the dark band) and the AI4S.fyi logo and QR codes
  are reused from the LiveLab poster; `qr_repo.svg` points to this repository. `cas_logo_reverse.png` is a white copy of the California Academy of Sciences logo, added at the author's request (she volunteers with its Scientific Computing team; the project is independent and uses public data only). The strips `misread_poster.png`, `fluent_poster.png` and `linking_page_poster.png` are cut from the real scans by `src/plot_scan_examples.py` (`poster_strip`, `poster_fluent_strip`, `poster_linking_strip`); `books_poster.png` and `bencao_glyph_poster.png` are README figures 11 and 10 with their title band and footnote cropped off (credits are in the poster captions).

Rebuild after editing the source:

```bash
python src/plot_poster_charts.py
cd poster && node render.js "$PWD"
```

`render.js` prints the height of each row and of the main area; if `main` scrolls past its client height, a row
overflowed and the bottom of the poster is cut. Type: three sizes only, as in LiveLab (83 px title, 34 px panel
titles, 26 px everything else).

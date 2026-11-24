# Poster

Portrait **A1 (594 × 841 mm)**, one page, for Deep Matters 2026 (Agents for Science, 26 November 2026). The organisers asked for A1 and for content that is "fun, engaging and agentic-related", so this version is lighter than the A0 one. Box titles stay the usual ones (01 Motivation, 02 Methodology, 03 Results, 04 Case study: 本草綱目, 05 Conclusion; the author, 2026-11-24), each with an agent-focused subtitle. Drawn on a 24 × 33.92 in canvas zoomed by 0.9744; body text prints at about 19 pt. The earlier A0 version is kept as `poster_a0.html` / `poster_a0.pdf` (`node render.js "$PWD" poster_a0 A0`).

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

# Poster

Portrait **A1 (594 × 841 mm)**, one page, for Deep Matters 2026 (Agents for Science, 26 November 2026). Version 4 (2026-11-25, the author: "想做成横向阅读的"): the v3 content in rows read left to right, each section a white box on a light grey ground. Row 1: 1 Motivation (BULIMUS scan, shell, the two readings) | 2 Methods (data, three texts, agent task, reference labels, analysis; test material). Row 2, full width: 3 Results, the agent's evidence chain running across the page (Figure 3: scanned page → read → extract → ground → link → review → database record, red where evidence was lost) above Figures 4–6 side by side (F1 by text with 95% intervals, names intact vs F1, link recall by linker). Row 3: 4 Two failures an agent cannot see (Figure 7: quiz with the answer upside down; a name read correctly that does not link) | 5 Work in progress: classical Chinese (本草綱目, Table 1; dev pages only). Row 4, full width: 6 Conclusions, one rule per step aligned with the five steps of the chain; limits, references, QR. One typeface (Inter) at four sizes (title 76, section 42, body 28, caption 22 px); Penn navy and red only for lost evidence. Charts: `src/plot_poster_v3.py` → `fig/v3/` (7.27 × 3.2 in); scan crops: `src/make_poster_assets.py` → `fig/v2/`. Canvas 24 × 33.92 in zoomed by 0.9744. Earlier versions kept: `poster_a1_v3.*` (three columns), `poster_a1_v2.*`, `poster_a1_v1.*`, `poster_a0.*`.

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

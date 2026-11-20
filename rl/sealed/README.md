# Sealed pages (next blind entity test)

16 pages (8 Butler, 8 Reeve) drawn by `src/rl_seal_pages.py` (seed 20261120) from Butler and Reeve
pages in `bhl-impact-gt`, excluding the 22 BioEvidenceBench sample pages, pages with under 300
characters of expert text, and BHL `Index` pages. Frame: 208 Butler and 259 Reeve pages.

Rules: no model is run on these pages and their text is not analysed until they are unsealed.
They are excluded from every task B split. To unseal: Gloria labels them (guide v0.10, the first
8 in `draw_order` first), the labels are committed unchanged, then a line goes into `rl/LOG.md`.

Note: task B splits by 10-page blocks, so a sealed page's neighbours may sit in task B's training
blocks. That does not touch entity labels, but a model trained on task B should not later be
evaluated on these pages without saying so.

`pages.csv.sha256` holds the hash of `pages.csv` at sealing time.

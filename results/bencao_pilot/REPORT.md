# 本草綱目 feasibility pilot: six half-leaves of 卷十二上 (exploratory)

*2026-11-23. Built by `src/bencao_pilot.py`. No model was called, nothing was labelled, no money was
spent. Feasibility of the sources: `docs/notes/bencao_feasibility.md`.*

## What was built

| Half-leaf | Content | Lines | Characters | Legacy OCR CER | IA image |
| --- | --- | ---: | ---: | ---: | ---: |
| 036-1b | 甘草 集解: places, cited authors, cited works | 8 | 292 | 0.96 | n11 |
| 036-5a | 甘草 附方: prescriptions | 8 | 284 | 0.97 | n18 |
| 036-7b | 黃耆 opens: heading, 釋名, 集解 | 8 | 215 | 1.00 | n23 |
| 036-12b | 人參 釋名: many alternative names | 8 | 307 | 0.97 | n33 |
| 036-13a | 人參 集解: producing regions | 8 | 299 | 0.98 | n34 |
| 036-30a | 桔梗 opens | 8 | 171 | 1.01 | n68 |

For each half-leaf: the Kanripo transcription with and without markup (`data/bencao/kanripo*/`), the
legacy OCR (`data/bencao/legacy_ia/`), the scan (`pages/`), and the page map
(`data/bencao/pilot_pages.csv`). `verify.html` shows each scan next to its transcription lines;
`scan_verify.xlsx` has one row per manuscript line for recording differences (`matches_scan`,
`scan_reading`, `note`).

## Findings

1. **Page alignment works.** Image n of Internet Archive item 06048793.cn is half-leaf index + 10
   (n10 = 036-1a). All six pilot images were checked by eye against the first and last transcription
   lines. Each image holds one half-leaf of 8 columns, and Kanripo's line breaks follow those columns.
2. **The legacy OCR carries almost no signal (CER 0.96–1.01).** Internet Archive's Tesseract read the
   vertical traditional-character manuscript with a horizontal simplified-Chinese model. In this case the
   legacy condition is "no usable text", unlike Butler and Reeve, where legacy OCR found the right place
   93–97% of the time. A modern OCR that reads vertical traditional Chinese is required for the
   comparison to mean anything.
3. **A free local OCR level exists but is weak.** Tesseract 5 with the vertical traditional-Chinese model
   (`chi_tra_vert`, psm 5; `python src/bencao_pilot.py tesseract`) reaches CER 0.67–0.74 on three
   pages and 0.86–1.09 on the three with dense small notes or a mixed layout. It can serve as an
   intermediate OCR level; it is not the modern OCR the comparison needs.
4. **The transcription has visible gaps.** Kanripo marks unread characters with blanks (036-2b `芫  甘遂`,
   probably 芫花; 036-5a `名涼膈丸  聖`). Scan verification has to fill these before a page can be
   `scan_verified`.
5. **Density is high.** About 170–310 characters per half-leaf, mostly in small two-column notes, with
   many cited authors, works and places per page (see the guide draft's examples). Six half-leaves are
   probably 150–250 mentions, far more per page than Butler or Reeve.
6. **The Commons copy could not be fetched from this environment** (Wikimedia returned HTTP 429). The
   working images come from the Internet Archive copy of the same CADAL scan; Commons is cited for the
   licence. To confirm in a browser: Commons DjVu page 11 shows the same page as image n10 (036-1a).

## Next steps (each needs the author's decision)

1. Check the six pages against the scans (`verify.html`, `scan_verify.xlsx`) and mark the ones that
   pass as `scan_verified`.
2. ~~Decide the open points of the guide~~ done: guide v0.1 (`docs/notes/bencao_guide.md`), the
   proposals adopted by the author on 2026-11-23.
3. Choose the modern OCR: an open model that reads vertical traditional Chinese, or a vision LLM (if a
   Claude model, it shares a family with the extractor; to be stated). A 5-page cost pilot comes first.
4. Only then label the pilot pages (dev) and draft the plan for a locked test set.

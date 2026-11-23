# Feasibility check: *Bencao gangmu* (本草綱目) as an external case in classical Chinese

*2026-11-23. Desk check only: nothing was labelled or run, and no money was spent. Everything here
was checked against the live sources on that date, except where marked "not verified".*

**Verdict: feasible on the Siku quanshu (文淵閣四庫全書) edition, where all three text versions exist for
the same pages. Licence and rights were settled on 2026-11-23 (below); what remains is a scan check of
the transcription on every sampled page.**

## The three text versions

| Version | Source | Status |
| --- | --- | --- |
| Scan | **Wikimedia Commons**: the CADAL scans of 四庫全書 · 本草綱目, each file with a public-domain statement (checked by the author, 2026-11-23). The same scans are on Internet Archive (`universallibrary`, `06048773.cn` … `06048820.cn`, 48 of 49 volumes) without a rights statement, so Commons is the source to cite | Available. Fetch by script and cite the Commons file pages |
| Legacy OCR | The same items: Tesseract 5.3 text (`_djvu.txt`) and hOCR with word boxes | Available, but close to unusable: on vertical classical Chinese it returns scattered characters. The legacy condition will sit near zero |
| Edition-aligned scholarly transcription | Kanripo (Kanseki Repository, 漢籍リポジトリ), repository `kanripo/KR3e0079`, `BASEEDITION WYG` (文淵閣) | Available, with a page marker per half-leaf (`<pb:KR3e0079_WYG_121-1a>`) and a line break per manuscript line. **Licence: CC BY-SA 4.0**, stated for the whole collection on the Kanseki Repository's GitHub organisation page (checked by the author, 2026-11-23; the single repository has no licence file). Not yet a verified reference: see below |
| Modern OCR | None ready-made (FineBooks does not cover Chinese) | Must be produced: an open OCR or vision model that reads vertical traditional Chinese. If a Claude model reads the image, OCR and extraction come from the same family; say so |

## How the transcription is used

- It is called an **edition-aligned scholarly transcription**, not an expert reference: it follows the
  right edition page by page, but nobody here has checked it character by character against the scan.
- Every sampled page is checked against the Commons scan by hand before labelling. A page that passes
  is marked **`scan_verified`**; differences found are logged (as `data/transcription_errata.csv` does
  for the IMPACT texts), and only `scan_verified` pages are used as the reference for scoring.
- **CC BY-SA 4.0 obligations.** Any transcription text published here, whole or adapted (including
  excerpts carried in gold files), keeps the attribution to the Kanseki Repository and is released
  under CC BY-SA 4.0, separately from the project's MIT code and CC BY 4.0 gold licence. The Kanripo
  transcription is never presented as this project's own data.
- Before redistributing more than the sampled pages, ask the maintainers whether the WYG texts include
  third-party upstream material.

## Sources that do not work

| Source | Why not |
| --- | --- |
| ctext.org | The API returns `ERR_REQUIRES_AUTHENTICATION` for texts (institutional subscription or key), and its terms forbid scraping. Its punctuated Siku text (`ctp:wb8`) would be the best transcription; usable only through an institutional subscription |
| Wikisource (zh) 本草綱目 | Marked 未校訂 (not proofread), text quality 25%, no stated source edition |
| National Library of China edition on Internet Archive (`nlc-892-cbm1377-*`, 明萬曆 翻刻本, 40 volumes) | Public domain mark and Tesseract OCR, but no transcription of this edition, and the Siku text differs in layout and variants |

## Linking

A plain GBIF lookup by Chinese vernacular name is weak, as expected (species search, `qField=VERNACULAR`,
Catalogue of Life checklist, 7 test names): `人參` (traditional) found nothing useful while `人参`
(simplified) did; `黄连` matched four *Coptis* species exactly but not *C. chinensis*; `桔梗` returned
*Campanula*, not *Platycodon*; `麻黄` had no exact vernacular match. A naive linker will lose many names,
which is the hypothesis the case would test. Gold links need scholarly identifications (for example
《中华本草》 or Unschuld's *Dictionary of the Ben cao gang mu*), consulted by hand, not redistributed.
The Catalogue of Life China API needs a key and was not tested.

## Points to settle before any labelling

1. ~~The Kanripo licence~~ settled: CC BY-SA 4.0 (collection-level statement). Still open: how the WYG text was proofread.
2. ~~The rights to the scans~~ settled: use the Commons copies with their public-domain statements.
3. ~~The mapping from Commons file pages to Kanripo half-leaf markers~~ checked for 卷十二上 by the author
   in a browser (2026-11-23): Commons file CADAL06048793 confirmed; its DjVu page 11 shows the same image
   as Internet Archive n10, which is Kanripo half-leaf 036-1a. So Commons page = IA image n + 1 =
   half-leaf index + 11 (`commons_page` in `data/bencao/pilot_pages.csv`). Other volumes need their own
   one-page check.
4. ~~Which modern OCR to run~~ Claude Opus and Haiku (paid, $0.16) and PaddleOCR (open, local, $0); see
   `results/bencao_pilot/REPORT.md`.
5. The Siku copy is a hand-written manuscript in regular script, not a print, and has taboo-avoidance
   changes; both should be stated as conditions of the case.

# Feasibility check: *Bencao gangmu* (本草綱目) as an external case in classical Chinese

*2026-11-23. Desk check only: nothing was labelled or run, and no money was spent. Everything here
was checked against the live sources on that date, except where marked "not verified".*

**Verdict: feasible on the Siku quanshu (文淵閣四庫全書) edition, where all three text versions exist for
the same pages. Two things must be checked by hand first: the licence of the transcription and the
rights to the scans.**

## The three text versions

| Version | Source | Status |
| --- | --- | --- |
| Scan | Internet Archive, collection `universallibrary`, items `06048773.cn` … `06048820.cn`: 欽定四庫全書 · 子部 · 醫家類 本草綱目, scanned by Zhejiang University Library (CADAL), 48 of 49 volumes | Available. **No rights statement** on the items; the manuscript (18th century) is public domain, the photographic reproduction's status is not stated. Do not commit images; fetch by script |
| Legacy OCR | The same items: Tesseract 5.3 text (`_djvu.txt`) and hOCR with word boxes | Available, but close to unusable: on vertical classical Chinese it returns scattered characters. The legacy condition will sit near zero |
| Expert transcription | Kanripo (漢籍リポジトリ), repository `kanripo/KR3e0079` on GitHub, base edition WYG (文淵閣) | Available, with a page marker per half-leaf (`<pb:KR3e0079_WYG_010-1b>`) and a line break per manuscript line, so it can be aligned page by page and line by line. **Licence not verified** (no licence file in the repository; kanripo.org could not be reached from here). **Quality not verified**: spot-check two or three pages against the scan |
| Modern OCR | None ready-made (FineBooks does not cover Chinese) | Must be produced: an open OCR or vision model that reads vertical traditional Chinese. If a Claude model reads the image, OCR and extraction come from the same family; say so |

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

1. The Kanripo licence (and whether its WYG text was proofread against the manuscript).
2. The rights to the CADAL scans for research use and display.
3. The mapping from Internet Archive image numbers to Kanripo half-leaf markers (per volume).
4. Which modern OCR to run, and its cost.
5. The Siku copy is a hand-written manuscript in regular script, not a print, and has taboo-avoidance
   changes; both should be stated as conditions of the case.

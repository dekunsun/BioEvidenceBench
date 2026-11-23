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
4. **Double blanks in the transcription mean two different things.** Sometimes a missing character
   (036-7b: Kanripo has `(活函金匱/玉  方)`, putting 函 in the right sub-column and leaving its place in
   the left one blank; the scan has 活金匱 / 玉函方; the same pattern on 036-7b line 5, 名 in
   `藥性論名時珍…/之長故  今`, and 036-12b line 2, 薓 in `廣雅薓時珍/曰人  年深`: where the right sub-column
   has a layout space, Kanripo moved the left sub-column's character at that height into it), sometimes
   only layout spacing before an attribution
   (036-30a `立瘥  蘇頌圖經`). Characters outside Unicode are written as entities (`&KR1171;`, twice on
   036-12b; counted as one placeholder 〓). Scan verification has to settle each blank before a page
   can be `scan_verified`.
5. **Density is high.** About 170–310 characters per half-leaf, mostly in small two-column notes, with
   many cited authors, works and places per page (see the guide draft's examples). Six half-leaves are
   probably 150–250 mentions, far more per page than Butler or Reeve.
6. **The Commons copy could not be fetched from this environment** (Wikimedia returned HTTP 429). The
   working images come from the Internet Archive copy of the same CADAL scan; Commons is cited for the
   licence. To confirm in a browser: Commons DjVu page 11 shows the same page as image n10 (036-1a).

## Next steps (each needs the author's decision)

1. ~~Check the six pages against the scans~~ done by the author on 2026-11-23 (archived unchanged as
   `data/bencao/received/2026-11-23_scan_verify_gloria.xlsx`; status in `data/bencao/scan_status.csv`):
   all six half-leaves are `scan_verified`. Her three later answers (spaces, not 名 or 薓, in the right
   sub-columns; the two 〓 on 036-12b are one rare character) are logged in
   `data/bencao/scan_verify_changes.csv` and applied in `data/bencao/scan_verify_working.csv`. The
   corrected reference is `data/bencao/verified_plain/`; OCR CER against it barely moves (Opus 0.032,
   Haiku 0.150). She re-checked 庾 on 036-30a line 7 (not 廋; `data/bencao/probe_a_changes.csv`). Probe A's
   `site_confirmed` is filled from her check (118 of 118).
2. ~~Decide the open points of the guide~~ done: guide v0.1 (`docs/notes/bencao_guide.md`), the
   proposals adopted by the author on 2026-11-23.
3. ~~Choose the modern OCR~~ option A run (below). Before Claude output is used as the modern-OCR
   level for Claude extraction, decide whether to add a second, non-Claude OCR (option B or C).
4. Only then label the pilot pages (dev) and draft the plan for a locked test set.

## Modern OCR, option A (run 2026-11-23, approved by the author: "跑")

Claude models transcribe each half-leaf from the scan alone (`src/bencao_ocr_claude.py`; runs
`results/20261123-0058_bencao_ocr_claude-haiku-5-5/` and `results/20261123-0059_bencao_ocr_claude-opus-5-5/`).
CER against the Kanripo transcription, markup removed (`python src/bencao_pilot.py score` →
`ocr_levels.csv`):

| Half-leaf | Internet Archive OCR | Tesseract `chi_tra_vert` | Claude Haiku 5.5 | Claude Opus 5.5 |
| --- | ---: | ---: | ---: | ---: |
| 036-1b | 0.96 | 0.73 | 0.08 | 0.03 |
| 036-5a | 0.97 | 0.86 | 0.21 | 0.03 |
| 036-7b | 1.00 | 1.04 | 0.36 | 0.08 |
| 036-12b | 0.97 | 0.73 | 0.15 | 0.06 |
| 036-13a | 0.98 | 0.67 | 0.05 | 0.02 |
| 036-30a | 1.01 | 1.09 | 0.15 | 0.02 |
| **median** | **0.98** | **0.80** | **0.15** | **0.03** |
| median, glyph-folded (auxiliary) | 0.98 | 0.79 | 0.08 | 0.007 |
| cost, six pages | — | $0 | $0.011 | $0.148 |

The folded row folds the fixed table `data/bencao/variant_table.csv` (glyph variants and the
missing-stroke taboo forms 𢎞/弘, 𤣥/玄) on both sides before comparing; it is the auxiliary OCR metric of
guide v0.2 rule 10. The primary figure stays the unfolded one. Contextual substitutions (元 written for
玄) are never folded.

How to read it:

- **This is disagreement with an unverified transcription, not error.** Most of Opus's 77 differences
  are variant glyphs (隂/陰, 𢎞/弘, 毎/每, 録/錄, 黒/黑): one side keeps the manuscript form, the other a
  standard form. Which side matches the scan is settled only by the scan check. Folding the variant
  table lowers Opus's median from 0.032 to 0.007 (row above).
- **The levels are well separated**, which is what the comparison needs: near-nothing (Internet
  Archive), poor (vertical Tesseract), fair (Haiku) and close (Opus).
- **Small two-column notes can be read in the wrong order.** On 036-7b, column 1, Opus wrote 活金匱 水莨菪
  菜中有…有毒 玉函方 誤食…: all right sub-columns first, then the left ones, and it dropped 毒 from
  水莨菪毒. The scan's order is 活金匱 玉函方 水莨菪毒 菜中有…有毒 誤食…. CER counts this only as a few
  edits, so reading order needs its own check before Opus output is used for extraction.
- **At Kanripo's gaps Opus agrees with the scan**: it writes 玉函方 where Kanripo has a blank, and leaves
  the layout blank before 蘇頌 empty.
- **Recall versus reading cannot be told apart yet.** 本草綱目 is famous; Opus may partly recall the text.
  A probe for later: places where the Siku copy differs from the common printed editions (taboo
  changes, copyist variants). If Opus writes the common-edition reading where the manuscript shows
  something else, it is recalling.
- **Same family.** If Claude also extracts, OCR and extraction share a model family; a non-Claude OCR
  level (Gemini, or an open model on a GPU) would remove that confound.

## Read or recall? Two dev-only probes (2026-11-23, designed with the author)

`src/bencao_probes.py`. Both probes are reported as **evidence about image dependence on these six
pages, not as proof** for or against memorisation.

**A. Edition probe (no API call).** Wikisource's 本草綱目/草之一 stands for the text that circulates
online, the most likely source of anything memorised. Kanripo's Siku text, the Wikisource text and each
OCR output are aligned character by character; at every place where Siku and Wikisource differ, the
output follows the manuscript, the circulating text, or neither (`probe_a_sites.csv`,
`probe_a_summary.csv`). Sites are split into glyph variants (same character, another form), interchangeable
usages (暴/曝, 註/注, 欬/咳 …) and different words. The split is proposed from fixed lists; the author
confirms it in `kind_confirmed`, and the Siku reading at each site against the scan in `site_confirmed`.

Kinds as decided by the author (2026-11-23, `data/bencao/received/2026-11-23_probe_a_kinds_gloria.xlsx`;
the proposal is kept in `kind`, her decision in `kind_final`). Adjacent sites of the same kind count as
one variation event (即是/地近 is one event, her note).

| Kind (her decision) | Sites | Events | Opus follows manuscript | Opus follows Wikisource | Haiku follows manuscript | Haiku follows Wikisource |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| different words (諸道/諸地, 即是/地近, 隂廣/附廣, 是/見, 鍾/鐘, 庾/瘦) | 7 | 6 | 7 | 0 | 7 | 0 |
| place-name miswriting candidate (枹䍐/抱䍐, twice) | 2 | 2 | 2 | 0 | 2 | 0 |
| interchangeable usages (暴/曝 ×2, 註/注, 欬/咳 ×2, 詞/辭) | 6 | 6 | 6 | 0 | 5 | 1 |
| glyph variants | 103 | 103 | 67 | 30 | 6 | 77 |

The author's changes to the proposal: 鍾/鐘 is a different word, not a usage (鍾 is a vessel or measure,
鐘 a bell; Wikisource's 鐘 may be its own error); 枹䍐/抱䍐 is a place name whose 抱 may be a copying error
from the similar radical, kept as its own kind and never folded; 庾詞/瘦辭 has a third attested form
廋詞; she re-checked the scan, which reads 庾 (not 廋), and classed it as a different word (Wikisource's
瘦 may be an error of that electronic text). Interchangeable usages are accepted in context
only; they are never folded globally. Where the two texts differ in wording, both models write what the
manuscript shows. Where they differ only in glyph form, Opus mostly keeps the manuscript form and Haiku
mostly writes the standard form, which is normalisation, not evidence of recall. Six word-level events
are few.

**B. Occlusion probe (paid, $0.15).** Columns 2 and 5 (from the right) of each half-leaf were painted
white, located from the ruled column lines; the image was otherwise unchanged and the prompt was the
same. Measure: of each column's own 3-character sequences (those in no other column of the page), the
share that appears in the output (`probe_b_summary.csv`; runs `results/20261123-0110_bencao_probe_b_claude-opus-5-5/`,
`results/20261123-0111_bencao_probe_b_claude-haiku-5-5/`, masked images inside).

| Model | Visible columns | Hidden columns |
| --- | ---: | ---: |
| Claude Opus 5.5 | 929 / 1,083 = 0.86 | 2 / 335 = 0.006 |
| Claude Haiku 5.5 | 803 / 1,083 = 0.74 | 1 / 335 = 0.003 |

Both models left the hidden columns out (Opus returned 6 columns for 036-5a) rather than filling them
in. A plain character-overlap measure gave 0.22 for hidden columns, but that came from formulaic wording
repeated across columns (甘草二兩水三升煑…服…合), not from the hidden text.

**Reading.** On these pages the output depends on what is visible: hidden text is not reproduced, and
where the manuscript's wording differs from the circulating text the models follow the manuscript.
Limits: six pages, two models from one family, one prompt that asks for what is written (a model might
withhold recalled text because of the instruction). The reference is now scan-verified by the author.

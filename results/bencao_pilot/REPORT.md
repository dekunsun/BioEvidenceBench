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
   licence. The author confirmed in a browser (2026-11-23) that Commons DjVu page 11 shows 036-1a, the
   page of Internet Archive image n10: Commons page = image n + 1 (`commons_page` in
   `data/bencao/pilot_pages.csv`).

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
3. ~~Choose the modern OCR~~ option A run (below); a non-Claude level, PaddleOCR, added on 2026-11-23
   (section "Non-Claude OCR" below). Gemini not run: PaddleOCR already gives a usable non-Claude level
   at $0.
4. Label 036-1b first (`gold/labelling_bencao_036-1b.xlsx`), record the time, then decide the other five.
5. ~~Commons page check~~ done: the author confirmed in a browser that DjVu page 11 begins
   欽定四庫全書 / 本草綱目卷十二上 (half-leaf 036-1a).
6. Only then draft the plan for a locked test set.

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

## Non-Claude OCR: PaddleOCR (2026-11-23, approved by the author, "1-4 都做")

Open-source PaddleOCR 3.7 (PP-OCRv6 medium, `lang="chinese_cht"`), run locally on CPU, $0
(`src/bencao_ocr_paddle.py`; install and settings in its docstring). PaddleOCR returns one box per
sub-column or stretch of large text; `assemble` puts boxes into the 8 ruled columns, drops the fold
margin, and reads each column top to bottom, the two sub-columns of a note right first.

| Run | Detector input | CER median vs scan-verified reference |
| --- | --- | ---: |
| `results/20261123-0539_bencao_ocr_paddleocr/` | default | 0.36 |
| `results/20261123-0547_bencao_ocr_paddleocr/` (used: `data/bencao/paddleocr/`) | long side up to 1600 px | 0.26 |

The first run missed whole sub-columns (036-1b, column 2, was empty); the larger detector input
recovered most of them. Two settings were tried on these same six pages, so the 0.26 is tuned on them.

| Half-leaf | 1b | 5a | 7b | 12b | 13a | 30a |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| PaddleOCR CER | 0.07 | 0.36 | 0.27 | 0.42 | 0.11 | 0.25 |
| missed / misread / extra characters | 2 / 15 / 2 | 43 / 31 / 28 | 21 / 18 / 20 | 24 / 93 / 5 | 21 / 11 / 0 | 14 / 19 / 9 |

It sits between vertical Tesseract (0.80) and Claude Haiku (0.15): a usable non-Claude level, strong on
clean pages (036-1b 0.07), weak on dense small notes and rare glyphs (036-12b reads 薓 and 〓 badly).
It normalises some forms the scan keeps (枹䍐 read as 抱旱/抱罕), which the folded metric does not
forgive, since 枹/抱 is not in the variant table.

## Claude extraction against the author's labels (2026-11-24, approved by the author, "跑吧")

Run `results/20261124-0826_bencao_extract_claude-opus-5-5/` (`src/bencao_extract.py`): Claude Opus 5.5,
effort medium, JSON schema enforced, one request per half-leaf on the scan-verified reference text
(`data/bencao/verified_plain/`), $0.242 in total, about $0.04 per half-leaf. As in the English books' G1
condition the model returns field + line + verbatim quote and code slices the value; 0 of 230 quotes
were invalid evidence. Gold: `gold/gold_mentions_bencao_gloria.csv` (224 rows, labelled alone by the
author, about 5 hours for the six half-leaves); the 18 `expert_pending` rows are optional.

**Not blind.** The guide was written from these pages and the prompt rules were written by Claude after
seeing the author's labels (examples taken only from half-leaves 036-1a and 036-2a). After the first
scoring the locator was changed once: within a line, a quote is looked for after the previous mention
first (the model lists mentions in reading order). This moved two values (`乾薑` on 036-5a line 6 from an
unlabelled `乾薑湯` to the labelled occurrence; `河西` on 036-1b line 2); the first placement is kept as
`mentions_locator_v1.csv`. Scores below are after the change. These numbers check that the pipeline
works on a classical Chinese text; they are not an independent result.

| Field | Gold rows (required) | Exact P / R / F1 | Overlap F1 |
| --- | ---: | --- | ---: |
| taxon | 97 | 0.94 / 1.00 / 0.97 | 0.97 |
| person | 18 | 1.00 / 1.00 / 1.00 | 1.00 |
| locality | 53 | 0.86 / 0.83 / 0.85 | 0.94 |
| cited_work | 38 | 0.95 / 0.95 / 0.95 | 0.99 |
| **all primary** | 206 | **0.93 / 0.95 / 0.94** | **0.97** |

`substance` (4 outputs: 水 and similar) has no gold rows: the author labelled no substances on these pages.

What the 26 exact-match differences are (`errors.csv`):

- **Place-name chains (most of the locality loss).** The model keeps a chain as one span where the
  author split it: `隴西洮陽` (gold `隴西` + `洮陽`), `潞州太行紫團山` (3 gold rows), `河東蒲坂縣` (2),
  and `首陽之山` against gold `首陽`. Guide rule "narrow to wide is one span" does not say what to do
  with wide-to-narrow chains or with `之山`; this is a guide question, not a model error as such.
- **Names inside other spans:** `人參` inside the cited title `人參讚`, `椵` inside `椵樹`, `枹䍐` labelled
  as a place inside the regional drug name (rule 12 says no nested locality).
- **Cited-work boundaries:** `本經下品` (gold `本經`), `傷寒類要` across the column break (no gold row).
- **Things the author did not label:** `蜜`, `米泔`, `蓍` as taxa; `蜀` / `漢中` where the gold row `蜀漢中`
  is `expert_pending`.

No person was missed or invented; every taxon in the gold was found. Next, if wanted: the same run on
PaddleOCR and Haiku OCR text (the OCR → extraction question of the English books), after deciding the
place-chain rule.

## From OCR to extraction (2026-11-24, the author: "继续做吧")

The same extraction (Claude Opus 5.5, same prompt and schema) run on three OCR versions of the six
half-leaves, $0.73 together (`results/20261124-0835…_paddleocr`, `…0836…_claude_haiku`,
`…0838…_claude_opus`; table `results/bencao_pilot/ocr_to_extraction.csv`, `python src/bencao_extract.py
summary <runs>`). Main metric: **value F1**, as in the English books: per half-leaf and field, the
extracted strings against the author's strings, so a name counts only if every character is right.
`folded` forgives glyph variants and missing-stroke taboo forms from `data/bencao/variant_table.csv`
(auxiliary, guide rule 10). "Names intact" = share of the 206 required gold values that occur letter for
letter in the text before any extraction.

| Text given to the extractor | OCR CER (median) | Names intact (folded) | Value F1 primary (folded) | taxon | person | locality | cited_work |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Scan-verified reference | 0 | 1.00 (1.00) | **0.94** (0.94) | 0.97 | 1.00 | 0.87 | 0.95 |
| Claude Opus OCR | 0.03 | 0.88 (0.98) | **0.83** (0.91) | 0.83 | 0.80 | 0.78 | 0.90 |
| Claude Haiku OCR | 0.15 | 0.69 (0.87) | **0.63** (0.79) | 0.62 | 0.73 | 0.75 | 0.47 |
| PaddleOCR 3.7 | 0.26 | 0.68 (0.81) | **0.68** (0.78) | 0.67 | 0.71 | 0.76 | 0.55 |

Reading:

- As in the English books, the share of names that survive OCR tracks extraction better than CER does:
  Haiku has the lower CER (0.15 against 0.26) but PaddleOCR keeps as many names (0.68–0.69) and scores a
  little higher (0.68 against 0.63). Four text versions, six pages: an observation, not a correlation.
- Opus OCR's CER is 0.03, yet one name in eight breaks, mostly because it writes the standard form where
  the scan has a variant (𢎞景 → 弘景, 宻 → 密). Folded, it loses about 3 points against the reference.
  Whether such a name is "wrong" depends on the use: wrong for an edition-faithful record, harmless for
  linking (guide rule 10 keeps the scan's form in gold and the standard form in `restored_form`).
- Haiku OCR loses cited works most (0.47): the small two-column source notes (別録 and others) are where
  its reading order and characters fail.
- 0–1 invalid quotes per run: the evidence check holds on OCR text too; it cannot tell whether the OCR
  text itself is right.

Same caveats as above: not blind, six half-leaves, one extraction model; the PaddleOCR detector size was
chosen on these pages.

## Prompt p2 after guide v0.4 rule 15 (2026-11-24, the author: "按你的建议来")

Rule 15 (place-name chains, `docs/notes/bencao_guide.md`) was written to match how the author had already
labelled the chains; no gold row changed. Prompt `bencao-p2-guide-v0.4` states it; all four texts re-run,
$0.985 (`results/20261124-0900…`, `…0901…_claude_opus`, `…0902…_claude_haiku`, `…0904…_paddleocr`;
table `results/bencao_pilot/ocr_to_extraction_p2.csv`; the p1 runs stay as history). The rule was written
after seeing the errors on these same pages, so the gain is partly fitted to them.

| Text | Names intact (folded) | Value F1 primary p1 → **p2** (folded) | locality p1 → p2 |
| --- | ---: | ---: | ---: |
| Scan-verified reference | 1.00 (1.00) | 0.94 → **0.98** (0.98) | 0.87 → 0.98 |
| Claude Opus OCR | 0.88 (0.98) | 0.83 → **0.87** (0.95) | 0.78 → 0.93 |
| Claude Haiku OCR | 0.69 (0.87) | 0.63 → **0.68** (0.85) | 0.75 → 0.91 |
| PaddleOCR 3.7 | 0.68 (0.81) | 0.68 → **0.72** (0.83) | 0.76 → 0.90 |

On the reference text 12 differences remain (`errors.csv`): `枹䍐` inside the regional drug name
`枹䍐草` (rule 12), `人參` inside the title `人參讚`, the unlabelled `傷寒類要` across a column break,
`蜀` / `漢中` against the `expert_pending` `蜀漢中`, and words the author did not label (`蜜`, `米泔`,
`小便`, `蓍`). With the rule question settled, the order is the English books' one: the extractor is near
the ceiling on the right text, and what is lost on OCR text is mostly names that did not survive OCR.

## How names are lost in each OCR text (2026-11-24, the author: "写进去")

Before any extraction: for each of the 206 required primary gold values, why it does or does not survive
in each OCR text (`python src/bencao_extract.py losses` → `name_loss_by_text.csv`, one row per case in
`name_loss_cases.csv`). The gold span is mapped into the OCR text by character alignment, then classified
in this order: **intact**; **normalised form** (equal once glyph variants and missing-stroke forms from
`variant_table.csv` are folded); **reading order** (not at the aligned place but a spare occurrence is
elsewhere on the half-leaf, or all its characters are next to the place but not contiguous); **missing**
(most characters have no counterpart); **misread** (anything else). A heuristic: where the OCR reorders
text the alignment itself can go wrong, so reading order and misread trade some cases.

| OCR text | CER | Intact | Normalised form | Reading order | Missing | Misread |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Claude Opus | 0.03 | 182 (88%) | 19 | 0 | 1 | 4 |
| Claude Haiku | 0.15 | 138 (67%) | **30** | 9 | 5 | 24 |
| PaddleOCR 3.7 | 0.26 | 122 (59%) | 18 | **25** | 8 | **33** |

(Intact here is per gold row at its own place, so it is a little lower than the count-based "names intact"
above: a value that survives only at another occurrence counts as reading order.)

- **The two OCR systems lose names in different ways.** The Claude readers write the standard form of a
  character more often (`别録` → `別錄`, `陶𢎞景` → `陶弘景`): Haiku 30 of its 68 losses. PaddleOCR misreads
  more (`枹䍐草` → `抱旱草`, `䖅` → `藿`) and loses more to reading order, mostly the two sub-columns of small
  notes: 25 against Haiku's 9.
- **This is why Haiku's lower CER does not give a higher value F1.** Scored letter for letter, a normalised
  form is as wrong as a misreading, and Haiku normalises most. With forms folded the order flips (value F1
  0.85 Haiku against 0.83 PaddleOCR, p2).
- **Opus OCR** loses 24 names, 19 of them only by form. Its four misreadings are rare characters (`䖅` → `蘦`,
  `蓍` → `着`).
- The first count in chat (Haiku 37 normalised / 26 other, PaddleOCR 26 / 39) was count-based and did not
  separate reading order; this table replaces it.

### Glyph fidelity and meaning are two targets (the author's reading, 2026-11-24)

Opus OCR keeps 88% of names letter for letter and 98% once variant forms are folded: it reads the same
word but writes the common form. For an edition-faithful record that is an error; for search and linking it
is not. The guide already keeps the two apart (gold `text` keeps the scan's form, `restored_form` the
standard one); reports for this case therefore give both numbers. Two cautions: a folded match shows the
same word, not that the model "understood" the name; and the 98% is fitted, since the 68 pairs in the
variant table were collected from these six pages.

The same effect exists in the English books but is small. On the 16 test pages (all 421 gold values,
`data/sample/`), folding ligatures and long s (æ→ae, œ→oe, ſ→s):

| Text | Intact | Folded | Gap |
| --- | ---: | ---: | ---: |
| Butler + Reeve, legacy OCR | 61% | 63% | 2 points |
| Butler + Reeve, dots.mocr | 94% | 94% | 0 |
| 本草綱目, Opus OCR | 88% | 98% | 10 points |
| 本草綱目, PaddleOCR | 68% | 81% | 13 points |
| 本草綱目, Haiku OCR | 69% | 87% | 18 points |

dots.mocr kept 31 of the 35 values with æ/œ, and none of its four losses is a ligature change. Not the
same comparison: the English row is an OCR model, the Chinese rows include Claude used as OCR, which was
not measured for ligatures on the English books. In classical Chinese the gap is large enough to change
which OCR ranks first; in this English print it is negligible.

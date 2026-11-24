# 本草綱目 case: pre-registration for the test set (draft, 2026-11-24)

*Draft for the author's review. Once she confirms it, it is frozen like `PREREGISTRATION.md` for the English
books: deviations go in `DEVIATIONS.md`, never into this file.*

## 1. What is frozen

`data/bencao/FREEZE_bencao.json` (`python src/bencao_freeze.py --verify` must report nothing changed before
any test output is scored): guide v0.5, prompt `bencao-p2-guide-v0.4` with its schema, locator and scorer
(`src/bencao_extract.py`), the variant table used by the folded metrics, the three OCR scripts and their
settings (PaddleOCR 3.7 with the 1600 px detector; Claude Opus 5.5 and Haiku 5.5 reading the scan), the
link-key rule, and the six dev half-leaves' gold. The test runs repeat the settings of the four dev runs
named in the freeze file.

## 2. Test set

Eight half-leaves, chosen on 2026-11-24 by `src/bencao_test_pages.py select` (seed 20261124) from the
Kanripo text only, before any model read them: one per content stratum in each volume.

| Half-leaf | Volume | Stratum |
| --- | --- | --- |
| 036-46b | 卷十二上 | names_places (釋名 / 集解) |
| 036-20a | 卷十二上 | prescriptions (附方) |
| 036-10a | 卷十二上 | note_dense |
| 036-15b | 卷十二上 | prose |
| 037-42b | 卷十二下 | names_places |
| 037-9a | 卷十二下 | prescriptions |
| 037-3b | 卷十二下 | note_dense |
| 037-26b | 卷十二下 | prose |

卷十二下 covers other drugs (天麻, 白及, 术 and others), so it tests whether the dev findings hold beyond
the entries the guide was written from.

## 3. Order of work

1. The author checks the eight transcriptions against the scans (`verify_test.html`,
   `scan_verify_test.xlsx`); her corrections make the test reference (`data/bencao/verified_plain/`).
2. She labels the eight half-leaves alone with guide v0.5, without seeing any model output; the file is
   archived unchanged in `gold/received/` and committed before anything else is run. Rows that need an
   expert are `expert_pending` (optional in scoring).
3. Only then: OCR of the eight scans (Opus, Haiku, PaddleOCR) and the frozen extraction on the four texts.
   Estimated cost about $2 (OCR about $0.25, extraction about $1.3).
4. Score once; report everything below, whatever the result.

Rules found on test pages go into the guide and the test gold, never into the prompt; such rows are marked
`later_rule` and scores are reported with all rows and with those rows optional.

## 4. Hypotheses and what would falsify them

Primary metric: value F1 on the primary fields (taxon, person, locality, cited_work), exact forms. 95%
intervals by bootstrap over half-leaves (8 pages: wide intervals are expected and reported as they are).
Results are given for all eight and per volume.

| | Hypothesis (from the dev pages) | Falsified if |
| --- | --- | --- |
| H1 | On the scan-verified reference the extraction is close to the labels: value F1 ≥ 0.90 (dev 0.98). | The point estimate is below 0.90. |
| H2 | Names that survive OCR, not CER, track extraction: the order of the three OCR texts by names intact equals their order by value F1, and Opus OCR scores highest of the three (dev: 0.87 against 0.72 and 0.68). | The two orders differ, or Opus OCR is not highest. |
| H3 | Glyph fidelity and meaning differ: for Opus OCR, names intact after folding variant forms exceed names intact letter for letter by at least 5 points (dev 10). | The gap is below 5 points. |
| H4 | The OCR systems lose names differently: a larger share of Haiku's lost names are normalised forms than of PaddleOCR's, and PaddleOCR loses more names to reading order than Haiku (dev 30 vs 18; 25 vs 9). | Either comparison goes the other way. |
| H5 | The evidence requirement holds on every text: invalid quotes ≤ 1% of quotes. | Above 1% on any text. |

H2 compares three systems on eight pages; it is descriptive and reported with the per-page numbers, not as
a significance test. The folded metric uses the frozen variant table; variants that first appear on test
pages are listed and not added before scoring.

## 5. What this cannot show

Eight half-leaves from one edition (文淵閣四庫全書) of one work; one extraction model (Claude Opus 5.5),
two of the three OCR readers from the same family; one labeller without domain training (expert questions
stay pending); public text that may be in pre-training data (the read-or-recall probes on the dev pages
found no sign of recall, which is not proof of none).

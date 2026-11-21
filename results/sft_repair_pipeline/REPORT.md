# The released SFT repair model inside the extraction pipeline (exploratory)

*2026-11-21. Rules fixed before the run in [PLAN.md](PLAN.md); logged in `DEVIATIONS.md`. The 16 test
pages were unsealed on 2026-11-20, so this is not a blind test. Code: `src/sft_repair_pipeline.py`
(`build`, `assemble`, `report`), `rl/training/repair_pages.py` (pod).*

**Question.** If BHL's legacy OCR is first repaired line by line by the released research checkpoint
(`rl-sft-ocr-repair-v1`, Qwen3-0.6B SFT seed 2), how much of the extraction loss does it recover?

**Answer.** A little, and not enough to matter as a route. Value F1 rises by about 0.07–0.08 per book
(paired page bootstrap excludes zero), from 0.60 to 0.67 (Butler) and 0.64 to 0.72 (Reeve). Re-OCR with
dots.mocr (0.95 / 0.98) and Opus repairing while it extracts (G2, 0.96 / 0.91) recover nearly all of it;
so does Haiku G2 on Butler (0.87). The small model also changes correct names into other plausible names.

## Repair step (GPU, run `rl/training/runs/20261121-2313_repair22/`)

- 991 non-empty legacy lines on 22 pages; 924 repaired (≥ 15 characters and 2 words), 586 changed,
  6 fell back to the OCR line (length rule). Generation 4.6 s; pod 4.8 min on a Secure RTX 4090,
  about **$0.07**. Checkpoint SHA-256 checked against the release (`bfeb5657…`).

## Text quality (all primary-field gold mentions; `summary.csv`, `pages.csv`, `mentions.csv`)

| book · split | median page CER legacy → repaired | gold mentions intact legacy → repaired |
|:--|--:|--:|
| Butler · test (7 pages) | 4.7% → 3.3% | 61% → 67% |
| Reeve · test (9 pages) | 8.6% → 7.1% | 66% → 74% |
| Butler · dev (3 pages) | 2.0% → 0.9% | 81% → 79% |
| Reeve · dev (3 pages) | 5.9% → 3.1% | 71% → 74% |

For comparison, dots.mocr keeps 96% / 99% of test-page mentions intact (OCR ladder).

On the 350 primary test mentions the repair fixed 31 and broke 6. All 6 are intact names it replaced:
`LICHT.` → `LINN.`, `Motacilla beema` → `Motacilla bema`, `SOWERBY` → `SOVERBY`, `B. oreades` →
`B. ovoletes`, `Linn.` → `Linnæus`, and `Darwin` lost from its line. On all 22 pages (including
vernacular names) further cases are `A. liopus` → `A. lutescens`, `A. dulcivox` → `A. dulcivorus`,
`St. John` → `V. John`, `Daw` → `Daffod`. These are the "unsupported changes" Gloria found in 7c: a
fluent wrong name is harder to catch than OCR junk.

## Extraction (Claude Opus 5.5, frozen G1 prompt `p4-guide-v0.6`, batch; run `results/20261121-sftrepair_claude-opus-5-5_test_G1/`, $0.25)

ALL_PRIMARY value F1 on the 16 test pages (`extraction.csv`):

| route | Butler | Reeve |
|:--|--:|--:|
| legacy OCR, G1 (frozen run) | 0.597 [0.45, 0.74] | 0.638 [0.52, 0.72] |
| **legacy + SFT repair, G1** | **0.667 [0.54, 0.79]** | **0.718 [0.55, 0.80]** |
| Haiku G2 on legacy (repair while extracting) | 0.873 [0.77, 0.95] | 0.767 [0.69, 0.87] |
| Opus G2 on legacy | 0.956 [0.92, 0.98] | 0.906 [0.79, 0.95] |
| dots.mocr, G1 (frozen run) | 0.952 [0.92, 0.98] | 0.977 [0.95, 1.00] |

Paired page bootstrap, repaired − legacy (`extraction_diff.csv`, 10,000 resamples): Butler +0.070
[0.044, 0.102], Reeve +0.079 [0.017, 0.117]. G2 rows are copied from `results/exploratory_conditions/`
(same scorer and gold).

## Reading

- The training result carries over in direction: the model repairs about 40% of damaged words on test
  lines, and here it recovers about a fifth of the F1 gap between legacy OCR and dots.mocr.
- It is not a substitute for re-OCR or for an API model's repair: the line-level model cannot see the
  page image, only repairs inside lines, and its wrong repairs are fluent names. In a pipeline these
  would also be quoted as "evidence" by G1, because the repaired text becomes the source.
- A pipeline that uses it must keep the original OCR next to the repaired line and mark every changed
  name, so a reviewer can see what the model changed.

## Limits

16 pages, two books, one checkpoint, greedy decoding, one extraction run; exploratory, decided after
unsealing. Lines under 15 characters (headings, short names) were not repaired, as in training.

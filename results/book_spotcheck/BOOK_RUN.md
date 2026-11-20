# Whole-book run (exploratory)

Frozen G1 prompt (p4-guide-v0.6), effort medium, FineBooks dots.mocr text, every page of Butler 1907 vol. 2 and Reeve 1849 vol. 5 with at least 20 characters (682 of 989; blank pages and plates skipped). Message Batches API. Runs `20261120-0201_book_opus-5-5` and `20261120-0201_book_haiku-5-5`.

| | Opus 5.5 | Haiku 5.5 |
|---|---|---|
| Requests answered | 682 / 682 (all `end_turn`, 0 unparsed) | 682 / 682 (all `end_turn`, 0 unparsed) |
| Cost | $7.64 ($11.2 per 1,000 pages) | $0.40 ($0.59 per 1,000 pages) |
| Batch wall time | 7.5 min | 7.5 min |
| Mentions | 16,045 | 15,834 |
| Evidence not located cleanly | 1 invalid | 1 invalid, 1 wrong line |
| Type check fails | 876 (862 are lower-case bare epithets as `taxon`, e.g. `venosus`) | 787 |
| Calibration: value F1 on the 16 test pages inside this run (Butler / Reeve) | 0.956 / 0.977 | 0.938 / 0.936 |

The calibration rows reproduce the frozen and model-comparison runs on the same pages (Opus 0.952 / 0.977, Haiku 0.941 / 0.945), so the batch at book scale behaves like the evaluated setting.

Review strata for Opus's mentions on the 660 pages outside the sample (Haiku as the second model, `analysis.flag_auto_accept` + OCR-junk check):

| stratum   |   mentions_in_book |   sampled |
|:----------|-------------------:|----------:|
| A         |              14045 |        70 |
| B         |               1404 |        40 |
| C         |                318 |        30 |

A = both models agree and checks pass (91% of Opus's mentions); B = everything else Opus produced; C = Haiku-only mentions (possible Opus misses). `spotcheck_sheet.xlsx` samples 70 / 40 / 30, shuffled, stratum hidden (`spotcheck_key.csv`). After Gloria returns it: `python src/make_spotcheck_sheet.py --score` (precision per stratum with Wilson intervals, whole-book precision weighted by stratum size). Recall outside the sample is not measured.

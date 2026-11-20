# Whole-book spot-check (exploratory)

Checked by Gloria against the scans: 60 of 140 shuffled rows (sheet `2026-11-20_spotcheck_gloria.xlsx`). `unsure` rows are left out of precision.

## All pages (as sampled)

| stratum   |   checked |   correct |   precision |    lo |    hi |   mentions_in_book |   boundary |   wrong_field |   not_a_mention |   misread |
|:----------|----------:|----------:|------------:|------:|------:|-------------------:|-----------:|--------------:|----------------:|----------:|
| A         |        20 |        20 |       1     | 0.839 | 1     |              14045 |          0 |             0 |               0 |         0 |
| B         |         5 |         5 |       1     | 0.566 | 1     |               1404 |          0 |             0 |               0 |         0 |
| C         |        14 |        10 |       0.714 | 0.454 | 0.883 |                318 |          0 |             1 |               3 |         0 |

Opus precision, weighted by stratum size (A+B): 1.000; `unsure` rows left out: 21. Stratum C is what Haiku found and Opus did not: `correct` there are Opus misses.

## In scope: `Index` pages excluded

| stratum   |   checked |   correct |   precision |    lo |    hi |   mentions_in_book |   boundary |   wrong_field |   not_a_mention |   misread |
|:----------|----------:|----------:|------------:|------:|------:|-------------------:|-----------:|--------------:|----------------:|----------:|
| A         |        20 |        20 |       1     | 0.839 | 1     |              12487 |          0 |             0 |               0 |         0 |
| B         |         5 |         5 |       1     | 0.566 | 1     |                555 |          0 |             0 |               0 |         0 |
| C         |        14 |        10 |       0.714 | 0.454 | 0.883 |                310 |          0 |             1 |               3 |         0 |

Opus precision, weighted by stratum size (A+B): 1.000; `unsure` rows left out: 2. Stratum C is what Haiku found and Opus did not: `correct` there are Opus misses.

Opus mentions on `Index` pages (removed by the scope rule): 2407 of 15449 outside the sample.

Review time, 9 timed rows: median 30 s per item (range 20-35).

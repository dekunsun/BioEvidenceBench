# Whole-book spot-check (exploratory)

| stratum   |   checked |   correct |   precision |    lo |    hi |   mentions_in_book |   boundary |   wrong_field |   not_a_mention |   misread |
|:----------|----------:|----------:|------------:|------:|------:|-------------------:|-----------:|--------------:|----------------:|----------:|
| A         |        20 |        20 |       1     | 0.839 | 1     |              14045 |          0 |             0 |               0 |         0 |
| B         |         5 |         5 |       1     | 0.566 | 1     |               1404 |          0 |             0 |               0 |         0 |
| C         |        14 |        10 |       0.714 | 0.454 | 0.883 |                318 |          0 |             1 |               3 |         0 |

Opus precision on the whole book, weighted by stratum size (A+B): 1.000. Stratum C is what Haiku found and Opus did not: `correct` there are likely Opus misses.

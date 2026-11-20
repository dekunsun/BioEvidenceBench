# Whole-book spot-check (exploratory)

| stratum   |   checked |   correct |   precision |    lo |    hi |   mentions_in_book |   boundary |   wrong_field |   not_a_mention |   misread |
|:----------|----------:|----------:|------------:|------:|------:|-------------------:|-----------:|--------------:|----------------:|----------:|
| A         |        20 |        20 |       1     | 0.839 | 1     |              14045 |          0 |             0 |               0 |         0 |
| B         |         5 |         5 |       1     | 0.566 | 1     |               1404 |          0 |             0 |               0 |         0 |
| C         |        14 |        10 |       0.714 | 0.454 | 0.883 |                318 |          0 |             1 |               3 |         0 |

Opus precision on the whole book, weighted by stratum size (A+B): 1.000. Stratum C is what Haiku found and Opus did not: `correct` there are likely Opus misses.
## Notes (Claude, after scoring)

Gloria checked the first 60 shuffled rows (A 25, B 20, C 15), against the scans. Verdicts by stratum and BHL page type (`PageTypeName` from bhl-metadata):

|                     |   correct |   not_a_mention |   unsure |   wrong_field |
|:--------------------|----------:|----------------:|---------:|--------------:|
| ('A', 'index page') |         0 |               0 |        4 |             0 |
| ('A', 'other page') |        20 |               0 |        1 |             0 |
| ('B', 'index page') |         0 |               0 |       15 |             0 |
| ('B', 'other page') |         5 |               0 |        0 |             0 |
| ('C', 'other page') |        10 |               3 |        1 |             1 |

- 19 of the 21 `unsure` rows are entries in Reeve's index (species epithets and authorities in the book-end index), all on pages BHL types as `Index`. Guide v0.10 does not say whether index entries are mentions. They are a scope question, not model errors: Opus extracts 2,407 mentions (16% of its output outside the sample) from `Index` pages.
- Leaving `unsure` aside, every checked Opus output was correct (A 20/20, B 5/5); no `misread` at all on dots.mocr text.
- Stratum B (no agreement or a failed check) is mostly index pages (15 of 20): the routing signal points at a guideline gap, not at errors.
- Stratum C (Haiku only): 10 of 14 decided rows are real mentions Opus missed, so a second model finds misses; 3 were not mentions and 1 had the wrong field.
- Review time, 9 timed rows: median 30 s per item (range 20-35).

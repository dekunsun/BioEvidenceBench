# Task B step 4: units, alignment and damage per book

Built by `src/rl_task_b_build.py` under Reward v1.2 rules (case-only words neutral, MUFI ligatures folded, references with U+FFFD or unidentified private-use characters invalid, lines with a mixed Latin/Cyrillic word set aside) and split v2 (`../SPLIT_V2.md`). Cuvier (held-out book) not touched; the 38 excluded pages not used. Content pages that gave no line: 0 (none; `missing_pages.csv`).

**Coverage is not accuracy.** `usable` counts lines that passed the automatic checks; whether they are paired correctly is measured by the audits (`audit_round1/`, `audit_sample.csv`).

Unit files (not committed; regenerate with the script) and their SHA-256:

- `train.jsonl`: 32333 usable units, `c66648ca97ee2c0e…`
- `dev.jsonl`: 3919 usable units, `e7a8c00a907e3ce9…`
- `intest.jsonl`: 3818 usable units, `a9fb5bfa1cd5a6a8…`

## Lines per book

| book          |   pages |   lines |   valid |   usable |   usable_share |
|:--------------|--------:|--------:|--------:|---------:|---------------:|
| Butler        |     235 |    6975 |    6487 |     6487 |          0.93  |
| Chitinskelett |      73 |    2498 |    2430 |     2427 |          0.972 |
| Piscium       |      43 |    1153 |     970 |      969 |          0.84  |
| Reeve         |     418 |   18532 |   17014 |    17013 |          0.918 |
| Trudy         |     480 |   15925 |   13174 |    13174 |          0.827 |

## Lines not used, by reason

Every one is kept with page, line, input, target and reason in `set_aside.jsonl` (cache) for a later hard-case set.

| reason                                                                                      |   Butler |   Chitinskelett |   Piscium |   Reeve |   Trudy |   All |
|:--------------------------------------------------------------------------------------------|---------:|----------------:|----------:|--------:|--------:|------:|
| coverage                                                                                    |      303 |              10 |        21 |     864 |    1356 |  2554 |
| coverage + similarity                                                                       |        5 |               3 |         4 |      76 |     574 |   662 |
| coverage + similarity + span ratio                                                          |       12 |              22 |        32 |     141 |     338 |   545 |
| coverage + similarity + span ratio + unreadable character in reference                      |        3 |               0 |         2 |       7 |       4 |    16 |
| coverage + similarity + unreadable character in reference                                   |        5 |               1 |         0 |       1 |       4 |    11 |
| coverage + span ratio                                                                       |       98 |               3 |         0 |     168 |     180 |   449 |
| coverage + span ratio + unreadable character in reference                                   |        2 |               0 |         0 |       0 |       0 |     2 |
| coverage + unreadable character in reference                                                |        2 |               0 |         3 |       0 |       5 |    10 |
| excluded: engraved plate caption; reference typos (Pinaa / Sinisra) and OCR unreadable      |        0 |               0 |         1 |       0 |       0 |     1 |
| excluded: engraved plate credit; reference typo (Soweby) and OCR unreadable                 |        0 |               0 |         0 |       1 |       0 |     1 |
| excluded: engraved plate imprint; OCR unreadable and reference doubtful                     |        0 |               1 |         0 |       0 |       0 |     1 |
| excluded: engraved plate imprint; reference garbled (Sehweizerbaresche Vertagsbuchhardlung) |        0 |               1 |         0 |       0 |       0 |     1 |
| excluded: engraved plate imprint; reference garbled (Wirtre FrankturtrM)                    |        0 |               1 |         0 |       0 |       0 |     1 |
| mixed-script word in reference                                                              |        0 |               1 |         0 |       0 |      59 |    60 |
| no aligned legacy text                                                                      |        1 |              20 |        27 |     134 |      27 |   209 |
| similarity                                                                                  |       17 |               1 |         1 |      77 |     118 |   214 |
| similarity + span ratio                                                                     |       15 |               0 |         0 |      20 |      21 |    56 |
| similarity + span ratio + unreadable character in reference                                 |        2 |               0 |         0 |       0 |       0 |     2 |
| similarity + unreadable character in reference                                              |        6 |               0 |         0 |       7 |       1 |    14 |
| span ratio                                                                                  |        4 |               1 |         2 |       9 |      30 |    46 |
| unreadable character in reference                                                           |       13 |               6 |        91 |      14 |      34 |   158 |
| All                                                                                         |      488 |              71 |       184 |    1519 |    2751 |  5013 |

## Similarity buckets (all lines; similarity ignores case)

| book          |   0.3-0.5 |   0.5-0.8 |   0.8-1.0 |   <0.3 |   no text |   All |
|:--------------|----------:|----------:|----------:|-------:|----------:|------:|
| Butler        |       117 |       484 |      6308 |     65 |         1 |  6975 |
| Chitinskelett |        17 |        81 |      2353 |     27 |        20 |  2498 |
| Piscium       |         9 |       167 |       911 |     37 |        29 |  1153 |
| Reeve         |       301 |      1778 |     15990 |    322 |       141 | 18532 |
| Trudy         |       808 |       748 |     13282 |   1060 |        27 | 15925 |
| All           |      1252 |      3258 |     38844 |   1511 |       218 | 45083 |

Usable lines with similarity 0.3-0.5 (would be rejected under a 0.5 floor):

| book          |   usable_only_at_0.3 |
|:--------------|---------------------:|
| Butler        |                   14 |
| Chitinskelett |                    7 |
| Piscium       |                    2 |
| Reeve         |                  102 |
| Trudy         |                  122 |

## Damaged and case-only words (usable lines)

Case-only words are neutral in Reward v1.2: not damaged, not penalised for case.

| book          |   words |   damaged |   damaged_reading |   case_only |   lines_with_damaged_name |   case_only_mismatch_rate |   damaged_rate |   damaged_rate_reading |
|:--------------|--------:|----------:|------------------:|------------:|--------------------------:|--------------------------:|---------------:|-----------------------:|
| Butler        |   80691 |      3130 |              3130 |         422 |                       144 |                    0.0052 |         0.0388 |                 0.0388 |
| Chitinskelett |   29168 |      1908 |              1908 |          21 |                        88 |                    0.0007 |         0.0654 |                 0.0654 |
| Piscium       |    6656 |      3419 |              3419 |           5 |                       103 |                    0.0008 |         0.5137 |                 0.5137 |
| Reeve         |  112964 |     23448 |             23448 |        3737 |                      1011 |                    0.0331 |         0.2076 |                 0.2076 |
| Trudy         |  108435 |      5388 |              5388 |          38 |                       251 |                    0.0004 |         0.0497 |                 0.0497 |

## Damaged words per usable line (share)

| book          |     0 |     1 |   2-5 |    >5 |
|:--------------|------:|------:|------:|------:|
| Butler        | 0.662 | 0.237 | 0.099 | 0.002 |
| Chitinskelett | 0.557 | 0.263 | 0.169 | 0.011 |
| Piscium       | 0.03  | 0.103 | 0.713 | 0.154 |
| Reeve         | 0.409 | 0.244 | 0.33  | 0.017 |
| Trudy         | 0.722 | 0.19  | 0.086 | 0.002 |

Counts:

| book          |     0 |    1 |   2-5 |   >5 |   All |
|:--------------|------:|-----:|------:|-----:|------:|
| Butler        |  4296 | 1539 |   640 |   12 |  6487 |
| Chitinskelett |  1351 |  638 |   411 |   27 |  2427 |
| Piscium       |    29 |  100 |   691 |  149 |   969 |
| Reeve         |  6964 | 4149 |  5614 |  286 | 17013 |
| Trudy         |  9506 | 2508 |  1139 |   21 | 13174 |
| All           | 22146 | 8934 |  8495 |  495 | 40070 |

## Heuristic flags (all lines)

| book          |   OCR merges words |   OCR splits words |   case-only words |   crosses OCR line break |   hyphen at line end |   missing text |   span length off |   special characters |
|:--------------|-------------------:|-------------------:|------------------:|-------------------------:|---------------------:|---------------:|------------------:|---------------------:|
| Butler        |                307 |                494 |               224 |                      129 |                  248 |            431 |               136 |                  230 |
| Chitinskelett |                 83 |                502 |                20 |                        5 |                  306 |             59 |                26 |                 1590 |
| Piscium       |                483 |                119 |                 6 |                        6 |                  441 |             89 |                36 |                 1016 |
| Reeve         |               1031 |               1165 |              2070 |                      179 |                 2553 |           1391 |               345 |                 4874 |
| Trudy         |               1331 |               1789 |                42 |                      535 |                 3067 |           2488 |               573 |                 6929 |

## Usable units per split

| book          |   dev |   intest |   train |   All |
|:--------------|------:|---------:|--------:|------:|
| Butler        |   607 |      571 |    5309 |  6487 |
| Chitinskelett |   314 |      383 |    1730 |  2427 |
| Piscium       |   209 |      156 |     604 |   969 |
| Reeve         |  1304 |     1578 |   14131 | 17013 |
| Trudy         |  1485 |     1130 |   10559 | 13174 |
| All           |  3919 |     3818 |   32333 | 40070 |

## Long s in *Piscium querelae*

40 of 60 pages contain ſ. The pages without it are blank pages, the title page, a modern bookplate and an all-caps dedication (capital S has no long form): the transcription uses ſ consistently. See `piscium_long_s.csv`.

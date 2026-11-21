# Task B step 4: units, alignment and damage per book

Built by `src/rl_task_b_build.py` under Reward v1.2 rules (case-only words neutral, MUFI ligatures folded, references with U+FFFD or unidentified private-use characters invalid, lines with a mixed Latin/Cyrillic word or leader dots set aside) and split v2 (`../SPLIT_V2.md`). Cuvier (held-out book) not touched; the 38 excluded pages not used. Content pages that gave no line: 0 (none; `missing_pages.csv`).

**Coverage is not accuracy.** `usable` counts lines that passed the automatic checks; whether they are paired correctly is measured by the audits (`audit_round1/`, `audit_sample.csv`).

Unit files (not committed; regenerate with the script) and their SHA-256:

- `train.jsonl`: 32060 usable units, `7cefbfa0a24012da…`
- `dev.jsonl`: 3894 usable units, `9afa77c5fb187392…`
- `intest.jsonl`: 3750 usable units, `879e356b7407770c…`

## Lines per book

| book          |   pages |   lines |   valid |   usable |   usable_share |
|:--------------|--------:|--------:|--------:|---------:|---------------:|
| Butler        |     235 |    6975 |    6381 |     6381 |          0.915 |
| Chitinskelett |      73 |    2498 |    2429 |     2426 |          0.971 |
| Piscium       |      43 |    1153 |     970 |      969 |          0.84  |
| Reeve         |     418 |   18532 |   16974 |    16973 |          0.916 |
| Trudy         |     480 |   15925 |   12955 |    12955 |          0.814 |

## Lines not used, by reason

Every one is kept with page, line, input, target and reason in `set_aside.jsonl` (cache) for a later hard-case set.

| reason                                                                                           |   Butler |   Chitinskelett |   Piscium |   Reeve |   Trudy |   All |
|:-------------------------------------------------------------------------------------------------|---------:|----------------:|----------:|--------:|--------:|------:|
| coverage                                                                                         |       34 |               6 |        21 |     188 |     410 |   659 |
| coverage + index/contents line with leader dots                                                  |      269 |               4 |         0 |     676 |     936 |  1885 |
| coverage + index/contents line with leader dots + mixed-script word in reference                 |        0 |               0 |         0 |       0 |       1 |     1 |
| coverage + index/contents line with leader dots + mixed-script word in reference + similarity    |        0 |               0 |         0 |       0 |       1 |     1 |
| coverage + index/contents line with leader dots + similarity                                     |        5 |               0 |         0 |       0 |     394 |   399 |
| coverage + index/contents line with leader dots + similarity + span ratio                        |       12 |              10 |         0 |      56 |     259 |   337 |
| coverage + index/contents line with leader dots + similarity + unreadable character in reference |        0 |               0 |         0 |       0 |       1 |     1 |
| coverage + index/contents line with leader dots + span ratio                                     |       98 |               3 |         0 |     158 |     156 |   415 |
| coverage + index/contents line with leader dots + unreadable character in reference              |        0 |               0 |         0 |       0 |       4 |     4 |
| coverage + mixed-script word in reference                                                        |        0 |               0 |         0 |       0 |       9 |     9 |
| coverage + mixed-script word in reference + similarity                                           |        0 |               0 |         0 |       0 |       3 |     3 |
| coverage + similarity                                                                            |        0 |               3 |         4 |      76 |     176 |   259 |
| coverage + similarity + span ratio                                                               |        0 |              12 |        32 |      85 |      79 |   208 |
| coverage + similarity + span ratio + unreadable character in reference                           |        3 |               0 |         2 |       7 |       4 |    16 |
| coverage + similarity + unreadable character in reference                                        |        5 |               1 |         0 |       1 |       3 |    10 |
| coverage + span ratio                                                                            |        0 |               0 |         0 |      10 |      24 |    34 |
| coverage + span ratio + unreadable character in reference                                        |        2 |               0 |         0 |       0 |       0 |     2 |
| coverage + unreadable character in reference                                                     |        2 |               0 |         3 |       0 |       1 |     6 |
| excluded: engraved plate caption; reference typos (Pinaa / Sinisra) and OCR unreadable           |        0 |               0 |         1 |       0 |       0 |     1 |
| excluded: engraved plate credit; reference typo (Soweby) and OCR unreadable                      |        0 |               0 |         0 |       1 |       0 |     1 |
| excluded: engraved plate imprint; OCR unreadable and reference doubtful                          |        0 |               1 |         0 |       0 |       0 |     1 |
| excluded: engraved plate imprint; reference garbled (Sehweizerbaresche Vertagsbuchhardlung)      |        0 |               1 |         0 |       0 |       0 |     1 |
| excluded: engraved plate imprint; reference garbled (Wirtre FrankturtrM)                         |        0 |               1 |         0 |       0 |       0 |     1 |
| index/contents line with leader dots                                                             |      106 |               1 |         0 |      40 |     219 |   366 |
| index/contents line with leader dots + similarity                                                |        8 |               0 |         0 |      16 |      76 |   100 |
| index/contents line with leader dots + similarity + span ratio                                   |       13 |               0 |         0 |      12 |      10 |    35 |
| index/contents line with leader dots + span ratio                                                |        4 |               0 |         0 |       4 |      15 |    23 |
| index/contents line with leader dots + unreadable character in reference                         |        0 |               0 |         0 |       0 |       1 |     1 |
| mixed-script word in reference                                                                   |        0 |               1 |         0 |       0 |      59 |    60 |
| mixed-script word in reference + unreadable character in reference                               |        0 |               0 |         0 |       0 |       3 |     3 |
| no aligned legacy text                                                                           |        1 |              20 |        27 |     134 |      27 |   209 |
| similarity                                                                                       |        9 |               1 |         1 |      61 |      42 |   114 |
| similarity + span ratio                                                                          |        2 |               0 |         0 |       8 |      11 |    21 |
| similarity + span ratio + unreadable character in reference                                      |        2 |               0 |         0 |       0 |       0 |     2 |
| similarity + unreadable character in reference                                                   |        6 |               0 |         0 |       7 |       1 |    14 |
| span ratio                                                                                       |        0 |               1 |         2 |       5 |      15 |    23 |
| unreadable character in reference                                                                |       13 |               6 |        91 |      14 |      30 |   154 |
| All                                                                                              |      594 |              72 |       184 |    1559 |    2970 |  5379 |

## Similarity buckets (all lines; similarity ignores case)

| book          |   0.3-0.5 |   0.5-0.8 |   0.8-1.0 |   <0.3 |   no text |   All |
|:--------------|----------:|----------:|----------:|-------:|----------:|------:|
| Butler        |       115 |       485 |      6309 |     65 |         1 |  6975 |
| Chitinskelett |        17 |        81 |      2353 |     27 |        20 |  2498 |
| Piscium       |         9 |       167 |       911 |     37 |        29 |  1153 |
| Reeve         |       301 |      1776 |     15992 |    322 |       141 | 18532 |
| Trudy         |       808 |       746 |     13284 |   1060 |        27 | 15925 |
| All           |      1250 |      3255 |     38849 |   1511 |       218 | 45083 |

Usable lines with similarity 0.3-0.5 (would be rejected under a 0.5 floor):

| book          |   usable_only_at_0.3 |
|:--------------|---------------------:|
| Butler        |                    8 |
| Chitinskelett |                    7 |
| Piscium       |                    2 |
| Reeve         |                   96 |
| Trudy         |                   25 |

## Damaged and case-only words (usable lines)

Case-only words are neutral in Reward v1.2: not damaged, not penalised for case.

| book          |   words |   damaged |   damaged_reading |   case_only |   lines_with_damaged_name |   case_only_mismatch_rate |   damaged_rate |   damaged_rate_reading |
|:--------------|--------:|----------:|------------------:|------------:|--------------------------:|--------------------------:|---------------:|-----------------------:|
| Butler        |   80263 |      2944 |              2944 |         424 |                       120 |                    0.0053 |         0.0367 |                 0.0367 |
| Chitinskelett |   29151 |      1908 |              1908 |          21 |                        88 |                    0.0007 |         0.0655 |                 0.0655 |
| Piscium       |    6656 |      3419 |              3419 |           5 |                       103 |                    0.0008 |         0.5137 |                 0.5137 |
| Reeve         |  112773 |     23194 |             23194 |        3812 |                      1011 |                    0.0338 |         0.2057 |                 0.2057 |
| Trudy         |  107740 |      3830 |              3830 |          41 |                       222 |                    0.0004 |         0.0355 |                 0.0355 |

## Damaged words per usable line (share)

| book          |     0 |     1 |   2-5 |    >5 |
|:--------------|------:|------:|------:|------:|
| Butler        | 0.675 | 0.231 | 0.092 | 0.002 |
| Chitinskelett | 0.556 | 0.263 | 0.169 | 0.011 |
| Piscium       | 0.03  | 0.103 | 0.713 | 0.154 |
| Reeve         | 0.415 | 0.241 | 0.327 | 0.017 |
| Trudy         | 0.783 | 0.164 | 0.052 | 0.001 |

Counts:

| book          |     0 |    1 |   2-5 |   >5 |   All |
|:--------------|------:|-----:|------:|-----:|------:|
| Butler        |  4310 | 1475 |   584 |   12 |  6381 |
| Chitinskelett |  1350 |  638 |   411 |   27 |  2426 |
| Piscium       |    29 |  100 |   691 |  149 |   969 |
| Reeve         |  7049 | 4097 |  5543 |  284 | 16973 |
| Trudy         | 10145 | 2119 |   673 |   18 | 12955 |
| All           | 22883 | 8429 |  7902 |  490 | 39704 |

## Heuristic flags (all lines)

| book          |   OCR merges words |   OCR splits words |   case-only words |   crosses OCR line break |   hyphen at line end |   missing text |   span length off |   special characters |
|:--------------|-------------------:|-------------------:|------------------:|-------------------------:|---------------------:|---------------:|------------------:|---------------------:|
| Butler        |                307 |                494 |               224 |                      129 |                  248 |            431 |               136 |                  230 |
| Chitinskelett |                 83 |                502 |                20 |                        5 |                  306 |             59 |                26 |                 1590 |
| Piscium       |                483 |                119 |                 6 |                        6 |                  441 |             89 |                36 |                 1016 |
| Reeve         |               1030 |               1166 |              2096 |                      179 |                 2553 |           1391 |               345 |                 4874 |
| Trudy         |               1331 |               1789 |                45 |                      535 |                 3067 |           2488 |               573 |                 6929 |

## Usable units per split

| book          |   dev |   intest |   train |   All |
|:--------------|------:|---------:|--------:|------:|
| Butler        |   607 |      571 |    5203 |  6381 |
| Chitinskelett |   314 |      383 |    1729 |  2426 |
| Piscium       |   209 |      156 |     604 |   969 |
| Reeve         |  1279 |     1578 |   14116 | 16973 |
| Trudy         |  1485 |     1062 |   10408 | 12955 |
| All           |  3894 |     3750 |   32060 | 39704 |

## Long s in *Piscium querelae*

40 of 60 pages contain ſ. The pages without it are blank pages, the title page, a modern bookplate and an all-caps dedication (capital S has no long form): the transcription uses ſ consistently. See `piscium_long_s.csv`.

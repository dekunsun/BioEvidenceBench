# Task B step 4: units, alignment and damage per book

Built by `src/rl_task_b_build.py` under Reward v1.2 rules (case-only words neutral, MUFI ligatures folded, references with U+FFFD or unidentified private-use characters invalid, lines with a mixed Latin/Cyrillic word or leader dots set aside) and split v2 (`../SPLIT_V2.md`). Cuvier (held-out book) not touched; the 38 excluded pages not used. Content pages that gave no line: 0 (none; `missing_pages.csv`).

**Coverage is not accuracy.** `usable` counts lines that passed the automatic checks; whether they are paired correctly is measured by the audits (`audit_round1/`, `audit_sample.csv`).

Unit files (not committed; regenerate with the script) and their SHA-256:

- `train.jsonl`: 31909 usable units, `d032f8d4a3129141…`
- `dev.jsonl`: 3787 usable units, `a072b28944e92b6b…`
- `intest.jsonl`: 3743 usable units, `3c502cc252db95b2…`

## Lines per book

| book          |   pages |   lines |   valid |   usable |   usable_share |   recoverable_deletion |
|:--------------|--------:|--------:|--------:|---------:|---------------:|-----------------------:|
| Butler        |     235 |    6975 |    6381 |     6380 |          0.915 |                      0 |
| Chitinskelett |      73 |    2498 |    2396 |     2392 |          0.958 |                      0 |
| Piscium       |      43 |    1153 |     970 |      968 |          0.84  |                      0 |
| Reeve         |     418 |   18532 |   16879 |    16878 |          0.911 |                      0 |
| Trudy         |     480 |   15925 |   12826 |    12821 |          0.805 |                      1 |

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
| reference typo, confirmed                                                                        |        1 |               1 |         1 |       0 |       5 |     8 |
| similarity                                                                                       |        9 |               1 |         1 |      61 |      42 |   114 |
| similarity + span ratio                                                                          |        2 |               0 |         0 |       8 |      11 |    21 |
| similarity + span ratio + unreadable character in reference                                      |        2 |               0 |         0 |       0 |       0 |     2 |
| similarity + unreadable character in reference                                                   |        6 |               0 |         0 |       7 |       1 |    14 |
| span ratio                                                                                       |        0 |               1 |         2 |       5 |      15 |    23 |
| unreadable character in reference                                                                |       13 |               6 |        91 |      14 |      30 |   154 |
| unrecoverable deletion (word not in OCR or context)                                              |        0 |              33 |         0 |      95 |     129 |   257 |
| All                                                                                              |      595 |             106 |       185 |    1654 |    3104 |  5644 |

## Similarity buckets (all lines; similarity ignores case)

| book          |   0.3-0.5 |   0.5-0.8 |   0.8-1.0 |   <0.3 |   no text |   All |
|:--------------|----------:|----------:|----------:|-------:|----------:|------:|
| Butler        |       115 |       482 |      6312 |     65 |         1 |  6975 |
| Chitinskelett |        17 |        81 |      2353 |     27 |        20 |  2498 |
| Piscium       |         9 |       167 |       911 |     37 |        29 |  1153 |
| Reeve         |       301 |      1775 |     15993 |    322 |       141 | 18532 |
| Trudy         |       808 |       746 |     13284 |   1060 |        27 | 15925 |
| All           |      1250 |      3251 |     38853 |   1511 |       218 | 45083 |

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
| Butler        |   80247 |      2897 |              2897 |         445 |                       120 |                    0.0055 |         0.0361 |                 0.0361 |
| Chitinskelett |   28879 |      1837 |              1837 |          17 |                        87 |                    0.0006 |         0.0636 |                 0.0636 |
| Piscium       |    6649 |      3416 |              3416 |           5 |                       103 |                    0.0008 |         0.5138 |                 0.5138 |
| Reeve         |  112325 |     22965 |             22965 |        3866 |                      1006 |                    0.0344 |         0.2045 |                 0.2045 |
| Trudy         |  106668 |      3590 |              3590 |          39 |                       206 |                    0.0004 |         0.0337 |                 0.0337 |

## Damaged words per usable line (share)

| book          |     0 |     1 |   2-5 |    >5 |
|:--------------|------:|------:|------:|------:|
| Butler        | 0.681 | 0.228 | 0.09  | 0.002 |
| Chitinskelett | 0.564 | 0.263 | 0.161 | 0.011 |
| Piscium       | 0.03  | 0.103 | 0.713 | 0.154 |
| Reeve         | 0.42  | 0.238 | 0.325 | 0.017 |
| Trudy         | 0.791 | 0.16  | 0.048 | 0.001 |

Counts:

| book          |     0 |    1 |   2-5 |   >5 |   All |
|:--------------|------:|-----:|------:|-----:|------:|
| Butler        |  4342 | 1452 |   574 |   12 |  6380 |
| Chitinskelett |  1350 |  629 |   386 |   27 |  2392 |
| Piscium       |    29 |  100 |   690 |  149 |   968 |
| Reeve         |  7087 | 4024 |  5484 |  283 | 16878 |
| Trudy         | 10145 | 2045 |   618 |   13 | 12821 |
| All           | 22953 | 8250 |  7752 |  484 | 39439 |

## Heuristic flags (all lines)

| book          |   OCR merges words |   OCR splits words |   case-only words |   crosses OCR line break |   hyphen at line end |   missing text |   recoverable deletion |   span length off |   special characters |
|:--------------|-------------------:|-------------------:|------------------:|-------------------------:|---------------------:|---------------:|-----------------------:|------------------:|---------------------:|
| Butler        |                307 |                494 |               225 |                      129 |                  248 |            431 |                      0 |               136 |                  230 |
| Chitinskelett |                 83 |                502 |                20 |                        5 |                  306 |             59 |                      0 |                26 |                 1590 |
| Piscium       |                483 |                119 |                 6 |                        6 |                  441 |             89 |                      0 |                36 |                 1016 |
| Reeve         |               1026 |               1167 |              2097 |                      179 |                 2553 |           1391 |                      0 |               345 |                 4874 |
| Trudy         |               1331 |               1789 |                45 |                      535 |                 3067 |           2488 |                      1 |               573 |                 6929 |

## Usable units per split

| book          |   dev |   intest |   train |   All |
|:--------------|------:|---------:|--------:|------:|
| Butler        |   606 |      571 |    5203 |  6380 |
| Chitinskelett |   293 |      383 |    1716 |  2392 |
| Piscium       |   208 |      156 |     604 |   968 |
| Reeve         |  1203 |     1574 |   14101 | 16878 |
| Trudy         |  1477 |     1059 |   10285 | 12821 |
| All           |  3787 |     3743 |   31909 | 39439 |

## Long s in *Piscium querelae*

40 of 60 pages contain ſ. The pages without it are blank pages, the title page, a modern bookplate and an all-caps dedication (capital S has no long form): the transcription uses ſ consistently. See `piscium_long_s.csv`.

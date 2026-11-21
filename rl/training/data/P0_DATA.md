# P0 data (module 7b, stage 3)

*Built by `rl/training/make_data_p0.py`, seed 20261121. Training lines from split v2 `train`, dev lines from `dev`; set-aside lines excluded by the build. Kinds: `name` = at least one damaged scientific-name word, `clean` = no damaged word, `other` = damaged, no damaged name word.*

Training blocks of 16 (one GRPO optimizer step each, read in order): 8 name, 3 clean, 5 other.

## Training mix

`rl/training/data/p0_train.jsonl`: 4800 lines, 3680 distinct, SHA-256 `0b2019742352ccae4f73fdb063b2e2b2f99835518fded90caee5589ec647d8af`

| book          |   clean |   name |   other |   All |
|:--------------|--------:|-------:|--------:|------:|
| Butler        |     169 |    203 |     173 |   545 |
| Chitinskelett |      38 |    129 |      89 |   256 |
| Piscium       |       1 |    140 |      68 |   209 |
| Reeve         |     295 |   1615 |     905 |  2815 |
| Trudy         |     397 |    313 |     265 |   975 |
| All           |     900 |   2400 |    1500 |  4800 |

Share by kind: name 50.0%, other 31.2%, clean 18.8%

## Dev evaluation set

`rl/training/data/p0_dev_eval.jsonl`: 500 lines, 500 distinct, SHA-256 `1ab3169dad3b708999e3970d3d2240f5bc96ed4f0837a4f89e41c4462e6f53be`

| book          |   clean |   name |   other |   All |
|:--------------|--------:|-------:|--------:|------:|
| Butler        |      71 |      0 |      29 |   100 |
| Chitinskelett |      55 |      3 |      42 |   100 |
| Piscium       |       0 |      9 |      91 |   100 |
| Reeve         |      37 |      1 |      62 |   100 |
| Trudy         |      78 |      0 |      22 |   100 |
| All           |     241 |     13 |     246 |   500 |

Share by kind: other 49.2%, clean 48.2%, name 2.6%

## Dev name lines

`rl/training/data/p0_dev_names.jsonl`: 85 lines, 85 distinct, SHA-256 `a2e4d03747d4748a18cdf1ccec417470d1c6b218db258d1ea7da0c0dea051cca`

| book          |   name |   All |
|:--------------|-------:|------:|
| Butler        |      6 |     6 |
| Chitinskelett |      4 |     4 |
| Piscium       |      8 |     8 |
| Reeve         |     56 |    56 |
| Trudy         |     11 |    11 |
| All           |     85 |    85 |

Share by kind: name 100.0%

# Locked test sets (module 7b, stage 4)

*Drawn once by `rl/training/make_test_p0.py`, seed 20261122, 2026-11-21, before any test line was scored. In-book: 100 per training book from split v2 `intest`, leaving out the 17 usable lines that the alignment audits displayed. Cuvier: 500 usable lines drawn uniformly. Rest: every other usable in-book test line. Context = nearest OCR line above / below on the same page.*

## p0_test_inbook

`rl/training/data/p0_test_inbook.jsonl`: 500 lines, 500 distinct, SHA-256 `49e97c1e6bcfc089c35fd88658377830b7afbbf4a8633357b7a617c8fe950cee`

| book          |   clean |   name |   other |   All |
|:--------------|--------:|-------:|--------:|------:|
| Butler        |      59 |      1 |      40 |   100 |
| Chitinskelett |      63 |      2 |      35 |   100 |
| Piscium       |       0 |      5 |      95 |   100 |
| Reeve         |      38 |     11 |      51 |   100 |
| Trudy         |      79 |      2 |      19 |   100 |
| All           |     239 |     21 |     240 |   500 |

Share by kind: other 48.0%, clean 47.8%, name 4.2%

## p0_test_cuvier

`rl/training/data/p0_test_cuvier.jsonl`: 500 lines, 500 distinct, SHA-256 `38395e1872681524e3abd212cc44d3baf85b0d6ab4020c38c749a3667c96e5b7`

| book   |   clean |   name |   other |   All |
|:-------|--------:|-------:|--------:|------:|
| Cuvier |     376 |      7 |     117 |   500 |
| All    |     376 |      7 |     117 |   500 |

Share by kind: clean 75.2%, other 23.4%, name 1.4%

## p0_test_inbook_rest

`rl/training/data/p0_test_inbook_rest.jsonl`: 3226 lines, 3226 distinct, SHA-256 `62a347ff2463b1731ad689bb5e3fc2b5e30b5235311c1ce3b1e070265c1f07c6`

| book          |   clean |   name |   other |   All |
|:--------------|--------:|-------:|--------:|------:|
| Butler        |     302 |      4 |     165 |   471 |
| Chitinskelett |     168 |     11 |     102 |   281 |
| Piscium       |       1 |      6 |      46 |    53 |
| Reeve         |     613 |     74 |     775 |  1462 |
| Trudy         |     786 |     27 |     146 |   959 |
| All           |    1870 |    122 |    1234 |  3226 |

Share by kind: clean 58.0%, other 38.3%, name 3.8%

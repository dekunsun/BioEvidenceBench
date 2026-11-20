# Task B split v2: by content pages

Rule and reasons: docstring of `src/rl_split_task_b_v2.py` (Gloria's decision, 2026-11-20). No model had been run on any task B page when the split was changed, and the rule reads only the expert transcription, so the change cannot pick pages by results. Cuvier is not read. `splits.csv` (v1) is kept unchanged. SHA-256 of `splits_v2.csv`: `8358ba28cb83259c505d2092dec906eb236edeefaf9bd32c85f917caca508365`.

## Pages per split, v1

| book          |   dev |   excluded |   heldout_book |   intest |   train |   All |
|:--------------|------:|-----------:|---------------:|---------:|--------:|------:|
| Butler        |    38 |         18 |              0 |       39 |     246 |   341 |
| Chitinskelett |    10 |          0 |              0 |       10 |      64 |    84 |
| Cuvier        |     0 |          0 |            516 |        0 |       0 |   516 |
| Piscium       |    10 |          0 |              0 |       10 |      40 |    60 |
| Reeve         |    59 |         20 |              0 |       58 |     511 |   648 |
| Trudy         |    50 |          0 |              0 |       50 |     416 |   516 |
| All           |   167 |         38 |            516 |      167 |    1277 |  2165 |

## Pages per split, v2

| book          |   dev |   excluded |   heldout_book |   intest |   no_text |   train |   All |
|:--------------|------:|-----------:|---------------:|---------:|----------:|--------:|------:|
| Butler        |    20 |         18 |              0 |       20 |        88 |     195 |   341 |
| Chitinskelett |    10 |          0 |              0 |       10 |        11 |      53 |    84 |
| Cuvier        |     0 |          0 |            516 |        0 |         0 |       0 |   516 |
| Piscium       |    10 |          0 |              0 |        8 |        17 |      25 |    60 |
| Reeve         |    38 |         20 |              0 |       40 |       210 |     340 |   648 |
| Trudy         |    50 |          0 |              0 |       50 |        36 |     380 |   516 |
| All           |   128 |         38 |            516 |      128 |       362 |     993 |  2165 |

## Pages that changed split (v1 → v2)

|                             |   dev |   intest |   no_text |   train |
|:----------------------------|------:|---------:|----------:|--------:|
| ('Butler', 'dev')           |     0 |        0 |         8 |      27 |
| ('Butler', 'intest')        |     0 |        0 |        16 |      23 |
| ('Butler', 'train')         |    17 |       20 |        64 |       0 |
| ('Chitinskelett', 'dev')    |     0 |        0 |         5 |       5 |
| ('Chitinskelett', 'intest') |     4 |        0 |         0 |       6 |
| ('Chitinskelett', 'train')  |     6 |       10 |         6 |       0 |
| ('Piscium', 'dev')          |     0 |        2 |         8 |       0 |
| ('Piscium', 'intest')       |     0 |        0 |         0 |       9 |
| ('Piscium', 'train')        |    10 |        5 |         9 |       0 |
| ('Reeve', 'dev')            |     0 |        4 |        16 |      30 |
| ('Reeve', 'intest')         |    10 |        0 |        19 |      29 |
| ('Reeve', 'train')          |    19 |       36 |       175 |       0 |
| ('Trudy', 'dev')            |     0 |       10 |         0 |      40 |
| ('Trudy', 'intest')         |     0 |        0 |         0 |      30 |
| ('Trudy', 'train')          |    50 |       20 |        36 |       0 |

784 of 2165 pages changed split. Line counts per split are in `build/STATS.md`.
